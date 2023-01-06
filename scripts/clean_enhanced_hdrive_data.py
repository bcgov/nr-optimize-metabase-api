# -------------------------------------------------------------------------------
# Name:        clean_enhanced_hdrive_data.py
# Purpose:     the purpose of the script is to clean the OCIO quarterly enhanced
#              H: drive usage data:
#              1.) Add a ministry column
#              2.) Combine all ministries into one file
#              3.) Add a date to the output filename
#
# Author:      HHAY, PPLATTEN, CAMWARIN
#
# Created:     2022
# Copyright:   (c) Optimization Team 2022
# Licence:     mine
#
#
# usage: clean_h_drive_data.py -i <input_directory> -d <YYYY-MM>
# example:  clean_enhanced_hdrive_data.py -i J:\Scripts\Python\Data -d 2022-05
# -------------------------------------------------------------------------------

import glob
import sys
import argparse
import pandas as pd
import os
import re


def main(argv):
    # take an input directory and datestamp argument in
    # print ('Number of arguments:', len(sys.argv), 'arguments.')
    # print ('Argument List:', str(sys.argv))

    inputdirectory = ""
    frames = []
    ministry = []

    syntaxcmd = "Insufficient number of commands passed: clean_enhanced_hdrive_data.py -i <input_directory> -d <YYYY-MM>"

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
    parser.add_argument(
        "-d",
        "--date",
        dest="datestamp",
        required=True,
        help="Year and month of report",
        metavar="string",
        type=str,
    )
    args = parser.parse_args()

    inputdirectory = args.inputdirectory
    datestamp = args.datestamp

    # grab all the .csv files in the input directory
    csv_names = glob.glob(os.path.join(inputdirectory, "*.csv"))

    # pull the data out of each csv, and aggregate it
    for name in csv_names:

        # find the ministry based on the filename
        ministry = name.rpartition("-")[0]
        ministry = re.split(r"\\", ministry)[-1]

        # read in csv, turn into dataframes
        frame = pd.read_csv(name, header=None, index_col=None)

        # add ministry column
        frame.insert(1, "ministry", ministry)

        # update ministry acronyms
        frame["ministry"] = frame["ministry"].apply(lambda x: x.replace("AFF", "AF"))
        frame["ministry"] = frame["ministry"].apply(lambda x: x.replace("FLNR", "FOR"))

        frame = frame[1:]

        frames.append(frame)

    # merge the datasets together, add headers back in
    combined = pd.concat(frames)
    combined.columns = [
        "Path",
        "Ministry",
        "AppData - Size GB",
        "AppData - File Count",
        "Archive - Size GB",
        "Archive - File Count",
        "Audio - Size GB",
        "Audio - File Count",
        "Backups - Size GB",
        "Backups - File Count",
        "CAD - Size GB",
        "CAD - File Count",
        "Database - Size GB",
        "Database - File Count",
        "Disk Images - Size GB",
        "Disk Images - File Count",
        "Documents - Size GB",
        "Documents - File Count",
        "Email - Size GB",
        "Email - File Count",
        "Encase - Size GB",
        "Encase - File Count",
        "Executables - Size GB",
        "Executables - File Count",
        "Images - Size GB",
        "Images - File Count",
        "Map - Size GB",
        "Map - File Count",
        "P2P - Size GB",
        "P2P - File Count",
        "Source Code - Size GB",
        "Source Code - File Count",
        "System - Size GB",
        "System - File Count",
        "Temporary - Size GB",
        "Temporary - File Count",
        "Video - Size GB",
        "Video - File Count",
        "Web Page - Size GB",
        "Web Page - File Count",
        "Empty Extension - Size GB",
        "Empty Extension - File Count",
        "Default - Size GB",
        "Default - File Count",
        "Other - Size GB",
        "Other - File Count",
    ]

    # export to file
    combined.to_csv(
        datestamp + "_NRM_Enhanced_HDrive_Usage.csv", header=True, index=False
    )


if __name__ == "__main__":
    main(sys.argv[1:])
