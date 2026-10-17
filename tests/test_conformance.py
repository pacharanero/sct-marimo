# SPDX-FileCopyrightText: 2026 Marcus Baw and Baw Medical Ltd
# SPDX-License-Identifier: AGPL-3.0-or-later

from __future__ import annotations

import json
from hashlib import sha256
from importlib.metadata import version
from pathlib import Path
from typing import Any, cast

from sct_py import Snomed

from sct_marimo import TerminologyAdapter

FIXTURES = Path(__file__).parent / "fixtures"
DATABASE = FIXTURES / "sct-v0.29.0-synthetic.db"
ORACLE = FIXTURES / "sct-v0.29.0-conformance.json"


def oracle() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(ORACLE.read_text()))


def test_fixture_identity_matches_the_certified_cross_surface_oracle(
    synthetic_database: Path,
) -> None:
    expected = oracle()

    assert version("sct-py") == expected["database"]["sct_version"]
    assert sha256(DATABASE.read_bytes()).hexdigest() == expected["database"]["sha256"]

    with Snomed(synthetic_database) as terminology:
        provenance = terminology.provenance()

    assert provenance is not None
    assert provenance["content_fingerprint"] == expected["database"]["content_fingerprint"]
    assert provenance["sct_version"] == expected["database"]["sct_version"]
    assert provenance["release_date"] == expected["database"]["release_date"]


def test_python_sdk_matches_representative_rust_sdk_and_cli_observations(
    synthetic_database: Path,
) -> None:
    expected = oracle()

    with Snomed(synthetic_database) as terminology:
        for concept_id, concept_expected in expected["concepts"].items():
            concept = terminology.concept(concept_id)
            assert concept is not None
            assert concept["preferred_term"] == concept_expected["preferred_term"]
            assert concept["fsn"] == concept_expected["fsn"]
            assert concept["active"] is concept_expected["active"]
            assert [parent["id"] for parent in concept["parents"]] == concept_expected["parent_ids"]
            if "attribute_ids" in concept_expected:
                attribute_ids = sorted(
                    value["id"] for values in concept["attributes"].values() for value in values
                )
                assert attribute_ids == concept_expected["attribute_ids"]
            if "refset_ids" in concept_expected:
                assert [
                    membership["id"] for membership in concept["member_of"]
                ] == concept_expected["refset_ids"]

        for expression, identifiers in expected["ecl"].items():
            assert terminology.expand(expression) == identifiers

        search = expected["search"]
        hits = terminology.search(search["query"], limit=search["limit"], literal=True)
        assert [hit["id"] for hit in hits] == search["ids"]

        hierarchy = expected["hierarchy"]
        children = terminology.children(hierarchy["concept_id"], limit=hierarchy["limit"])
        assert [child["id"] for child in children] == hierarchy["child_ids"]


def test_validated_adapter_matches_the_same_conformance_oracle(
    synthetic_database: Path,
) -> None:
    expected = oracle()

    with TerminologyAdapter.open(synthetic_database) as terminology:
        myocardial_infarction = terminology.concept("22298006")
        type_one_diabetes = terminology.concept("46635009")
        expanded = terminology.expand("<<73211009")
        hits = terminology.search("heart attack", limit=1)
        children = terminology.direct_children("73211009", limit=1)

    assert myocardial_infarction is not None
    assert (
        myocardial_infarction.preferred_term == expected["concepts"]["22298006"]["preferred_term"]
    )
    assert [attribute.label for attribute in myocardial_infarction.display_attributes] == [
        "associated_morphology",
        "finding_site",
    ]
    assert type_one_diabetes is not None
    assert [membership.id for membership in type_one_diabetes.member_of] == expected["concepts"][
        "46635009"
    ]["refset_ids"]
    assert list(expanded.ids) == expected["ecl"]["<<73211009"]
    assert [hit.id for hit in hits] == expected["search"]["ids"]
    assert [child.id for child in children.children] == expected["hierarchy"]["child_ids"]
    assert children.total_count == expected["hierarchy"]["total_count"]
    assert children.truncated is expected["hierarchy"]["truncated"]
    assert terminology.release.edition_label == "Unrecognised local edition"
    assert terminology.release.release_id == ""
    assert "tests/fixtures" not in repr(terminology.release)
