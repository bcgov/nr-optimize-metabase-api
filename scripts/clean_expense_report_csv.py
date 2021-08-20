# -------------------------------------------------------------------------------
# Name:        clean_expense_report_csv.py
# Purpose:     the purpose of the script is to clean the CAS Expense report:
#              1.) add a category field
#              2.) fix the recovery period field format
#
# Author:      MRDOUVIL
#
# Created:     2020-02-14
# Copyright:   (c) MRDOUVIL 2020
# Licence:     mine
#
#
# usage: 'clean_expense_report_csv.py -i <inputcsvfile> -c <categoriesfile> -t <datestampcolname> -s <servicenamecolname>'
# example: ' 'clean_expense_report_csv.py' '-i' 'data/Report20180401to20200131-KRIS.csv' '-c' 'data/OptimizeLookupCategories.csv' '-t' 'Recovery Period' '-s' 'Service Name'
# -------------------------------------------------------------------------------

from csv import writer

import csv
import sys
import argparse


def isHeaderFooter(row):
    if row[0] == "Owner Party":
        skip = False
    elif row[0] == "NATURAL RESOURCE MINISTRIES":
        skip = False
    else:
        skip = True
    # print(f'first column in row: {row[0]}')
    return skip


def add_column_in_csv(
    convertedcsv,
    output_file,
    header_of_new_col,
    categoriesobj,
    datestampcolname,
    servicenamecolname,
    header_of_funding_model,
    header_of_ministry,
):
    """Append a column in existing csv using csv.reader / csv.writer classes"""
    # Open the output_file in write mode
    with open(output_file, "w", newline="") as write_obj:
        # Create a csv.writer object from the output file object
        csv_writer = writer(write_obj)
        print("opened the files successfully")
        # Read each row of the input csv file as list
        count = 0
        recoveryperiodpos = 0

        for row in convertedcsv:
            # add the category field in the output csv
            if count == 0:
                print("looking at first row of input csv")
                row.append(header_of_new_col)
                count = count + 1

                # find the row number based on the row header
                fields = len(row)
                a = 0
                datestampcol = 0
                servicenamecol = 0
                fundingmodelcol = 0
                ministrycol = 0

                for a in range(0, fields):
                    # strip spaces and make lower case headers prep for postgres
                    row[a] = row[a].lower().strip().replace(" ", "")
                    if row[a] == "sdaparty":
                        row[a] = "ministry"

                    if row[a] == "inventoryitemnumber":
                        row[a] = "inventoryitem"

                    if row[a] == "fundingmodelcolour":
                        row[a] = "fundingmodelstatus"

                    if datestampcolname.lower().strip().replace(" ", "") == row[
                        a
                    ].lower().strip().replace(" ", ""):
                        datestampcol = a
                        recoveryperiodpos = a
                        print("found column with datestamp: " + str(datestampcol))

                    if servicenamecolname.lower().strip().replace(" ", "") == row[
                        a
                    ].lower().strip().replace(" ", ""):
                        servicenamecol = a
                        print("found column with servicename: " + str(servicenamecol))

                    if header_of_funding_model.lower().strip().replace(" ", "") == row[
                        a
                    ].lower().strip().replace(" ", ""):
                        fundingmodelcol = a
                        print(
                            "found column with fundingmodelstatus: "
                            + str(fundingmodelcol)
                        )

                    if header_of_ministry.lower().strip().replace(" ", "") == row[
                        a
                    ].lower().strip().replace(" ", ""):
                        ministrycol = a
                        print("found column with ministry: " + str(ministrycol))

                if datestampcol == 0:
                    print("Recovery Period field not found please check input csv field header names")
                    sys.exit()
                if servicenamecol == 0:
                    print("Service Name field not found please check input csv field header names")
                    sys.exit()
                if fundingmodelcol == 0:
                    print("Funding Model Colour field not found please check input csv field header names")
                    sys.exit()
                if ministrycol == 0:
                    print("Ministry field not found please check input csv field header names")
                    sys.exit()

            else:
                rowservicename1 = row[servicenamecol].strip()
                cat = lookup_categories(rowservicename1, categoriesobj)
                row.append(cat)
                count = count + 1

                # grab sda party and replace with ministry acronyms
                ministry = row[ministrycol].strip()

                formattedministry = fix_ministry_names(ministry)
                row[ministrycol] = formattedministry

                # grab funding model colour and replace with VOTED or RECOVERY
                fundingmodel = row[fundingmodelcol].strip()

                formattedfunding = fix_funding_model(fundingmodel)
                row[fundingmodelcol] = formattedfunding

                # grab unformatted date, and append it to the data set
                rawdate = row[datestampcol].strip()

                # put formatteddate back into recoveryperiod column
                formatteddate = fix_recovery_period(rawdate)
                row[recoveryperiodpos] = formatteddate

            csv_writer.writerow(row)
    print(f"Number of rows read: {count}")


def lookup_categories(rowservicename, categoriesobj):
    # open the categories csv file and for each row lookup the category from the service name attribute in the expense report
    # pass the service name in the row of the expense report and look up the category in the categories csv file and return the category into the new field
    # find the service name in the second column of categoriesobj

    category = "no category"
    rowtest = rowservicename.strip()
    cnt = 0
    found = 0
    for catrow in categoriesobj:
        cnt = cnt + 1
        catrowservicename = catrow.split(",")[1].strip()
        if rowtest == catrowservicename:
            found = 1
            category = catrow.split(",")[0].strip()
            # print ('found category for '+rowtest+ " ----------- "+category)
            break
    if found == 0:
        print(f"DID NOT find a category for {rowtest}")
    categoriesobj.seek(0)
    # print ('number of rows in categories csv searched - '+str(cnt))
    return category


def fix_funding_model(colour):
    # fix the funding model colour to replace green with VOTED and orange with RECOVERY

    fundingcolour = ""

    if colour.lower().strip() == "green":
        fundingcolour = "VOTED"
    elif colour.lower().strip() == "orange":
        fundingcolour = "RECOVERY"
    else:
        fundingcolour = colour
    return fundingcolour


def fix_ministry_names(ministry):
    # fix the ministry column to replace sda party with ministry acronyms

    ministryname = ""

    if ministry == "AGRICULTURE":
        ministryname = "AFF"

    elif ministry == "AGRICULTURE, FOOD AND FISHERIES":
        ministryname = "AFF"

    elif ministry == "ENERGY, MINES AND PETROLEUM RESOURCES":
        ministryname = "EMLI"

    elif ministry == "ENERGY, MINES AND LOW CARBON INNOVATION":
        ministryname = "EMLI"

    elif ministry == "ENVIRONMENT AND CLIMATE CHANGE STRATEGY":
        ministryname = "ENV"

    elif (
        ministry == "FORESTS, LANDS, NATURAL RESOURCE OPERATIONS AND RURAL DEVELOPMENT"
    ):
        ministryname = "FLNR"

    elif ministry == "INDIGENOUS RELATIONS AND RECONCILIATION":
        ministryname = "IRR"

    elif ministry == "NATURAL RESOURCE MINISTRIES":
        ministryname = "NRM"

    else:
        ministryname = ministry

    return ministryname


def fix_recovery_period(rowtimestamp):
    # fix the timestamp file "recovery period" in the expense report csv file
    # expense report recovery period is by fiscal year and the syntax looks like this: 2020-12-20 (but this actually represents Calaendar year 2019-12)
    # SO for all months in the expense report we want to do something like this:
    #  January, Feburary, March *-0[1-3]-* (leave as is)
    #  April, May, June, July, August, September, October, November, December *-[04-12]-* (minus 1 for left(4))
    # converted to the recommended timestamp for ease of import - https://www.postgresql.org/docs/9.1/datatype-datetime.html
    # 2019-01-01  ISO 8601; January 1 in any mode (recommended format)
    # ISSUE - WHAT HAPPENS IF THIS GETS RUN MORE THAN ONCE????
    # perhaps a check against against the filename? OR we create a net new field -- yes (so we don't lose the source field)
    months = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]
    newtimestamp = ""

    # determine month string and position
    month = rowtimestamp[3:6]
    monthposition = months.index(month) + 1

    # determine year string and convert to 4 digits
    year = int(rowtimestamp[0:2])
    year = year + 2000

    # create datestring in correct format yyyy-mm-dd
    try:
        # if month between jan - mar
        if monthposition < 4:
            monthstring = "0" + str(monthposition)
            newtimestamp = f"{year}-{monthstring}-01"
        # if month between apr - sep
        elif monthposition < 10 and monthposition > 3:
            monthstring = "0" + str(monthposition)
            year = year - 1
            newtimestamp = f"{year}-{monthstring}-01"
        # if month between oct - dec
        else:
            monthstring = str(monthposition)
            year = year - 1
            newtimestamp = f"{year}-{monthstring}-01"
    except Exception:
        print(f"{rowtimestamp} can't be converted to number")
        newtimestamp = rowtimestamp

    return newtimestamp


def main(argv):
    print(f"Number of arguments: {len(sys.argv)} arguments.")
    print(f"Argument List: {str(sys.argv)}")

    csvfile = ""
    csvoutfile = ""
    categoriesfile = ""
    syntaxcmd = "clean_expense_report_csv.py -i <inputcsvfile> -c <categoriesfile> -t <datestampcolname> -s <servicenamecolname>"

    if len(sys.argv) < 2:
        print(syntaxcmd)
        sys.exit(2)

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-i",
        "--input",
        dest="csvfile",
        required=True,
        help="input expense report csv file",
        metavar="FILE",
    )
    parser.add_argument(
        "-c",
        "--categories",
        dest="categoriesfile",
        required=True,
        help="input export categories lookup file",
        metavar="FILE",
    )
    parser.add_argument(
        "-t",
        "--datestampcol",
        dest="datestampcolname",
        required=True,
        help="column name for the datestamp",
        metavar="string",
        type=str,
    )
    parser.add_argument(
        "-s",
        "--servicenamecol",
        dest="servicenamecolname",
        required=True,
        help="column name for the servicename",
        metavar="String",
        type=str,
    )
    args = parser.parse_args()

    csvfile = args.csvfile
    csvoutfile = csvfile[: csvfile.find(".")] + "_UPDATED.csv"
    categoriesfile = args.categoriesfile
    datestampcolname = args.datestampcolname
    servicenamecolname = args.servicenamecolname

    print(f'Input RAW Expense Report CSV file is {csvfile}')
    print(f'Input Category CSV file is {categoriesfile}')
    print(f'Output CSV file is {csvoutfile}')
    print(f"Datestamp in RAW expense report is in column {datestampcolname}")
    print(f"Service Name in RAW expense report is in column {servicenamecolname}")

    categoriesobj = open(args.categoriesfile, "r")

    print("Add a column with same values to an existing csv file with header")

    header_of_new_col = "category"
    header_of_funding_model = "fundingmodelstatus"
    header_of_ministry = "ministry"

    # convert tab delimited to csv, without trailing empty columns
    convertedcsv = list()
    count = 0
    with open(csvfile) as in_file:
        for row in csv.reader((in_file), delimiter="\t"):
            # exclude any non-data rows
            if isHeaderFooter(row):
                count += 1
                continue

            # find how many headders there are, so that we know how many columns are relevant
            if row[0] == "Owner Party":
                cleanrow = list(filter(None, row))
                fields = len(cleanrow)

            # cut out blank columns, leave the 'recovery end date' column
            convertedcsv.append(row[:fields])
            count += 1

    # print ("Add the category column in csv file with header in "+csvoutfile)
    add_column_in_csv(
        convertedcsv,
        csvoutfile,
        header_of_new_col,
        categoriesobj,
        datestampcolname,
        servicenamecolname,
        header_of_funding_model,
        header_of_ministry,
    )


if __name__ == "__main__":
    main(sys.argv[1:])
