# -------------------------------------------------------------------------------
# Name:        clean_incremental_data_csv.py
# Purpose:     the purpose of the script is to clean the CAS incremental usage data:
#              1.) Chnge reporting customer to only be Ministry
#              2.) Fill empty cells with na
#              3.) Only include usefull data
#
# Author:      HHAY, JMONTEBE
#
# Created:     2020-11-03
# Copyright:   (c) Optimization Team 2020
# Licence:     mine
#
#
# usage: clean_incremental_data.py -i <input_directory>
# example:  clean_incremental_data.py -i J:\Scripts\Python\Data
# -------------------------------------------------------------------------------

import glob
import sys
import argparse
import pandas as pd


def main(argv):
    # take a single input directory argument in
    # print ('Number of arguments:', len(sys.argv), 'arguments.')
    # print ('Argument List:', str(sys.argv))

    inputdirectory = ""
    frames = []
    syntaxcmd = "Insufficient number of commands passed: clean_incremental_data.py -i <input_directory>"

    if len(sys.argv) < 3:
        print(syntaxcmd)
        sys.exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input",
        dest="inputdirectory",
        required=True,
        help="path to directory containing usage reports",
        metavar="string",
        type=str,
    )
    args = parser.parse_args()

    inputdirectory = args.inputdirectory

    # grab all the .xlsx files in the input directory
    excel_names = glob.glob(inputdirectory + r"\*.xlsx")

    # pull the data out of each xlsx, and aggregate it
    for name in excel_names:

        # read in xlsx, turn into dataframes
        excelsheet = pd.ExcelFile(name)
        frame = excelsheet.parse(
            excelsheet.sheet_names[0],
            index_col=None,
            usecols=[
                "Reporting Customer",
                "OM Asset Tag",
                "SP Quantity",
                "SP IDIR",
                "SP Server",
                "SP Consumption Date",
                "SP Mailbox Item Count",
                "SP Consumption Sub Type",
                "SP Service Identifier",
            ],
            skipfooter=23,
        )

        # remove rows where first column is blank
        frame = frame.dropna(thresh=1)

        # update ministry acronyms
        frame["OM Asset Tag"] = frame["OM Asset Tag"].apply(
            lambda x: x.replace("AGRI", "AFF")
        )
        frame["OM Asset Tag"] = frame["OM Asset Tag"].apply(
            lambda x: x.replace("EMPR", "EMLI")
        )

        # find the date based on the filename
        pos = name.rfind("\\") + 1
        datestamp = name[pos : pos + 7].strip() + "-01"

        # remove the header row -- assumes it's the first

        frame = frame[1:]

        frames.append(frame)

    # merge the datasets together90
    combined = pd.concat(frames)

    # add headers back in
    combined.columns = [
        "reportingcustomer",
        "ministry",
        "datausagegb",
        "idir",
        "server",
        "date",
        "mailboxitemcount",
        "consumptiontype",
        "serviceidentifier",
    ]

    # If mailboxitemcount cell is blank, fill with na
    combined.mailboxitemcount.fillna("0", inplace=True)

    # If server cell is blanks fill with na
    combined.server.fillna("na", inplace=True)

    # If idir cell is blank, fill with na
    combined.idir.fillna("na", inplace=True)

    # If serviceidtentifier cell is blank, fill with na
    combined.serviceidentifier.fillna("na", inplace=True)

    # export to file
    combined.to_csv(
        datestamp[0:-3] + "_NRM_CAS_INCREMENTAL_Usage.csv", header=True, index=False
    )


if __name__ == "__main__":
    main(sys.argv[1:])
