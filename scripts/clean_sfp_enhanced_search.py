# -------------------------------------------------------------------------------
# Name:        clean_h_drive_data_csv.py
# Purpose:     the purpose of the script is to clean the H: drive usage data:
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
# usage: clean_sfp_enhanced_data.py -i <input_directory>
# example:  clean_sfp_enhanced_data.py -i J:\Scripts\Python\Data
# -------------------------------------------------------------------------------

from csv import writer

import csv
import sys
import glob
import argparse


def isHeader(row):
    # Check for header Path
    if row[1] == "Path":
        print(f"Found header: {row[1]}")
        skip = True
    else:
        skip = False

    return skip


"""
def isContainer(row):
    containercolname = 'container'
    containercol = 0
    count = 0
    for row in convertedcsv:

        if count==0:
            print ('looking at first row of input csv')
            fields = len(row)
            a = 0

            for a in range(0, fields):
                if containercolname.lower().strip().replace(" ", "") == row[a].lower().strip().replace(" ", ""):
                    containercol = a
                    print ('found column with datestamp: '+str(containercol))

    return containercol
"""

'''
def add_column_in_csv(convertedcsv, output_file,header_of_date):
    """ Append a column in existing csv using csv.reader / csv.writer classes"""
    # Open the output_file in write mode
    with open(output_file, 'w', newline='', encoding="utf8") as write_obj:
        csv_writer = writer(write_obj)

        # write header row
        csv_writer.writerow(['filename','path','sizemb','lastaccessdate','lastmodifieddate','share','container','owner'])

        count=0

        for row in convertedcsv:
            # add the date field in the output csv
            if count==0:
                print ('looking at first row of input csv')
                row.append(header_of_date)
                count=count+1

            csv_writer.writerow(row)
            count = count+1

    print ('Number of rows read:' +str(count) )


    with open(output_file, 'w', newline='') as write_obj:
        # Create a csv.writer object from the output file object
        csv_writer = writer(write_obj)
        print('opened the files successfully')

        csv_writer.writerow(['File Name,Path,Size MB,Last Access Date,Modification Date,Share,Container,Owner'])

        # Read each row of the input csv file as list
        count=0

        for row in convertedcsv:
            # add the category field in the output csv
            if count==0:
                print ('looking at first row of input csv')
                row.append(header_of_date)
                count=count+1

                #find the row number based on the row header
                fields = len(row)
                a = 0
                datestampcol = 0

                for a in range(0, fields):
                    #strip spaces and make lower case headers prep for postgres
                    row
                    row[a]=row[a].lower().strip().replace(" ", "")


            else:


                #grab funding model colour and replace with VOTED or RECOVERY
                fundingmodel = row[fundingmodelcol].strip()

                formattedfunding = fix_funding_model(fundingmodel)
                row[fundingmodelcol] = formattedfunding


                # grab unformatted date, and append it to the data set
                rawdate = row[datestampcol].strip()
                row.append(rawdate)

                # put formatteddate back into recoveryperiod column

                formatteddate = fix_recovery_period(rawdate)
                row[recoveryperiodpos] = formatteddate

            csv_writer.writerow(row)
    print ('Number of rows read:' +str(count) )
'''


def main(argv):
    # take a single input directory argument in
    # print ('Number of arguments:', len(sys.argv), 'arguments.')
    # print ('Argument List:', str(sys.argv))

    inputdirectory = ""
    date = ""
    path_contains = ""
    # header_of_date = date
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
    parser.add_argument(
        "-p",
        "--path",
        dest="pathcontains",
        required=True,
        help="user provided path for searching",
        metavar="string",
        type=str,
    )
    args = parser.parse_args()

    inputdirectory = args.inputdirectory
    # csvoutfile = inputfile[:inputfile.find('.')]+'_UPDATED.csv'
    path_contains = args.pathcontains
    date = args.date

    csv_names = glob.glob(inputdirectory + r"\*.csv")

    convertedcsv = list()
    count = 0
    containercolname = "container"
    sizembcolname = "sizemb"
    pathcolname = "path"
    containercol = 0
    sizembcol = 0
    pathcol = 0

    for name in csv_names:

        # find ministry in file name for additional column
        ministries = ["agri", "empr", "env", "irr", "flnr", "emli", "aff"]
        for findname in ministries:
            if name.lower().find(findname) != -1:
                ministryname = findname.upper()
                ministryname = ministryname.replace("AGRI", "AFF").replace(
                    "EMPR", "EMLI"
                )
                print(ministryname)
                break

        # convert tab delimited to csv, without trailing empty columns

        with open(name, encoding="utf8") as in_file:
            for row in csv.reader(in_file):

                # find the container column number
                if count == 0:
                    print("looking at first row of input csv")
                    fields = len(row)
                    a = 0

                    for a in range(0, fields):
                        if containercolname.lower().strip().replace(" ", "") == row[
                            a
                        ].lower().strip().replace(" ", ""):
                            containercol = a
                            print("found column with container: " + str(containercol))

                        if sizembcolname.lower().strip().replace(" ", "") == row[
                            a
                        ].lower().strip().replace(" ", ""):
                            sizembcol = a
                            print("found column with sizemb: " + str(sizembcol))

                        if pathcolname.lower().strip().replace(" ", "") == row[
                            a
                        ].lower().strip().replace(" ", ""):
                            pathcol = a
                            print("found column with path: " + str(pathcol))

                # exclude header row
                if isHeader(row):
                    count += 1
                    continue

                # remove container column and add in ministry and date
                if row[0] != "File Name":
                    del row[containercol]
                    row[sizembcol] = row[sizembcol].replace(",", "")
                    row.append(ministryname)
                    row.append(date)
                    cleanrow = list(filter(None, row))
                    fields = len(cleanrow)

                    # print (cleanrow)

                # cut out blank columns, leave the 'recovery end date' column
                convertedcsv.append(row[:fields])
                count += 1

    print(date)

    file_name = path_contains.lower().strip().replace(" ", "")
    filename = file_name.lower().strip().replace("\\", "")

    output_file = date + filename + "_SFP_Enhanced_Data.csv"
    # Open the output_file in write mode
    with open(output_file, "w", newline="", encoding="utf8") as write_obj:
        csv_writer = writer(write_obj)

        csv_writer.writerow(
            [
                "filename",
                "path",
                "sizemb",
                "lastaccessdate",
                "lastmodifieddate",
                "share",
                "owner",
                "ministry",
                "date",
            ]
        )

        count = 0

        for row in convertedcsv:
            if path_contains.lower() in row[pathcol].lower():
                # print(f'Found string: {row[pathcol]}')

                csv_writer.writerow(row)
                count = count + 1

    print(f"Number of rows read: {count}")

    # print ("Add the category column in csv file with header in "+csvoutfile)
    # add_column_in_csv(convertedcsv, output_file,header_of_date,date)


if __name__ == "__main__":
    main(sys.argv[1:])
