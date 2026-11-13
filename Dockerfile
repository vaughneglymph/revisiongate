FROM node:22-bookworm-slim AS ui
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.13-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8080
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir --disable-pip-version-check -r requirements.txt
COPY backend/ ./backend/
COPY fixtures/ ./fixtures/
COPY prompts/ ./prompts/
COPY schema/ ./schema/
COPY --from=ui /build/dist ./frontend/dist
USER 65532:65532
EXPOSE 8080
CMD ["sh", "-c", "exec python -m uvicorn backend.main:app --host 0.0.0.0 --port \"$PORT\""]
