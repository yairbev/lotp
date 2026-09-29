FROM python:3.12.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN useradd --create-home --uid 10001 appuser
WORKDIR /opt/lab

COPY demo/prod/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY demo/prod/collector.py demo/prod/supervisor.py ./
RUN python -c "from collector import app; assert app.title"
RUN mkdir -p /data /srv/releases /srv/runtime /opt/lab/canaries \
    && printf '%s\n' 'LAB_ONLY_KEY_CANARY' > /opt/lab/canaries/demo-key-canary.txt \
    && chown -R appuser:appuser /data /srv/runtime /opt/lab

USER appuser
EXPOSE 8000 9000
CMD ["python", "supervisor.py"]
