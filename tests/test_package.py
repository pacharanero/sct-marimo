# SPDX-FileCopyrightText: 2026 Marcus Baw and Baw Medical Ltd
# SPDX-License-Identifier: AGPL-3.0-or-later

from __future__ import annotations

import sct_marimo


def test_public_api_is_explicit() -> None:
    assert sct_marimo.__all__ == [
        "AdapterContractError",
        "AdapterError",
        "AdapterInputError",
        "AdapterQueryError",
        "Concept",
        "ConceptSet",
        "ConceptSummary",
        "EvidenceAvailability",
        "HierarchyPage",
        "Provenance",
        "SearchHit",
        "TerminologyAdapter",
    ]
