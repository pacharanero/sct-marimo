# Roadmap

This file contains unfinished work only. Delete shipped entries in the same pull request that delivers them and record durable behaviour in the relevant specification. Identifiers are stable and must never be renumbered or reused.

- [ ] `M3` **Prove trust and output boundaries.** Add adversarial synthetic output tests, redacted structured failures, export/cache/snapshot denial, in-memory cleanup, and observed zero-egress private sessions without pairing or agent access.
- [ ] `M4` **Test human-agent usability on synthetic data.** Ask a clinician and an authorised agent to inspect and correct the same deliberately flawed expression; measure whether the human can explain changed concepts and aggregates without reading generated scripts.
- [ ] `M5` **Evaluate atlas-component reuse after upstream evidence exists.** Compare the concept-inspector contract with `sct` roadmap item `R38` only after its search-to-concept slice ships; choose reuse, adaptation, or intentional separation for a measured reason rather than making either project depend on an unshipped component library.
- [ ] `M6` **Gate an application-data bridge on upstream coverage contracts.** After `sct` roadmap item `R87` resolves encounter keys, duplicate policy, denominators, matching mode, and provenance, test a synthetic external read-only rule runner that returns aggregate changes only. Historical matching additionally depends on validated `R25` reconstruction.
