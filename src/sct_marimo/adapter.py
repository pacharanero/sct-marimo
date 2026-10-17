# SPDX-FileCopyrightText: 2026 Marcus Baw and Baw Medical Ltd
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Fail-closed typed adapter over the synchronous ``sct-py`` session."""

from __future__ import annotations

from collections.abc import Callable
from importlib.metadata import PackageNotFoundError, version
from os import PathLike
from typing import Any, Protocol, TypeVar, cast

from sct_py import SctError, Snomed

from sct_marimo.models import (
    AdapterContractError,
    AdapterInputError,
    AdapterQueryError,
    Concept,
    ConceptSet,
    ConceptSummary,
    HierarchyPage,
    Provenance,
    SearchHit,
)

T = TypeVar("T")


class SnomedSession(Protocol):
    @property
    def closed(self) -> bool: ...

    def close(self) -> None: ...

    def provenance(self) -> dict[str, Any] | None: ...

    def concept(self, concept_id: str) -> dict[str, Any] | None: ...

    def concepts(self, concept_ids: list[str]) -> list[dict[str, Any] | None]: ...

    def search(
        self,
        query: str,
        limit: int = 20,
        *,
        hierarchy: str | None = None,
        literal: bool = False,
    ) -> list[dict[str, Any]]: ...

    def expand(self, expression: str) -> list[str]: ...

    def children(self, concept_id: str, limit: int = 100) -> list[dict[str, Any]]: ...


def _identifier(value: str) -> str:
    if (
        not value.isascii()
        or not value.isdigit()
        or not 6 <= len(value) <= 18
        or value.startswith("0")
    ):
        raise AdapterInputError("concept identifier must be 6-18 digits without a leading zero")
    return value


def _limit(value: int) -> int:
    if type(value) is not int or not 1 <= value <= 4_294_967_295:
        raise AdapterInputError("limit must be an integer between 1 and 4294967295")
    return value


class TerminologyAdapter:
    """Own one serial, read-only terminology session for one query worker."""

    def __init__(self, session: SnomedSession, *, sct_py_version: str) -> None:
        self._session = session
        raw_provenance = self._query("read provenance", session.provenance)
        if raw_provenance is None:
            raise AdapterContractError("the terminology database has no recorded provenance")
        self._release = Provenance.from_value(raw_provenance)
        self._sct_py_version = sct_py_version

    @classmethod
    def open(cls, path: str | PathLike[str]) -> TerminologyAdapter:
        try:
            session = cast(SnomedSession, Snomed(path))
        except SctError:
            raise AdapterQueryError("open terminology database") from None
        try:
            package_version = version("sct-py")
        except PackageNotFoundError:
            session.close()
            raise AdapterContractError("the installed sct-py distribution has no version") from None
        try:
            return cls(session, sct_py_version=package_version)
        except Exception:
            session.close()
            raise

    @property
    def release(self) -> Provenance:
        return self._release

    @property
    def closed(self) -> bool:
        return self._session.closed

    def close(self) -> None:
        self._session.close()

    def __enter__(self) -> TerminologyAdapter:
        if self.closed:
            raise AdapterQueryError("enter closed terminology session")
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        self.close()

    def concept(self, concept_id: str) -> Concept | None:
        identifier = _identifier(concept_id)
        raw = self._query("look up concept", lambda: self._session.concept(identifier))
        if raw is None:
            return None
        result = Concept.from_value(raw, history_evidence=self.release.history_evidence)
        if result.id != identifier:
            raise AdapterContractError("concept lookup returned a different identifier")
        return result

    def concepts(self, concept_ids: list[str]) -> tuple[Concept | None, ...]:
        identifiers = [_identifier(identifier) for identifier in concept_ids]
        raw = self._query("look up concepts", lambda: self._session.concepts(identifiers))
        if len(raw) != len(identifiers):
            raise AdapterContractError("concept batch must preserve input cardinality")
        results = tuple(
            None
            if item is None
            else Concept.from_value(
                item,
                history_evidence=self.release.history_evidence,
                path=f"concepts[{index}]",
            )
            for index, item in enumerate(raw)
        )
        for expected, result in zip(identifiers, results, strict=True):
            if result is not None and result.id != expected:
                raise AdapterContractError("concept batch did not preserve input order")
        return results

    def search(
        self,
        query: str,
        *,
        limit: int = 20,
        hierarchy: str | None = None,
    ) -> tuple[SearchHit, ...]:
        if not query.strip():
            raise AdapterInputError("search query must not be empty")
        checked_limit = _limit(limit)
        if hierarchy is not None and not hierarchy.strip():
            raise AdapterInputError("hierarchy must be non-empty when provided")
        raw = self._query(
            "search concepts",
            lambda: self._session.search(
                query,
                checked_limit,
                hierarchy=hierarchy,
                literal=True,
            ),
        )
        return tuple(
            SearchHit.from_value(item, f"search_hits[{index}]") for index, item in enumerate(raw)
        )

    def expand(self, expression: str) -> ConceptSet:
        if not expression.strip():
            raise AdapterInputError("ECL expression must not be empty")
        raw = self._query("expand ECL", lambda: self._session.expand(expression))
        return ConceptSet.from_value(
            expression=expression,
            value=raw,
            release=self.release,
            sct_py_version=self._sct_py_version,
        )

    def direct_parents(self, concept_id: str) -> tuple[Concept, ...]:
        focus = self.concept(concept_id)
        if focus is None:
            raise AdapterInputError("concept was not found")
        parent_ids = [parent.id for parent in focus.parents]
        if not parent_ids:
            return ()
        parents = self.concepts(parent_ids)
        if any(parent is None for parent in parents):
            raise AdapterContractError("a direct parent is absent from the loaded database")
        return cast(tuple[Concept, ...], parents)

    def direct_children(self, concept_id: str, *, limit: int = 100) -> HierarchyPage:
        focus = self.concept(concept_id)
        if focus is None:
            raise AdapterInputError("concept was not found")
        checked_limit = _limit(limit)
        raw = self._query(
            "load direct children",
            lambda: self._session.children(focus.id, checked_limit),
        )
        children = tuple(
            ConceptSummary.from_value(item, f"children[{index}]") for index, item in enumerate(raw)
        )
        if len({child.id for child in children}) != len(children):
            raise AdapterContractError("direct children must have unique identifiers")
        expected_count = min(checked_limit, focus.children_count)
        if len(children) != expected_count:
            raise AdapterContractError("direct children did not match the expected page size")
        return HierarchyPage(
            focus=focus,
            children=children,
            total_count=focus.children_count,
            limit=checked_limit,
            truncated=len(children) < focus.children_count,
        )

    @staticmethod
    def _query(operation: str, call: Callable[[], T]) -> T:
        try:
            return call()
        except (SctError, RuntimeError):
            raise AdapterQueryError(operation) from None
