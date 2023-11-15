# -------------------------------------------------------------------------------
# Name:        push_csv_to_openshift.py
# Purpose:     the purpose of the script is to push the CAS Expense report to the metabase openshift contain:
#               1.) login to openshift
#               2.) import data to openshift
#
# Author:      MRDOUVIL
#
# Created:     2020-02-14
# Copyright:   (c) MRDOUVIL 2020
# Licence:     mine
#
#
# usage:
# example:
# -------------------------------------------------------------------------------
# This file is incomplete and has not been worked on since 2020-02-14
# Linter exceptions are added below so that it does not show problems in VSCode for unrelated work:
# flake8: noqa
# type: ignore

""" postgres destination table looks like this :
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

current appraoch uses OC openshift commands to copy data over:
# oc login https://console.pathfinder.gov.bc.ca:8443 --token=<token>
# c:\sw_nt\openshift\oc rsync ./data postgresql-1-5n6l2:/tmp/

-U postgres -d metabase
psql -U $POSTGRESQL_USER -d $POSTGRESQL_DATABASE metabase=# \COPY "hostingexpense" FROM '/tmp/data/HostingServicesExpenseReport.csv' WITH CSV HEADER;
"""

import sys
import argparse


def upload_csv_openshift(input_file, openshift):
    # open the categories csv file and for each row lookup the category from the service name attribute in the expense report
    # pass the service name in the row of the expense report and look up the category in the categories csv file and return the category into the new field
    # find the service name in the second column of categoriesobj
    category = "no category"
    rowtest = rowservicename.strip()
    cnt = 0
    found = 0
    for catrow in categoriesobj:
        cnt = cnt + 1
        catrowservicename = catrow.split(",")[1].strip()
        if rowtest == catrowservicename:
            found = 1
            category = catrow.split(",")[0].strip()
            # print ('found category for '+rowtest+ " ----------- "+category)
            break
    if found == 0:
        print("DID NOT find a category for " + rowtest)

    categoriesobj.seek(0)
    # print ('number of rows in categories csv searched - '+str(cnt))
    return category


def main(argv):
    print("Number of arguments:", len(sys.argv), "arguments.")
    print("Argument List:", str(sys.argv))

    csvfile = ""
    csvoutfile = ""
    openshift = "postgresql-1-5n6l2"
    syntaxcmd = "push_csv_to_openshift.py -i <inputcsvfile> -o <openshiftcontainer>"

    if len(sys.argv) < 2:
        print(syntaxcmd)
        sys.exit(2)

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-i",
        "--input",
        dest="csvfile",
        required=True,
        help="input expense report csv file",
        metavar="FILE",
    )
    parser.add_argument(
        "-o",
        "--occontainer",
        dest="occontainer",
        required=True,
        help="input export categories lookup file",
        metavar="FILE",
    )
    parser.add_argument(
        "-t",
        "--datestampcol",
        dest="datestampcolname",
        required=True,
        help="column name for the datestamp",
        metavar="string",
        type=str,
    )
    parser.add_argument(
        "-s",
        "--servicenamecol",
        dest="servicenamecolname",
        required=True,
        help="column name for the servicename",
        metavar="String",
        type=str,
    )
    args = parser.parse_args()

    csvfile = args.csvfile
    csvoutfile = csvfile[: csvfile.find(".")] + "_PREPforMETABASE.csv"
    categoriesfile = args.categoriesfile
    datestampcolname = args.datestampcolname
    servicenamecolname = args.servicenamecolname

    print('Input RAW Expense Report CSV file is "', csvfile)
    print('Input Category CSV file is "', categoriesfile)
    print('Output CSV file is "', csvoutfile)
    print("Datestamp in RAW expense report is in column", datestampcolname)
    print("Service Name in RAW expense report is in column", servicenamecolname)

    categoriesobj = open(args.categoriesfile, "r")

    print("Add a column with same values to an existing csv file with header")

    header_of_new_col = "category"

    print("Add the category column in csv file with header in " + csvoutfile)
    # add_column_in_csv(csvfile, csvoutfile,lambda row, line_num: row.append(header_of_new_col) if line_num == 1 else row.append(lookup_categories(row[3], categoriesobj)))
    add_column_in_csv(
        csvfile,
        csvoutfile,
        header_of_new_col,
        categoriesobj,
        datestampcolname,
        servicenamecolname,
    )


if __name__ == "__main__":
    main(sys.argv[1:])
