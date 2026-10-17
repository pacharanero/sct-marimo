# SPDX-FileCopyrightText: 2026 Marcus Baw and Baw Medical Ltd
# SPDX-License-Identifier: AGPL-3.0-or-later

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from sct_marimo import (
    AdapterContractError,
    AdapterInputError,
    AdapterQueryError,
    EvidenceAvailability,
    TerminologyAdapter,
)


def provenance(*, history: bool = False) -> dict[str, Any]:
    companions: list[dict[str, object]] = []
    if history:
        companions.append(
            {
                "kind": "history",
                "schema_version": 1,
                "record_count": 0,
                "content_fingerprint": "sha256:empty-history",
            }
        )
    return {
        "_type": "sct_provenance",
        "edition_label": "Synthetic edition",
        "release_date": "2026-01-01",
        "release_id": "synthetic-20260101",
        "content_fingerprint": "sha256:synthetic-content",
        "companions": companions,
        "source_paths": ["/private/licensed/release.zip"],
        "sct_version": "0.29.0",
        "created_at": "2026-01-02T03:04:05Z",
    }


def concept(
    concept_id: str = "22298006",
    *,
    parent_ids: tuple[str, ...] = ("404684003",),
    children_count: int = 0,
) -> dict[str, Any]:
    return {
        "id": concept_id,
        "fsn": "Myocardial infarction (disorder)",
        "preferred_term": "Myocardial infarction",
        "synonyms": ["Heart attack"],
        "hierarchy": "Clinical finding",
        "hierarchy_path": ["Clinical finding", "Disease"],
        "parents": [
            {"id": parent_id, "fsn": "Clinical finding (finding)"} for parent_id in parent_ids
        ],
        "children_count": children_count,
        "attributes": {
            "Finding site": [{"id": "80891009", "fsn": "Heart structure (body structure)"}]
        },
        "active": True,
        "definition_status": "Fully defined",
        "module": "900000000000207008",
        "effective_time": "20260101",
        "ctv3_codes": ["X200"],
        "read2_codes": [],
        "member_of": [{"id": "991381000000107", "preferred_term": "Synthetic reference set"}],
        "inactivation_reason": None,
        "historical_associations": [],
    }


def summary(concept_id: str) -> dict[str, Any]:
    return {
        "id": concept_id,
        "preferred_term": f"Concept {concept_id}",
        "fsn": f"Concept {concept_id} (finding)",
        "active": True,
    }


def search_hit(concept_id: str = "22298006") -> dict[str, Any]:
    return {
        "id": concept_id,
        "preferred_term": "Myocardial infarction",
        "fsn": "Myocardial infarction (disorder)",
        "hierarchy": "Clinical finding",
        "active": True,
    }


class FakeSession:
    def __init__(self, *, has_history: bool = False) -> None:
        self.closed = False
        self.provenance_result: dict[str, Any] | None = provenance(history=has_history)
        self.concept_results: dict[str, dict[str, Any] | None] = {
            "22298006": concept(children_count=2),
            "404684003": concept("404684003", parent_ids=()),
        }
        self.search_result: list[dict[str, Any]] = [search_hit()]
        self.expand_result = ["44054006", "46635009", "73211009"]
        self.children_result = [summary("44054006")]
        self.search_call: tuple[str, int, str | None, bool] | None = None
        self.failure: RuntimeError | None = None

    def close(self) -> None:
        self.closed = True

    def provenance(self) -> dict[str, Any] | None:
        return deepcopy(self.provenance_result)

    def concept(self, concept_id: str) -> dict[str, Any] | None:
        if self.failure is not None:
            raise self.failure
        return deepcopy(self.concept_results.get(concept_id))

    def concepts(self, concept_ids: list[str]) -> list[dict[str, Any] | None]:
        return [deepcopy(self.concept_results.get(concept_id)) for concept_id in concept_ids]

    def search(
        self,
        query: str,
        limit: int = 20,
        *,
        hierarchy: str | None = None,
        literal: bool = False,
    ) -> list[dict[str, Any]]:
        self.search_call = (query, limit, hierarchy, literal)
        return deepcopy(self.search_result)

    def expand(self, expression: str) -> list[str]:
        return list(self.expand_result)

    def children(self, concept_id: str, limit: int = 100) -> list[dict[str, Any]]:
        return deepcopy(self.children_result[:limit])


def adapter(session: FakeSession | None = None) -> TerminologyAdapter:
    return TerminologyAdapter(session or FakeSession(), sct_py_version="0.29.0")


def test_provenance_redacts_source_paths_and_distinguishes_loaded_empty_history() -> None:
    without_history = adapter().release
    with_history = adapter(FakeSession(has_history=True)).release

    assert not hasattr(without_history, "source_paths")
    assert "/private/licensed/release.zip" not in repr(without_history)
    assert without_history.history_evidence is EvidenceAvailability.UNAVAILABLE
    assert with_history.history_evidence is EvidenceAvailability.AVAILABLE
    assert with_history.companions[0].record_count == 0

    private_release = FakeSession()
    assert private_release.provenance_result is not None
    private_release.provenance_result.update(
        {
            "edition_label": "SnomedCT_secret-patient-cohort",
            "release_id": "SnomedCT_secret-patient-cohort",
            "source_paths": ["/private/patients/SnomedCT_secret-patient-cohort"],
        }
    )
    redacted = adapter(private_release).release
    assert redacted.edition_label == "Unrecognised local edition"
    assert redacted.release_id == ""
    assert "secret-patient-cohort" not in repr(redacted)


def test_provenance_discriminator_and_unsigned_counts_fail_closed() -> None:
    session = FakeSession()
    session.provenance_result["_type"] = "different_contract"  # type: ignore[index]
    with pytest.raises(AdapterContractError, match="must be sct_provenance"):
        adapter(session)

    session = FakeSession()
    session.concept_results["22298006"]["children_count"] = -1  # type: ignore[index]
    with pytest.raises(AdapterContractError, match="must not be negative"):
        adapter(session).concept("22298006")


def test_concept_validates_nested_records_and_propagates_history_evidence() -> None:
    result = adapter(FakeSession(has_history=True)).concept("22298006")

    assert result is not None
    assert result.id == "22298006"
    assert result.parents[0].id == "404684003"
    assert result.display_attributes[0].label == "Finding site"
    assert result.history_evidence is EvidenceAvailability.AVAILABLE


def test_unknown_or_malformed_concept_fields_fail_closed() -> None:
    session = FakeSession()
    session.concept_results["22298006"]["future_field"] = "not silently accepted"  # type: ignore[index]
    with pytest.raises(AdapterContractError, match="unexpected fields"):
        adapter(session).concept("22298006")

    session = FakeSession()
    session.concept_results["22298006"]["children_count"] = True  # type: ignore[index]
    with pytest.raises(AdapterContractError, match="must be an integer"):
        adapter(session).concept("22298006")


def test_invalid_identifiers_and_limits_are_rejected_before_the_sdk_call() -> None:
    terminology = adapter()

    with pytest.raises(AdapterInputError, match="6-18 digits"):
        terminology.concept("22<script>")
    with pytest.raises(AdapterInputError, match="6-18 digits"):
        terminology.concept("12345")
    with pytest.raises(AdapterInputError, match="leading zero"):
        terminology.concept("012345")
    with pytest.raises(AdapterInputError, match="between 1"):
        terminology.search("heart", limit=0)
    with pytest.raises(AdapterInputError, match="must not be empty"):
        terminology.expand("   ")


def test_search_is_literal_and_validates_results() -> None:
    session = FakeSession()
    terminology = adapter(session)

    results = terminology.search("heart attack", limit=5, hierarchy="Clinical finding")

    assert results[0].id == "22298006"
    assert session.search_call == ("heart attack", 5, "Clinical finding", True)


def test_ecl_results_are_exact_sorted_sets_with_reproducibility_metadata() -> None:
    result = adapter().expand("<<73211009")

    assert result.ids == ("44054006", "46635009", "73211009")
    assert result.fully_materialized
    assert result.sct_py_version == "0.29.0"
    assert len(result.result_sha256) == 64

    session = FakeSession()
    session.expand_result = ["73211009", "46635009"]
    with pytest.raises(AdapterContractError, match="sorted"):
        adapter(session).expand("<<73211009")


def test_hierarchy_reports_known_total_returned_count_and_truncation() -> None:
    session = FakeSession()
    terminology = adapter(session)

    parents = terminology.direct_parents("22298006")
    children = terminology.direct_children("22298006", limit=1)

    assert [parent.id for parent in parents] == ["404684003"]
    assert children.returned_count == 1
    assert children.total_count == 2
    assert children.truncated

    with pytest.raises(AdapterContractError, match="expected page size"):
        terminology.direct_children("22298006", limit=100)

    session.children_result = [summary("44054006"), summary("44054006")]
    with pytest.raises(AdapterContractError, match="unique identifiers"):
        terminology.direct_children("22298006", limit=100)


def test_sdk_failures_are_redacted_at_the_adapter_boundary() -> None:
    session = FakeSession()
    session.failure = RuntimeError("failed at /private/licensed/release.zip")
    terminology = adapter(session)

    with pytest.raises(AdapterQueryError) as caught:
        terminology.concept("22298006")

    assert caught.value.operation == "look up concept"
    assert "/private/" not in str(caught.value)
    assert caught.value.__cause__ is None


def test_batch_cardinality_drift_fails_closed() -> None:
    class BrokenBatchSession(FakeSession):
        def concepts(self, concept_ids: list[str]) -> list[dict[str, Any] | None]:
            return []

    with pytest.raises(AdapterContractError, match="cardinality"):
        adapter(BrokenBatchSession()).concepts(["22298006"])


def test_lookup_identity_drift_fails_closed() -> None:
    session = FakeSession()
    assert session.concept_results["22298006"] is not None
    session.concept_results["22298006"]["id"] = "404684003"
    with pytest.raises(AdapterContractError, match="different identifier"):
        adapter(session).concept("22298006")

    class ReorderedBatchSession(FakeSession):
        def concepts(self, concept_ids: list[str]) -> list[dict[str, Any] | None]:
            results = super().concepts(concept_ids)
            return list(reversed(results))

    with pytest.raises(AdapterContractError, match="preserve input order"):
        adapter(ReorderedBatchSession()).concepts(["22298006", "404684003"])
