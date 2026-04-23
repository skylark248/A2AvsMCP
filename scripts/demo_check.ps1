param(
  [ValidateSet("dev", "demo", "llm")]
  [string]$Profile = "demo",
  [ValidateSet("in_process", "stdio", "http", "remote_http", "all")]
  [string]$Transport = "in_process",
  [string]$RemoteDbUrl = $env:REMOTE_MCP_DB_URL,
  [string]$RemoteDocsUrl = $env:REMOTE_MCP_DOCS_URL,
  [switch]$SkipTransportRun
)

$ErrorActionPreference = "Continue"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot

$failures = New-Object System.Collections.Generic.List[string]

function Check-Step {
  param(
    [string]$Name,
    [scriptblock]$Action
  )
  Write-Host "==> $Name"
  try {
    & $Action
    if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) {
      throw "Command exited with $LASTEXITCODE"
    }
    Write-Host "OK: $Name"
  } catch {
    $failures.Add("${Name}: $($_.Exception.Message)")
    Write-Host "FAIL: $Name - $($_.Exception.Message)"
  }
  $global:LASTEXITCODE = 0
}

Check-Step "Python package imports" {
  py -c "import fastapi, jinja2, mcp, openai, uvicorn; print('python deps ok')"
}

Check-Step "Seed database" {
  py -c "from pathlib import Path; import sys; root=Path.cwd(); sys.path.insert(0, str(root/'src')); from a2a_vs_mcp.dataset import DemoRepository; repo=DemoRepository(root); print(repo.db_path)"
}

Check-Step "Scenario fixtures" {
  py scripts\validate_scenarios.py
}

Check-Step "Demo presets" {
  py scripts\validate_presets.py
}

Check-Step "Artifact directories" {
  New-Item -ItemType Directory -Force artifacts\reports, artifacts\traces, artifacts\logs, artifacts\users | Out-Null
}

Check-Step "Platform state store" {
  py -c "from pathlib import Path; import sys; root=Path.cwd(); sys.path.insert(0, str(root/'src')); from a2a_vs_mcp.persistence import PlatformStore; store=PlatformStore(root); print(store.db_path)"
}

Check-Step "Frontend project files" {
  if (!(Test-Path frontend\package.json)) { throw "frontend\package.json missing" }
  if (!(Test-Path frontend\package-lock.json)) { throw "frontend\package-lock.json missing" }
  if (!(Test-Path frontend\node_modules)) { throw "frontend\node_modules missing; run npm.cmd install in frontend" }
  if (!(Test-Path frontend\dist\index.html)) { throw "frontend build missing; run npm.cmd run build in frontend" }
}

Check-Step "Generated API types" {
  if (!(Test-Path frontend\src\lib\types\api.generated.ts)) { throw "generated TypeScript API types missing" }
}

if ($Profile -eq "llm") {
  Check-Step "OpenAI configuration" {
    if (!$env:OPENAI_API_KEY) { throw "OPENAI_API_KEY is not set for llm profile" }
  }
} else {
  if (!$env:OPENAI_API_KEY) {
    Write-Host "INFO: OPENAI_API_KEY is not set; mock/demo profiles do not require it."
  }
}

if (!$SkipTransportRun) {
  $transports = if ($Transport -eq "all") { @("in_process", "stdio", "http", "remote_http") } else { @($Transport) }
  foreach ($item in $transports) {
    if ($item -eq "remote_http") {
      if (!$RemoteDbUrl -or !$RemoteDocsUrl) {
        $failures.Add("MCP transport smoke test (remote_http): RemoteDbUrl and RemoteDocsUrl are required for remote readiness checks.")
        Write-Host "FAIL: MCP transport smoke test (remote_http) - RemoteDbUrl and RemoteDocsUrl are required."
        continue
      }
    }
    Check-Step "MCP transport smoke test ($item)" {
      if ($item -eq "remote_http") {
        py scripts\check_remote_mcp.py --db-url $RemoteDbUrl --docs-url $RemoteDocsUrl --scenario setup_error --mode mcp | Out-Host
      } else {
        py main.py --profile dev --scenario setup_error --mode mcp --runtime mock --mcp-transport $item --no-save-report --no-export-logs | Out-Host
      }
    }
  }
}

if ($failures.Count -gt 0) {
  Write-Host ""
  Write-Host "Demo readiness: FAIL"
  $failures | ForEach-Object { Write-Host "- $_" }
  exit 1
}

Write-Host ""
Write-Host "Demo readiness: PASS"
exit 0
