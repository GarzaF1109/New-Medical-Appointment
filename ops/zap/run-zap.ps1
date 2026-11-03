# Script de PowerShell para correr OWASP ZAP automatizado en Windows
$ErrorActionPreference = "Continue"

$rootDir = (Get-Item $PSScriptRoot\..\..).FullName
$reportDir = Join-Path $rootDir "docs\security\zap-reports"
$zapImage = "zaproxy/zap-stable:latest"

if (-not (Test-Path $reportDir)) {
    New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
}

Copy-Item "$rootDir\ops\zap\rules.tsv" "$reportDir\rules.tsv" -Force

Write-Host "==> 1. Verificando que el backend responda en :8000/health..."
try {
    $res = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 3
    Write-Host "Backend saludable: $($res.status)"
} catch {
    Write-Warning "El backend no responde en localhost:8000. Asegurate de tener docker compose up -d activo."
}

Write-Host "==> 2. Ejecutando ZAP API Scan (dirigido por openapi.json de FastAPI)..."
docker run --rm --add-host=host.docker.internal:host-gateway `
  -v "${reportDir}:/zap/wrk/:rw" `
  $zapImage zap-api-scan.py `
  -t http://host.docker.internal:8000/openapi.json `
  -f openapi `
  -r api-report.html `
  -J api-report.json `
  -I

Write-Host "==> 3. Ejecutando ZAP Baseline Scan (crawling de la interfaz web en :8085)..."
docker run --rm --add-host=host.docker.internal:host-gateway `
  -v "${reportDir}:/zap/wrk/:rw" `
  $zapImage zap-baseline.py `
  -t http://host.docker.internal:8085 `
  -r baseline-report.html `
  -J baseline-report.json `
  -c /zap/wrk/rules.tsv `
  -I

Write-Host "==> Reportes generados en: $reportDir"
Get-ChildItem $reportDir
