# -------------------------------------------------------------------------------
# Name:        send_usage_graph_v2.py
# Purpose:     the purpose of the script is to email a list of users a bar chart of their H:drive usage over the past 2 reporting periods:
#                    1.) Combine 2 most recent NRM H:drive .csv files into one file
#                    2.) Remove IDIRs that have "opted-out" by using exclusion list
#                    3.) Create a bar chart per IDIR
#                    4.) E-mail message + embedded chart to each user using ADquery
#                    5.) Remove remaining .png and .csv from directory
#
# Author:      HHAY, JMONTEBE, PPLATTEN
#
# Created:     2021
# Copyright:   (c) Optimization Team 2021
# Licence:     mine
#
# usage: send_usage_graph_v2.py -i <input_directory> -f <destination_directory> -e <exclusion_directory>
# example:  send_usage_graph_v2.py -i J:\Scripts\Python\Data -f J:\Scripts\Python\Data\Output -e J:\Scripts\Python\Data\Lists
# -------------------------------------------------------------------------------

import pyad.adquery
import sys
import smtplib
import calendar
import argparse
import glob
import time
import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.text import MIMEText

q = pyad.adquery.ADQuery()
f = open("error_log.csv", "w")
f.write("Timestamp,IDIR,Error"+"\n")
f.close()


# combine previous two months csv's to one file for generating graphs
def combine_csvs(input_directory, dest_directory):
    frames = []
    # grab all the .csv files in the input directory (the ones that start with <yyyy-mm>_H_Drive_NRM_Usage)
    csv_names = pd.DataFrame()
    for file_name in glob.glob(os.join(input_directory, "*.csv")):
        frame = pd.read_csv(file_name, low_memory=False)
        csv_names = pd.concat([csv_names, frame], axis=0)

        # drop displayname and ministry columns (if this line interferes with email script portion, it can be removed)
        frame1 = frame.drop(["displayname", "ministry"], axis=1)

        # drop soft deleted home drives from dataframe
        frame1 = frame1[frame1.idir != "Soft deleted Home Drives"]

        # remove the header row -- assumes it's the first
        frame1 = frame1[1:]
        frames.append(frame1)
    # merge the datasets together, add headers back in
    # if dropped columns are added back in, remember to add them to combined.columns below)
    combined = pd.concat(frames)
    combined.columns = ["idir", "datausage", "date"]
    # export to file
    combined.to_csv(
        os.path.join(dest_directory, 'H_Drive_NRM_Usage_Report.csv'), header=True, index=False
    )


# update a user dictionary with AD information
def get_ad_info(user):
    idir = user["idir"]
    q.execute_query(["samaccountname", "givenName", "mail"], where_clause=f"samaccountname='{idir}'")
    error_message = ""
    if q.get_row_count() == 0:
        error_message = "not found in active directory."
    else:
        idir_info = q.get_single_result()
        if "givenName" in idir_info and idir_info["givenName"] is not None:
            user["givenName"] = idir_info["givenName"]
        else:
            error_message = "givenName not found. "
        if "mail" in idir_info and idir_info["mail"] is not None:
            user["mail"] = idir_info["mail"]
        else:
            error_message = error_message + "mail not found. "

    errors = error_message != ""
    user["all_ad_attributes_found"] = not errors
    if errors:
        user["error"] = error_message
        f = open("error_log.csv", "a")
        f.write(datetime.now().isoformat()+","+user["idir"]+","+error_message+"\n")
        f.close()
    return user


# create and save graph
def generate_graph(idir, dest_directory, prev_month, current_month):

    df = pd.read_csv(os.join(dest_directory, "H_Drive_NRM_Usage_Report.csv"))
    df = df[df["idir"].isin([idir])]
    counts = df["idir"].count()

    # Select plot theme
    sns.set()
    sns.set_theme(style="whitegrid")
    fig = plt.figure()
    ax1 = plt.axes()

    # Create a colour array
    colors = ["#e3a82b", "#234075"]

    # Set custom colour palette
    sns.set_palette(sns.color_palette(colors))

    # Build bar chart
    sns.barplot(
        data=df,
        x="date",
        y="datausage",
        hue="date",
        ci=None,
        dodge=False,
        alpha=0.9,
        estimator=min,
    )

    # Apply labels, legends and alignments
    plt.title(str(idir) + " - H: Drive Data Usage", fontsize=14)
    plt.ylabel("Data size (GB)", fontsize=10)
    x_axis = ax1.axes.get_xaxis()
    x_axis.set_visible(False)
    if counts == 1:
        plt.legend(
            title="Month",
            fontsize="small",
            fancybox=True,
            framealpha=1,
            shadow=True,
            bbox_to_anchor=(1.01, 1),
            labels=[current_month],
            borderaxespad=0,
        )
    elif counts > 1:
        plt.legend(
            title="Month",
            fontsize="small",
            fancybox=True,
            framealpha=1,
            shadow=True,
            bbox_to_anchor=(1.01, 1),
            labels=[prev_month, current_month],
            borderaxespad=0,
        )
    caption = " "
    fig.text(0.5, 0.01, caption, ha="center")
    plt.tight_layout()
    # Save the plot to file
    plt.savefig(os.path.join(dest_directory, 'graph.png'))
    # plt.show()  # Show the plot


# get the users usage for each month
def get_usage(idir, users):
    print(users)
    print(idir)
    df_new = users[users["idir"].str.contains(idir)]
    print(df_new)

    # print('found:'+str(idir))


# send email to user with previously generated graph
def send_email(
    name,
    prev_month,
    current_month,
    dest_directory,
    recipient,
    prev_month_data,
    curr_month_data,
    prev_month_cost,
    curr_month_cost,
):
    sender = "IITD.Optimize@gov.bc.ca"
    # recipient = "IITD.Optimize@gov.bc.ca"
    # cc = "IITD.Optimize@gov.bc.ca"

    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart("related")
    msg["Subject"] = "Your H: Drive Usage Report for " + str(current_month)
    msg["From"] = sender
    # msg['Cc'] = cc
    msg["To"] = recipient

    # rcpt = cc.split(',') + [recipient]

    # Create the body of the message (a plain-text and an HTML version).
    html = (
        """\
    <html>
        <head></head>
        <body>
        <p>
            Hi """
        + str(name)
        + """!<br>
            <br>
            The Optimization Team is making personalized H: Drive Usage Reports available to NRM users by email on a monthly basis.<br>
            <br>
            H: Drive usage information is provided mid-month from the OCIO.
            Below, you will find a graph highlighting your H: Drive usage for """
        + str(prev_month)
        + """ and """
        + str(current_month)
        + """.
            At the time the data usage snapshot was taken, your H: Drive size was """
        + str(curr_month_data)
        + """GB,
            costing your Ministry $"""
        + str(curr_month_cost)
        + """ for the month of """
        + str(current_month)
        + """.
            In """
        + str(prev_month)
        + """, you used """
        + str(prev_month_data)
        + """GB at a cost of $"""
        + str(prev_month_cost)
        + """.<br>
            <br>
            <img src="cid:image1" alt="Graph" style="width:250px;height:50px;"><br>
            <br>
            <b>Why is My Data Usage Important?</b><br>
            Data storage on the H: Drive is expensive and billed at $2.70 per GB, per month.
            This communication is meant to raise awareness and encourage you to proactively keep costs down.<br>
            <br>
            <b>Did the size of your H:Drive go up this month?</b><br>
            Here are 3 simple actions to help you reduce your storage expense "footprint":
            <ol>
                <li>Delete duplicate files and old drafts (time suggested: 5-10 mins)</li>
                <li><a href="https://intranet.gov.bc.ca/iit/products-services/technical-support/storage-tips-and-info#Emptyyourrecycling">Empty</a>
                your Recycle Bin (time suggested: 1 min)</li>
                <li><a href="https://intranet.gov.bc.ca/iit/onedrive/onedriveinfo?">Move</a> your files to OneDrive (time suggested: 20 mins)</li>
            </ol>
            <br>
            More suggestions on how to reduce can be found on our
            <a href="https://intranet.gov.bc.ca/iit/products-services/technical-support/storage-tips-and-info">StorageTips and Information page</a>.<br>
            <br>
            We welcome your questions, comments, and ideas! Connect with us at IITD.Optimize@gov.bc.ca.<br>
            <br>
            Signed,<br>
            Your Friendly Neighbourhood Optimization Team<br>
            (Chris, Hannah, Heather, Joseph, Kristal, Lolanda, and Peter)<br>
            <br>
            <br>
            </p>
            <p style="font-size: 10px">If you do not wish to receive these emails, please reply with the subject line "unsubscribe".</p>
        </body>
    </html>
    """
    )
    # Record the MIME types of both parts - text/plain and text/html.
    body = MIMEText(html, "html")
    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(body)

    # open image and read as binary
    fp = open(os.join(dest_directory, "graph.png"), "rb")
    msgImage = MIMEImage(fp.read())
    fp.close()

    # define the image's ID as referenced above
    msgImage.add_header("Content-ID", "<image1>")
    msg.attach(msgImage)

    # send the message via local SMTP server.
    s = smtplib.SMTP("apps.smtp.gov.bc.ca")
    # sendmail function takes 3 arguments: sender's address, recipient's address
    # and message to send - here it is sent as one string.

    s.sendmail(sender, recipient, msg.as_string())
    s.quit()


def main(argv):
    # take a single input directory argument in
    # take a single file destination argument in
    # print ('Number of arguments:', len(sys.argv), 'arguments.')
    # print ('Argument List:', str(sys.argv))

    input_directory = ""
    dest_directory = ""
    exclude_list = ""
    users = []

    syntaxcmd = "Insufficient number of commands passed: combine_hdrive_reports.py -i <input_directory> -r <recent_csv> -f <dest_directory> -e <exclude_list>"
    if len(sys.argv) < 3:
        print(syntaxcmd)
        sys.exit(1)
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input",
        dest="input_directory",
        required=True,
        help="path to directory containing usage reports",
        metavar="string",
        type=str,
    )
    parser.add_argument(
        "-r",
        "--recent_csv",
        dest="recent_csv",
        required=True,
        help="the most recent usage report file name",
        metavar="string",
        type=str,
    )
    parser.add_argument(
        "-f",
        "--file",
        dest="dest_directory",
        required=True,
        help="path to directory containing output file",
        metavar="string",
        type=str,
    )
    parser.add_argument(
        "-e",
        "--exclude_list",
        dest="exclude_list",
        required=True,
        help="list of excluded idirs",
        metavar="string",
        type=str,
    )

    args = parser.parse_args()
    input_directory = args.input_directory
    recent_csv = args.recent_csv
    dest_directory = args.dest_directory
    exclude_list = args.exclude_list

    combine_csvs(input_directory, dest_directory)

    users = pd.read_csv(
        os.join(input_directory, recent_csv), low_memory=False
    )

    dict_of_users = users.to_dict('records')

    # import exclusion list for opted out users
    excluded_idirs = pd.read_csv(exclude_list, low_memory=False)["idir"].values.tolist()

    # remove excluded idirs from dict_of_users
    dict_of_users = [user for user in dict_of_users if user["idir"] not in excluded_idirs]

    # explicitly define users for testing so as to not spam all users in the usage report list
    """
    dict_of_users = [
        {'idir': 'HHAY', 'displayname': 'Hay, Heather IIT:EX', 'datausage': 0.36, 'ministry': 'ENV', 'date': '2021-05-01'},
        {'idir': 'JMONTEBE', 'displayname': 'Montebello, Joseph IIT:EX', 'datausage': 0.03, 'ministry': 'ENV', 'date': '2021-05-01'},
        {'idir': 'PPLATTEN', 'displayname': 'Platten, Peter IIT:EX', 'datausage': 0.01, 'ministry': 'ENV', 'date': '2021-05-01'}
    ]
    """

    # get current month and subtract 1 month from it to get previous month and set current month to be equal to it.
    # This ensures that if it is sent on the first of the new month that the email states the correct months for the data
    cur_month_number = datetime.now().month
    cur_month_number = cur_month_number - 1
    if cur_month_number == 0:
        cur_month_number = 12
    prev_month_number = cur_month_number - 1
    if prev_month_number == 0:
        prev_month_number = 12
    # convert current and previous month numbers to text
    current_month = calendar.month_name[cur_month_number]
    prev_month = calendar.month_name[prev_month_number]

    for user in dict_of_users:
        user = get_ad_info(user)
        if user["all_ad_attributes_found"]:
            idir = user["idir"]
            name = user["givenName"]
            recipient = user["mail"]
            print(idir + ", " + name + ", " + recipient)

            generate_graph(idir, dest_directory, prev_month, current_month)

            # get_usage(idir,users)
            df_new = users[users["idir"] == idir]
            print(len(df_new))
            print(df_new)
            if len(df_new) == 2:
                prev_month_data = df_new["datausage"].iloc[0]
                prev_month_cost = prev_month_data * 2.7
                curr_month_data = df_new["datausage"].iloc[1]
                curr_month_cost = curr_month_data * 2.7
                if prev_month_data < 1.5:
                    prev_month_cost = 0
                if curr_month_data < 1.5:
                    curr_month_cost = 0
                prev_month_cost = round(prev_month_cost, 2)
                curr_month_cost = round(curr_month_cost, 2)

            if len(df_new) == 1:
                curr_month_data = df_new["datausage"].iloc[0]
                curr_month_cost = curr_month_data * 2.7
                prev_month_data = 0
                prev_month_cost = 0
                if curr_month_data < 1.5:
                    curr_month_cost = 0
                curr_month_cost = round(curr_month_cost, 2)

            send_email(
                name,
                prev_month,
                current_month,
                dest_directory,
                recipient,
                prev_month_data,
                curr_month_data,
                prev_month_cost,
                curr_month_cost,
            )
        else:
            time.sleep(2)
    # delete the left over graph from last user in list
    os.remove(os.join(dest_directory, "graph.png"))
    # delete the csv file that was generated for graph creation
    os.remove(os.join(dest_directory, "H_Drive_NRM_Usage_Report.csv"))


if __name__ == "__main__":
    main(sys.argv[1:])
