$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$StaticPort = 4173
$ApiPort = 8000

Write-Host "[1/5] Verificando estructura..."
$required = @(
  "index.html",
  "styles.css",
  "app.js",
  "SCENI_01_NUEVO/app/main.py"
)
foreach ($file in $required) {
  if (-not (Test-Path (Join-Path $Root $file))) {
    throw "Falta archivo requerido: $file"
  }
}

Write-Host "[2/5] Levantando sitio estático en puerto $StaticPort..."
$static = Start-Process -FilePath "python" -ArgumentList "-m http.server $StaticPort --directory `"$Root`"" -PassThru
Start-Sleep -Seconds 1

Write-Host "[3/5] Levantando API demo en puerto $ApiPort..."
$apiMain = Join-Path $Root "SCENI_01_NUEVO/app/main.py"
$api = Start-Process -FilePath "python" -ArgumentList "`"$apiMain`"" -PassThru
Start-Sleep -Seconds 1

try {
  Write-Host "[4/5] Ejecutando smoke tests..."
  $home = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$StaticPort/"
  if ($home.Content -notmatch "SCENI_01") { throw "Frontend no contiene SCENI_01" }

  $js = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$StaticPort/app.js"
  if ($js.Content -notmatch "setupDashboard") { throw "app.js no contiene lógica dashboard" }

  $ready = $false
  for ($i = 0; $i -lt 10; $i++) {
    try {
      Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$ApiPort/health" | Out-Null
      $ready = $true
      break
    }
    catch {
      Start-Sleep -Milliseconds 500
    }
  }
  if (-not $ready) { throw "API no disponible en puerto $ApiPort" }

  $apiRoot = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$ApiPort/"
  if ($apiRoot.Content -notmatch '"status":"ok"|"status": "ok"') { throw "API / no responde status ok" }

  $health = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$ApiPort/health"
  if ($health.Content -notmatch '"status":"healthy"|"status": "healthy"') { throw "API /health no responde healthy" }

  $docs = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$ApiPort/docs"
  if ($docs.Content -notmatch "available_endpoints") { throw "API /docs no responde" }

  $storage = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$ApiPort/api/v1/storage/status"
  if ($storage.Content -notmatch "designs_v2") { throw "API storage/status no responde" }

  Write-Host "[5/5] OK - Desarrollo en acción"
  Write-Host "- Frontend: http://localhost:$StaticPort"
  Write-Host "- API:      http://localhost:$ApiPort/docs"
}
finally {
  if ($static -and -not $static.HasExited) { Stop-Process -Id $static.Id -Force }
  if ($api -and -not $api.HasExited) { Stop-Process -Id $api.Id -Force }
}
