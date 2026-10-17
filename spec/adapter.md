# Python Adapter Contract

Status: implemented for roadmap item `M1` against `sct-py` 0.29.0.

## Ownership

`sct-py` is the synchronous Python adapter over the typed Rust `sct` SDK. It owns terminology lookup, ECL evaluation, lexical search, hierarchy queries, and read-only database access. `sct-marimo` does not reproduce those semantics. Its `TerminologyAdapter` owns application validation, export-safe provenance, bounded result envelopes, and errors suitable for a notebook surface.

The native binding serialises Rust records through JSON and exposes ordinary Python dictionaries, lists, scalars, and `None`. Every dictionary crossing into this project is therefore validated into a frozen local model. Missing fields, unexpected fields, wrong scalar types, transport-invalid identifier shapes, cardinality drift, duplicate children, and inconsistent hierarchy totals fail closed with `AdapterContractError`; the notebook never receives `dict[str, Any]` from the adapter.

## Verified Dependency Boundary

The project requires Python 3.10 or newer because the pinned [marimo 0.25.1](https://pypi.org/project/marimo/0.25.1/) distribution requires Python 3.10. The pinned [`sct-py` 0.29.0](https://pypi.org/project/sct-py/0.29.0/) distribution requires Python 3.9 and publishes CPython 3.9 stable-ABI wheels for Linux, macOS, and Windows, so Python 3.10 is within both declared support ranges. `sct-py` has no Python runtime dependencies; it carries the native Rust engine in its wheel.

The package is built with [hatchling 1.32.4](https://pypi.org/project/hatchling/1.32.4/). Development uses [uv 0.13.1](https://github.com/astral-sh/uv/releases/tag/0.13.1) with committed `uv.lock`, [pytest 9.1.1](https://pypi.org/project/pytest/9.1.1/), [mypy 2.4.0](https://pypi.org/project/mypy/2.4.0/), and [Ruff 0.17.1](https://pypi.org/project/ruff/0.17.1/). Direct requirements are exact while this application is pre-release, and the lockfile records the complete resolution.

## Behaviour

- One adapter owns one serial `sct_py.Snomed` session. It is a context manager and does not claim concurrency safety.
- Opening and all terminology queries delegate to `sct-py`; SDK exceptions become operation-labelled `AdapterQueryError` values without the source message or sensitive database path.
- Provenance retains recognised release identity, `sct` version, timestamp, content fingerprint, and companion evidence. Source paths are validated and then deliberately discarded so they cannot enter model representations or exportable results. Because upstream falls back to a source-directory basename for unrecognised editions, an unrecognised path-derived release ID and matching edition label are redacted too; the content fingerprint remains the reproducible identity.
- Companion markers determine evidence availability independently of row count. A declared zero-record history companion is loaded-empty and therefore `available`; absence is `unavailable`.
- Concept lookup models the current stored concept, a representative hierarchy path, direct parents, display-oriented flattened attributes, reference-set membership, status, and optional history fields. Display attributes do not claim role-group-preserving semantics.
- Search always calls `sct-py` with `literal=True`; user text cannot become FTS syntax. Results and optional hierarchy filters are validated.
- ECL remains an opaque expression passed to the upstream parser/evaluator. The returned complete SCTID list must be duplicate-free and numerically sorted. The result records the exact expression, release provenance, `sct-py` version, and SHA-256 of newline-delimited result identifiers.
- Direct parents come from the validated concept record and are resolved through batch lookup. Direct children carry recorded total count, returned count, requested limit, and explicit truncation. The adapter refuses inconsistent totals.

## Known Upstream Gaps

This boundary does not manufacture capabilities absent from `sct-py` 0.29.0. In particular, ECL failures currently cross the binding as exception text rather than structured parser/evaluator diagnostics, term-annotation warnings are not exposed as a structured channel, and concept lookup cannot distinguish unavailable inactivation-reason evidence from loaded evidence with no matching row. The adapter checks the transport syntax of concept identifiers (ASCII digits, 6-18 characters, no leading zero), but `sct-py` does not expose upstream SCTID check-digit validation and this project deliberately does not reproduce the terminology algorithm. The adapter exposes history companion availability as the nearest truthful release-level evidence marker, but the first notebook slice remains gated on upstream structured ECL diagnostics and warnings as specified in [product.md](product.md).
