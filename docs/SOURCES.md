# Primary sources

Verified on 2026-09-28.

- [Gitea 1.26.4 API documentation](https://docs.gitea.com/api/1.26/) documents the API version used for repository and Actions-secret bootstrap operations.
- [Gitea 1.26.4 release files](https://dl.gitea.com/gitea/1.26.4/) establish the pinned Gitea release.
- [Gitea Runner 1.0.0 release](https://blog.gitea.com/release-of-runner-1.0.0/) documents the renamed `gitea/runner:1.0.0` image and its registration environment variables.
- [Gitea Runner labels](https://docs.gitea.com/runner/labels/) documents the `name:host` label form used to execute jobs directly inside the runner container.
- [Gitea Runner Docker installation](https://docs.gitea.com/runner/installation/docker/) documents the image entrypoint variables, persistent `/data` registration state, Compose health dependency, and why the Docker socket can be omitted for host-mode jobs.
- [Gitea Actions quick start](https://docs.gitea.com/usage/actions/quickstart/) describes runner registration, job execution, and the distinction between the browser URL and the runner-reachable instance address.
- [Gitea Actions secrets](https://docs.gitea.com/usage/actions/secrets/) documents secret naming, scope, and `${{ secrets.NAME }}` access.
- [Gitea Actions job-token permissions](https://docs.gitea.com/usage/actions/token-permissions/) documents job-level and workflow-level token permission controls.
- [Gitea API: create or update a repository secret](https://docs.gitea.com/api/next/operations/update-repo-secret/) documents the request used by the bootstrap script.
- [Install Docker Engine on Ubuntu](https://docs.docker.com/engine/install/ubuntu/) documents the apt repository, signing key, conflicting-package list, and Docker Engine, Buildx, and Compose plugin packages used by `preflight.sh --build`.
- [GitHub artifact attestations](https://docs.github.com/en/actions/concepts/security/artifact-attestations) provides an official example of provenance binding an artifact to workflow, repository, commit, event, and builder identity. The talk uses this as a general provenance concept, not as a claim that the local Gitea lab implements GitHub attestations.

Version and product behavior can change. Recheck these sources before reusing the project after September 2026.
