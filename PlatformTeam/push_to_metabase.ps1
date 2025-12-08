
param (
    [string]$scriptname,
    [string]$arg1,
    [string]$arg2
)

Write-Output "Primary script: $scriptname"
Write-Output "Arg1: $arg1"
Write-Output "Arg2: $arg2"

# Initialize flags
$delete = $false
$deleteFlag = ""
$secondScript = ""

# Argument parsing
foreach ($arg in @($arg1, $arg2)) {
    if ($arg) {
        if ($arg -eq 'd' -or $arg -eq 'dfy') {
            $delete = $true
            $deleteFlag = $arg
        } elseif (-not $secondScript) {
            $secondScript = $arg
        }
    }
}

# Kill any previous oc.exe processes
Write-Output "Cleaning up previous oc.exe processes..."
taskkill /im oc.exe /f 2>$null

# Get PostgreSQL pod name
Write-Output "Retrieving PostgreSQL pod name..."
$POSTGRES_DB_POD = oc get pods --selector name=postgresql --field-selector status.phase=Running -o custom-columns=POD:.metadata.name --no-headers
if (-not $POSTGRES_DB_POD) {
    Write-Error "No running PostgreSQL pod found. Exiting."
    exit 1
}

Write-Output "Found pod: $POSTGRES_DB_POD"

# Start port-forward
Write-Output "Starting port-forward on 5431 -> 5432..."
$portForwardProcess = Start-Process -FilePath "oc.exe" -ArgumentList "port-forward", $POSTGRES_DB_POD, "5431:5432" -PassThru

# Wait for port-forward to be ready
Write-Output "Waiting for port-forward to establish..."
$maxWait = 60
$elapsed = 0
while (-not (Test-NetConnection -ComputerName "localhost" -Port 5431).TcpTestSucceeded -and $elapsed -lt $maxWait) {
    Start-Sleep -Seconds 5
    $elapsed += 5
    Write-Output "Checking port-forward... ($elapsed sec)"
}

if ($elapsed -ge $maxWait) {
    Write-Error "Port-forward failed to establish within $maxWait seconds. Exiting."
    Stop-Process -Id $portForwardProcess.Id -Force
    exit 1
}

Write-Output "Port-forward established successfully."

# Run primary Python script
if ($delete) {
    Write-Output "Running: python $scriptname -$deleteFlag"
    Start-Process -FilePath "python.exe" -ArgumentList $scriptname, "-$deleteFlag" -Wait
} else {
    Write-Output "Running: python $scriptname"
    Start-Process -FilePath "python.exe" -ArgumentList $scriptname -Wait
}

# Run second script if provided
if ($secondScript) {
    Write-Output "Running second script: python $secondScript"
    Start-Process -FilePath "python.exe" -ArgumentList $secondScript -Wait
}

# Cleanup port-forward
Write-Output "Cleaning up port-forward process..."
Stop-Process -Id $portForwardProcess.Id -Force
Write-Output "All tasks completed successfully."
