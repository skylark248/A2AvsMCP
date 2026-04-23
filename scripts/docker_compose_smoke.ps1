param(
    [switch]$KeepRunning,
    [switch]$SkipRemoteRun,
    [string]$ArtifactRoot = ".tmp\compose_smoke_artifacts"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")

function Invoke-Checked {
    param(
        [string]$Command,
        [string[]]$Arguments
    )

    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Command $($Arguments -join ' ') failed with exit code $LASTEXITCODE"
    }
}

function Wait-WebHealth {
    param(
        [string]$Url,
        [int]$TimeoutSeconds = 45
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $lastError = $null
    while ((Get-Date) -lt $deadline) {
        try {
            $payload = Invoke-RestMethod -Uri $Url -TimeoutSec 3
            if ($payload.status -eq "ok") {
                Write-Host "ok web health: $Url"
                return
            }
            $lastError = "unexpected status '$($payload.status)'"
        } catch {
            $lastError = $_.Exception.Message
        }
        Start-Sleep -Seconds 1
    }

    throw "Web health check failed for $Url after $TimeoutSeconds seconds: $lastError"
}

Push-Location $ProjectRoot
try {
    Write-Host "Checking Docker Compose configuration..."
    Invoke-Checked "docker" @("compose", "config")

    Write-Host "Starting web app and hosted remote A2A specialists..."
    Invoke-Checked "docker" @("compose", "up", "--build", "-d")

    Write-Host "Checking web API health..."
    Wait-WebHealth "http://127.0.0.1:8008/api/health"

    Write-Host "Checking remote A2A specialist Agent Cards and tasks..."
    Invoke-Checked "py" @("scripts\check_remote_a2a.py")

    if (-not $SkipRemoteRun) {
        Write-Host "Running golden demo smoke with remote A2A included..."
        Invoke-Checked "py" @("scripts\golden_demo_smoke.py", "--include-remote-a2a", "--artifact-root", $ArtifactRoot)
    }

    Write-Host "Docker Compose smoke: PASS"
}
finally {
    if (-not $KeepRunning) {
        Write-Host "Stopping Docker Compose services..."
        Invoke-Checked "docker" @("compose", "down")
    }
    Pop-Location
}