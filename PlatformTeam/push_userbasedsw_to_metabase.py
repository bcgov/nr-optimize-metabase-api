# -------------------------------------------------------------------------------
# Name:        push_userbasedsw_to_metabase.py
# Purpose:     the purpose of the script is to ETL RESE & AFIN data into metabase for the
#              Platform Team, so they can track user-based software licenses for MS Dynamics
#              and Power Apps
#              1.) Read in csv data
#              2.) Transform the data using lookup tables & PowerShell script
#              3.) Insert User Based Storage data to Metabase
#              4.) Output formatted User Based Storage Reports as Excel file(s) to local machine
#
# Author:      HHAY
#
# Created:     2024
# Copyright:   (c) Optimization Team 2024
# Licence:     mine
#
#
# usage: push_userbasedsw_to_metabase.py
# requirements:
#              1.) Must have the RESE /AFIN csv file(s) in same folder as .py script
#              2.) Must have text file of all IDIRs in the report to run .ps1 script
#              3.) Must have an open port to metabase database
# -------------------------------------------------------------------------------

import pandas as pd
from datetime import datetime
from datetime import date
import numpy as np
import psycopg2
import push_postgres_constants as constants

# read in the CAS report for AFIN user-based software
main_df = pd.read_csv(
    r"C:\Git_Repo\nr-optimize-metabase-api\PlatformTeam\RESE_UserBasedSoftware_Recoverable_AttributesFilter.csv"
)

#rename column
main_df.rename(columns={'IDIR Account':'IDIR'}, inplace=True)

# read in the IDIR lookup table
lookup_df = pd.read_csv(
    r"C:\Git_Repo\nr-optimize-metabase-api\PlatformTeam\PlatformTeam_LookupTable.csv"
)

# read in the EA lookup table
ea_lookup_df = pd.read_csv(
    r"C:\Git_Repo\nr-optimize-metabase-api\PlatformTeam\EAdetails_AFIN_UserBasedSoftware_Recoverable_AttributesFilter.csv"
)

# match IDIRs to display names and email addresses
main_df["DisplayName"] = main_df.IDIR.map(
    dict(lookup_df[["IDIR", "DisplayName"]].values)
)

main_df["Email"] = main_df.IDIR.map(dict(lookup_df[["IDIR", "Email"]].values))

# remove any GL Period anomalies
main_df["RESE GL Period"] = main_df["RESE GL Period"].replace(
     to_replace="ADJ1-25", value="Jan-25"
 )

# match Assets to EA email addresses, recovery start & end dates
main_df["Expense Authority"] = main_df["AFIN Asset"].map(
    dict(ea_lookup_df[["AFIN Asset", "Expense Authority"]].values)
)

main_df["AFIN Recovery Start Date"] = main_df["AFIN Asset"].map(
    dict(ea_lookup_df[["AFIN Asset", "AFIN Recovery Start Date"]].values)
)

main_df["AFIN Recovery End Date"] = main_df["AFIN Asset"].map(
    dict(ea_lookup_df[["AFIN Asset", "AFIN Recovery End Date"]].values)
)

# main_df["AFIN Asset"] = main_df["AFIN Asset"].astype(str) # might not need this line, leftover from troubleshooting during script creation


def fix_gl_period(rowtimestamp):
    # the input dates for GL Period are in the format YY-mm based on fiscal year, i.e 25-2 is February 2025 but 25-8 is actually August 2024. Day is assumed to be 01.

    # for fiscal_year we use the day of the month
    rowtimestamp = datetime.strptime(rowtimestamp, "%b-%y").strftime("%m-%y")
    rowtimestamp = pd.to_datetime(rowtimestamp, format="%m-%y")
    fiscal_year = rowtimestamp.year

    # months after April need to be -1 year to account for the fiscal year.
    month = rowtimestamp.month
    if month >= 4:
        calendar_year = fiscal_year - 1
    else:
        calendar_year = fiscal_year

    rowtimestamp = date(calendar_year, month, 1)

    return pd.to_datetime(rowtimestamp)


formatteddate = main_df["RESE GL Period"].apply(fix_gl_period)
main_df["RESE GL Period"] = formatteddate

# test that GL period function is working as intended
# print(main_df["RESE GL Period"].head())

main_df = main_df.replace(np.nan, None)

# export pandas dataframe to csv output
main_df.to_csv(
    r"C:\Git_Repo\nr-optimize-metabase-api\PlatformTeam\userbasedsw_metabase.csv",
    sep=",",
    encoding="utf-8",
    index=False,
    header=True,
)

# convert pandas dataframe into tuples
record_tuples = list(main_df.itertuples(index=False, name=None))


# insert tuples into metabase
def insert_records_to_metabase(record_tuples):
    conn = None
    try:
        # Open a connection
        conn = psycopg2.connect(
            host="localhost",
            port="5431",
            database=constants.POSTGRES_DB_NAME,
            user=constants.POSTGRES_USER,
            password=constants.POSTGRES_PASS,
        )
        cur = conn.cursor()

        print("Inserting new data")

        cur.executemany(
            """
            INSERT into userbasedsw(afinasset, idiraccount, servicecategory, serviceattribute, ministry, reseglperiod, reseexpenseaccount, reseamount, afinrecoverytype, fundingmodel, displayname, email, expenseauth, startdate, enddate)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
        """,
            record_tuples,
        )
        print("Insert Complete")

        # close the communication with the PostgreSQL database
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print("Database connection closed.")


if __name__ == "__main__":
    insert_records_to_metabase(record_tuples)
