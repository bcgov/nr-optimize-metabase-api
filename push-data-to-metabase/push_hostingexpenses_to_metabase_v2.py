# -------------------------------------------------------------------------------
# Name:        push_hostingexpenses_to_metabase.py
# Purpose:     the purpose of the script is to ETL hosting expenses metadata into metabase:
#              1.) Read in xlsx data
#              2.) Transform the data
#              3.) Insert to Metabase
#
# Author:      HHAY, PPLATTEN
#
# Created:     2022
# Copyright:   (c) Optimization Team 2022
# Licence:     mine
#
#
# usage: push_hostingexpenses_to_metabase.py
# requirements:
#              1.) Must have open port to metabase database (can use push_to_metabase.bat to bind port with oc)
#              2.) Must have all hosting expenses xlsx in same folder
# -------------------------------------------------------------------------------

import glob
import os
import pandas as pd
import datetime
import sys
import psycopg2
import push_postgres_constants as constants

ministry_renames = {
    "": "No Tag",
    "AGRICULTURE": "AF",
    "AGRICULTURE, FOOD AND FISHERIES": "AF",
    "AGRICULTURE AND FOOD": "AF",
    "ENERGY, MINES AND PETROLEUM RESOURCES": "EMLI",
    "ENERGY, MINES AND LOW CARBON INNOVATION": "EMLI",
    "ENVIRONMENT AND CLIMATE CHANGE STRATEGY": "ENV",
    "FORESTS": "FOR",
    "FORESTS, LANDS, NATURAL RESOURCE OPERATIONS AND RURAL DEVELOPMENT": "FOR",
    "INDIGENOUS RELATIONS AND RECONCILIATION": "IRR",
    "NATURAL RESOURCE MINISTRIES": "NRM",
    "LAND, WATER AND RESOURCE STEWARDSHIP": "LWRS",
}

delete_FY_before_insert = False

# variables for column lookups and required columns:
required_columns_str = "Owner Party, SDA Party, Service Name, Funding Model Colour, Reporting Customer, Service Level 1, Inventory Item Number, "
required_columns_str += "Service Level 2, OM Asset Tag, Quantity, Price, Expense Amount, Recovery Frequency, Recovery Type, Recovery Period, GL Period"
required_columns_list = required_columns_str.split(", ")
column_map = {}


# return the number of columns in a row that actually have values
def number_of_columns(row):
    column_with_value_count = 0
    for column in row:
        if column != "":
            column_with_value_count += 1
    return column_with_value_count


# gets all .xlsx files from the python files directory
def get_records_from_csv():

    record_tuples = []

    # grab all the .xlsx file names in the python file's directory
    current_file_path = os.path.dirname(os.path.realpath(__file__))
    csv_names = glob.glob(
        os.path.join(current_file_path, "*.csv[!OptimizeLookupCategories]")
    )
    categoriesobj = open(
        os.path.join(current_file_path, "OptimizeLookupCategories.csv"), "r"
    )

    # populate the nrm_ministries dictionary from the xlxs files
    for file_path in csv_names:
        frame = pd.read_csv(file_path, header=0, index_col=None)

        # Check all required columns exist, get indexes for later reference
        column_name = ""
        try:
            for column_name in required_columns_list:
                column_map[column_name.lower().strip()] = frame.columns.get_loc(
                    column_name
                )
        except Exception:
            print(f"Error in file: {file_path}")
            print("The following columns are required:")
            print(required_columns_str)
            print(f"The column {column_name} was not found")

        # Handle row value replacement
        for row in frame.values:

            # Replace sda party / ministry name with the acronym
            ministry = row[column_map["sda party"]]
            if ministry.strip() in ministry_renames:
                row[column_map["sda party"]] = ministry_renames[ministry.strip()]

            # Null out broken timestamps from blank cells
            gl_period = row[column_map["gl period"]]
            if pd.isnull(gl_period):
                row[column_map["gl period"]] = None

            # Replace funding model colour and replace with VOTED or RECOVERY
            # The column is now called "funding model status" in the database instead of using colours
            fundingmodel = row[column_map["funding model colour"]]
            if fundingmodel.lower().strip() == "green":
                row[column_map["funding model colour"]] = "VOTED"
            elif fundingmodel.lower().strip() == "orange":
                row[column_map["funding model colour"]] = "RECOVERY"

            # Switch the format of recovery period
            rawdate = row[column_map["recovery period"]]
            formatteddate = fix_recovery_period(rawdate)
            row[column_map["recovery period"]] = formatteddate

            # Add a new column value for category
            category = lookup_categories(row[column_map["service name"]], categoriesobj)

            # Convert to tuple and add extra column data
            tup = tuple(row)
            tup = tup + (category,)

            record_tuples.append(tup)

    return record_tuples


def lookup_categories(rowservicename, categoriesobj):
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
        print(f"DID NOT find a category for {rowtest}")
    categoriesobj.seek(0)
    # print ('number of rows in categories csv searched - '+str(cnt))
    return category


def fix_recovery_period(rowtimestamp):
    # The input dates are in the format 19-2 for 2019-2, i.e.
    #   February in Fiscal year 2019 is 19-2, and shows in excel as 19-Feb, or 2021-02-19
    #   October in Fiscal year 2019 is 19-10, and shows in excel as 19-Oct, or 2021-10-19
    # The year of the date is the year that the cell was populated.
    # I hypothesize the excel is imported from a text format where Feb-19 makes sense and the day is assumed
    # Regardless, we need to rework this date into a calendar year for Metabase.

    # For fiscal_year we use the day of the month
    fiscal_year = rowtimestamp.day + 2000
    # Months after April need to be -1 year to account for the fiscal year.
    if rowtimestamp.month >= 4:
        calendar_year = fiscal_year - 1
    else:
        calendar_year = fiscal_year

    return datetime.date(calendar_year, rowtimestamp.month, 1)


def get_FY_date_range_clause(record_tuples):
    fiscal_years = []
    for tup in record_tuples:
        recovery_period = tup[column_map["recovery period"]]
        if recovery_period.month >= 0 and recovery_period.month <= 3:
            year = recovery_period.year
        elif recovery_period.month > 3 and recovery_period.month <= 11:
            year = recovery_period.year + 1
        if year not in fiscal_years:
            fiscal_years.append(year)

    clauses = []
    for year in fiscal_years:
        year_before = year - 1
        clause = f"recoveryperiod BETWEEN '{year_before}-04-01' AND '{year}-03-31'"
        clauses.append(clause)

    return " AND ".join(clauses)


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

        datetimes = []
        datetime_sets = []
        i = 0
        for tup in record_tuples:
            datetimes.append(tup[15])
            i += 1
            if i == 300:
                i = 0
                datetime_sets.append(datetimes)
                datetimes = []

        if delete_FY_before_insert:
            FY_date_range_clause = get_FY_date_range_clause(record_tuples)
            print(
                "Deleting data from the fiscal year of the csv files using this where clause:"
            )
            print(FY_date_range_clause)
            cur.execute(
                """"""DELETE FROM hostingexpenses where """ (FY_date_range_clause);"""
            )
            print("Delete complete")

        print("Inserting new data")

        cur.executemany(
            """
            INSERT INTO hostingexpenses (ownerparty, ministry, servicename, fundingmodelstatus, reportingcustomer, servicelevel1, inventoryitem,
              servicelevel2, omassettag, quantity, price, expenseamount, recoveryfrequency, recoverytype, recoveryperiod, glperiod, category)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
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
    if "-dfy" in sys.argv:
        delete_FY_before_insert = True

    record_tuples = get_records_from_csv()
    insert_records_to_metabase(record_tuples)
