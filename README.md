# sct-marimo

A local-first marimo workbench for formulating, inspecting, and testing SNOMED CT concept sets with [`sct`](https://github.com/pacharanero/sct).

> [!IMPORTANT]
> This repository is an exploratory implementation. Its working notebook is validated only against synthetic data, is not a medical device, and must not be used to make clinical decisions.

## Product Hypothesis

`sct-marimo` aims to give a clinician and a trusted agent one shared, inspectable surface for moving from a clinical question to an editable terminology expression, an artefact-pinned concept set, a bounded view of change, and the concepts behind that change.

The first useful slice is deliberately narrow: run supported ECL against a selected local `sct` artefact, compare exact SCTID sets, inspect concepts and direct hierarchy neighbours, and retain enough release provenance to reproduce the query. The workbench delegates terminology semantics to `sct-py` and the typed `sct` Rust SDK.

## Non-goals

- No second terminology engine, RF2 importer, or independent ECL implementation.
- No patient store, clinical-truth engine, SNOMED CT authoring environment, or competition scoring system.
- No silent approximation of unsupported ECL, historical editions, hierarchy completeness, or application-data effects.
- No licensed SNOMED CT content, private rows, or sensitive paths in this repository, its examples, generated artefacts, logs, or agent context.

## Status

The strict Python application boundary and the first synthetic marimo concept-set workflow are implemented and tested. The notebook runs two supported ECL expressions only after an explicit request, marks edited results stale, presents an exact display-bounded set diff, and opens a persistent concept and direct-hierarchy inspector. See the [adapter contract](spec/adapter.md), [product specification](spec/product.md), [roadmap](spec/roadmap.md), and [safety statement](SAFETY.md).

The project currently pins Python 3.10-compatible `marimo` and `sct-py` releases and commits the complete uv resolution. The adapter validates untyped SDK results into immutable local models, removes sensitive source paths from exportable provenance, and preserves explicit unavailable and truncated states.

The broader product first-slice acceptance is not complete. `sct-py` 0.29.0 does not yet expose structured ECL parser/evaluator diagnostics or term-annotation warnings, and private-session output and egress controls remain roadmap work.

## Run The Synthetic Workbench

After installing the locked environment, launch the notebook against the committed licence-free test database:

```sh
uv run --locked marimo run notebooks/concept-set-workbench.py \
  --no-sandbox \
  -- --db tests/fixtures/sct-v0.29.0-synthetic.db
```

The database path is accepted as a launch argument and is not placed in result models or rendered provenance. For licensed terminology, supply an authorised local database built through the canonical `sct` RF2 -> NDJSON -> SQLite pipeline.

## Development

Install [uv](https://docs.astral.sh/uv/), then create the locked environment:

```sh
uv sync --locked --all-groups
```

Use `s/lint` for format, lint, strict notebook checks, and strict type checks; `s/test` for unit, notebook-startup, and synthetic conformance tests; `s/build` for distributions; and `reuse lint` for licensing metadata. The same gates run in CI.

## Relationship To `sct`

[`sct`](https://github.com/pacharanero/sct) remains the terminology engine and the owner of RF2 ingestion, canonical NDJSON, derived read-only databases, ECL semantics, hierarchy queries, provenance, and the typed SDK. Capability gaps discovered here should be fixed and tested at the appropriate `sct` boundary rather than worked around in notebook cells.

## Data And Licensing

Use synthetic data by default. SNOMED CT content and databases derived from it are separately licensed material and are not distributed by this project.

Software source is licensed under [AGPL-3.0-or-later](LICENSES/AGPL-3.0-or-later.txt). Project documentation is licensed under [CC-BY-SA-4.0](LICENSES/CC-BY-SA-4.0.txt). See [LICENSE](LICENSE) for the file-level policy.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) and [agent-instructions.md](agent-instructions.md). Security issues must be reported privately as described in [SECURITY.md](SECURITY.md).

Maintained by [Marcus Baw](https://github.com/pacharanero) and Baw Medical Ltd.
