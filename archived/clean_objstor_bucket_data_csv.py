# -------------------------------------------------------------------------------
# Name:        clean_objstor_bucket_data_csv.py
# Purpose:     the purpose of the script is to parse bucket tags and aggregate into ministry reports
#
# Author:      CCOCKER
#
# Created:     2021
# Copyright:   (c) Optimization Team 2021
# Licence:     mine
#
#
# usage: clean_objstor_bucket_data.py -i <inputcsvfile>
# example:  clean_objstor_bucket_data.py -i J:\Scripts\Python\Data\ObjectStorageReport.xlsx
# -------------------------------------------------------------------------------

import sys
import argparse
import pandas as pd
import csv


def main(argv):
    # take a single input directory argument in
    # print ('Number of arguments:', len(sys.argv), 'arguments.')
    # print ('Argument List:', str(sys.argv))

    csvfile = ""
    csvoutfile = ""
    syntaxcmd = "Insufficient number of commands passed: clean_objstor_bucket_data.py -i <inputcsvfile>"

    if len(sys.argv) < 3:
        print(syntaxcmd)
        sys.exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input",
        dest="csvfile",
        required=True,
        help="path to file containing object storage report",
        metavar="FILE",
    )
    args = parser.parse_args()

    csvfile = args.csvfile
    csvoutfile = csvfile[: csvfile.find(".")] + "_UPDATED.csv"

    # process CSV - tally ministry usage
    with open(csvfile) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=",")
        line_count = 0

        # empty dictionary for ministry consumption totals
        consumed = dict()

        # empty lists for untagged/empty buckets
        untagged = []
        empty = []

        # placeholder for any unnacounted usage
        unnacounted = float()

        for row in csv_reader:

            # check for tags, start after heading rows
            if line_count > 5 and len(row) > 10:
                # get GiB used - skip if empty
                if row[7] != "":
                    used = float(row[7])
                else:
                    empty.append(row[0])
                    line_count += 1
                    continue

                # parse buckets with tags
                if row[10] != "":

                    # Historic tags have multiple KV pairs separated by commas - replace comma to separate
                    tag_string = row[10].replace(",", ";")

                    # split tags into list, removing trailing whitespace
                    tags = dict(s.strip().split("=") for s in tag_string.split(";"))

                    # only interested in Ministry for data consumption
                    if "Ministry" in tags.keys():
                        ministry = tags["Ministry"]

                        # check for ministry to add in dictionary or append consumption amount
                        if ministry in consumed.keys():
                            consumed[ministry] += used
                        else:
                            consumed[ministry] = used
                    else:
                        # flag bucket name for review (tags, but no usage)
                        untagged.append(row[0])
                else:
                    unnacounted += float(row[7])
                    untagged.append(row[0])
            line_count += 1

        # Add unnacounted usage to dictionary
        consumed["Untagged"] = unnacounted

        # create consumption report csv
        # TODO: Make this work better - only wrote untagged? Write back to where the data was sourced - check other scripts to follow pattern.
        (
            pd.DataFrame.from_dict(data=consumed, orient="index").to_csv(
                csvoutfile, header=False
            )
        )


if __name__ == "__main__":
    main(sys.argv[1:])
