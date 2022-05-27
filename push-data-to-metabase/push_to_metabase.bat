REM Script requires that user is already logged in to OC with appropriate credentials
REM Correct project must be selected

REM Clean up any open port binds from previous last runs!
taskkill /FI "WindowTitle eq oc-port-forward*" /T /F
taskkill /FI "WindowTitle eq Administrator: port-bind" /T /F
taskkill /FI "WindowTitle eq port-bind" /T /F
REM Clean up complete!

REM Run Bind Port script and wait for it to run
start "port-bind" cmd /k "bind_to_ocp_database_port.bat"
timeout /t 50

REM Push to Objstor Table
REM Optional parameter -d will delete records before adding new ones from csv
REM python.exe push_objstor_to_metabase.py -d
"python.exe" %1 %2

REM Clean up any open port bind windows!
taskkill /FI "WindowTitle eq oc-port-forward*" /T /F
taskkill /FI "WindowTitle eq Administrator: port-bind" /T /F
taskkill /FI "WindowTitle eq port-bind" /T /F
REM Clean up complete!