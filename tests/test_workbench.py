# SPDX-FileCopyrightText: 2026 Marcus Baw and Baw Medical Ltd
# SPDX-License-Identifier: AGPL-3.0-or-later

from __future__ import annotations

from pathlib import Path

import pytest

from sct_marimo import (
    AdapterInputError,
    DiffMembership,
    QueryRequest,
    TerminologyAdapter,
    compare_concept_sets,
    inspect_comparison_concept,
)

REQUEST = QueryRequest(
    candidate_expression="<<73211009",
    reference_expression="22298006 OR 46635009",
)


def test_exact_diff_is_display_bounded_without_losing_full_counts(
    synthetic_database: Path,
) -> None:
    with TerminologyAdapter.open(synthetic_database) as terminology:
        result = compare_concept_sets(terminology, REQUEST, display_limit=1)

    assert result.exact_diff.added_ids == ("44054006", "73211009")
    assert result.exact_diff.removed_ids == ("22298006",)
    assert result.exact_diff.unchanged_ids == ("46635009",)
    assert result.added.total_count == 2
    assert result.added.returned_count == 1
    assert result.added.omitted_count == 1
    assert result.added.truncated
    assert [row.membership for row in result.rows] == [
        DiffMembership.ADDED,
        DiffMembership.REMOVED,
        DiffMembership.UNCHANGED,
    ]
    assert [row.concept.id for row in result.rows] == [
        "44054006",
        "22298006",
        "46635009",
    ]
    assert result.invocations[0].method == "sct_py.Snomed.expand"
    assert result.invocations[0].expression == REQUEST.candidate_expression
    assert result.invocations[0].content_fingerprint == result.release.content_fingerprint


def test_draft_edits_mark_a_result_stale_without_changing_it(
    synthetic_database: Path,
) -> None:
    with TerminologyAdapter.open(synthetic_database) as terminology:
        result = compare_concept_sets(terminology, REQUEST)

    assert not result.is_stale(REQUEST)
    assert result.is_stale(
        QueryRequest(
            candidate_expression="<73211009",
            reference_expression=REQUEST.reference_expression,
        )
    )
    assert result.candidate.expression == REQUEST.candidate_expression


def test_display_limit_is_validated_before_expansion(synthetic_database: Path) -> None:
    with (
        TerminologyAdapter.open(synthetic_database) as terminology,
        pytest.raises(AdapterInputError, match="display limit"),
    ):
        compare_concept_sets(terminology, REQUEST, display_limit=0)


def test_inspector_preserves_membership_and_hierarchy_limits(
    synthetic_database: Path,
) -> None:
    with TerminologyAdapter.open(synthetic_database) as terminology:
        result = compare_concept_sets(terminology, REQUEST)
        inspection = inspect_comparison_concept(
            terminology,
            result,
            "73211009",
            child_limit=1,
        )

    assert inspection.concept.preferred_term == "Diabetes mellitus"
    assert inspection.in_candidate
    assert not inspection.in_reference
    assert [parent.id for parent in inspection.parents] == ["404684003"]
    assert [child.id for child in inspection.children.children] == ["46635009"]
    assert inspection.children.total_count == 2
    assert inspection.children.returned_count == 1
    assert inspection.children.truncated


def test_inspector_rejects_concepts_outside_the_compared_sets(
    synthetic_database: Path,
) -> None:
    with TerminologyAdapter.open(synthetic_database) as terminology:
        result = compare_concept_sets(terminology, REQUEST)
        with pytest.raises(AdapterInputError, match="not in the compared sets"):
            inspect_comparison_concept(terminology, result, "404684003")
