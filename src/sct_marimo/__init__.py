# SPDX-FileCopyrightText: 2026 Marcus Baw and Baw Medical Ltd
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Typed application boundary between the workbench and ``sct-py``."""

from sct_marimo.adapter import TerminologyAdapter
from sct_marimo.models import (
    AdapterContractError,
    AdapterError,
    AdapterInputError,
    AdapterQueryError,
    Concept,
    ConceptSet,
    ConceptSummary,
    EvidenceAvailability,
    HierarchyPage,
    Provenance,
    SearchHit,
)
from sct_marimo.workbench import (
    ComparisonResult,
    ConceptInspection,
    DiffMembership,
    DiffRow,
    DiffSection,
    ExactSetDiff,
    QueryRequest,
    SdkInvocation,
    compare_concept_sets,
    inspect_comparison_concept,
)

__all__ = [
    "AdapterContractError",
    "AdapterError",
    "AdapterInputError",
    "AdapterQueryError",
    "ComparisonResult",
    "Concept",
    "ConceptInspection",
    "ConceptSet",
    "ConceptSummary",
    "DiffMembership",
    "DiffRow",
    "DiffSection",
    "EvidenceAvailability",
    "ExactSetDiff",
    "HierarchyPage",
    "Provenance",
    "QueryRequest",
    "SdkInvocation",
    "SearchHit",
    "TerminologyAdapter",
    "compare_concept_sets",
    "inspect_comparison_concept",
]
