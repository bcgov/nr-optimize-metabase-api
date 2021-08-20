# -------------------------------------------------------------------------------
# Name:        clean_groupshare_data_csv.py
# Purpose:     the purpose of the script is to clean the group share usage data:
#              1.) Add a date column
#              2.) Add a ministry column
#              3.) Combine all ministries into one file
#
# Author:      HHAY, JMONTEBE
#
# Created:     2021
# Copyright:   (c) Optimization Team 2021
# Licence:     mine
#
#
# usage: clean_groupshare_data.py -i <input_directory>
# example:  clean_groupshare_data.py -i J:\Scripts\Python\Data
# -------------------------------------------------------------------------------

import glob
import sys
import argparse
import pandas as pd
import os


def main(argv):
    # take a single input directory argument in
    # print ('Number of arguments:', len(sys.argv), 'arguments.')
    # print ('Argument List:', str(sys.argv))

    inputdirectory = ""
    frames = []
    syntaxcmd = "Insufficient number of commands passed: clean_groupshare_data.py -i <input_directory>"

    if len(sys.argv) < 3:
        print(syntaxcmd)
        sys.exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input",
        dest="inputdirectory",
        required=True,
        help="path to directory containing group share reports",
        metavar="string",
        type=str,
    )
    args = parser.parse_args()

    inputdirectory = args.inputdirectory

    # grab all the .xlsx files in the input directory
    excel_names = glob.glob(os.path.join(inputdirectory, "*.xlsx"))

    # pull the data out of each xlsx, and aggregate it
    for name in excel_names:

        # find the ministry based on the filename
        ministries = ["agri", "aff", "empr", "mem", "emli", "env", "abr", "irr", "flnr", "fpro"]
        for findname in ministries:
            if name.lower().find(findname) != -1:
                ministryname = findname.upper()
                break

        # find the date based on the filename
        pos = name.rfind("\\") + 1
        datestamp = name[pos : pos + 7].strip() + "-01"

        # read in xlsx, turn into dataframes
        excelsheet = pd.ExcelFile(name)
        frame = excelsheet.parse(excelsheet.sheet_names[2], header=None, index_col=None)

        # remove rows where User ID is blank
        frame = frame.dropna(thresh=1)

        # add ministry and date columns
        frame = frame.assign(ministry=ministryname)
        frame = frame.assign(date=datestamp)

        # update ministry acronyms
        frame["ministry"] = frame["ministry"].apply(lambda x: x.replace("AGRI", "AFF"))
        frame["ministry"] = frame["ministry"].apply(lambda x: x.replace("EMPR", "EMLI"))
        frame["ministry"] = frame["ministry"].apply(lambda x: x.replace("MEM", "EMLI"))
        frame["ministry"] = frame["ministry"].apply(lambda x: x.replace("ABR", "IRR"))

        # remove the header row -- assumes it's the first
        frame = frame[1:]

        frames.append(frame)

    # merge the datasets together, add headers back in
    combined = pd.concat(frames)
    combined.columns = ["server", "sharename", "datausage", "ministry", "date"]

    # export to file
    combined.to_csv(
        datestamp[0:-3] + "_Group_Share_NRM_Usage.csv", header=True, index=False
    )


if __name__ == "__main__":
    main(sys.argv[1:])
