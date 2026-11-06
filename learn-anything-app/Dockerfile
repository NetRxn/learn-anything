# No npm/node — frontend served via CDN + static files only
#
# Base images: DHI hardened images (dhi.io) for managed deployments.
# Self-hosters: replace with python:3.14-slim if DHI registry is unavailable.

# --- Builder stage ---
FROM dhi.io/python:3.14-dev AS builder

WORKDIR /app
RUN pip install uv

COPY pyproject.toml .
COPY app/ app/
COPY templates/ templates/
COPY static/ static/
COPY alembic/ alembic/
COPY alembic.ini .

RUN uv pip install --system "."

# --- Runtime stage ---
FROM dhi.io/python:3.14 AS runtime

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app

# Create non-root user matching service_uid
RUN groupadd -g 1000 appuser && useradd -u 1000 -g 1000 -s /bin/false appuser
USER 1000:1000

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
