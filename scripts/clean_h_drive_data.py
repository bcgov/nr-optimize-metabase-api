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
import math
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
        ad_info = ldap_util.getADInfo(idir, conn, ["givenName", "department"])
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


def manipulate_frame(frame, ministryname, datestamp):
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

    ldap_util = ldap.LDAPUtil()
    conn = ldap_util.getLdapConnection()

    idir_count = len(frame)
    departments = []
    recent_percent = "0.0"
    for i in range(len(frame.values)):
        percent_complete = math.floor(i*100.0/idir_count)
        percent_complete = f"{percent_complete:.1f}%"
        if recent_percent != percent_complete:
            recent_percent = percent_complete
            print(percent_complete)
        idir = frame.values[i][0]
        departments.append(get_department(idir, ldap_util, conn))
    frame['division'] = departments

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

        # Second tab is the primary h drive data dump
        frame = excelsheet.parse(excelsheet.sheet_names[1], header=None, index_col=None)
        frame = manipulate_frame(frame, ministryname, datestamp)

        # FOR also has a BCWS tab which is seperate from the primary h drive data, so get that too
        for sheet in excelsheet.sheet_names:
            if sheet == "Home Drives - BCWS":
                frame1 = excelsheet.parse(sheet, header=None, index_col=None)
                frame1 = manipulate_frame(frame1, ministryname, datestamp)
                frames.append(frame1)
            continue

        frames.append(frame)

    # merge the datasets together
    combined = pd.concat(frames)

    # UNCOMMENT THIS BLOCK TO STORE DETAILS ABOUT THE USERS WITHOUT DEPARTMENT
    # print("Writing dept_errors.txt")
    # ldap_util = ldap.LDAPUtil()
    # conn = ldap_util.getLdapConnection()
    # with open('dept_errors.txt', 'w') as f:
    #     out_attributes = ['sAMAccountName', 'title', 'company', 'homeDrive', 'badPwdCount', 'userAccountControl', 'lastLogon', 'lockoutTime', 'bcgovAccountType',
    #                       'mailboxOrgCode', 'bcgovHrDepartmentID', 'bcgovHrStatus', 'bcgovHrClientAccountCode', 'bcgovHrJobFunctionCode', 'msRTCSIP-UserEnabled',
    #                       'bcgovEmploymentType']
    #     f.write("\t".join(out_attributes))

    #     for idir in dept_errors:
    #         try:
    #             # Connect to AD to get user info
    #             # ad_info = ldap_util.getADInfo(idir, conn, ["givenName", "department"])
    #             ad_info = ldap_util.getADInfo(idir, conn)
    #         except (Exception, AttributeError) as error:
    #             print(f"Error while doing follow up search for IDIR: {idir}")
    #             print(error)
    #         if ad_info is not None:
    #             attribute_values = []
    #             for attribute in out_attributes:
    #                 if attribute in ad_info:
    #                     attribute_values.append(str(ad_info[attribute]))
    #                 else:
    #                     attribute_values.append("")
    #             f.write("\n"+"\t".join(attribute_values))

    # Log the users not found in LDAP
    with open('not_found.txt', 'w') as f:
        for idir in not_found:
            f.write(f"{idir}\n")

    # add headers back in
    combined.columns = ["idir", "displayname", "datausage", "ministry", "date", "division"]

    # If displayname cell is blank, copy idir name to cell
    combined.displayname.fillna(combined.idir, inplace=True)

    # export to file
    combined.to_csv(
        datestamp[0:-3] + "_H_Drive_NRM_Usage.csv", header=True, index=False
    )


if __name__ == "__main__":
    main(sys.argv[1:])
