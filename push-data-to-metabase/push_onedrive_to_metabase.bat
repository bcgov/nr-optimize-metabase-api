REM Script requires that user is already logged in to OC with appropriate credentials
REM Correct project must be selected
REM Optional parameter -d will delete records before adding new ones from csv


REM Run Bind Port script
start "port-bind" cmd /k "bind_to_ocp_database_port.bat"

REM Push to OneDrive Table
"python.exe" push_onedrive_to_metabase.py %1

REM Clean up!
taskkill /FI "WindowTitle eq port-bind*" /T /F