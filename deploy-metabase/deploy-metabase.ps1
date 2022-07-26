# Script assumes user is signed in with OC

$BASE_URL="https://raw.githubusercontent.com/bcgov/nr-showcase-devops-tools/master/tools/metabase/openshift"
$ADMIN_EMAIL="iitd.optimize@gov.bc.ca"
$TOOLS_NAMESPACE="15be76-tools"
$ORIGIN_NAMESPACE="15be76-test"
$TARGET_NAMESPACE="15be76-prod"
$PREFIX="nridsco"
$METABASE_VERSION="v0.41.5"
$POSTGRES_USER=" "
$POSTGRES_PASS=" "
$POSTGRES_DB_NAME=" "

$ORIGIN_METABASE_DB_POD=oc get pods -n $ORIGIN_NAMESPACE --selector name=metabase-postgresql --field-selector status.phase=Running -o custom-columns=POD:.metadata.name --no-headers
$ORIGIN_POSTGRES_DB_POD=oc get pods -n $ORIGIN_NAMESPACE --selector name=postgresql --field-selector status.phase=Running -o custom-columns=POD:.metadata.name --no-headers

# Add the role to the default service account in target namespace which allows it to pull images from the tools namespace
# Can check success using: oc describe rolebinding.rbc -n $TOOLS_NAMESPACE
oc policy add-role-to-user system:image-puller system:serviceaccount:$TARGET_NAMESPACE`:default -n $TOOLS_NAMESPACE

# Apply quickstart network security policies, which allows:
# - The namespace to talk to the internet and itself
# - The pods to talk to the k8s (a.k.a Kubernetes) api
# Note: The only difference between quickstart-nsp.yaml and the online version is we use NetworkPolicy instead of NetworkSecurityPolicy.
#       I believe this is a version issue
#       Original: https://raw.githubusercontent.com/BCDevOps/platform-services/master/security/aporeto/docs/sample/quickstart-nsp.yaml
oc -n $TARGET_NAMESPACE process -f quickstart-nsp.yaml NAMESPACE=$TARGET_NAMESPACE | oc -n $TARGET_NAMESPACE apply -f -

# Deploy the build config to the tools namespace and build :latest image:
oc process -n $TOOLS_NAMESPACE -f $BASE_URL/metabase.bc.yaml -p METABASE_VERSION=$METABASE_VERSION -o yaml | oc apply -n $TOOLS_NAMESPACE -f -

# Create copies of origin databases
oc exec $ORIGIN_METABASE_DB_POD -n $ORIGIN_NAMESPACE -- pg_dumpall -f /tmp/all_metabase_postgresql_dbs.sql
oc exec $ORIGIN_POSTGRES_DB_POD -n $ORIGIN_NAMESPACE -- pg_dumpall -f /tmp/all_postgresql_dbs.sql


# Create folders to store the sql in if they do not already exist:
New-Item -ItemType Directory -Force -Path temp-metabase
New-Item -ItemType Directory -Force -Path temp-postgresql

# Copy origin database backups to local temp folder
oc rsync --progress -n $ORIGIN_NAMESPACE $ORIGIN_METABASE_DB_POD`:/tmp/all_metabase_postgresql_dbs.sql ./temp-metabase/
oc rsync --progress -n $ORIGIN_NAMESPACE $ORIGIN_POSTGRES_DB_POD`:/tmp/all_postgresql_dbs.sql ./temp-postgresql/

# Clean copies off of origin pods
oc exec $ORIGIN_METABASE_DB_POD -n $ORIGIN_NAMESPACE -- rm /tmp/all_metabase_postgresql_dbs.sql
oc exec $ORIGIN_POSTGRES_DB_POD -n $ORIGIN_NAMESPACE -- rm /tmp/all_postgresql_dbs.sql

# Copy origin secrets
oc get secret metabase-secret -n $ORIGIN_NAMESPACE -o yaml | sed "s/namespace:.*/namespace: $TARGET_NAMESPACE/" | oc apply -n $TARGET_NAMESPACE -f -
oc get secret metabase-postgresql -n $ORIGIN_NAMESPACE -o yaml | sed "s/namespace:.*/namespace: $TARGET_NAMESPACE/" | oc apply -n $TARGET_NAMESPACE -f -
oc get secret postgresql -n $ORIGIN_NAMESPACE -o yaml | sed "s/namespace:.*/namespace: $TARGET_NAMESPACE/" | oc apply -n $TARGET_NAMESPACE -f -

# Copy origin database creation secrets to variables
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

# Create new database deployments
oc new-app -n $TARGET_NAMESPACE -e POSTGRESQL_USER=$METABASE_DB_USER -e POSTGRESQL_PASSWORD=$METABASE_DB_PASS -e POSTGRESQL_DATABASE=$METABASE_DB_NAME postgresql:10-el8 --name=metabase-postgresql
oc new-app -n $TARGET_NAMESPACE -e POSTGRESQL_USER=$POSTGRES_USER -e POSTGRESQL_PASSWORD=$POSTGRES_PASS -e POSTGRESQL_DATABASE=$POSTGRES_DB_NAME postgresql:10-el8 --name=postgresql

# Get the new pod names
$TARGET_METABASE_DB_POD=oc get pods -n $TARGET_NAMESPACE --selector deployment=metabase-postgresql --field-selector status.phase=Running -o custom-columns=POD:.metadata.name --no-headers
$TARGET_POSTGRES_DB_POD=oc get pods -n $TARGET_NAMESPACE --selector deployment=postgresql --field-selector status.phase=Running -o custom-columns=POD:.metadata.name --no-headers

WHILE (($null -eq $TARGET_METABASE_DB_POD) -or ($null -eq $TARGET_POSTGRES_DB_POD)) {
    $TARGET_METABASE_DB_POD=oc get pods -n $TARGET_NAMESPACE --selector deployment=metabase-postgresql --field-selector status.phase=Running -o custom-columns=POD:.metadata.name --no-headers
    $TARGET_POSTGRES_DB_POD=oc get pods -n $TARGET_NAMESPACE --selector deployment=postgresql --field-selector status.phase=Running -o custom-columns=POD:.metadata.name --no-headers
    Write-Output("Waiting for pods to come online...")
    Start-Sleep -Seconds 1.5
}

# Copy the origin databases to the new deployments
oc rsync --progress --no-perms -n $TARGET_NAMESPACE ./temp-metabase/ $TARGET_METABASE_DB_POD`:/tmp/
oc rsync --progress --no-perms -n $TARGET_NAMESPACE ./temp-postgresql/ $TARGET_POSTGRES_DB_POD`:/tmp/

# Restore the databases on the target namespace 
oc exec $TARGET_METABASE_DB_POD -n $TARGET_NAMESPACE -- psql -f /tmp/all_metabase_postgresql_dbs.sql
oc exec $TARGET_POSTGRES_DB_POD -n $TARGET_NAMESPACE -- psql -f /tmp/all_postgresql_dbs.sql

# Deploy DeployConfig to target namespace
oc process -n $TOOLS_NAMESPACE -f ./metabase.dc.yaml -p NAMESPACE=$TOOLS_NAMESPACE -p PREFIX=$PREFIX -p VERSION=$METABASE_VERSION -o yaml | oc apply -n $TARGET_NAMESPACE -f -

# Clean up the now migrated database files
Remove-Item -LiteralPath "temp-metabase" -Force -Recurse
Remove-Item -LiteralPath "temp-postgresql" -Force -Recurse