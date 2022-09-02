# -------------------------------------------------------------------------------
# Name:        push_onedrive_to_metabase.py
# Purpose:     the purpose of the script is to ETL onedrive data into metabase:
#              1.) Read in xlsx data
#              2.) Transform the data
#              3.) Insert to Metabase
#
# Author:      HHAY, JMONTEBE, PPLATTEN
#
# Created:     2021
# Copyright:   (c) Optimization Team 2021
# Licence:     mine
#
#
# usage: push_onedrive_to_metabase.py
# requirements:
#              1.) Must have open port to metabase database (can use push_to_onedrive.bat to bind port with oc)
#              2.) Must have all onedrive xlsx in same folder
# -------------------------------------------------------------------------------

import glob
import pandas as pd
import os
import sys
from datetime import datetime
import psycopg2
import push_postgres_constants as constants


ministry_renames = {
    "AGRI": "AF",
    "AFF": "AF",
    "EMPR": "EMLI",
    "EAO": "ENV",
    "CSNR": "ENV",
    "IIT": "LWRS",
    "FLNR": "FOR",
}

nrm_ministries = ["AFF", "EMLI", "ENV", "FLNR", "IRR"]

delete_before_insert = False


# gets all .xlsx files from the python files directory
def get_records_from_xlsx():
    ministry_data = {}

    # grab all the .xlsx file names in the python file's directory
    current_file_path = os.path.dirname(os.path.realpath(__file__))
    excel_names = glob.glob(os.path.join(current_file_path, "*.xlsx"))

    # populate the nrm_ministries dictionary from the xlxs files
    for file_path in excel_names:
        gb_for_file = 0
        file_name = os.path.split(file_path)[1]
        file_date = datetime.strptime(file_name.lower(), 'onedrive-%Y-%m.xlsx')
        excelsheet = pd.ExcelFile(file_path)
        frame = excelsheet.parse(excelsheet.sheet_names[0], header=0, index_col=None)
        for row in frame.values:
            ministry = row[0]
            gb_used = row[1]
            # handle "total" row in xlxs
            if ministry.lower() == "total":
                continue
            # handle renames
            if ministry in ministry_renames:
                ministry = ministry_renames[ministry]
            # handle non nrm ministries
            if ministry not in nrm_ministries:
                ministry = "non nrm"
            # merge gb_used from same ministry for each month
            if ministry not in ministry_data:
                ministry_data[ministry] = {}
            if file_date in ministry_data[ministry]:
                ministry_data[ministry][file_date] = ministry_data[ministry][file_date]+gb_used
            else:
                ministry_data[ministry][file_date] = gb_used
            gb_for_file = gb_for_file + gb_used

    # flatten ministry_data into tuples
    record_tuples = []
    for ministry in ministry_data:
        for record_date in ministry_data[ministry]:
            gb_used = ministry_data[ministry][record_date]
            record_tuples.append((ministry, record_date, gb_used))

    return record_tuples


# inserts tuples into metabase
def insert_records_to_metabase(record_tuples):
    conn = None
    try:
        # Open a connection
        conn = psycopg2.connect(
            host="localhost",
            database=constants.POSTGRES_DB_NAME,
            user=constants.POSTGRES_USER,
            password=constants.POSTGRES_PASS
        )
        cur = conn.cursor()

        if delete_before_insert:
            print('Deleting old data')
            cur.execute('DELETE FROM onedriveusage')
            print('Delete complete')

        print('Inserting new data')
        cur.executemany('''
            INSERT INTO onedriveusage (ministry, reporteddate, datausagegb)
            VALUES (%s, %s, %s);
        ''', record_tuples)
        print('Insert Complete')

        # close the communication with the PostgreSQL
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed.')


if __name__ == "__main__":
    if "-d" in sys.argv:
        delete_before_insert = True
    record_tuples = get_records_from_xlsx()
    insert_records_to_metabase(record_tuples)
