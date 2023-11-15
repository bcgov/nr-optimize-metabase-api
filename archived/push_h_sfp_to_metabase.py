# -------------------------------------------------------------------------------
# Name:        push_h_to_metabase.py
# Purpose:     the purpose of the script is to ETL onedrive data into metabase:
#              1.) Read in xlsx data
#              2.) Transform the data
#              3.) Insert to Metabase
#
# Author:      PPLATTEN, HHAY, CWARING
#
# Created:     2022
# Copyright:   (c) Optimization Team 2022
# Licence:     mine
#
#
# usage: push_h_to_metabase.py
# requirements:
#              1.) Must have open port to metabase database (can use push_to_onedrive.bat to bind port with oc)
#              2.) Must have h drive xlsx in same folder
# -------------------------------------------------------------------------------

import glob
import ldap_helper as ldap
import pandas as pd
import os
import sys
import psycopg2
import push_postgres_constants as constants

errors = {
    "department": [],
    "physicalDeliveryOfficeName": [],
    "other": [],
    "not_found": [],
}

ministry_renames = {
    "AGRI": "AF",
    "AFF": "AF",
    "FLNR": "FOR",
    "EMPR": "EMLI",
    "MEM": "EMLI",
    "ABR": "IRR",
    "LWRS": "WLRS",
}

delete_before_insert = False


def get_ad_attribute(idir, ldap_util, conn, attribute="givenName"):
    attributes = [attribute]
    ad_info = None

    try:
        # Connect to AD to get user info
        ad_info = ldap_util.getADInfo(idir, conn, attributes)
    except (Exception, AttributeError):
        errors[attribute].append(idir)
        return None

    if ad_info is None or attribute not in ad_info:
        # attribute was not found, if it's an attribute that we track, append it.
        if attribute in errors:
            errors[attribute].append(idir)
        return None
    else:
        return ad_info[attribute]


def manipulate_frame(frame, ministryname, datestamp):
    # remove rows where User ID is blank
    frame = frame.dropna(thresh=1)

    # add ministry and date columns
    frame = frame.assign(ministry=ministryname)
    frame = frame.assign(date=datestamp)

    # update ministry acronyms
    for original_name in ministry_renames:
        frame["ministry"] = frame["ministry"].apply(
            lambda x: x.replace(original_name, ministry_renames[original_name])
        )

    # remove the header row -- assume it's the first
    frame = frame[1:]

    return frame


def add_column(frame, column_ad_name, column_postgress_name):
    ldap_util = ldap.LDAPUtil()
    conn = ldap_util.getLdapConnection()

    values = []
    for i in range(len(frame.values)):
        idir = frame.values[i][0]
        if type(idir) == str and idir != "User ID":
            values.append(get_ad_attribute(idir, ldap_util, conn, column_ad_name))
        else:
            values.append("")
    frame[column_postgress_name] = values

    return frame


# gets all .xlsx files from the python files directory
def get_records_from_xlsx(sheet_name):

    # grab all the .xlsx file names in the python file's directory
    current_file_path = os.path.dirname(os.path.realpath(__file__))
    excel_names = glob.glob(os.path.join(current_file_path, "*.xlsx"))

    frames = []

    # pull the data out of each xlsx, and aggregate it
    for name in excel_names:

        # find the ministry based on the filename
        ministries = [
            "agri",
            "empr",
            "env",
            "irr",
            "flnr",
            "emli",
            "aff",
            "mem",
            "abr",
            "fpro",
            "bcws",
            "af",
            "for",
            "lwrs",
            "wlrs",
        ]
        for ministry_acronym in ministries:
            if ministry_acronym in name.lower():
                ministryname = ministry_acronym.upper()
                break

        # find the date based on the filename
        pos = name.rfind("\\") + 1
        datestamp = name[pos : pos + 7].strip() + "-01"

        # read in xlsx, turn into dataframes
        excelsheet = pd.ExcelFile(name)

        # get and touch up data for all sheets which include the selected sheet name
        for current_sheet_name in excelsheet.sheet_names:
            if sheet_name.lower() in current_sheet_name.lower():
                print(f"Working on file {name} sheet {current_sheet_name}")
                frame = excelsheet.parse(
                    current_sheet_name, header=None, index_col=None
                )
                if sheet_name.lower() == "home drives":
                    frame = add_column(frame, "department", "division")
                    frame = add_column(frame, "physicalDeliveryOfficeName", "branch")
                frame = manipulate_frame(frame, ministryname, datestamp)
                frame = frame.drop(frame.iloc[:, 1:7], axis=1)
                frames.append(frame)
    # Merge the datasets together
    combined = pd.concat(frames)

    ldap_util = ldap.LDAPUtil()
    conn = ldap_util.getLdapConnection()
    for idir in errors["department"] and errors["physicalDeliveryOfficeName"]:
        # If the user has no department or branch, maybe they have a name?
        givenName = get_ad_attribute(idir, ldap_util, conn, "givenName")
        if givenName is None:
            errors["not_found"].append(idir)
            errors["department"].remove(idir)
            errors["physicalDeliveryOfficeName"].remove(idir)

    # Log the users not found in LDAP
    with open("not_found.txt", "w") as f:
        for idir in errors["not_found"]:
            f.write(f"{idir}\n")

    # add headers back in
    if sheet_name.lower() == "home drives":
        combined.columns = [
            "idir",
            "displayname",
            "datausage",
            "ministry",
            "division",
            "branch",
            "date",
        ]
        # also fill blank displaynames with idir
        combined.displayname.fillna(combined.idir, inplace=True)
    elif sheet_name.lower() == "group shares":
        combined.columns = ["sharename", "server", "datausage", "ministry", "date"]

    # flatten data into tuples
    record_tuples = []
    for row in combined.values:
        if type(row[0]) == str:
            record_tuples.append(tuple(row))

    return record_tuples


def get_conn():
    return psycopg2.connect(
        host="localhost",
        database=constants.POSTGRES_DB_NAME,
        user=constants.POSTGRES_USER,
        password=constants.POSTGRES_PASS,
    )


# inserts h drive tuples into metabase
def insert_h_drive_records_to_metabase(record_tuples):
    conn = None
    try:
        # Open a connection
        conn = get_conn()
        cur = conn.cursor()

        if delete_before_insert:
            print("Deleting old h drive data")
            cur.execute("DELETE FROM hdriveusage")
            print("Delete from hdriveusage complete")

        print("Inserting new h drive data")
        cur.executemany(
            """
            INSERT INTO hdriveusage (idir, displayname, datausage, division, branch, ministry, date)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """,
            record_tuples,
        )
        print("Insert to hdriveusage Complete")

        # close the communication with the PostgreSQL
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print("Database connection closed.")


# inserts group share tuples into metabase
def insert_group_share_records_to_metabase(record_tuples):
    conn = None
    try:
        # Open a connection
        conn = get_conn()
        cur = conn.cursor()

        if delete_before_insert:
            print("Deleting old group share data")
            cur.execute("DELETE FROM sfpmonthly")
            print("Delete from sfpmonthly complete")

        print("Inserting new group share data")
        cur.executemany(
            """
            INSERT INTO sfpmonthly (sharename, server, datausage, ministry, date)
            VALUES (%s, %s, %s, %s, %s);
        """,
            record_tuples,
        )
        print("Insert to sfpmonthly Complete")

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
    record_tuples = get_records_from_xlsx("home drives")
    insert_h_drive_records_to_metabase(record_tuples)

    record_tuples = get_records_from_xlsx("group shares")
    insert_group_share_records_to_metabase(record_tuples)
