# SPDX-FileCopyrightText: 2026 Marcus Baw and Baw Medical Ltd
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Strict immutable models for the untyped dictionaries returned by ``sct-py``."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from typing import cast


class AdapterError(Exception):
    """Base error for the workbench terminology boundary."""


class AdapterInputError(AdapterError):
    """Caller input is invalid for the adapter contract."""


class AdapterQueryError(AdapterError):
    """The terminology engine rejected or could not complete an operation."""

    def __init__(self, operation: str) -> None:
        self.operation = operation
        super().__init__(f"{operation} failed at the terminology boundary")


class AdapterContractError(AdapterError):
    """The installed ``sct-py`` result does not match the pinned contract."""


class EvidenceAvailability(str, Enum):
    """Whether the loaded artefact declares evidence for an optional field family."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


def _mapping(value: object, path: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise AdapterContractError(f"{path} must be an object with string keys")
    return cast(Mapping[str, object], value)


def _list(value: object, path: str) -> list[object]:
    if not isinstance(value, list):
        raise AdapterContractError(f"{path} must be a list")
    return cast(list[object], value)


def _exact_keys(
    value: Mapping[str, object],
    path: str,
    required: set[str],
    optional: set[str] | None = None,
) -> None:
    allowed = required | (optional or set())
    missing = sorted(required - value.keys())
    unexpected = sorted(value.keys() - allowed)
    if missing:
        raise AdapterContractError(f"{path} is missing fields: {', '.join(missing)}")
    if unexpected:
        raise AdapterContractError(f"{path} has unexpected fields: {', '.join(unexpected)}")


def _string(value: object, path: str) -> str:
    if not isinstance(value, str):
        raise AdapterContractError(f"{path} must be a string")
    return value


def _optional_string(value: object, path: str) -> str | None:
    if value is None:
        return None
    return _string(value, path)


def _identifier(value: object, path: str) -> str:
    identifier = _string(value, path)
    if (
        not identifier.isascii()
        or not identifier.isdigit()
        or not 6 <= len(identifier) <= 18
        or identifier.startswith("0")
    ):
        raise AdapterContractError(f"{path} must be a 6-18 digit identifier without a leading zero")
    return identifier


def _integer(value: object, path: str) -> int:
    if type(value) is not int:
        raise AdapterContractError(f"{path} must be an integer")
    return value


def _nonnegative_integer(value: object, path: str) -> int:
    result = _integer(value, path)
    if result < 0:
        raise AdapterContractError(f"{path} must not be negative")
    return result


def _boolean(value: object, path: str) -> bool:
    if type(value) is not bool:
        raise AdapterContractError(f"{path} must be a boolean")
    return value


def _strings(value: object, path: str) -> tuple[str, ...]:
    return tuple(_string(item, f"{path}[{index}]") for index, item in enumerate(_list(value, path)))


def _source_name(value: str) -> str:
    name = value.replace("\\", "/").rstrip("/").rsplit("/", 1)[-1]
    if name.lower().endswith(".zip"):
        return name[:-4]
    return name


@dataclass(frozen=True, slots=True)
class CompanionArtifact:
    kind: str
    schema_version: int
    record_count: int
    content_fingerprint: str

    @classmethod
    def from_value(cls, value: object, path: str) -> CompanionArtifact:
        data = _mapping(value, path)
        _exact_keys(
            data,
            path,
            {"kind", "schema_version", "record_count", "content_fingerprint"},
        )
        return cls(
            kind=_string(data["kind"], f"{path}.kind"),
            schema_version=_nonnegative_integer(data["schema_version"], f"{path}.schema_version"),
            record_count=_nonnegative_integer(data["record_count"], f"{path}.record_count"),
            content_fingerprint=_string(data["content_fingerprint"], f"{path}.content_fingerprint"),
        )


@dataclass(frozen=True, slots=True)
class Provenance:
    """Export-safe provenance with sensitive source paths deliberately discarded."""

    record_type: str
    edition_label: str
    release_date: str
    release_id: str
    sct_version: str
    created_at: str
    content_fingerprint: str | None
    companions: tuple[CompanionArtifact, ...]

    @classmethod
    def from_value(cls, value: object) -> Provenance:
        path = "provenance"
        data = _mapping(value, path)
        _exact_keys(
            data,
            path,
            {
                "_type",
                "edition_label",
                "release_date",
                "release_id",
                "source_paths",
                "sct_version",
                "created_at",
            },
            {"content_fingerprint", "companions"},
        )
        source_names = {
            _source_name(source_path)
            for source_path in _strings(data["source_paths"], f"{path}.source_paths")
        }
        companion_values = _list(data.get("companions", []), f"{path}.companions")
        companions = tuple(
            CompanionArtifact.from_value(item, f"{path}.companions[{index}]")
            for index, item in enumerate(companion_values)
        )
        content_fingerprint = (
            _string(data["content_fingerprint"], f"{path}.content_fingerprint")
            if "content_fingerprint" in data
            else None
        )
        record_type = _string(data["_type"], f"{path}._type")
        if record_type != "sct_provenance":
            raise AdapterContractError(f"{path}._type must be sct_provenance")
        edition_label = _string(data["edition_label"], f"{path}.edition_label")
        release_id = _string(data["release_id"], f"{path}.release_id")
        if release_id and release_id == edition_label and release_id in source_names:
            edition_label = "Unrecognised local edition"
            release_id = ""
        return cls(
            record_type=record_type,
            edition_label=edition_label,
            release_date=_string(data["release_date"], f"{path}.release_date"),
            release_id=release_id,
            sct_version=_string(data["sct_version"], f"{path}.sct_version"),
            created_at=_string(data["created_at"], f"{path}.created_at"),
            content_fingerprint=content_fingerprint,
            companions=companions,
        )

    @property
    def history_evidence(self) -> EvidenceAvailability:
        if any(companion.kind == "history" for companion in self.companions):
            return EvidenceAvailability.AVAILABLE
        return EvidenceAvailability.UNAVAILABLE


@dataclass(frozen=True, slots=True)
class ConceptRef:
    id: str
    fsn: str

    @classmethod
    def from_value(cls, value: object, path: str) -> ConceptRef:
        data = _mapping(value, path)
        _exact_keys(data, path, {"id", "fsn"})
        return cls(
            id=_identifier(data["id"], f"{path}.id"),
            fsn=_string(data["fsn"], f"{path}.fsn"),
        )


@dataclass(frozen=True, slots=True)
class RefsetMembership:
    id: str
    preferred_term: str

    @classmethod
    def from_value(cls, value: object, path: str) -> RefsetMembership:
        data = _mapping(value, path)
        _exact_keys(data, path, {"id", "preferred_term"})
        return cls(
            id=_identifier(data["id"], f"{path}.id"),
            preferred_term=_string(data["preferred_term"], f"{path}.preferred_term"),
        )


@dataclass(frozen=True, slots=True)
class InactivationReason:
    id: str
    label: str

    @classmethod
    def from_value(cls, value: object, path: str) -> InactivationReason:
        data = _mapping(value, path)
        _exact_keys(data, path, {"id", "label"})
        return cls(
            id=_identifier(data["id"], f"{path}.id"),
            label=_string(data["label"], f"{path}.label"),
        )


@dataclass(frozen=True, slots=True)
class HistoricalAssociation:
    source: str
    association: str
    target: str
    target_display: str | None

    @classmethod
    def from_value(cls, value: object, path: str) -> HistoricalAssociation:
        data = _mapping(value, path)
        _exact_keys(data, path, {"source", "association", "target", "target_display"})
        return cls(
            source=_identifier(data["source"], f"{path}.source"),
            association=_string(data["association"], f"{path}.association"),
            target=_identifier(data["target"], f"{path}.target"),
            target_display=_optional_string(data["target_display"], f"{path}.target_display"),
        )


@dataclass(frozen=True, slots=True)
class DisplayAttribute:
    """A display-oriented flattened attribute, not a role-group-preserving definition."""

    label: str
    values: tuple[ConceptRef, ...]


@dataclass(frozen=True, slots=True)
class Concept:
    id: str
    fsn: str
    preferred_term: str
    synonyms: tuple[str, ...]
    hierarchy: str
    representative_hierarchy_path: tuple[str, ...]
    parents: tuple[ConceptRef, ...]
    children_count: int
    display_attributes: tuple[DisplayAttribute, ...]
    active: bool
    definition_status: str
    module: str
    effective_time: str
    ctv3_codes: tuple[str, ...]
    read2_codes: tuple[str, ...]
    member_of: tuple[RefsetMembership, ...]
    inactivation_reason: InactivationReason | None
    historical_associations: tuple[HistoricalAssociation, ...]
    history_evidence: EvidenceAvailability

    @classmethod
    def from_value(
        cls,
        value: object,
        *,
        history_evidence: EvidenceAvailability,
        path: str = "concept",
    ) -> Concept:
        data = _mapping(value, path)
        _exact_keys(
            data,
            path,
            {
                "id",
                "fsn",
                "preferred_term",
                "synonyms",
                "hierarchy",
                "hierarchy_path",
                "parents",
                "children_count",
                "attributes",
                "active",
                "definition_status",
                "module",
                "effective_time",
                "ctv3_codes",
                "read2_codes",
                "member_of",
                "inactivation_reason",
                "historical_associations",
            },
        )
        parents = tuple(
            ConceptRef.from_value(item, f"{path}.parents[{index}]")
            for index, item in enumerate(_list(data["parents"], f"{path}.parents"))
        )
        attributes = _mapping(data["attributes"], f"{path}.attributes")
        display_attributes = tuple(
            DisplayAttribute(
                label=label,
                values=tuple(
                    ConceptRef.from_value(item, f"{path}.attributes.{label}[{index}]")
                    for index, item in enumerate(
                        _list(attributes[label], f"{path}.attributes.{label}")
                    )
                ),
            )
            for label in sorted(attributes)
        )
        memberships = tuple(
            RefsetMembership.from_value(item, f"{path}.member_of[{index}]")
            for index, item in enumerate(_list(data["member_of"], f"{path}.member_of"))
        )
        associations = tuple(
            HistoricalAssociation.from_value(item, f"{path}.historical_associations[{index}]")
            for index, item in enumerate(
                _list(data["historical_associations"], f"{path}.historical_associations")
            )
        )
        reason_value = data["inactivation_reason"]
        reason = (
            None
            if reason_value is None
            else InactivationReason.from_value(reason_value, f"{path}.inactivation_reason")
        )
        return cls(
            id=_identifier(data["id"], f"{path}.id"),
            fsn=_string(data["fsn"], f"{path}.fsn"),
            preferred_term=_string(data["preferred_term"], f"{path}.preferred_term"),
            synonyms=_strings(data["synonyms"], f"{path}.synonyms"),
            hierarchy=_string(data["hierarchy"], f"{path}.hierarchy"),
            representative_hierarchy_path=_strings(
                data["hierarchy_path"], f"{path}.hierarchy_path"
            ),
            parents=parents,
            children_count=_nonnegative_integer(data["children_count"], f"{path}.children_count"),
            display_attributes=display_attributes,
            active=_boolean(data["active"], f"{path}.active"),
            definition_status=_string(data["definition_status"], f"{path}.definition_status"),
            module=_identifier(data["module"], f"{path}.module"),
            effective_time=_string(data["effective_time"], f"{path}.effective_time"),
            ctv3_codes=_strings(data["ctv3_codes"], f"{path}.ctv3_codes"),
            read2_codes=_strings(data["read2_codes"], f"{path}.read2_codes"),
            member_of=memberships,
            inactivation_reason=reason,
            historical_associations=associations,
            history_evidence=history_evidence,
        )


@dataclass(frozen=True, slots=True)
class SearchHit:
    id: str
    preferred_term: str
    fsn: str
    hierarchy: str
    active: bool

    @classmethod
    def from_value(cls, value: object, path: str = "search_hit") -> SearchHit:
        data = _mapping(value, path)
        _exact_keys(data, path, {"id", "preferred_term", "fsn", "hierarchy", "active"})
        return cls(
            id=_identifier(data["id"], f"{path}.id"),
            preferred_term=_string(data["preferred_term"], f"{path}.preferred_term"),
            fsn=_string(data["fsn"], f"{path}.fsn"),
            hierarchy=_string(data["hierarchy"], f"{path}.hierarchy"),
            active=_boolean(data["active"], f"{path}.active"),
        )


@dataclass(frozen=True, slots=True)
class ConceptSummary:
    id: str
    preferred_term: str
    fsn: str
    active: bool

    @classmethod
    def from_value(cls, value: object, path: str) -> ConceptSummary:
        data = _mapping(value, path)
        _exact_keys(data, path, {"id", "preferred_term", "fsn", "active"})
        return cls(
            id=_identifier(data["id"], f"{path}.id"),
            preferred_term=_string(data["preferred_term"], f"{path}.preferred_term"),
            fsn=_string(data["fsn"], f"{path}.fsn"),
            active=_boolean(data["active"], f"{path}.active"),
        )


@dataclass(frozen=True, slots=True)
class ConceptSet:
    expression: str
    ids: tuple[str, ...]
    release: Provenance
    sct_py_version: str
    result_sha256: str
    fully_materialized: bool = True

    @classmethod
    def from_value(
        cls,
        *,
        expression: str,
        value: object,
        release: Provenance,
        sct_py_version: str,
    ) -> ConceptSet:
        identifiers = tuple(
            _identifier(item, f"concept_set.ids[{index}]")
            for index, item in enumerate(_list(value, "concept_set.ids"))
        )
        if len(set(identifiers)) != len(identifiers):
            raise AdapterContractError("concept_set.ids must not contain duplicates")
        if identifiers != tuple(sorted(identifiers, key=int)):
            raise AdapterContractError("concept_set.ids must be sorted by numeric identifier")
        digest_input = "".join(f"{identifier}\n" for identifier in identifiers).encode()
        return cls(
            expression=expression,
            ids=identifiers,
            release=release,
            sct_py_version=sct_py_version,
            result_sha256=sha256(digest_input).hexdigest(),
        )


@dataclass(frozen=True, slots=True)
class HierarchyPage:
    focus: Concept
    children: tuple[ConceptSummary, ...]
    total_count: int
    limit: int
    truncated: bool

    @property
    def returned_count(self) -> int:
        return len(self.children)
