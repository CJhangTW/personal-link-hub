FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.11.21 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project

COPY . .

RUN uv sync --locked --no-dev \
    && DEBUG=0 SECRET_KEY=build-only ALLOWED_HOSTS=localhost STATIC_ROOT=/app/staticfiles uv run python manage.py collectstatic --noinput

RUN addgroup --system app && adduser --system --ingroup app app \
    && mkdir -p /app/staticfiles \
    && chown -R app:app /app

USER app

EXPOSE 8080

CMD ["sh", "-c", "exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8080} --workers 2 --access-logfile - --error-logfile -"]
