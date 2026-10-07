ARG GITEA_RUNNER_VERSION=1.0.0
FROM docker.io/gitea/runner:${GITEA_RUNNER_VERSION}

USER root

RUN if command -v apk >/dev/null 2>&1; then \
      apk add --no-cache bash coreutils curl git gzip openssl python3 py3-pip tar vim; \
    elif command -v apt-get >/dev/null 2>&1; then \
      apt-get update; \
      apt-get install -y --no-install-recommends bash ca-certificates coreutils curl git gzip openssl python3 python3-pip python3-venv tar vim; \
      rm -rf /var/lib/apt/lists/*; \
    else \
      echo "Unsupported runner base image: no apk or apt-get" >&2; \
      exit 1; \
    fi \
    && python3 -m venv /opt/lab-venv

COPY demo/repository/requirements.txt /tmp/requirements.txt
COPY demo/repository/requirements-dev.txt /tmp/requirements-dev.txt
RUN /opt/lab-venv/bin/pip install --no-cache-dir -r /tmp/requirements-dev.txt \
    && rm -f /tmp/requirements.txt /tmp/requirements-dev.txt

ENV PATH="/opt/lab-venv/bin:${PATH}"

RUN mkdir -p /data/work /srv/releases
