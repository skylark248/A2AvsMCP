param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$HostAddress = "127.0.0.1"
)

$ErrorActionPreference = "Stop"
$env:PYTHONPATH = Join-Path $ProjectRoot "src"

$agents = @(
    @{ Role = "customer_data"; Port = 9101 },
    @{ Role = "documentation"; Port = 9102 },
    @{ Role = "policy_billing"; Port = 9103 }
)

Write-Host "Starting remote A2A specialist servers. Stop the printed process IDs to end the demo."
foreach ($agent in $agents) {
    $role = $agent.Role
    $port = $agent.Port
    $arguments = "-m a2a_vs_mcp.a2a.remote_server --role $role --host $HostAddress --port $port --project-root `"$ProjectRoot`""
    Start-Process -FilePath "py" -WorkingDirectory $ProjectRoot -ArgumentList $arguments
    Write-Host "Started $role on http://$HostAddress`:$port"
}


