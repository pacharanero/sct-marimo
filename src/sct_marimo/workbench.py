# SPDX-FileCopyrightText: 2026 Marcus Baw and Baw Medical Ltd
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Pure application logic for comparing and inspecting terminology concept sets."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from sct_marimo.adapter import TerminologyAdapter
from sct_marimo.models import (
    AdapterContractError,
    AdapterInputError,
    Concept,
    ConceptSet,
    HierarchyPage,
    Provenance,
)


class DiffMembership(str, Enum):
    """How a concept participates in an exact candidate/reference comparison."""

    ADDED = "added"
    REMOVED = "removed"
    UNCHANGED = "unchanged"


@dataclass(frozen=True, slots=True)
class QueryRequest:
    candidate_expression: str
    reference_expression: str


@dataclass(frozen=True, slots=True)
class ExactSetDiff:
    added_ids: tuple[str, ...]
    removed_ids: tuple[str, ...]
    unchanged_ids: tuple[str, ...]

    @classmethod
    def between(cls, candidate: ConceptSet, reference: ConceptSet) -> ExactSetDiff:
        candidate_ids = set(candidate.ids)
        reference_ids = set(reference.ids)
        return cls(
            added_ids=tuple(sorted(candidate_ids - reference_ids, key=int)),
            removed_ids=tuple(sorted(reference_ids - candidate_ids, key=int)),
            unchanged_ids=tuple(sorted(candidate_ids & reference_ids, key=int)),
        )


@dataclass(frozen=True, slots=True)
class DiffRow:
    membership: DiffMembership
    concept: Concept


@dataclass(frozen=True, slots=True)
class DiffSection:
    membership: DiffMembership
    exact_ids: tuple[str, ...]
    rows: tuple[DiffRow, ...]
    display_limit: int

    @property
    def total_count(self) -> int:
        return len(self.exact_ids)

    @property
    def returned_count(self) -> int:
        return len(self.rows)

    @property
    def omitted_count(self) -> int:
        return self.total_count - self.returned_count

    @property
    def truncated(self) -> bool:
        return self.omitted_count > 0


@dataclass(frozen=True, slots=True)
class SdkInvocation:
    """A reproducible structured record of one semantic SDK call."""

    method: str
    expression: str
    sct_py_version: str
    content_fingerprint: str | None


@dataclass(frozen=True, slots=True)
class ComparisonResult:
    request: QueryRequest
    candidate: ConceptSet
    reference: ConceptSet
    exact_diff: ExactSetDiff
    added: DiffSection
    removed: DiffSection
    unchanged: DiffSection
    invocations: tuple[SdkInvocation, ...]

    @property
    def release(self) -> Provenance:
        return self.candidate.release

    @property
    def rows(self) -> tuple[DiffRow, ...]:
        return self.added.rows + self.removed.rows + self.unchanged.rows

    def is_stale(self, draft: QueryRequest) -> bool:
        return draft != self.request


@dataclass(frozen=True, slots=True)
class ConceptInspection:
    release: Provenance
    concept: Concept
    parents: tuple[Concept, ...]
    children: HierarchyPage
    in_candidate: bool
    in_reference: bool


def _display_limit(value: int) -> int:
    if type(value) is not int or not 1 <= value <= 1_000:
        raise AdapterInputError("display limit must be an integer between 1 and 1000")
    return value


def _section(
    membership: DiffMembership,
    exact_ids: tuple[str, ...],
    concepts: dict[str, Concept],
    display_limit: int,
) -> DiffSection:
    visible_ids = exact_ids[:display_limit]
    return DiffSection(
        membership=membership,
        exact_ids=exact_ids,
        rows=tuple(DiffRow(membership, concepts[identifier]) for identifier in visible_ids),
        display_limit=display_limit,
    )


def compare_concept_sets(
    terminology: TerminologyAdapter,
    request: QueryRequest,
    *,
    display_limit: int = 25,
) -> ComparisonResult:
    """Expand two ECL expressions and build a bounded view of their exact set diff."""

    checked_limit = _display_limit(display_limit)
    candidate = terminology.expand(request.candidate_expression)
    reference = terminology.expand(request.reference_expression)
    if candidate.release != reference.release:
        raise AdapterContractError("concept sets were expanded against different releases")

    exact_diff = ExactSetDiff.between(candidate, reference)
    visible_ids = (
        exact_diff.added_ids[:checked_limit]
        + exact_diff.removed_ids[:checked_limit]
        + exact_diff.unchanged_ids[:checked_limit]
    )
    resolved = terminology.concepts(list(visible_ids)) if visible_ids else ()
    if any(concept is None for concept in resolved):
        raise AdapterContractError("an expanded concept is absent from the loaded database")
    concepts = {
        identifier: concept
        for identifier, concept in zip(visible_ids, resolved, strict=True)
        if concept is not None
    }

    fingerprint = candidate.release.content_fingerprint
    return ComparisonResult(
        request=request,
        candidate=candidate,
        reference=reference,
        exact_diff=exact_diff,
        added=_section(DiffMembership.ADDED, exact_diff.added_ids, concepts, checked_limit),
        removed=_section(DiffMembership.REMOVED, exact_diff.removed_ids, concepts, checked_limit),
        unchanged=_section(
            DiffMembership.UNCHANGED,
            exact_diff.unchanged_ids,
            concepts,
            checked_limit,
        ),
        invocations=(
            SdkInvocation(
                method="sct_py.Snomed.expand",
                expression=request.candidate_expression,
                sct_py_version=candidate.sct_py_version,
                content_fingerprint=fingerprint,
            ),
            SdkInvocation(
                method="sct_py.Snomed.expand",
                expression=request.reference_expression,
                sct_py_version=reference.sct_py_version,
                content_fingerprint=fingerprint,
            ),
        ),
    )


def inspect_comparison_concept(
    terminology: TerminologyAdapter,
    comparison: ComparisonResult,
    concept_id: str,
    *,
    child_limit: int = 25,
) -> ConceptInspection:
    """Load one selected concept without overstating hierarchy or release evidence."""

    if terminology.release != comparison.release:
        raise AdapterContractError("the selected terminology release changed after comparison")
    all_ids = set(comparison.candidate.ids) | set(comparison.reference.ids)
    if concept_id not in all_ids:
        raise AdapterInputError("the selected concept is not in the compared sets")
    concept = terminology.concept(concept_id)
    if concept is None:
        raise AdapterContractError("the selected concept is absent from the loaded database")
    return ConceptInspection(
        release=terminology.release,
        concept=concept,
        parents=terminology.direct_parents(concept_id),
        children=terminology.direct_children(concept_id, limit=child_limit),
        in_candidate=concept_id in comparison.candidate.ids,
        in_reference=concept_id in comparison.reference.ids,
    )
