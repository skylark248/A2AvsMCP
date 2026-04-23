param(
  [switch]$ClearReports,
  [switch]$ClearTraces,
  [switch]$ClearLogs,
  [switch]$ClearUserArtifacts,
  [switch]$ClearTelemetry,
  [switch]$CleanGenerated,
  [switch]$ClearTmpArtifacts,
  [switch]$ResetRemoteRegistry,
  [switch]$ClearFrontendBuild,
  [switch]$RegenerateApiTypes,
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot

if ($CleanGenerated) {
  $ClearReports = $true
  $ClearTraces = $true
  $ClearLogs = $true
  $ClearUserArtifacts = $true
  $ClearTelemetry = $true
  $ClearTmpArtifacts = $true
}

function Remove-ArtifactFiles {
  param(
    [string]$Path,
    [string[]]$Patterns
  )
  if (!(Test-Path $Path)) { return }
  $root = (Resolve-Path $Path).Path
  foreach ($pattern in $Patterns) {
    Get-ChildItem -LiteralPath $root -Filter $pattern -File | ForEach-Object {
      if ($DryRun) {
        Write-Host "DRY RUN remove $($_.FullName)"
      } else {
        Remove-Item -LiteralPath $_.FullName -Force
        Write-Host "Removed $($_.FullName)"
      }
    }
  }
}

function Remove-PathIfPresent {
  param([string]$Path)
  if (!(Test-Path $Path)) { return }
  $resolved = (Resolve-Path $Path).Path
  if ($DryRun) {
    Write-Host "DRY RUN remove $resolved"
  } else {
    Remove-Item -LiteralPath $resolved -Recurse -Force
    Write-Host "Removed $resolved"
  }
}

Write-Host "Resetting seed database artifacts"
Remove-PathIfPresent artifacts\support_demo.db
Remove-PathIfPresent artifacts\seed_manifest.json
if (!$DryRun) {
  py -c "from pathlib import Path; import sys; root=Path.cwd(); sys.path.insert(0, str(root/'src')); from a2a_vs_mcp.dataset import DemoRepository; repo=DemoRepository(root); print(repo.db_path)"
}

if ($ClearReports) { Remove-ArtifactFiles artifacts\reports @("*.json", "*.html", "*.pdf") }
if ($ClearTraces) { Remove-ArtifactFiles artifacts\traces @("*.json") }
if ($ClearLogs) { Remove-ArtifactFiles artifacts\logs @("*.ndjson") }
if ($ClearUserArtifacts) { Remove-PathIfPresent artifacts\users }
if ($ClearTelemetry) { Remove-PathIfPresent artifacts\platform_state.db }
if ($ClearFrontendBuild) { Remove-PathIfPresent frontend\dist }
if ($ClearTmpArtifacts) {
  Remove-PathIfPresent .tmp\test_artifacts
  Remove-PathIfPresent .tmp\compose_smoke_artifacts
}

if ($ResetRemoteRegistry) {
  if ($DryRun) {
    Write-Host "DRY RUN sync REMOTE_MCP_REGISTRY.json into platform state"
  } else {
    py -c "from pathlib import Path; import sys; root=Path.cwd(); sys.path.insert(0, str(root/'src')); from a2a_vs_mcp.persistence import PlatformStore; from a2a_vs_mcp.remote_registry import RemoteMCPRegistry; registry=RemoteMCPRegistry(root, PlatformStore(root)); synced=registry.sync_from_file(); print(f'Synced remote MCP registry entries: {len(synced)}')"
  }
}

if ($RegenerateApiTypes) {
  if ($DryRun) {
    Write-Host "DRY RUN regenerate frontend API types"
  } else {
    py scripts\generate_api_types.py
  }
}

Write-Host "Demo reset complete"
