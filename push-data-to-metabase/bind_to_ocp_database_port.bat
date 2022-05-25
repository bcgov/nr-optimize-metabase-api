REM -----------------Bind the OC database port to a PC for data upload--------------------
REM ALLOWS_REMOTE_CONNECTIONS is a string which must match an environment value name on the pod via the deployment config
REM Pod name cannot have . or / in the name.
SET ENV_VARIABLE_NAME=ALLOWS_REMOTE_CONNECTIONS
oc get pods -o json | jq .items > auto_gen_temp_file
REM Replace . and / with _
powershell -Command "(gc auto_gen_temp_file) -replace '[\./]', '_' | Out-File -encoding ASCII auto_gen_temp_file"
REM Filter with JQ
type auto_gen_temp_file | jq "[.[] | { name: .metadata.name, containers: .spec.containers}]" | jq -r ".[] | select(.name != null) | select(.containers[] != null)| select(.containers[].env != null)| select(.containers[].env[] | .name == \"%ENV_VARIABLE_NAME%\")" | jq .name > auto_gen_temp_file2
REM Erase quotation marks
powershell -Command "(gc auto_gen_temp_file2) -replace '[\""]', '' | Out-File -encoding ASCII auto_gen_temp_file3"
REM Stash pod name into environment variable
SET /p POD_NAME= <auto_gen_temp_file3
del auto_gen_temp_file
del auto_gen_temp_file2
del auto_gen_temp_file3
REM Bind Pod
start "oc-port-forward" cmd /k "SET PATH=%cd%;%PATH% & oc port-forward %POD_NAME% 5432:5432"
