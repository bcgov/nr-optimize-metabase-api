# -------------------------------------------------------------------------------
# Name:        push_userbasedsw_to_metabase.py
# Purpose:     the purpose of the script is to ETL RESE & AFIN data into metabase for the
#              Platform Team, so they can track user-based software licenses for MS Dynamics
#              and Power Apps
#              1.) Read in csv data
#              2.) Create IDIR lookup table
#              3.) Transform the data using lookup table
#              4.) Output formatted user-based storage reports as Excel file(s) to local machine
#              5.) Insert user-based storage data to Metabase 
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
#              2.) Keep your IDIR credentials in .env file current for successful Active Directory connection
#              3.) Must have an open port to metabase database
# -------------------------------------------------------------------------------

from ldap3 import Server, Connection, ALL, NTLM
import pandas as pd
import csv
from datetime import datetime
from datetime import date
import numpy as np
import psycopg2
import push_postgres_constants as constants

# Connect to AD
server1 = Server(constants.AD_SERVER, port=636, use_ssl=True, get_info=ALL)
conn1 = Connection(
    server1,
    user=constants.AD_USER,
    password=constants.AD_PASSWORD,
    authentication=NTLM,
    auto_bind=True,
)


if not conn1.bind():
    print("Failed to bind to server:", conn1.result)
    exit()


# Load IDIRs
df = pd.read_csv(
    r"C:\Git_Repo\nr-optimize-metabase-api\PlatformTeam\RESE_UserBasedSoftware_Recoverable_AttributesFilter.csv"
)
idirs = df["IDIR Account"].dropna().unique()

# Prepare output
results = []

for idir in idirs:
    conn1.search(
        search_base=constants.SEARCH_BASE,
        search_filter=f"(sAMAccountName={idir})",
        attributes=["sAMAccountName", "displayName", "mail"],
    )
    if conn1.entries:
        entry = conn1.entries[0]
        results.append(
            {
                "IDIR": entry.sAMAccountName.value,
                "DisplayName": entry.displayName.value,
                "Email": entry.mail.value,
            }
        )
    else:
        results.append({"IDIR": idir, "DisplayName": "Not Found", "Email": "Not Found"})

# Save to CSV
output_file = (
    r"C:\Git_Repo\nr-optimize-metabase-api\PlatformTeam\PlatformTeam_LookupTable.csv"
)
with open(output_file, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["IDIR", "DisplayName", "Email"])
    writer.writeheader()
    writer.writerows(results)

print(f"Saved {len(results)} entries to {output_file}")


# read in the CAS report for AFIN user-based software
main_df = pd.read_csv(
    r"C:\Git_Repo\nr-optimize-metabase-api\PlatformTeam\RESE_UserBasedSoftware_Recoverable_AttributesFilter.csv"
)

# rename column
main_df.rename(columns={"IDIR Account": "IDIR"}, inplace=True)

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
