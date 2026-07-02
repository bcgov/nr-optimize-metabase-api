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
$POSTGRES_DB_POD = oc get pods --selector name=postgresql --field-selector status.phase=Running `
    -o custom-columns=POD:.metadata.name --no-headers

if (-not $POSTGRES_DB_POD) {
    Write-Error "No running PostgreSQL pod found. Exiting."
    exit 1
}

Write-Output "Found pod: $POSTGRES_DB_POD"

# Start port-forward in background job (more stable than Start-Process)
Write-Output "Starting port-forward using job..."
$portJob = Start-Job -ScriptBlock {
    param($pod)
    oc port-forward $pod 5431:5432
} -ArgumentList $POSTGRES_DB_POD

# Wait for port-forward to be ready
Write-Output "Waiting for port-forward to establish..."
$maxWait = 60
$elapsed = 0

while (-not (Test-NetConnection -ComputerName "localhost" -Port 5431).TcpTestSucceeded -and $elapsed -lt $maxWait) {
    Start-Sleep -Seconds 2
    $elapsed += 2
    Write-Output "Checking port-forward... ($elapsed sec)"
}

if ($elapsed -ge $maxWait) {
    Write-Error "Port-forward failed to establish within $maxWait seconds."
    # Stop the job (no -Force in PS 5.1)
    if ($portJob.State -eq "Running") {
        Stop-Job -Job $portJob
    }

    # Wait briefly to ensure it's stopped
    Start-Sleep -Seconds 1

    # Remove the job using -Force (supported)
    Remove-Job -Job $portJob -Force
        exit 1
    }

Write-Output "Port-forward established successfully."

# Extra stabilization delay (prevents race conditions)
Start-Sleep -Seconds 3

# Optional: confirm job is still running
$jobState = (Get-Job -Id $portJob.Id).State
Write-Output "Port-forward job state: $jobState"

if ($jobState -ne "Running") {
    Write-Error "Port-forward job is not running. Exiting."
    # Stop the job (no -Force in PS 5.1)
    if ($portJob.State -eq "Running") {
        Stop-Job -Job $portJob
    }

    # Wait briefly to ensure it's stopped
    Start-Sleep -Seconds 1

    # Remove the job using -Force (supported)
    Remove-Job -Job $portJob -Force
        exit 1
    }

# Run primary Python script
if ($delete) {
    Write-Output "Executing Python script: $scriptname -$deleteFlag"
    & python $scriptname, "-$deleteFlag"
} else {
    Write-Output "Executing Python script: $scriptname"
    & python $scriptname
}

# Run second script if provided
if ($secondScript) {
    Write-Output "Executing second Python script: $secondScript"
    & python $secondScript
}

# Ensure everything has flushed before teardown
Write-Output "Finalizing operations..."
Start-Sleep -Seconds 2

# Cleanup port-forward
Write-Output "Stopping port-forward..."

if ($portJob) {
    try {
        if ($portJob.State -eq "Running") {
            Stop-Job -Job $portJob
        }

        # Give time for graceful shutdown
        Start-Sleep -Seconds 1

        Remove-Job -Job $portJob -Force -ErrorAction SilentlyContinue
    }
    catch {
        Write-Warning "Failed to fully clean up port-forward job: $_"
    }
}

Write-Output "All tasks completed successfully."