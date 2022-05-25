REM Script requires that user is already logged in to OC with appropriate credentials
REM Correct project must be selected


REM Run Bind Port script and wait for it to run
start "port-bind" cmd /k "bind_to_ocp_database_port.bat"
timeout /t 25

REM Push to Objstor Table
REM Optional parameter -d will delete records before adding new ones from csv
REM python.exe push_objstor_to_metabase.py -d
"python.exe" %1 %2

REM Clean up!
taskkill /FI "WindowTitle eq port-bind*" /T /F