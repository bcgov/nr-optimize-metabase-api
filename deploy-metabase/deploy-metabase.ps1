# NOTE: Script assumes user is signed in with OC and does not check
# NOTE: Script assumes it is in the "deploy-metabase" folder beside the dc and nsp yamls

# Set configuration Values
$BASE_URL="https://raw.githubusercontent.com/bcgov/nr-showcase-devops-tools/master/tools/metabase/openshift"
$ADMIN_EMAIL="iitd.optimize@gov.bc.ca"
$TOOLS_NAMESPACE="15be76-tools"
$ORIGIN_NAMESPACE="15be76-test"
$TARGET_NAMESPACE="15be76-dev"
$PREFIX="iitco-"
$SUFFIX="-dev"
$METABASE_VERSION="v0.41.5"

Write-Output("Deploying Metabase to {0} with data from {1}" -f $TARGET_NAMESPACE, $ORIGIN_NAMESPACE)
Write-Output("")

# Get the database pod names from the origin namespace 
Write-Output("Getting the database pod names from the origin namespace...")
$ORIGIN_METABASE_DB_POD=oc get pods -n $ORIGIN_NAMESPACE --selector name=metabase-postgresql --field-selector status.phase=Running -o custom-columns=POD:.metadata.name --no-headers
$ORIGIN_POSTGRES_DB_POD=oc get pods -n $ORIGIN_NAMESPACE --selector name=postgresql --field-selector status.phase=Running -o custom-columns=POD:.metadata.name --no-headers
Write-Output("Getting the database pod names from the origin namespace... DONE")
Write-Output("")

# Add the role to the default service account in target namespace which allows it to pull images from the tools namespace
# Can check success using: oc describe rolebinding.rbc -n $TOOLS_NAMESPACE
Write-Output("Adding the role to the default service account in target namespace which allows it to pull images...")
oc policy add-role-to-user system:image-puller system:serviceaccount:$TARGET_NAMESPACE`:default -n $TOOLS_NAMESPACE
Write-Output("Adding the role to the default service account in target namespace which allows it to pull images... DONE")
Write-Output("")

# Apply quickstart network security policies
# Note: This is a different flavor of the original metabase nsps, but works. 
Write-Output("Applying quickstart network security policies...")
oc -n $TARGET_NAMESPACE process -f quickstart-nsp.yaml NAMESPACE=$TARGET_NAMESPACE | oc -n $TARGET_NAMESPACE apply -f -
Write-Output("Applying quickstart network security policies... DONE")
Write-Output("")

# Deploy the build config to the tools namespace and build :latest image:
Write-Output("Deploying the build config to the tools namespace and build...")
oc process -n $TOOLS_NAMESPACE -f $BASE_URL/metabase.bc.yaml -p METABASE_VERSION=$METABASE_VERSION -o yaml | oc apply -n $TOOLS_NAMESPACE -f -
Write-Output("Deploying the build config to the tools namespace and build... DONE")
Write-Output("")

# Create copies of origin databases
Write-Output("Creating copies of origin databases...")
oc exec $ORIGIN_METABASE_DB_POD -n $ORIGIN_NAMESPACE -- pg_dumpall -f /tmp/all_metabase_postgresql_dbs.sql
oc exec $ORIGIN_POSTGRES_DB_POD -n $ORIGIN_NAMESPACE -- pg_dumpall -f /tmp/all_postgresql_dbs.sql
Write-Output("Creating copies of origin databases... DONE")
Write-Output("")

# Create folders to store the sql in if they do not already exist:
Write-Output("Creating folders to store the sql in if they do not already exist...")
New-Item -ItemType Directory -Force -Path temp-metabase
New-Item -ItemType Directory -Force -Path temp-postgresql
Write-Output("Creating folders to store the sql in if they do not already exist... DONE")
Write-Output("")

# Copy origin database backups to local temp folders
Write-Output("Copying origin database backups to local temp folders...")
oc rsync --progress -n $ORIGIN_NAMESPACE $ORIGIN_METABASE_DB_POD`:/tmp/all_metabase_postgresql_dbs.sql ./temp-metabase/
oc rsync --progress -n $ORIGIN_NAMESPACE $ORIGIN_POSTGRES_DB_POD`:/tmp/all_postgresql_dbs.sql ./temp-postgresql/
Write-Output("Copying origin database backups to local temp folders... DONE")
Write-Output("")

# Clean copies off of origin pods
Write-Output("Cleaning copies off of origin pods...")
oc exec $ORIGIN_METABASE_DB_POD -n $ORIGIN_NAMESPACE -- rm /tmp/all_metabase_postgresql_dbs.sql
oc exec $ORIGIN_POSTGRES_DB_POD -n $ORIGIN_NAMESPACE -- rm /tmp/all_postgresql_dbs.sql
Write-Output("Cleaning copies off of origin pods... DONE")
Write-Output("")


# Delete clear metabase items in new namespace
Write-Output("Deleting old metabase items...")
oc delete deployment metabase-postgresql -n $TARGET_NAMESPACE
oc delete deployment postgresql -n $TARGET_NAMESPACE
oc delete deploymentconfig metabase -n $TARGET_NAMESPACE
oc delete deploymentconfig metabase-postgresql -n $TARGET_NAMESPACE
oc delete deploymentconfig postgresql -n $TARGET_NAMESPACE
oc delete pvc metabase -n $TARGET_NAMESPACE
oc delete pvc metabase-postgresql -n $TARGET_NAMESPACE
oc delete pvc postgresql -n $TARGET_NAMESPACE
oc delete service metabase -n $TARGET_NAMESPACE
oc delete service metabase-postgresql -n $TARGET_NAMESPACE
oc delete service postgresql -n $TARGET_NAMESPACE
oc delete route metabase -n $TARGET_NAMESPACE
oc delete secret metabase-secret -n $TARGET_NAMESPACE
oc delete secret metabase-postgresql -n $TARGET_NAMESPACE
oc delete secret postgresql -n $TARGET_NAMESPACE
Write-Output("Deleting old metabase items... DONE")
Write-Output("")

# Copy origin secrets to new namespace
Write-Output("Copying origin secrets to new namespace...")
oc get secret metabase-secret -n $ORIGIN_NAMESPACE -o yaml | sed "s/namespace:.*/namespace: $TARGET_NAMESPACE/" | oc apply -n $TARGET_NAMESPACE -f -
oc get secret metabase-postgresql -n $ORIGIN_NAMESPACE -o yaml | sed "s/namespace:.*/namespace: $TARGET_NAMESPACE/" | oc apply -n $TARGET_NAMESPACE -f -
oc get secret postgresql -n $ORIGIN_NAMESPACE -o yaml | sed "s/namespace:.*/namespace: $TARGET_NAMESPACE/" | oc apply -n $TARGET_NAMESPACE -f -
Write-Output("Copying origin secrets to new namespace... DONE")
Write-Output("")

# Copy origin database creation secrets to variables
Write-Output("Copying origin database creation secrets to variables...")
$encoded_value = oc get secret metabase-postgresql -n $ORIGIN_NAMESPACE -o jsonpath="{.data['database-user']}"
$METABASE_DB_USER = [Text.Encoding]::Utf8.GetString([Convert]::FromBase64String($encoded_value))

$encoded_value = oc get secret metabase-postgresql -n $ORIGIN_NAMESPACE -o jsonpath="{.data['database-password']}"
$METABASE_DB_PASS = [Text.Encoding]::Utf8.GetString([Convert]::FromBase64String($encoded_value))

$encoded_value = oc get secret metabase-postgresql -n $ORIGIN_NAMESPACE -o jsonpath="{.data['database-name']}"
$METABASE_DB_NAME = [Text.Encoding]::Utf8.GetString([Convert]::FromBase64String($encoded_value))

$encoded_value = oc get secret postgresql -n $ORIGIN_NAMESPACE -o jsonpath="{.data['database-user']}"
$POSTGRES_USER = [Text.Encoding]::Utf8.GetString([Convert]::FromBase64String($encoded_value))

$encoded_value = oc get secret postgresql -n $ORIGIN_NAMESPACE -o jsonpath="{.data['database-password']}"
$POSTGRES_PASS = [Text.Encoding]::Utf8.GetString([Convert]::FromBase64String($encoded_value))

$encoded_value = oc get secret postgresql -n $ORIGIN_NAMESPACE -o jsonpath="{.data['database-name']}"
$POSTGRES_DB_NAME = [Text.Encoding]::Utf8.GetString([Convert]::FromBase64String($encoded_value))
Write-Output("Copying origin database creation secrets to variables... DONE")
Write-Output("")

# Wait for old pods to spin down...
Write-Output("Checking for old pods and waiting for them to spin down...")
function Wait-For-OldPodsToGoDown {
    param (
        $DeploymentConfig, $Namespace
    )
    $POD_NAME=oc get pods -n $Namespace --selector deploymentconfig=$DeploymentConfig --field-selector status.phase=Running -o custom-columns=POD:.metadata.name --no-headers
    WHILE (-not $null -eq $POD_NAME) {
        Write-Output("Waiting for old pod {0} for {1} to spin down..." -f $POD_NAME, $DeploymentConfig)
        Start-Sleep -Seconds 5
        $POD_NAME=oc get pods -n $Namespace --selector deploymentconfig=$DeploymentConfig --field-selector status.phase=Running -o custom-columns=POD:.metadata.name --no-headers
        if ($null -eq $POD_NAME) {
            Write-Output("Waiting for old pod for {0} to spin down... DONE" -f $DeploymentConfig)
        }
    }
}
Wait-For-OldPodsToGoDown -DeploymentConfig 'metabase-postgresql' -Namespace $TARGET_NAMESPACE 
Wait-For-OldPodsToGoDown -DeploymentConfig 'postgresql' -Namespace $TARGET_NAMESPACE 
Write-Output("Checking for old pods and waiting for them to spin down... DONE")
Write-Output("")

# Create new database deployments and services
Write-Output("Creating new database deployments and services...")
oc new-app -n $TARGET_NAMESPACE -p POSTGRESQL_USER=$METABASE_DB_USER -p POSTGRESQL_PASSWORD=$METABASE_DB_PASS -p POSTGRESQL_DATABASE=$METABASE_DB_NAME -p DATABASE_SERVICE_NAME=metabase-postgresql postgresql:10-el8 --name=metabase-postgresql --template=postgresql-persistent
oc new-app -n $TARGET_NAMESPACE -p POSTGRESQL_USER=$POSTGRES_USER -p POSTGRESQL_PASSWORD=$POSTGRES_PASS -p POSTGRESQL_DATABASE=$POSTGRES_DB_NAME -p DATABASE_SERVICE_NAME=postgresql postgresql:10-el8 --name=postgresql --template=postgresql-persistent
Write-Output("Creating new database deployments and services... DONE")
Write-Output("")

# Note: persistent postgres template comes with extra deployment
Write-Output("Deleting surplus deployment...")
oc delete deployment metabase-postgresql -n $TARGET_NAMESPACE
oc delete deployment postgresql -n $TARGET_NAMESPACE
Write-Output("Deleting surplus deployment... DONE")

Write-Output("Overwriting default services...")
Get-Content .\metabase-postgresql.service.yaml | oc replace -f -
Get-Content .\postgresql.service.yaml | oc replace -f -
Write-Output("Overwriting default services... DONE")
Write-Output("")

# Get the new pod names, will need to wait for the postgres pod to finish being created
WHILE (($null -eq $TARGET_METABASE_DB_POD) -or ($null -eq $TARGET_POSTGRES_DB_POD)) {    
    Write-Output("Waiting for new pods to be created...")
    Start-Sleep -Seconds 5
    $TARGET_METABASE_DB_POD=oc get pods -n $TARGET_NAMESPACE --selector deployment=metabase-postgresql --field-selector status.phase=Running -o custom-columns=POD:.metadata.name --no-headers
    $TARGET_POSTGRES_DB_POD=oc get pods -n $TARGET_NAMESPACE --selector deploymentconfig=postgresql --field-selector status.phase=Running -o custom-columns=POD:.metadata.name --no-headers

}
# There's a split-second where there's a deployment pod instead of the database pod. Try again in a while.
Start-Sleep -Seconds 5
$TARGET_METABASE_DB_POD = $null
$TARGET_POSTGRES_DB_POD = $null
WHILE (($null -eq $TARGET_METABASE_DB_POD) -or ($null -eq $TARGET_POSTGRES_DB_POD)) {    
    Write-Output("Waiting for new pods to be created...")
    Start-Sleep -Seconds 5
    $TARGET_METABASE_DB_POD=oc get pods -n $TARGET_NAMESPACE --selector deploymentconfig=metabase-postgresql --field-selector status.phase=Running -o custom-columns=POD:.metadata.name --no-headers
    $TARGET_POSTGRES_DB_POD=oc get pods -n $TARGET_NAMESPACE --selector deploymentconfig=postgresql --field-selector status.phase=Running -o custom-columns=POD:.metadata.name --no-headers
}
Write-Output("Pod online: {0}" -f $TARGET_METABASE_DB_POD)
Write-Output("Pod online: {0}" -f $TARGET_POSTGRES_DB_POD)
Write-Output("Waiting for new pods to come online... DONE")
Write-Output("")

Write-Output("Waiting for new pod ready status (10 minute timeout)...")
oc wait -n $TARGET_NAMESPACE --for=condition=Ready pod/$TARGET_METABASE_DB_POD --timeout=600s
oc wait -n $TARGET_NAMESPACE --for=condition=Ready pod/$TARGET_POSTGRES_DB_POD --timeout=600s
Write-Output("Waiting for new pod ready status... DONE")
Write-Output("")

# Copy the origin databases to the new deployments
Write-Output("Copying the origin databases to the new deployments...")
oc rsync --progress --no-perms -n $TARGET_NAMESPACE ./temp-metabase/ $TARGET_METABASE_DB_POD`:/tmp/
oc rsync --progress --no-perms -n $TARGET_NAMESPACE ./temp-postgresql/ $TARGET_POSTGRES_DB_POD`:/tmp/
Write-Output("Copying the origin databases to the new deployments... DONE")
Write-Output("")

# Restore the databases on the target namespace 
Write-Output("Restoring the databases on the target namespace...")
oc exec $TARGET_METABASE_DB_POD -n $TARGET_NAMESPACE -- psql -f /tmp/all_metabase_postgresql_dbs.sql --quiet
oc exec $TARGET_POSTGRES_DB_POD -n $TARGET_NAMESPACE -- psql -f /tmp/all_postgresql_dbs.sql --quiet
Write-Output("Restoring the databases on the target namespace... DONE")
Write-Output("")

# Deploy DeployConfig, persistent volume claim, metabase-secret secret, metabase service and route to target namespace
Write-Output("Deply dc, pvc, secret, service and route...")
oc process -n $TOOLS_NAMESPACE -f ./metabase.dc.yaml -p NAMESPACE=$TOOLS_NAMESPACE -p PREFIX=$PREFIX -p SUFFIX=$SUFFIX -p VERSION=$METABASE_VERSION -o yaml | oc apply -n $TARGET_NAMESPACE -f -
Write-Output("Deploy dc, pvc, secret, service and route... DONE")
Write-Output("")

# Clean up the now migrated database files from local temp folders
Write-Output("Cleaning up the now migrated database files from local temp folders...")
Remove-Item -LiteralPath "temp-metabase" -Force -Recurse
Remove-Item -LiteralPath "temp-postgresql" -Force -Recurse
Write-Output("Cleaning up the now migrated database files from local temp folders... DONE")
Write-Output("")

$TARGET_METABASE_APP_POD = $null
WHILE (($null -eq $TARGET_METABASE_APP_POD)) {    
    Write-Output("Waiting for new app pod to come online...")
    Start-Sleep -Seconds 5
    $TARGET_METABASE_APP_POD=oc get pods -n $TARGET_NAMESPACE --selector deploymentconfig=metabase --field-selector status.phase=Running -o custom-columns=POD:.metadata.name --no-headers
}
Write-Output("Waiting for new app pod to come online... DONE")
Write-Output("")

Write-Output("Waiting for new app pod ready status (10 minute timeout)...")
oc wait -n $TARGET_NAMESPACE --for=condition=Ready pod/$TARGET_METABASE_APP_POD --timeout=600s
Write-Output("Waiting for new app pod ready status... DONE")
Write-Output("")

Write-Output("SCRIPT COMPLETE")