ARG GITEA_VERSION=1.26.4
FROM docker.io/gitea/gitea:${GITEA_VERSION}-rootless

USER root
RUN apk add --no-cache vim

# Preserve the upstream rootless runtime identity.
USER 1000:1000
