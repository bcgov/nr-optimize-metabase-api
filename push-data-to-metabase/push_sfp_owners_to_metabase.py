# -------------------------------------------------------------------------------
# Name:        push_sfp_owners_to_metabase.py
# Purpose:     the purpose of the script is to ETL sfp owner data into metabase:
#              1.) Read in xlsx data
#              2.) Transform the data
#              3.) Insert to Metabase
#
# Author:      PPLATTEN, HHAY
#
# Created:     2023
# Copyright:   (c) Optimization Team 2023
# Licence:     mine
#
#
# usage: push_sfp_owners_to_metabase.py
# requirements:
#              1.) Must have open port to metabase database (can use push_to_metabase.bat to bind port with oc)
#              2.) Must have sfp owner xlsx in same folder
# -------------------------------------------------------------------------------

import glob
import pandas as pd
import os
import psycopg2
import push_postgres_constants as constants


# gets all .xlsx files from the python files directory
def get_records_from_xlsx(sheet_name):

    # grab all the report .xlsx file names in the python file's directory
    current_file_path = os.path.dirname(os.path.realpath(__file__))
    excel_names = glob.glob(os.path.join(current_file_path, "SharedDriveOwnershipReport-*.xlsx"))

    frames = []

    # pull the data out of each xlsx, and aggregate it
    for name in excel_names:

        # read in xlsx, turn into dataframes
        excelsheet = pd.ExcelFile(name)

        # get and touch up data for all sheets which include the selected sheet name
        for current_sheet_name in excelsheet.sheet_names:
            if sheet_name.lower() in current_sheet_name.lower():
                print(f"Reading in file {name} sheet {current_sheet_name}")
                frame = excelsheet.parse(
                    current_sheet_name, header=0, index_col=None
                )
                # Drop first two columns: Date, Org
                frame = frame.drop(frame.iloc[:, 0:2], axis=1)
                # Drop GB_Used, # of files, Drive, Type, SubType
                frame = frame.drop(frame.iloc[:, 1:6], axis=1)
                # Drop GL, Resp
                frame = frame.drop(frame.iloc[:, 3:5], axis=1)
                frames.append(frame)

    # grab the override .xlsx file name in the python file's directory
    current_file_path = os.path.dirname(os.path.realpath(__file__))
    excel_names = glob.glob(os.path.join(current_file_path, "OwnersOverride-*.xlsx"))

    if len(excel_names) != 1:
        print("SFP Owners script requires one OwnersOverride-*.xlsx file")
        exit
    first_sheet_name = excel_names[0]
    override_excel_file = pd.ExcelFile(first_sheet_name)
    override_sheet = override_excel_file.sheet_names[0]
    frame = override_excel_file.parse(override_sheet, header=0, index_col=None)
    frames.append(frame)

    # Merge the datasets together
    combined = pd.concat(frames)

    # flatten data into tuples
    record_tuples = []
    for row in combined.values:
        if type(row[0]) == str:
            record_tuples.append(tuple(row))

    return record_tuples


def condense_share_info(record_tuples):
    share_dict = {}
    for row in record_tuples:
        if row[0].lower() == 'share name':
            continue
        share_name = row[0]
        new_entry = {
                'possible_owner': row[1],
                'possible_owner_title': row[2],
                'ownership_hierarchy': row[3],
                'comment': row[4],
        }
        # if new share or higher ownership hierarchy
        if share_name not in share_dict or share_dict[share_name]['ownership_hierarchy'] < new_entry['ownership_hierarchy']:
            share_dict[share_name] = new_entry
    return share_dict


def get_conn():
    return psycopg2.connect(
        host="localhost",
        port='5431',
        database=constants.POSTGRES_DB_NAME,
        user=constants.POSTGRES_USER,
        password=constants.POSTGRES_PASS,
    )


# inserts group share tuples into metabase
def update_metabase(share_dict):
    conn = None
    try:
        # Open a connection
        conn = get_conn()
        cur = conn.cursor()

        for share_name in share_dict:
            possibleowner = share_dict[share_name]['possible_owner']
            print(f"Updating owner for {share_name}")
            psqlcommand = f"""
                UPDATE sfpmonthly SET possibleowner = '{possibleowner}'
                WHERE sharename = '{share_name}';
            """
            cur.execute(psqlcommand)

        # close the communication with the PostgreSQL
        conn.commit()
        cur.close()
        print("Update to sfpmonthly Complete")
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print("Database connection closed.")


if __name__ == "__main__":
    conn = get_conn()
    record_tuples = get_records_from_xlsx("Raw")
    share_dictionary = condense_share_info(record_tuples)
    update_metabase(share_dictionary)
