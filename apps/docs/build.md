## openshift for akqfbc project (IITDCO - Cost Optimization

	oc login https://console.pathfinder.gov.bc.ca:8443 --token=<token>
	oc get projects
	NAME               DISPLAY NAME                                        STATUS
	akqfbv-dev         IITDCO (dev)                                        Active
	akqfbv-prod        IITDCO (prod)                                       Active
	akqfbv-test        IITDCO (test)                                       Active
	akqfbv-tools       IITDCO (tools)                                      Active

## Setup security on each namespace

for all 4 namespaces - run https://raw.githubusercontent.com/BCDevOps/platform-services/master/security/aporeto/docs/sample/quickstart-nsp.yaml
	oc apply -f quickstart-nsptools.yaml
	
	oc policy add-role-to-user system:image-puller system:serviceaccount:akqfbv-dev:default -n akqfbv-tools
	oc policy add-role-to-user system:image-puller system:serviceaccount:akqfbv-test:default -n akqfbv-tools
	oc policy add-role-to-user system:image-puller system:serviceaccount:akqfbv-prod:default -n akqfbv-tools

-------------------------------------------------------------------------------------------------------------------------------------    
## Deploy Jenkins
-------------------------------------------------------------------------------------------------------------------------------------

provision from catalog.. BC Gov Pathfinder Jenkins (Persistent) 
- which deploys a PVC - "jenkins" using storage class gluster-file (RWO) - https://console.pathfinder.gov.bc.ca:8443/console/project/akqfbv-tools/browse/persistentvolumeclaims/jenkins
- and deploys an application "jenkins" - https://console.pathfinder.gov.bc.ca:8443/console/project/akqfbv-tools/browse/dc/jenkins?tab=history
	
create route
https://jenkins-akqfbv-tools.pathfinder.gov.bc.ca/

-------------------------------------------------------------------------------------------------------------------------------------
## DEPLOY METABASE and POSTGRES
-------------------------------------------------------------------------------------------------------------------------------------

Provision Postgres for image catalog
Pull/read docs from and customize - https://github.com/bcgov/nr-metabase-showcase/blob/master/docs/metabase.md
(also these docs were cloned to https://apps.nrs.gov.bc.ca/int/stash/projects/OPTIMIZE/repos/optimize-metabase-api/browse)
	
	psql -U $POSTGRESQL_USER -d $POSTGRESQL_DATABASE
	database-name
	metabase
	database-password
	<password>
	database-user
	metabaseps (readonly user for Metabase)
	Show Annotations
	
	metabase-> \du
	                                    List of roles
	 Role name  |                         Attributes                         | Member of
	------------+------------------------------------------------------------+-----------
	 metabaseps |                                                            | {}
	 postgres   | Superuser, Create role, Create DB, Replication, Bypass RLS | {}
	
	metabase->
	C:\sw_nt\openshift>oc rsh postgresql-1-5n6l2
	sh-4.2$ psql -U postgres -d metabase
	psql (9.6.10)
	
	
	metabase=# alter user metabaseps superuser;
	ALTER ROLE
	metabase=# CREATE USER readonlyuser WITH PASSWORD '<password>';  --- Metabase uses this to connect.
	CREATE ROLE
	GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonlyuser;


	CREATE TABLE hostingexpenses ( 
		OwnerParty TEXT, 
		SDAParty TEXT,
		ServiceName TEXT,
		FundingModelColour TEXT,
		ExpenseGLAccount TEXT,
		ReportingCustomer TEXT,
		ReportingCustomerNo TEXT, 
		ServiceLevel1 TEXT,
		InventoryItemNumber TEXT,
		InstanceNumber TEXT,
		ServiceLevel2 TEXT,
		OMAssetTag TEXT,
		OrderNumber TEXT,
		Quantity NUMERIC(12, 3),
		Price NUMERIC(12,3),
		ExpenseAmount NUMERIC(12, 3),
		RecoveryFrequency TEXT,
		RecoveryStartDate TIMESTAMP,
		RecoveryEndDate TIMESTAMP,
		RecoveryType TEXT,
		RecoveryPeriod TIMESTAMP,
		Comments TEXT,
		category TEXT);

-------------------------------------------------------------------------------------------------------------------------------------
## import data the hard way .. these is the part that needs to be in a pipeline
-------------------------------------------------------------------------------------------------------------------------------------

Note: you need to find the temporary pod name, then sync the local data to the pod.
oc login https://console.pathfinder.gov.bc.ca:8443 --token=xxxxxxxxx
oc projects
oc project akqfbv-dev
oc rsync ./data postgresql-1-<pod contained id>:/tmp/

	
    C:\sw_nt\Git\optimize-metabase-api>c:\sw_nt\openshift\oc rsync ./data postgresql-1-5n6l2:/tmp/
	Forwarding from 127.0.0.1:52286 -> 59382
	Forwarding from [::1]:52286 -> 59382
	Handling connection for 52286
	sending incremental file list
	data/
	data/HostingServicesExpenseReport.csv
	data/OptimizeLookupCategories.csv
	
	sent 11,962,510 bytes  received 58 bytes  1,595,009.07 bytes/sec
	total size is 11,959,364  speedup is 1.00

from within the pod terminal:
	sh-4.2$ cd data
	sh-4.2$ ls
	HostingServicesExpenseReport.csv  HostingServicesExpensetest.csv  HostingServicesExpensetest_UPDATED.csv  OptimizeLookupCategories.csv  Report20180401to20200131-KRIS.csv  Report20180401to20200131-KRIS_UPDATED.csv


	psql -U $POSTGRESQL_USER -d $POSTGRESQL_DATABASE
    truncate hostingexpenses; 
	\COPY "hostingexpenses" FROM '/tmp/data/HostingServicesExpenseReport_UPDATED.csv' WITH CSV HEADER;
	COPY 36910


Create and grant readonly privs for account used by metabase application (this is only at creationtime/initialize)

	metabase=# GRANT CONNECT ON DATABASE metabase TO readonlyuser;
	GRANT
	metabase=# GRANT USAGE ON SCHEMA public TO readonlyuser;
	GRANT
	metabase=# GRANT SELECT ON hostingexpense TO readonlyuser;
	GRANT
	metabase=# GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonlyuser;
	GRANT
	metabase=# ALTER DEFAULT PRIVILEGES IN SCHEMA public grant select on tables to readonlyuser

source - 
https://github.com/bcgov/nr-metabase-showcase/blob/master/docs/metabase.md
-------------------------------------------------------------------------------------------------------------------------------------

## made dashboard public
https://iitco-dev.pathfinder.gov.bc.ca/public/dashboard/f832c8f0-a60e-4f96-b162-a49bec5980c1
via docs here https://www.metabase.com/docs/v0.23.0/administration-guide/12-public-links.html

-------------------------------------------------------------------------------------------------------------------------------------

Next steps -
* build metabse viewer (using a pipeline) - same with postgres and metabase via bitbucket (sync data and app deploys via pipelines)
* connect keycloak via Metabase viewer for auth of Metabase dashboards.
* docs for setting up keycloak frontend viewer - Metabase viewer from showcase team - https://github.com/bcgov/nr-metabase-showcase/ 
* snapshot / copy placed in bit bucket - https://apps.nrs.gov.bc.ca/int/stash/projects/OPTIMIZE/repos/optimize-metabase-api/browse/apps/docs/springBootQuickstart.md 
* ocs token for bitbucket access - https://console.pathfinder.gov.bc.ca:8443/console/project/akqfbv-dev/browse/secrets/bitbucket-token
	
	git clone https://michelle.douville%40gov.bc.ca@bwa.nrs.gov.bc.ca/int/stash/scm/optimize/optimize-metabase-api.git
	Cloning into 'optimize-metabase-api'...
	remote: Counting objects: 2, done.
	remote: Total 2 (delta 0), reused 0 (delta 0)
	Unpacking objects: 100% (2/2), done.
	Checking connectivity... done.
	
	 CSV of CAS data and Lookup table for service name to optimization category are located here - https://apps.nrs.gov.bc.ca/int/stash/projects/OPTIMIZE/repos/optimize-metabase-api/browse/data
	
	curl -H "Authorization: Bearer <bitbucket-token>" 
	http://localhost:7990/bitbucket/rest/api/1.0/projects/WORK/repos/my-repo/commits/?until=master
https://apps.nrs.gov.bc.ca/int/stash/projects/OPTIMIZE/repos/optimize-metabase-api/browse

https://apps.nrs.gov.bc.ca/int/stash/rest/api/1.0/projects/OPTIMIZE/repos/optimize-metabase-api/commits/?until=master
x-token-auth:<bitbucket-token>

https://michelle.douville%40gov.bc.ca:<password>@bwa.nrs.gov.bc.ca/int/stash/rest/api/1.0/projects/OPTIMIZE/repos/optimize-metabase-api/commits/?until=master


going to read this first -https://jenkins.io/doc/book/blueocean/creating-pipelines/ 

-------------------------------------------------------------------------------------------------------------------------------------
## Create a service account called robot to run scripts:
-------------------------------------------------------------------------------------------------------------------------------------
oc create serviceaccount robot
serviceaccount/robot created

oc policy add-role-to-user admin system:serviceaccounts:akqfbv-dev:robot
role "admin" added: "system:serviceaccounts:akqfbv-dev:robot"

oc describe serviceaccount robot
Name:                robot
Namespace:           akqfbv-dev
Labels:              <none>
Annotations:         <none>
Image pull secrets:  robot-dockercfg-7m6gp
Mountable secrets:   robot-dockercfg-7m6gp
                     robot-token-lt4jg
Tokens:              robot-token-djn96
                     robot-token-lt4jg
Events:              <none>

oc describe secret robot-token-lt4jg
Name:         robot-token-lt4jg
Namespace:    akqfbv-dev
Labels:       <none>
Annotations:  kubernetes.io/service-account.name=robot
              kubernetes.io/service-account.uid=f5cc0b15-50de-11ea-a967-0050568348cc

Type:  kubernetes.io/service-account-token

Data
====
token:           eyJhbGciOiJSUzI1NiIsImtpZCI6IiJ9.xxx................
ca.crt:          1066 bytes
namespace:       10 bytes
service-ca.crt:  2182 bytes
