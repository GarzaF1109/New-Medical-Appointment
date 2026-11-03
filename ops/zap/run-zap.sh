#!/usr/bin/env bash
# Corre OWASP ZAP contra la pila ya levantada (docker compose up -d) y deja
# los reportes en docs/security/zap-reports/. Pensado para correr igual en
# una laptop (Docker Desktop) y en GitHub Actions (runner Linux).
#
# Uso:
#   docker compose up --build -d
#   ./ops/zap/run-zap.sh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REPORT_DIR="$ROOT_DIR/docs/security/zap-reports"
ZAP_IMAGE="zaproxy/zap-stable:latest"
HOST_GATEWAY_FLAG="--add-host=host.docker.internal:host-gateway"

mkdir -p "$REPORT_DIR"
# El contenedor de ZAP solo ve lo que montamos en /zap/wrk; copiamos las
# reglas ahi para poder referenciarlas con una ruta relativa al contenedor.
cp "$ROOT_DIR/ops/zap/rules.tsv" "$REPORT_DIR/rules.tsv"

echo "==> Esperando a que el backend responda en :8000/health"
for _ in $(seq 1 30); do
  if curl -fs http://localhost:8000/health >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

echo "==> API scan (dirigido por el openapi.json que expone FastAPI)"
docker run --rm $HOST_GATEWAY_FLAG \
  -v "$REPORT_DIR:/zap/wrk/:rw" \
  "$ZAP_IMAGE" zap-api-scan.py \
  -t http://host.docker.internal:8000/openapi.json \
  -f openapi \
  -r api-report.html \
  -J api-report.json \
  -I \
  || echo "ZAP API scan termino con hallazgos (codigo distinto de 0); revisar api-report.html"

echo "==> Baseline scan (crawling pasivo de la interfaz)"
docker run --rm $HOST_GATEWAY_FLAG \
  -v "$REPORT_DIR:/zap/wrk/:rw" \
  "$ZAP_IMAGE" zap-baseline.py \
  -t http://host.docker.internal:8080 \
  -r baseline-report.html \
  -J baseline-report.json \
  -c /zap/wrk/rules.tsv \
  -I \
  || echo "ZAP baseline scan termino con hallazgos (codigo distinto de 0); revisar baseline-report.html"

echo "==> Reportes en $REPORT_DIR"
ls -la "$REPORT_DIR"
