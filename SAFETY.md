# Safety

## Intended Use

`sct-marimo` is intended to become a local exploratory workbench for inspecting and testing SNOMED CT concept-set proposals against a named terminology artefact. It supports human review; it does not determine clinical truth.

## Current Status

The repository currently contains a specification and governance scaffold only. There is no working notebook and no validated clinical workflow. It must not be used for diagnosis, treatment, patient selection, clinical decision support, or production codelist approval.

## Excluded Uses

- Autonomous clinical decisions or unreviewed codelist acceptance.
- Patient-data storage, cohort management, or direct production database access.
- SNOMED CT authoring or redistribution of licensed terminology content.
- Claims of exact historical reconstruction before the upstream `sct` evidence model supports and validates them.
- Claims that concept-set count changes prove patient-level or application-level effects.

## Principal Hazards

| Hazard | Potential harm | Required control |
| --- | --- | --- |
| Unsupported ECL is approximated or flattened | Incorrect concept membership is accepted | Refuse unsupported semantics through the shared `sct` evaluator and surface structured errors |
| A release or historical context is mislabelled | A concept set is applied to the wrong terminology state | Show release identity and fingerprints; compare separately loaded artefacts until validated point-in-time reconstruction exists |
| Multiple parents, limits, or missing evidence are hidden | Reviewers infer a complete or unique hierarchy | Display multiple parents and every limit, truncation, omitted result, and unavailable evidence state |
| Terminology membership is conflated with clinical or row eligibility | An aggregate is mistaken for a clinical answer | Keep terminology, clinical interpretation, and application rules as separate typed stages |
| Licensed or private data persists or leaves the machine | Confidentiality, licensing, or governance breach | Synthetic-by-default fixtures, explicit private-session profile, blocked exports, redacted errors and provenance, zero-egress observation, and cleanup testing |
| Agent access is assumed safe because the notebook is local | Private content reaches a remote provider or tool | Permit pairing only in explicitly authorised synthetic sessions and treat every agent/provider boundary as separate egress |

## Safety Controls Before A First Release

- Cross-check representative concept and ECL results against the same synthetic build through the Rust SDK, Python SDK, and CLI.
- Add adversarial round-trip tests for markup, quotes, controls, newlines, paths, and identifier-like values at every output boundary.
- Prove private sessions expose no pairing or export route, persist no licensed/private output, redact failures, discard in-memory state on shutdown, and make no external requests under an enforced zero-egress profile.
- Make provenance, unavailable evidence, approximation, truncation, and stale results visible in the primary workflow rather than hidden in logs.
- Run human review with deliberately flawed synthetic expressions before claiming usability or safety benefit.

Safety claims must be evidence-backed and revised with the implementation. New hazards belong here or in a linked hazard log as the project grows.
