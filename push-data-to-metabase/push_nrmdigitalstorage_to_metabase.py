# -------------------------------------------------------------------------------
# Name:        push_nrmdigitalstorage_to_metabase.py
# Purpose:     ETL digital storage metadata into PostgreSQL (hostingexpenses table):
#              1.) Read xlsx data
#              2.) Transform the data
#              3.) Insert into PostgreSQL table, friendly view in Metabase
#
# Author:      HHAY, PPLATTEN
#
# Created:     2026
# Copyright:   (c) Optimization Team 2026
# Licence:     mine
#
# usage: push_nrmdigitalstorage_to_metabase.py
# requirements:
#   1.) Must have open port to metabase database
#   2.) Must have all digital storage metadata xlsx in same folder
# -------------------------------------------------------------------------------

import glob
import os
import pandas as pd
from datetime import datetime
import psycopg2
import push_postgres_constants as constants

ministry_renames = {
    "AGRICULTURE AND FOOD": "AF",
    "ENERGY AND CLIMATE SOLUTIONS": "ECS",
    "ENVIRONMENT AND PARKS": "ENV",
    "FORESTS": "FOR",
    "INDIGENOUS RELATIONS AND RECONCILIATION": "IRR",
    "MINING AND CRITICAL MINERALS": "MCM",
    "WATER LAND AND RESOURCE STEWARDSHIP": "WLRS"
}

ministry_code = {
    "130": "AF",
    "057": "ECS",
    "315": "ECS",
    "048": "ENV",
    "115": "ENV",
    "301": "ENV",
    "128": "FOR",
    "0AT": "FOR",
    "120": "IRR",
    "135": "MCM",
    "133": "WLRS"
}

delete_FY_before_insert = False


required_columns_list = [
    "RESE Expense Account",
    "RESE Funding Model",
    "FRA Organization",
    "RESE Service",
    "RESE FRA Description",
    "RESE Catalog Item",
    "RESE Asset Tag",
    "RESE Quantity",
    "RESE Price",
    "RESE Amount",
    "RESE Received Period",
    "RESE GL Period",
]

def get_records_from_xlsx():
    record_tuples = []

    current_file_path = os.path.dirname(os.path.realpath(__file__))
    excel_names = glob.glob(os.path.join(current_file_path, "*.xlsx"))

    categoriesobj = open(
        os.path.join(current_file_path, "OptimizeLookupCategories.csv"), "r"
    )

    numeric_columns = ["rese quantity", "rese price", "rese amount"]
    date_columns = ["rese received period", "rese gl period"]

    for file_path in excel_names:
        print(f"Processing file: {file_path}")

        # Read the only worksheet in the workbook
        frame = pd.read_excel(
            file_path,
            sheet_name=0,
            header=0,
            index_col=None,
            dtype={
                    "RESE Received Period": str,
                    "RESE GL Period": str,
                },
            )

        frame.columns = frame.columns.str.strip()

        # Validate required columns exist
        missing_columns = [
            col for col in required_columns_list
            if col not in frame.columns
        ]

        if missing_columns:
            print(
                f"Skipping {file_path}. Missing required columns: "
                f"{', '.join(missing_columns)}"
            )
            continue
        
        print("Using sheet: first worksheet")

        print(f"Rows loaded: {len(frame)}")

        # Build column map
        column_map = {}
        for column_name in required_columns_list:
            column_map[column_name.lower()] = frame.columns.get_loc(column_name)

        for row in frame.values:
            row = list(row)

            # --- Normalize / clean nulls SAFELY ---
            for col_name, idx in column_map.items():
                val = row[idx]

                if pd.isnull(val) or val == "":
                    if col_name in numeric_columns or col_name in date_columns:
                        row[idx] = None
                    else:
                        row[idx] = ""

            # --- Normalize ministry text ---
            ministry = row[column_map["fra organization"]]
            if isinstance(ministry, str):
                ministry_key = ministry.strip()
                if ministry_key in ministry_renames:
                    row[column_map["fra organization"]] = ministry_renames[ministry_key]

            # --- Prefix override ---
            expense_account = row[column_map["rese expense account"]]
            if expense_account is not None:
                expense_str = str(expense_account)
                for prefix, org in ministry_code.items():
                    if expense_str.startswith(prefix):
                        row[column_map["fra organization"]] = org
                        break

            # Normalize funding model
            fundingmodel = row[column_map["rese funding model"]]
            if isinstance(fundingmodel, str):
                fm = fundingmodel.lower().strip()
                if fm == "voted":
                    row[column_map["rese funding model"]] = "VOTED"
                elif fm == "recovery" or fm == "recoverable":
                    row[column_map["rese funding model"]] = "RECOVERY"

            # Fix recovery period (returns None for invalid)
            rawdate = row[column_map["rese received period"]]
            row[column_map["rese received period"]] = normalize_period(rawdate)

            rawdate = row[column_map["rese gl period"]]
            row[column_map["rese gl period"]] = normalize_period(rawdate)

            category = lookup_categories(
                row[column_map["rese service"]], categoriesobj
            )

            tup = ( 
                None,
                row[column_map["rese expense account"]],
                row[column_map["rese funding model"]],
                row[column_map["fra organization"]],
                row[column_map["rese service"]],
                row[column_map["rese fra description"]],
                None,
                None,
                row[column_map["rese catalog item"]],
                row[column_map["rese asset tag"]],
                row[column_map["rese quantity"]],
                row[column_map["rese price"]],
                row[column_map["rese amount"]],
                None,
                None,
                row[column_map["rese received period"]],
                row[column_map["rese gl period"]],
                category,
            )

            record_tuples.append(tup)

    print(f"Total records prepared: {len(record_tuples)}")
    return record_tuples


def lookup_categories(rowservicename, categoriesobj):
    category = "no category"
    if not isinstance(rowservicename, str):
        return category

    rowtest = rowservicename.strip()
    for catrow in categoriesobj:
        parts = catrow.split(",")
        if len(parts) >= 2 and rowtest == parts[1].strip():
            category = parts[0].strip()
            break

    categoriesobj.seek(0)
    return category

def normalize_period(value):
    """
    Normalize period values to the first day of the month.

    Supported input formats:
        FEB-26
        Feb-26
        2026-02-26
        2026-02-26 00:00:00
        pandas.Timestamp

    Output:
        pandas.Timestamp(YYYY, MM, 1)
    """

    if pd.isnull(value):
        return None

    value = str(value).strip()

    # Handle MON-YY format (FEB-26, Apr-27, etc.)
    try:
        dt = datetime.strptime(value.title(), "%b-%y")

        return pd.Timestamp(
            year=dt.year,
            month=dt.month,
            day=1,
        )
    except ValueError:
        pass

    # Handle Excel dates / timestamps / ISO dates
    try:
        dt = pd.to_datetime(value)

        return pd.Timestamp(
            year=dt.year,
            month=dt.month,
            day=1,
        )
    except Exception:
        raise ValueError(f"Unsupported period format: {value}")

def fix_recovery_period(rowtimestamp):
    """
    Convert fiscal period values to the corresponding calendar month.

    Examples:
        27-Apr -> 2026-04-01
        27-Dec -> 2026-12-01
        27-Jan -> 2027-01-01
        27-Mar -> 2027-03-01
    """
    if pd.isnull(rowtimestamp):
        return None

    dt = pd.to_datetime(rowtimestamp)
    return pd.Timestamp(
        year=dt.year,
        month=dt.month,
        day=1
    )

def insert_records_to_metabase(record_tuples):
    if not record_tuples:
        print("No records to insert.")
        return

    conn = None
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5431",
            database=constants.POSTGRES_DB_NAME,
            user=constants.POSTGRES_USER,
            password=constants.POSTGRES_PASS,
        )
        cur = conn.cursor()

        cur.executemany(
            """
            INSERT INTO hostingexpenses(
                ownerparty,
                accountcoding,
                fundingmodelstatus,
                ministry,
                servicename,
                servicelevel2,
                servicelevel1,
                inventoryitem,
                reportingcustomer,
                omassettag,
                quantity,
                price,
                expenseamount,
                recoveryfrequency,
                recoverytype,
                recoveryperiod,
                glperiod,
                category
            )
            VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s
            );
            """,
            record_tuples,
        )

        conn.commit()
        cur.close()

        print(f"Inserted {len(record_tuples)} records")

    except Exception as error:
        print(error)
        raise
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    record_tuples = get_records_from_xlsx()
    insert_records_to_metabase(record_tuples)
