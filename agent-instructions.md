# Agent Instructions

`sct-marimo` is an exploratory local-first marimo workbench built on the [`sct`](https://github.com/pacharanero/sct) terminology engine. Its Python application boundary exists, but its working notebook does not: do not infer that other described capabilities are implemented.

## Read First

- [README.md](README.md) - project scope and current status.
- [spec/product.md](spec/product.md) - product, architecture, trust, and acceptance boundaries.
- [spec/adapter.md](spec/adapter.md) - implemented Python boundary and known upstream gaps.
- [spec/roadmap.md](spec/roadmap.md) - unfinished work and stable identifiers.
- [SAFETY.md](SAFETY.md) - intended use, exclusions, hazards, and current controls.
- [CONTRIBUTING.md](CONTRIBUTING.md) - contribution workflow.

## Core Invariants

- `sct` is the terminology engine. Use `sct-py` and its typed Rust SDK; do not implement RF2 ingestion, terminology SQL, hierarchy semantics, or ECL again in this repository.
- The `sct` RF2 -> canonical NDJSON -> derived read-only SQLite path remains authoritative. Notebook and widget code must not bypass it.
- Unsupported, grouped, historical, incomplete, or truncated semantics remain explicit. Never guess, silently broaden, silently narrow, or present an approximation as exact.
- Keep terminology membership, clinical interpretation, and application row eligibility separate.
- Use synthetic data by default. Do not commit licensed SNOMED CT terms, private rows, patient-identifiable data, production databases, sensitive paths, generated outputs containing them, or competition data.
- Experimental ECL is data, not generated Python. Raw SQL, arbitrary user code, and external mutation are outside the first slice.
- Private sessions have no assumed export, cache, pairing, AI-provider, analytics, or network permission. Local execution does not imply local agent context.
- Machine-readable values remain lossless and display values are encoded for their output context. Data must not become HTML, JavaScript, SQL, shell, or Python syntax.

## Development

- Prefer the smallest vertical slice that proves the product hypothesis on synthetic fixtures.
- Keep marimo notebooks in Python-file format and keep reusable logic importable and independently testable.
- Validate Python dictionaries returned by `sct-py` into explicit local models at the adapter boundary.
- Add dependencies only after checking current official release and maintenance evidence. Commit the application lockfile once a Python project exists.
- Every source file must carry `SPDX-FileCopyrightText: 2026 Marcus Baw and Baw Medical Ltd` and the appropriate SPDX licence identifier. Documentation and other files use the bulk annotations in `REUSE.toml` where inline headers are unsuitable.
- Update the product specification, roadmap, safety evidence, and tests with behavioural changes. Remove shipped roadmap items rather than marking them complete.

## Validation

Run every gate before committing:

```sh
s/lint
s/test
s/build
reuse lint
```

Once a notebook exists, add its execution gate here and in CI. Trust-boundary acceptance must include adversarial synthetic values and observation of zero-egress/private-session behaviour, not only unit tests written alongside the implementation.

## Git

Use conventional commits such as `docs:`, `feat(workbench):`, `fix(adapter):`, and `test(trust):`. Commit each validated coherent parcel without waiting for a separate request. Do not push unless the user explicitly requests it or the local workflow authorises it. Never commit secrets or licensed terminology content.
