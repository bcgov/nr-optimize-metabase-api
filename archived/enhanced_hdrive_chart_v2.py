# -------------------------------------------------------------------------------
# Name:        enhanced_hdrive_chart_v2.py
# Purpose:     the purpose of the script is to clean the OCIO quarterly enhanced
#              H: drive usage data and visualize the data into charts:
#              1.) Add a ministry column
#              2.) Combine all ministries into one file
#              3.) Add a date to the output filename
#              4.) Create a bar chart of usage by ministry
#
# Author:      HHAY, PPLATTEN, CAMWARIN
#
# Created:     2022
# Copyright:   (c) Optimization Team 2022
# Licence:     mine
#
#
# usage: enhanced_hdrive_chart_v2.py -i <input_directory> -d <YYYY-MM>
# example:  enhanced_hdrive_chart_v2.py -i C:\TEMP\data\enhanced -d 2022-10
# -------------------------------------------------------------------------------

import glob
import sys
import argparse
import pandas as pd
import os
import re
import matplotlib.pyplot as plt
import matplotlib as mpl


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
        frame["ministry"] = frame["ministry"].apply(lambda x: x.replace("FPRO", "BCWS"))

        frame = frame[1:]

        frames.append(frame)

    # merge the datasets together, add headers back in
    combined = pd.concat(frames)
    combined.columns = [
        "User",  # replaced "Path" with "User" in FY22-23 Q3 iteration to accomodate change in OCIO .csv download <Ministry>-U FileTypeCategory Summary Report
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
        "Empty Extension - Size GB",
        "Empty Extension - File Count",
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
        # dropped Default - File Count, Default - Size GB, Other - File Count, and Other - Size GB
        # in FY22-23 Q3 iteration to accomodate change in OCIO .csv download <Ministry>-U FileTypeCategory Summary Report
    ]

    cols = combined.columns.drop(
        ["User", "Ministry"]
    )  # replaced "Path" with "User" in FY22-23 Q3 iteration to accomodate change in OCIO .csv download <Ministry>-U FileTypeCategory Summary Report

    combined[cols] = combined[cols].apply(pd.to_numeric, errors="coerce")

    # export to file
    combined.to_csv(
        datestamp + "_NRM_Enhanced_HDrive_Usage.csv", header=True, index=False
    )

    # file type names to dictionary
    filetype = [
        "AppData",
        "Archive",
        "Audio",
        "Backups",
        "CAD",
        "Database",
        "Disk Images",
        "Documents",
        "Email",
        "Empty Extension",
        "Encase",
        "Executables",
        "Images",
        "Map",
        "P2P",
        "Source Code",
        "System",
        "Temporary",
        "Video",
        "Web Page",
        # dropped Default in FY22-23 Q3 iteration to accomodate change in OCIO .csv download <Ministry>-U FileTypeCategory Summary Report
    ]

    # sum of size gb figures per file type
    totalsizegb = (
        sum(combined["AppData - Size GB"]),
        sum(combined["Archive - Size GB"]),
        sum(combined["Audio - Size GB"]),
        sum(combined["Backups - Size GB"]),
        sum(combined["CAD - Size GB"]),
        sum(combined["Database - Size GB"]),
        sum(combined["Disk Images - Size GB"]),
        sum(combined["Documents - Size GB"]),
        sum(combined["Email - Size GB"]),
        sum(combined["Empty Extension - Size GB"]),
        sum(combined["Encase - Size GB"]),
        sum(combined["Executables - Size GB"]),
        sum(combined["Images - Size GB"]),
        sum(combined["Map - Size GB"]),
        sum(combined["P2P - Size GB"]),
        sum(combined["Source Code - Size GB"]),
        sum(combined["System - Size GB"]),
        sum(combined["Temporary - Size GB"]),
        sum(combined["Video - Size GB"]),
        sum(combined["Web Page - Size GB"]),
        # dropped calculations for Default - Size GB in FY22-23 Q3 iteration
        # to accomodate change in OCIO .csv download <Ministry>-U FileTypeCategory Summary Report
    )

    # sum of file count figures per file type
    totalfilecount = (
        sum(combined["AppData - File Count"]),
        sum(combined["Archive - File Count"]),
        sum(combined["Audio - File Count"]),
        sum(combined["Backups - File Count"]),
        sum(combined["CAD - File Count"]),
        sum(combined["Database - File Count"]),
        sum(combined["Disk Images - File Count"]),
        sum(combined["Documents - File Count"]),
        sum(combined["Email - File Count"]),
        sum(combined["Empty Extension - File Count"]),
        sum(combined["Encase - File Count"]),
        sum(combined["Executables - File Count"]),
        sum(combined["Images - File Count"]),
        sum(combined["Map - File Count"]),
        sum(combined["P2P - File Count"]),
        sum(combined["Source Code - File Count"]),
        sum(combined["System - File Count"]),
        sum(combined["Temporary - File Count"]),
        sum(combined["Video - File Count"]),
        sum(combined["Web Page - File Count"]),
        # dropped calculations for Default - File Count in FY22-23 Q3 iteration
        # to accomodate change in OCIO .csv download <Ministry>-U FileTypeCategory Summary Report
    )

    # Arrange data by size (descending)
    totalsizegb, filetype = zip(*sorted(zip(totalsizegb, filetype)))
    totalfilecount, filetype = zip(*sorted(zip(totalfilecount, filetype)))

    # Figure Size
    fig, ax = plt.subplots(figsize=(16, 9))

    # Horizontal Bar Plot
    ax.barh(filetype, totalsizegb, color=["#003366", "#FCBA19", "#1A5A96", "#606060"])

    # Set tick marks
    ax.xaxis.set_ticks_position("bottom")
    ax.yaxis.set_ticks_position("none")

    # Remove spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Add padding between axes and labels
    ax.xaxis.set_tick_params(pad=5)
    ax.yaxis.set_tick_params(pad=10)

    # Add thousands separator to x-axis values
    ax.xaxis.set_major_formatter(mpl.ticker.StrMethodFormatter("{x:,.0f}"))

    # add axis labels
    plt.xlabel("Total Size (GB)")
    plt.ylabel("File Type")

    # Add annotation to bars with thousands separator and spacing
    container = ax.containers[0]
    ax.bar_label(
        container, labels=[f"{x:,.2f}" for x in container.datavalues], padding=5
    )

    # Add Plot Title
    ax.set_title(
        """Content of NRM H: Drives - Quarterly Report """ + (datestamp),
        loc="left",
    )

    # Save the plot
    plt.savefig("enhanced_hdrive_" + (datestamp) + ".png", bbox_inches="tight")

    # Show Plot
    plt.show()

    # Close Plot
    plt.close()


if __name__ == "__main__":
    main(sys.argv[1:])
