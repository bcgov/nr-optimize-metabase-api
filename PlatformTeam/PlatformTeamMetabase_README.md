## Platform Team - License Tracking & Cost - Metabase Import 
******

**Platform Team contacts:** [Eric Kimberlin](mailto:eric.kimberlin@gov.bc.ca). <br>
**Optimization Team contacts:** [Heather Hay](mailto:heather.hay@gov.bc.ca) and [Peter Platten](mailto:peter.platten@gov.bc.ca). <br>

**Main Script File(s):** push_userbasedsw_to_metabase.py <br>
**Supporting Script File(s):** .env, push_postgres_constants.py <br>

**Data Required:** <br>
- EAdetails_AFIN_UserBasedSoftware_Recoverable_AttributesFilter.csv <br>
- RESE_UserBasedSoftware_Recoverable_AttributesFilter.csv <br>
- PlatformTeam_LookupTable.csv (created by python script)

**Purpose:** This Python script combines the current fiscal year's recoverable expenses for user-based software from the EA and RESE tables in the CAS Data Warehouse, and creates a lookup table to apply the user's display name and email address based on their IDIR userID. The resulting report is then pushed into our postgresql database in OpenShift and served out through our Metabase application instance<br>

**Author:** Heather Hay <br>
**Copyright:** (c) Optimization Team 2025 <br>

**Created:** Nov 2024 <br>
**Updated:** October 2025 <br>

1.  The agents Heather has saved in the CAS Data Warehouse will run on the first of the month at 12:30 p.m. and send an email to NRIDS.Optimize@gov.bc.ca with a current copy of *EAdetails_AFIN_UserBasedSoftware_Recoverable_AttributesFilter.csv* and *RESE_UserBasedSoftware_Recoverable_AttributesFilter.csv* attached.

2. Take these 2 files and save them in the PlatformTeam folder of your local GitHub repo for nr-optimize-metabase-api. You may want to check that the path to your local GitHub repo matches what's in the Python file, and edit if needed.

3. Create or confirm there is an .env file in the PlatformTeam directory with the following values:
```
POSTGRES_USER = "postgres"
POSTGRES_PASS = ""
POSTGRES_DB_NAME = "metabase"

AD_SERVER = 'IDIR.bcgov'
AD_USER = 'IDIR\\YOUR-IDIR-USERNAME-HERE'
AD_PASSWORD = 'YOUR-IDIR-PW-HERE'
SEARCH_BASE = 'DC=idir,DC=bcgov'
```

4. Open Metabase and load the [Userbasedsw table, sorted by date descending](https://nrmccp-metabase.apps.silver.devops.gov.bc.ca/question#eyJkYXRhc2V0X3F1ZXJ5Ijp7ImRhdGFiYXNlIjoyLCJxdWVyeSI6eyJzb3VyY2UtdGFibGUiOjI1LCJvcmRlci1ieSI6W1siZGVzYyIsWyJmaWVsZCIsMjM2LG51bGxdXV19LCJ0eXBlIjoicXVlcnkifSwiZGlzcGxheSI6InRhYmxlIiwidmlzdWFsaXphdGlvbl9zZXR0aW5ncyI6e319) and note the data displayed. Keep the window open without refreshing so that you can compare it before and after the data insert.

5. Log into [OpenShift](https://oauth-openshift.apps.silver.devops.gov.bc.ca/oauth/authorize?client_id=console&redirect_uri=https%3A%2F%2Fconsole.apps.silver.devops.gov.bc.ca%2Fauth%2Fcallback&response_type=code&scope=user%3Afull&state=7cb25ec69e8afad8bdbe1b2976bcf5ba) with your credentials (IDIR-MFA) and copy your login command from the top right of the window after authenticating yourself and selecting display token. i.e.:
```
oc login --token=sha256~1234567890acdefghijklmnopqrst --server=https://api.silver.devops.gov.bc.ca:6443
```

6. Open a command prompt window in the PlatformTeam directory. Paste in and run the OpenShift login command. Confirm that you're using the TEST project, or run the following command to switch over to it:
```
oc project 15be76-test
```

7. From the same command prompt window, open a port to the OpenShift pod i.e.
```
# Get the data pod name from the current namespace
$POSTGRES_DB_POD=oc get pods --selector name=postgresql --field-selector status.phase=Running -o custom-columns=POD:.metadata.name --no-headers
# Launch a new thread with a port bind
$PATH=$Env:Path
# Start-Process "oc-port-forward" cmd /k "SET PATH=$CD;$PATH & oc port-forward $POSTGRES_DB_POD 5432:5432"
Start-Process -FilePath "oc.exe" -ArgumentList "port-forward",$POSTGRES_DB_POD,"5431:5432" -PassThru
```

8. Go back to OpenShift and choose 15be76-test from Projects, then go to Workloads > Pods and select the postgresql pod. Go to the Terminal tab and log into the Metabase database, then delete the current fiscal year's data from the userbasedsw table i.e.:
```
psql -U postgres -d metabase
delete from userbasedsw where reseglperiod > '2025-03-31';
```

9. Return to your open command prompt window in the PlatformTeam directory. Paste in and run the following command to load the new report to the userbasedsw table in Metabase:
```
python .\push_userbasedsw_to_metabase.py
```

10. When script is complete, check the userbasedsw table in Metabase to confirm the latest month's data is there and then notify Eric.  <br>
You can now remove/delete the .csv files in the PlatformTeam directory.
