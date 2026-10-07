# Vendor-neutral investigation queries

Field names below match `sample-events.jsonl`. Map them to the company’s actual schemas before use.

## Workflow changes without review

```text
event_kind = "git.change"
AND workflow_path IN SECURITY_SENSITIVE_PATHS
AND target_branch IN PROTECTED_BRANCHES
AND review_count < 1
```

Group by repository and actor. Display commit, changed paths, bypass reason, authentication method, source zone, and subsequent run IDs.

## Secret-bearing run with new destination

```text
event_kind = "ci.run" AND secret_context_used = true
JOIN event_kind = "network.connection" ON repository, commit, run_id
WHERE destination_allowed = false
WITHIN 15 minutes
```

Display runner identity, workflow path, step name, destination, process tree, token permissions, and artifacts produced by the run.

## Developer automation chain

```text
event_kind = "git.change" AND changed_path IN EXECUTABLE_DEVELOPER_PATHS
JOIN event_kind = "runtime.process" ON repository, commit
JOIN event_kind = "network.connection" ON host, process
WHERE destination_allowed = false
WITHIN 60 minutes
```

Do not assume a pull caused execution. Confirm the command, tool, IDE task, package script, or bootstrap action the developer invoked.

## Incident scope from a commit

```text
commit = SUSPECT_COMMIT
OR ancestor_commit = SUSPECT_COMMIT
RETURN runs, runners, secret_contexts, artifact_digests, package_versions, deployments, developer_hosts
```

The query depends on retained provenance. If the environment cannot answer it, record that gap as an incident-response dependency rather than filling it with inference.

