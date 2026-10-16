# sct-marimo

A local-first marimo workbench for formulating, inspecting, and testing SNOMED CT concept sets with [`sct`](https://github.com/pacharanero/sct).

> [!IMPORTANT]
> This repository is an exploratory specification and scaffold. It does not yet contain a working notebook, is not a medical device, and must not be used to make clinical decisions.

## Product Hypothesis

`sct-marimo` aims to give a clinician and a trusted agent one shared, inspectable surface for moving from a clinical question to an editable terminology expression, an artefact-pinned concept set, a bounded view of change, and the concepts behind that change.

The first useful slice is deliberately narrow: run supported ECL against a selected local `sct` artefact, compare exact SCTID sets, inspect concepts and direct hierarchy neighbours, and retain enough release provenance to reproduce the query. The workbench delegates terminology semantics to `sct-py` and the typed `sct` Rust SDK.

## Non-goals

- No second terminology engine, RF2 importer, or independent ECL implementation.
- No patient store, clinical-truth engine, SNOMED CT authoring environment, or competition scoring system.
- No silent approximation of unsupported ECL, historical editions, hierarchy completeness, or application-data effects.
- No licensed SNOMED CT content, private rows, or sensitive paths in this repository, its examples, generated artefacts, logs, or agent context.

## Status

The detailed product and safety boundaries have moved here from the exploratory `sct` specification. Implementation has not started. See the [product specification](spec/product.md), [roadmap](spec/roadmap.md), and [safety statement](SAFETY.md).

The first implementation decision is intentionally deferred until current Python, marimo, and `sct-py` packaging constraints have been verified. This repository will not acquire a speculative dependency file merely to look complete.

## Relationship To `sct`

[`sct`](https://github.com/pacharanero/sct) remains the terminology engine and the owner of RF2 ingestion, canonical NDJSON, derived read-only databases, ECL semantics, hierarchy queries, provenance, and the typed SDK. Capability gaps discovered here should be fixed and tested at the appropriate `sct` boundary rather than worked around in notebook cells.

## Data And Licensing

Use synthetic data by default. SNOMED CT content and databases derived from it are separately licensed material and are not distributed by this project.

Future software source is licensed under [AGPL-3.0-or-later](LICENSES/AGPL-3.0-or-later.txt). Project documentation is licensed under [CC-BY-SA-4.0](LICENSES/CC-BY-SA-4.0.txt). See [LICENSE](LICENSE) for the file-level policy.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) and [agent-instructions.md](agent-instructions.md). Security issues must be reported privately as described in [SECURITY.md](SECURITY.md).

Maintained by [Marcus Baw](https://github.com/pacharanero) and Baw Medical Ltd.
