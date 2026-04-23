FROM node:22-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS runtime
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONPATH=/app/src
COPY pyproject.toml README.md ./
COPY src ./src
COPY data ./data
COPY scripts ./scripts
COPY main.py serve_ui.py ./
COPY REMOTE_MCP_REGISTRY.json REMOTE_A2A_REGISTRY.json DEMO_PRESETS.json ./
COPY --from=frontend-build /app/frontend/dist ./frontend/dist
RUN python -m pip install --upgrade pip && python -m pip install .
RUN mkdir -p artifacts
EXPOSE 8008
CMD ["python", "-m", "uvicorn", "a2a_vs_mcp.web:app", "--host", "0.0.0.0", "--port", "8008"]

