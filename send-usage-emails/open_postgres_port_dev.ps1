
# Script requires that user is already logged in to OC with appropriate credentials
# Correct project must be selected

# Clean up any open port binds from previous runs
# Will display "ERROR: The process "oc.exe" not found." if there was not already an oc in progress, which is an unintuitive success message.
taskkill /im oc.exe /f

# Get the data pod name from the current namespace
$POSTGRES_DB_POD=oc get pods --selector name=postgresql --field-selector status.phase=Running -o custom-columns=POD:.metadata.name --no-headers
# Launch a new thread with a port bind
$PATH=$Env:Path
# Start-Process "oc-port-forward" cmd /k "SET PATH=$CD;$PATH & oc port-forward $POSTGRES_DB_POD 5432:5432"
Start-Process -FilePath "oc.exe" -ArgumentList "port-forward",$POSTGRES_DB_POD,"5432:5432" -PassThru
