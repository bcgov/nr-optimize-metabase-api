# -------------------------------------------------------------------------------
# Name:        clean_h_drive_data_csv.py
# Purpose:     the purpose of the script is to clean the H: drive usage data:
#              1.) Add a date column
#              2.) Add a ministry column
#              3.) Combine all ministries into one file
#
# Author:      HHAY, JMONTEBE, SSOYKUT
#
# Created:     2020
# Copyright:   (c) Optimization Team 2020
# Licence:     mine
#
#
# usage: clean_h_drive_data.py -i <input_directory>
# example:  clean_h_drive_data.py -i J:\Scripts\Python\Data
# -------------------------------------------------------------------------------

import glob
import sys
import argparse
import pandas as pd
import os
import ldap_helper as ldap

dept_errors = []
attribute_error_idirs = []
other_error_idirs = []
not_found = []


def get_department(idir, ldap_util, conn):
    ad_info = None
    try:
        # Connect to AD to get user info
        ad_info = ldap_util.getADInfo(idir, conn)
    except (Exception, AttributeError) as error:
        if AttributeError:
            print(f"Unable to find {idir} due to error {error}")
            if error.args[0] == "department" :
                dept_errors.append(idir)
            else:
                attribute_error_idirs.append(idir)
        else:
            print(f"Unable to find {idir} due to error {error}")
            other_error_idirs.append(idir)

    if ad_info is None or ad_info['givenName'] is None:
        not_found.append(idir)
        return None
    elif "department" in ad_info:
        return ad_info["department"]
    return None


def manipulate_frame(frame, ministryname, datestamp, ldap_util, conn):
    # remove rows where User ID is blank
    frame = frame.dropna(thresh=1)

    # add ministry and date columns
    frame = frame.assign(ministry=ministryname)
    frame = frame.assign(date=datestamp)

    # update ministry acronyms
    frame["ministry"] = frame["ministry"].apply(lambda x: x.replace("AGRI", "AF"))
    frame["ministry"] = frame["ministry"].apply(lambda x: x.replace("AFF", "AF"))
    frame["ministry"] = frame["ministry"].apply(lambda x: x.replace("FLNR", "FOR"))
    frame["ministry"] = frame["ministry"].apply(lambda x: x.replace("EMPR", "EMLI"))
    frame["ministry"] = frame["ministry"].apply(lambda x: x.replace("MEM", "EMLI"))
    frame["ministry"] = frame["ministry"].apply(lambda x: x.replace("ABR", "IRR"))

    # remove the header row -- assumes it's the first
    frame = frame[1:]

    frame["division"] = frame[0].apply(lambda idir: get_department(idir, ldap_util, conn))

    return frame


def main(argv):
    # take a single input directory argument in
    # print ('Number of arguments:', len(sys.argv), 'arguments.')
    # print ('Argument List:', str(sys.argv))

    inputdirectory = ""
    frames = []
    syntaxcmd = "Insufficient number of commands passed: clean_h_drive_data.py -i <input_directory>"

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
    excel_names = glob.glob(os.path.join(inputdirectory, "*.xlsx"))

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
        ]
        for findname in ministries:
            if name.lower().find(findname) != -1:
                ministryname = findname.upper()
                break

        # find the date based on the filename
        pos = name.rfind("\\") + 1
        datestamp = name[pos : pos + 7].strip() + "-01"

        # read in xlsx, turn into dataframes
        excelsheet = pd.ExcelFile(name)

        frame = excelsheet.parse(excelsheet.sheet_names[1], header=None, index_col=None)

        ldap_util = ldap.LDAPUtil()
        conn = ldap_util.getLdapConnection()

        for sheet in excelsheet.sheet_names:
            if sheet == "Home Drives - BCWS":
                frame1 = excelsheet.parse(sheet, header=None, index_col=None)
                frame1 = manipulate_frame(frame1, ministryname, datestamp, ldap_util, conn)
                frames.append(frame1)
            continue

        frame = manipulate_frame(frame, ministryname, datestamp, ldap_util, conn)

        frames.append(frame)

    with open('dept_errors.txt', 'w') as f:
        f.write(",".join(dept_errors))
    with open('not_found.txt', 'w') as f:
        f.write(",".join(not_found))

    # merge the datasets together, add headers back in
    combined = pd.concat(frames)
    combined.columns = ["idir", "displayname", "datausage", "ministry", "date", "division"]

    # If displayname cell is blank, copy idir name to cell
    combined.displayname.fillna(combined.idir, inplace=True)

    # export to file
    combined.to_csv(
        datestamp[0:-3] + "_H_Drive_NRM_Usage.csv", header=True, index=False
    )


if __name__ == "__main__":
    main(sys.argv[1:])
