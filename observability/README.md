# Observability package

The files in this directory use a small normalized schema so the presentation can join source-control, CI, runtime, artifact, and network events without depending on one vendor.

`sample-events.jsonl` is illustrative lab telemetry. It is not captured from Gitea or a company system. Replace field mappings and allowlists before adapting any detection to production.

Each detection requires tuning for protected branches, executable paths, runner pools, expected destinations, service accounts, maintenance windows, and available provenance.
