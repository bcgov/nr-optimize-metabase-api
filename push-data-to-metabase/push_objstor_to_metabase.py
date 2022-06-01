# -------------------------------------------------------------------------------
# Name:        push_objstor_to_metabase.py
# Purpose:     the purpose of the script is to ETL objstor metadata into metabase:
#              1.) Read in xlsx data
#              2.) Transform the data
#              3.) Insert to Metabase
#
# Author:      HHAY, JMONTEBE, PPLATTEN, CCOCKER
#
# Created:     2022
# Copyright:   (c) Optimization Team 2022
# Licence:     mine
#
#
# usage: push_objstor_to_metabase.py
# requirements:
#              1.) Must have open port to metabase database (can use push_to_metabase.bat to bind port with oc)
#              2.) Must have all objstor xlsx in same folder
# -------------------------------------------------------------------------------

import csv
import glob
import os
import re
import sys
from datetime import datetime
import psycopg2
import push_postgres_constants as constants


ministry_renames = {
    "AGRI": "AF",
    "AFF": "AF",
    "EMPR": "EMLI",
    "EAO Environmental Assessment Office": "ENV",
    "EAO": "ENV",
    "ENV Environmental Protection Division": "ENV",
    "ENV - Climate Action Secretariat": "ENV",
    "ENV Climate Action Secretariat": "ENV",
    "ENV EPD": "ENV",
    "ENV ESD": "ENV",
    "ENV IIT": "LWRS",
    "ENV IIT - Architecture": "LWRS",
    "CSNR": "ENV",
    "FLNR BC Wildfire Service - BCWS": "FOR",
    "FLNR IROD": "FOR",
    "FLNR Office of the Chief Forester": "FOR",
    "FLNRORD": "FOR",
    "FLNR Resource Stewardship Division": "FOR",
    "FLNR Strategic Initiatives": "FOR",
    "FLNR": "FOR",
    "IIT": "LWRS",
    "IIT ENV": "LWRS",
    "LWRS NRIDS": "LWRS",
    "LWRS NRIDS - Architecture": "LWRS"
}

nrm_ministries = ["AF", "EMLI", "ENV", "FOR", "IRR", "LWRS"]

delete_before_insert = False


# Ensure all the columns are in the correct position, to ensure we're mapping the correct columns
def check_column_placement(row):
    # The columns should be in this order:
    column_order_str = "Bucket, Owner, No. Objects, Data Uploaded, No. Objects Created, Data Downloaded, No. Objects Deleted, Used, Usage (%), Quota, Tag"
    order = column_order_str.split(", ")
    for i in range(len(order)):
        if row[i] != order[i]:
            if row[i] == "Download Count":
                # The FY2021 data has a Download Count field with all 0's instead of Data Downloaded
                continue
            if row[i] == "Tags" and order[i] == "Tag":
                # The FY2021 data uses 'Tags' instead of 'Tag'
                continue
            if len(row[i]) > 8 and row[i][len(row[i]) - 6 :] == " (GiB)":
                # The FY2021 data has some column headers which end in the unit
                continue
            print("The input csv should have the following columns in order:")
            print(column_order_str)
            print("Script failed, exiting")
            exit()


# return the number of columns in a row that actually have values
def number_of_columns(row):
    column_with_value_count = 0
    for column in row:
        if column != "":
            column_with_value_count += 1
    return column_with_value_count


# gets all .xlsx files from the python files directory
def get_records_from_xlsx():

    # grab all the .xlsx file names in the python file's directory
    current_file_path = os.path.dirname(os.path.realpath(__file__))
    csv_names = glob.glob(os.path.join(current_file_path, "*.csv"))

    value_tuples = []
    # populate the nrm_ministries dictionary from the xlxs files
    for file_path in csv_names:
        print(f"Processing: {file_path}")
        file_name = os.path.split(file_path)[1]
        file_date = None
        try:
            file_date = datetime.strptime(file_name.lower(), "nrs buckets %B %Y.csv")
        except (Exception) as error:
            print(
                "Exception while getting the date from file name. Format should be: NRS Buckets %B %Y.csv"
            )
            print(error)
            exit

        file_date = file_date

        # process CSV - tally ministry usage
        with open(file_path) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=",")
            column_headers_verified = False
            for row in csv_reader:
                # ignore rows with less than 6 columns
                if number_of_columns(row) < 6:
                    continue

                if column_headers_verified is False:
                    # script will exit if the columns are placed incorrectly
                    check_column_placement(row)
                    column_headers_verified = True
                    continue

                for i in range(len(row)):
                    if i in [2, 3, 4, 5, 6, 7, 8, 9] and row[i] == "":
                        row[i] = 0
                    if i in [2, 4, 9]:
                        row[i] = int(row[i])
                    elif i in [3, 5, 6, 7, 8]:
                        row[i] = float(row[i])

                ministry, branch, project, environment = (
                    "No Tag",
                    None,
                    None,
                    "No Tag/Name",
                )
                # Get tags used in metabase for columns
                if row[10] != "":
                    # Historic tags have multiple KV pairs separated by commas - replace comma to separate
                    tag_string = row[10].replace(",", ";")
                    # Split tags into list, removing trailing whitespace
                    tags = dict(s.strip().split("=") for s in tag_string.split(";"))
                    # Only interested in Ministry for data consumption
                    if "Ministry" in tags.keys():
                        ministry = tags["Ministry"]
                        if ministry in ministry_renames:
                            ministry = ministry_renames[ministry]
                    if "Branch" in tags.keys():
                        branch = tags["Branch"]
                    if "Project" in tags.keys():
                        project = tags["Project"]
                    if "Environment" in tags.keys():
                        environment = tags["Environment"]

                # Cut tags off the end of the list
                row = row[:9]

                # If Environment wasn't in a tag, is it in the username? If so, use that
                if environment == "No Tag/Name":
                    match = re.findall(r"-prd$|-tst$|-dlv$|-dev$|-sbx$", row[1])
                    if match:
                        environment = match[0][1:].upper()

                # Add back in the tags we care about
                row.extend([ministry, branch, project, environment, file_date])
                value_tuples.append(tuple(row))

    return value_tuples


# inserts tuples into metabase
def insert_records_to_metabase(record_tuples):
    conn = None
    try:
        # Open a connection
        conn = psycopg2.connect(
            host="localhost",
            database=constants.POSTGRES_DB_NAME,
            user=constants.POSTGRES_USER,
            password=constants.POSTGRES_PASS,
        )
        cur = conn.cursor()

        if delete_before_insert:
            print("Deleting old data")
            cur.execute("DELETE FROM objectstorage")
            print("Delete complete")

        print("Inserting new data")

        cur.executemany(
            """
            INSERT INTO objectstorage (bucket, owner, objectcount, uploadsize, newobjects, downloadsize, deletedobjects,
              size, quota, ministry, branch, project, environment, reportdate)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """,
            record_tuples,
        )
        print("Insert Complete")

        # close the communication with the PostgreSQL
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print("Database connection closed.")


if __name__ == "__main__":
    if "-d" in sys.argv:
        delete_before_insert = True
    record_tuples = get_records_from_xlsx()
    insert_records_to_metabase(record_tuples)
