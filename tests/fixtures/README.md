# Synthetic Conformance Fixture

`sct-v0.29.0-synthetic.db` is a generated, licence-free SQLite artefact built by `sct` v0.29.0 from the committed synthetic RF2 release in [`pacharanero/sct`](https://github.com/pacharanero/sct/tree/v0.29.0/tests/fixtures/rf2). It contains no production SNOMED CT release and is committed only under `tests/`. The wheel contains only `src/sct_marimo` and excludes this fixture; the source distribution retains it as executable conformance evidence.

The source revision is `bfcf41c2196152da5cc08e906c683ff3621b25a8`, the commit peeled from the `v0.29.0` tag. The artefact was built through the canonical RF2 -> NDJSON -> SQLite path with active concepts, `en-GB`, simple refsets, and transitive closure:

```sh
sct ndjson \
  --rf2 tests/fixtures/rf2/SnomedCT_SyntheticTest_PRODUCTION_20260101T120000Z \
  --locale en-GB \
  --refsets simple \
  --output synthetic.ndjson
sct sqlite \
  --ndjson synthetic.ndjson \
  --output synthetic.db \
  --transitive-closure
```

`sct-v0.29.0-conformance.json` records stable semantic observations cross-checked against the same database through the v0.29.0 Rust SDK, `sct-py`, and CLI. CI verifies the committed database hash, canonical content fingerprint, direct `sct-py` results, and the validated `sct-marimo` boundary against that oracle. The physical database hash protects this reviewed fixture but is not a regeneration identity because provenance includes a build timestamp.

The fixture database deliberately retains only the upstream relative synthetic source path. Application models discard it and redact the path-derived release label and identifier as `Unrecognised local edition`; the release date and canonical content fingerprint remain available.
