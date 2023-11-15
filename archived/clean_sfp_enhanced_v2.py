# -------------------------------------------------------------------------------
# Name:        clean_sfp_enhanced.py
# Purpose:     the purpose of the script is to clean the SFP enhanced report data:
#              1.) Add a date column
#              2.) Add a ministry column
#              3.) Remove the container column
#              4.) Process mutiple <ministry>-S Size File-Level Report.csv files (per ministry) into one file
#
# Author:      HHAY, JMONTEBE, PPLATTEN
#
# Created:     2021
# Copyright:   (c) Optimization Team 2022
# Licence:     mine
#
#
# usage: clean_sfp_enhanced_v2.py -i <input_directory> -d <first of the month report received> -m <ministry acronym>
# example:  clean_sfp_enhanced_v2.py -i C:\TEMP\data\ENV -d 2022-10-01 -m "ENV"
# -------------------------------------------------------------------------------

from csv import writer
import csv
import sys
import glob
import argparse


def isHeader(row, sizembcol):

    sizecol = sizembcol
    header = "file_size_mb"
    fields = len(row)
    a = 0

    # Check for header Path, skip row if exists
    for a in range(sizecol, fields):
        if header.lower().strip().replace(" ", "") == row[a].lower().strip().replace(
            " ", ""
        ):
            print("Found header: file_size_mb")
            print(row)
            skip = True
        else:
            skip = False

        return skip


def clean_data(csv_names, convertedcsv, date):
    # find the ministry of each input file to add in a ministry column to output csv
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
                    # call function to find size column
                    sizembcol = find_columns(row)
                    # check for header row and exlcude if it exists
                    if isHeader(row, sizembcol):
                        count += 1
                        continue
                    elif not isHeader(row, sizembcol):
                        count += 1
                        print("Did not find header row")

                # round up file size mb then remove container and file_owner columns and add in ministry and date
                if not isHeader(row, sizembcol):
                    row, fields = modify_columns(row, ministry, date)
                    # print (cleanrow)

                convertedcsv.append(row[:fields])
                count += 1
            print(f"Number of rows read: {count}")

    return convertedcsv


def find_columns(row):

    fields = len(row)
    a = 0
    sizembcolname = "file_size_mb"
    sizembcol = 0

    # look for the container and size column to find positions
    for a in range(0, fields):
        if sizembcolname.lower().strip().replace(" ", "") == row[
            a
        ].lower().strip().replace(" ", ""):
            sizembcol = a
            print(f"Column file_size_mb is column: {sizembcol}")

    if sizembcol != 4:
        sizembcol = 4
        print(
            f"WARNING: Could not find file_size_mb header. Setting to column: {sizembcol}"
        )
        print("Check input and output file to ensure correct column order and format")

    return sizembcol


def modify_columns(row, ministry, date):

    # add ministry and date columns
    row.append(ministry)
    row.append(date)
    # remove unnecessary columns
    del row[9]
    del row[9]
    cleanrow = list(filter(None, row))
    fields = len(cleanrow)

    return row, fields


def find_ministry(name):
    # find ministry by looking at file name for ministry names
    ministries = [
        "agri",
        "empr",
        "env",
        "irr",
        "flnr",
        "emli",
        "aff",
        "af",
        "for",
        "lwrs",
        "fpro",
        "bcws",
    ]
    for findname in ministries:
        if name.lower().find(findname) != -1:
            ministryname = findname.upper()
            ministryname = (
                ministryname.replace("AGRI", "AF")
                .replace("AFF", "AF")
                .replace("EMPR", "EMLI")
                .replace("FLNR", "FOR")
                .replace("FPRO", "BCWS")
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
    ministry = ""
    syntaxcmd = "Insufficient number of commands passed: clean_sfp_enhanced.py -i <input_file> -d <datecol> -m <ministry_acronym>"

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
    parser.add_argument(
        "-m",
        "--min",
        dest="ministry",
        required=True,
        help="user provided ministry acronym for output filename",
        metavar="string",
        type=str,
    )

    args = parser.parse_args()

    inputdirectory = args.inputdirectory
    date = args.date
    ministry = args.ministry

    csv_names = glob.glob(inputdirectory + r"\*.csv")

    convertedcsv = list()
    clean_data(csv_names, convertedcsv, date)

    output_file = date + "_" + ministry + "_SFP_Enhanced_Data.csv"
    # Open the output_file in write mode
    with open(output_file, "w", newline="", encoding="utf-8-sig") as write_obj:
        csv_writer = writer(write_obj)

        # Write the headers to the output file
        csv_writer.writerow(
            [
                "filename",
                "path",
                "filetype",
                "category",
                "sizemb",
                "lastaccessdate",
                "modificationdate",
                "creationdate",
                "share",
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
