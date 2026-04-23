param(
  [ValidateSet("dev", "demo", "llm")]
  [string]$Profile = "demo",
  [switch]$Install,
  [switch]$BuildFrontend,
  [switch]$SkipCheck
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot

if ($Install) {
  Push-Location frontend
  npm.cmd install
  Pop-Location
}

if ($BuildFrontend -or !(Test-Path frontend\dist\index.html)) {
  Push-Location frontend
  npm.cmd run build
  Pop-Location
}

if (!$SkipCheck) {
  powershell.exe -ExecutionPolicy Bypass -File scripts\demo_check.ps1 -Profile $Profile -Transport in_process -SkipTransportRun
}

$env:A2A_VS_MCP_PROFILE = $Profile
Write-Host "Starting FastAPI demo UI on http://127.0.0.1:8008 with profile '$Profile'"
py serve_ui.py
