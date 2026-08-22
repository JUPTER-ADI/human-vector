FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/hv-core:/app/hv-adk

WORKDIR /app

COPY hv-adk/requirements.txt /app/hv-adk/requirements.txt

RUN python -m pip install --no-cache-dir -r /app/hv-adk/requirements.txt

COPY hv-core /app/hv-core
COPY hv-adk /app/hv-adk

EXPOSE 8080

CMD ["sh", "-c", "exec adk api_server --host 0.0.0.0 --port ${PORT:-8080} /app/hv-adk"]
