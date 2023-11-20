# Script requires that user is already logged in to OC with appropriate credentials
# Correct project must be selected
# Arguments can be passed in like so: 
# powershell .\push_to_metabase.ps1 push_objstor_to_metabase.py
# powershell ./push_to_metabase.ps1 push_hostingexpenses_to_metabase.py,-dfy
# powershell .\push_to_metabase.ps1 push_h_sfp_to_metabase_dsr.py,-d
# powershell .\push_to_metabase.ps1 push_h_sfp_to_metabase_dsr.py,-d,push_sfp_owners_to_metabase.py
# powershell .\push_to_metabase.ps1 push_h_sfp_to_metabase_dsr.py,push_sfp_owners_to_metabase.py


param (
    [string]$scriptname,
    [string]$arg1,
    [string]$arg2
)
write-output $scriptname
write-output $arg1
write-output $arg2

$delete = $false
$secondScript = ""

if ($arg1) {
    if ($arg1 == '-d' or $arg1 == '-dfy'){
        $delete = $true
    } else {
        $secondScript = $arg1
    }
}
if ($arg2) {
    if ($arg2 == '-d' or $arg2 == '-dfy'){
        $delete = $true
    } else {
        $secondScript = $arg2
    }
}

# Clean up any open pot binds from previous runs
taskkill /im oc.exe /f

# Get the data pod name from the current namespace
$POSTGRES_DB_POD=oc get pods --selector name=postgresql --field-selector status.phase=Running -o custom-columns=POD:.metadata.name --no-headers
# Launch a new thread with a port bind
$PATH=$Env:Path
# Start-Process "oc-port-forward" cmd /k "SET PATH=$CD;$PATH & oc port-forward $POSTGRES_DB_POD 5432:5432"
Start-Process -FilePath "oc.exe" -ArgumentList "port-forward",$POSTGRES_DB_POD,"5432:5432" -PassThru

# Run Bind Port script and wait for it to run
timeout /t 50

# Push to Table using python script
if ($delete){
    write-output "Run: "+$scriptname+ " with " + $delete
    # Start-Process -FilePath "python.exe" -ArgumentList $scriptname,$delete -Wait
} else {
    write-output "Run: "+$scriptname
    # Start-Process -FilePath "python.exe" -ArgumentList $scriptname -Wait
}

# Run a second script after the first
if ($secondScript){
    write-output "Run: "+$secondScript
    # Start-Process -FilePath "python.exe" -ArgumentList $secondScript -Wait
}

# Clean up any open pot binds from previous runs
taskkill /im oc.exe /f
