# -------------------------------------------------------------------------------
# Name:        clean_sfp_enhanced_data.py
# Purpose:     the purpose of the script is to clean the SFP enhanced report data:
#              1.) Add a date column
#              2.) Add a ministry column
#              3.) Remove the container column
#              4.) Combine all ministries into one file
#
# Author:      HHAY, JMONTEBE
#
# Created:     2021
# Copyright:   (c) Optimization Team 2022
# Licence:     mine
#
#
# usage: clean_sfp_enhanced_data.py -i <input_directory> -d <first of the month report received>
# example:  clean_sfp_enhanced_data.py -i J:\Scripts\Python\data_to_process -d 2021-01-01
# note: run this per ministry and rename the output with the ministry acronym. 
# -------------------------------------------------------------------------------

from csv import writer
import csv
import sys
import glob
import argparse


def isHeader(row, sizembcol):

    sizecol = sizembcol
    header = "sizemb"
    fields = len(row)
    a = 0

    # Check for header Path, skip row if exists
    for a in range(sizecol, fields):
        if header.lower().strip().replace(" ", "") == row[a].lower().strip().replace(
            " ", ""
        ):
            print("Found header: Size MB")
            print(row)
            skip = True
        else:
            skip = False

        return skip


def clean_data(csv_names, convertedcsv, date):
    # find the ministry of each input file to add in a ministry column to output csv
    # find the container and size columns to remove the commas from the size column and remove the container column completely
    # check for the header row and exclude skip it if exists
    # add and remove columns

    # counter = 0
    # run through each of the input csv files
    for name in csv_names:

        count = 0

        # find ministry from file name
        ministry = find_ministry(name)

        # open each file and parse through contents
        with open(name, encoding="utf-8", errors="ignore") as in_file:
            for row in csv.reader(in_file):

                # find the size and container columns
                if count == 0:
                    # call function to find size and container columns
                    sizembcol, containercol = find_columns(row)
                    # check for header row and exlcude if it exists
                    if isHeader(row, sizembcol):
                        count += 1
                        continue
                    elif not isHeader(row, sizembcol):
                        count += 1
                        print("Did not find header row")

                    # print ('Column sizemb is column: '+str(sizembcol))
                    # print ('Column container is column: '+str(containercol))

                # remove container column and add in ministry and date
                if not isHeader(row, sizembcol):
                    row, fields = modify_columns(
                        row, sizembcol, containercol, ministry, date
                    )
                    # print (cleanrow)

                convertedcsv.append(row[:fields])
                count += 1
            print(f"Number of rows read: {count}")

    return convertedcsv


def find_columns(row):

    fields = len(row)
    a = 0
    containercolname = "container"
    sizembcolname = "sizemb"
    containercol = 0
    sizembcol = 0

    # look for the container and size column to find positions
    for a in range(0, fields):
        if sizembcolname.lower().strip().replace(" ", "") == row[
            a
        ].lower().strip().replace(" ", ""):
            sizembcol = a
            print(f"Column sizemb is column: {sizembcol}")

        if containercolname.lower().strip().replace(" ", "") == row[
            a
        ].lower().strip().replace(" ", ""):
            containercol = a
            print(f"Column container is column: {containercol}")

    if sizembcol != 2:
        sizembcol = 2
        print(f"WARNING: Could not find sizemb header. Setting to column: {sizembcol}")
        print("Check input and output file to ensure correct column order and format")

    if containercol != 6:
        containercol = 6
        print(
            f"WARNING: Could not find container header. Setting to column: {containercol}"
        )
        print("Check input and output file to ensure correct column order and format")

    return sizembcol, containercol


def modify_columns(row, sizembcol, containercol, ministry, date):

    # remove container column
    del row[containercol]
    # remove commas from size column
    row[sizembcol] = row[sizembcol].replace(",", "")
    # add ministry and date columns
    row.append(ministry)
    row.append(date)
    cleanrow = list(filter(None, row))
    fields = len(cleanrow)

    return row, fields


def find_ministry(name):
    # find ministry by looking at file name for ministry names
    ministries = ["agri", "empr", "env", "irr", "flnr", "emli", "aff", "af", "for"]
    for findname in ministries:
        if name.lower().find(findname) != -1:
            ministryname = findname.upper()
            ministryname = (
                ministryname.replace("AGRI", "AF")
                .replace("AFF", "AF")
                .replace("EMPR", "EMLI")
                .replace("FLNR", "FOR")
            )
            print(f"Found ministry name: {ministryname}")
            break

    return ministryname


def main(argv):
    # take a single input directory argument in
    # print ('Number of arguments:', len(sys.argv), 'arguments.')
    # print ('Argument List:', str(sys.argv))

    inputdirectory = ""
    date = ""
    syntaxcmd = "Insufficient number of commands passed: clean_sfp_enhanced.py -i <input_file> -d <datecol> -p <path_contains>"

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
        dest="date",
        required=True,
        help="user provided date for date column",
        metavar="string",
        type=str,
    )
    args = parser.parse_args()

    inputdirectory = args.inputdirectory
    date = args.date

    csv_names = glob.glob(inputdirectory + r"\*.csv")

    convertedcsv = list()
    clean_data(csv_names, convertedcsv, date)

    output_file = date + "_SFP_Enhanced_Data.csv"
    # Open the output_file in write mode
    with open(output_file, "w", newline="", encoding="utf-8-sig") as write_obj:
        csv_writer = writer(write_obj)

        # Write the headers to the output file
        csv_writer.writerow(
            [
                "filename",
                "path",
                "sizemb",
                "lastaccessdate",
                "modificationdate",
                "creationdate",
                "share",
                "owner",
                "ministry",
                "date",
            ]
        )

        count = 0

        for row in convertedcsv:
            csv_writer.writerow(row)
            count = count + 1

    print(f"Total number of rows writen: {count}")


if __name__ == "__main__":
    main(sys.argv[1:])
