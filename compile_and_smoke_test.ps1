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
  if ($js.Content -notmatch "renderCards") { throw "app.js no contiene renderCards" }

  $apiRoot = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$ApiPort/"
  if ($apiRoot.Content -notmatch '"status": "ok"') { throw "API / no responde status ok" }

  $health = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$ApiPort/health"
  if ($health.Content -notmatch '"status": "healthy"') { throw "API /health no responde healthy" }

  Write-Host "[5/5] OK - Desarrollo en acción"
  Write-Host "- Frontend: http://localhost:$StaticPort"
  Write-Host "- API:      http://localhost:$ApiPort/health"
}
finally {
  if ($static -and -not $static.HasExited) { Stop-Process -Id $static.Id -Force }
  if ($api -and -not $api.HasExited) { Stop-Process -Id $api.Id -Force }
}
