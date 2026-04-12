FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY . .
RUN uv sync --extra api --no-dev
EXPOSE 8741
CMD ["uv", "run", "anamnesis", "serve"]
