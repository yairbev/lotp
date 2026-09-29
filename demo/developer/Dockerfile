FROM python:3.12.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl git tini \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10002 --shell /bin/bash developer \
    && install -d -o developer -g developer /home/developer/work

COPY demo/developer/entrypoint.sh /usr/local/bin/developer-entrypoint
RUN chmod 0755 /usr/local/bin/developer-entrypoint

USER developer
ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/developer-entrypoint"]
