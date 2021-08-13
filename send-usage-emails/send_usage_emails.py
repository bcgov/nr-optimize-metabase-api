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

# import pyad.adquery
import constants
import sys
import smtplib
import psycopg2
import calendar
# import glob
# import time
# import os
# import matplotlib.pyplot as plt

from datetime import datetime
from email.mime.multipart import MIMEMultipart
# from email.mime.image import MIMEImage
from email.mime.text import MIMEText

# q = pyad.adquery.ADQuery()
# q.default_ldap_server = "ldaps://plywood.idir.bcgov:636"

"""
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
"""


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
    """
    # open image and read as binary
    fp = open(os.path.join(dest_directory, "graph.png"), "rb")
    msgImage = MIMEImage(fp.read())
    fp.close()

    # define the image's ID as referenced above
    msgImage.add_header("Content-ID", "<image1>")
    msg.attach(msgImage)
    """
    # send the message via local SMTP server.
    s = smtplib.SMTP(constants.SMTP_SERVER)
    # sendmail function takes 3 arguments: sender's address, recipient's address
    # and message to send - here it is sent as one string.
    s.sendmail(sender, recipient, msg.as_string())
    s.quit()


def get_sample(gb, sample_datetime: datetime):
    return {
        "gb": gb,
        "sample_datetime": sample_datetime,
        "month": calendar.month_name[sample_datetime.month]
    }


def send_error_email(error_message):
    msg = MIMEMultipart("related")
    msg["Subject"] = "Script failure"
    msg["From"] = "IITD.Optimize@gov.bc.ca"
    msg["To"] = "IITD.Optimize@gov.bc.ca"
    if constants.USE_DEBUG_IDIR.upper() == "TRUE":
        msg["To"] = "peter.platten@gov.bc.ca"
    html = (
        """<html><head></head><body><p>
        A scheduled script has failed to complete. Error Message:<br />"""
        + str(error_message)
        + """</p></body></html>"""
    )
    msg.attach(MIMEText(html, "html"))
    s = smtplib.SMTP(constants.SMTP_SERVER)
    s.quit()


def get_hdrive_data():
    conn = None
    data = None
    try:
        # Open a connection
        conn = psycopg2.connect(
            host="postgresql",
            database="metabase",
            user=constants.POSTGRES_USER,
            password=constants.POSTGRES_PASSWORD
        )
        # create a cursor
        cur = conn.cursor()

        # execute a statement
        print('PostgreSQL database version:')
        cur.execute('SELECT version()')
    # display the PostgreSQL database server version
        db_version = cur.fetchone()
        print(db_version)

        print('H Drive data from the last two months:')
        sql_expression = """
        SELECT idir, datausage, date FROM hdriveusage WHERE (date_trunc('month',
         CAST(date AS timestamp)) BETWEEN date_trunc('month', CAST((CAST(now()
         AS timestamp) + (INTERVAL '-2 month')) AS timestamp)) AND
         date_trunc('month', CAST(now() AS timestamp)) AND idir <> 'Soft
         deleted Home Drives') ORDER BY idir ASC;
        """
        cur.execute(sql_expression)
        all_results = cur.fetchall()
        data = {}
        for result in all_results:
            idir = result[0]
            if constants.USE_DEBUG_IDIR.upper() == "TRUE":
                if idir != constants.DEBUG_IDIR:
                    continue
            gb = result[1]
            sample_datetime = result[2]
            if idir not in data:
                data[idir] = {
                    "idir": idir,
                    "samples": [
                        get_sample(gb, sample_datetime)
                    ],
                    "email": "peter.platten@gov.bc.ca",
                    "name": "Peter Platten"
                }
            else:
                data[idir]["samples"].append(get_sample(gb, sample_datetime))
        for idir in data:
            # sort the samples
            data[idir]["samples"].sort(
                key=lambda s: s["sample_datetime"]
            )
            if constants.USE_DEBUG_IDIR.upper() == "TRUE":
                data[idir]["samples"][0]["gb"] = 12.456
                data[idir]["samples"][1]["gb"] = 16.543

    # close the communication with the PostgreSQL
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        send_error_email(error)
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed.')
    return data


def get_gb_cost(gb):
    cost = (gb - 1.5) * 2.7
    if cost > 0:
        return cost
    return 0


def send_idir_email(idir, data):
    idir_info = data[idir]
    samples = idir_info["samples"]
    name = idir_info["name"]
    recipient = idir_info["email"]
    msg = MIMEMultipart("related")
    # last_month is the most recent reporting month
    last_month_sample = samples[len(samples)-1]
    last_month_name = last_month_sample["month"]
    last_month_gb = last_month_sample["gb"]
    last_month_cost = get_gb_cost(last_month_gb)
    month_before_last_sample = None
    if len(samples) > 1:
        month_before_last_sample = samples[len(samples)-2]
        month_before_last_name = month_before_last_sample["month"]
        month_before_last_gb = month_before_last_sample["gb"]
        month_before_last_cost = get_gb_cost(month_before_last_gb)

    msg["Subject"] = f"Your H: Drive Usage Report for {last_month_name}"
    msg["From"] = "IITD.Optimize@gov.bc.ca"
    msg["To"] = recipient

    html_intro = f"""
    <html><head></head><body><p>
        Hi {name}!<br><br>

        The Optimization Team is making personalized H: Drive Usage Reports available
         to NRM users by email on a monthly basis.<br><br>

        H: Drive usage information is provided mid-month from the OCIO.
        Below, you will find a graph highlighting your H: Drive usage for {last_month_name}"""
    if month_before_last_sample is not None:
        html_intro = html_intro + f" and {month_before_last_name}"
    html_snapshot_taken = f""".
    At the time the data usage snapshot was taken, your H: Drive size was {last_month_gb}
    GB, costing your Ministry ${last_month_cost} for the month of {last_month_name}."""
    if month_before_last_sample is not None:
        html_snapshot_taken = html_snapshot_taken + f"""
        In {month_before_last_name}, you used {month_before_last_gb}GB at a cost of
        ${month_before_last_cost}.
        """
    html_img = """<br><br><img src="cid:image1" alt="Graph" style="width:250px;height:50px;">"""
    html_img = html_img
    html_why_important = """
    <br><br>
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
    """
    html_footer = """
    <br><br>
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
    html = (html_intro + html_snapshot_taken + html_why_important + html_footer)
    msg.attach(MIMEText(html, "html"))
    s = smtplib.SMTP(constants.SMTP_SERVER)
    s.quit()
    print(f"Email sent to {recipient}.")


def main(argv):
    data = get_hdrive_data()
    if data is None:
        return
    for idir in data:
        # print the samples
        for sample in data[idir]["samples"]:
            gb = sample["gb"]
            sample_datetime = sample["sample_datetime"]
            month = sample["month"]
            print(f"GB: {gb}, Datetime: {sample_datetime}, Month: {month}")
        send_idir_email(idir, data)
    # users = {}
    # get a dictionary of user > usage: {date/data usage}, name, from H Drive Usage

    # remove excluded idirs from dict_of_users
    # dict_of_users = [user for user in dict_of_users if user["idir"] not in excluded_idirs]

    # explicitly define users for testing so as to not spam all users in the usage report list
    """
    if constants.USE_DEBUG_IDIR.upper() == 'TRUE':
        dict_of_users = [user for user in dict_of_users if user["idir"] == constants.DEBUG_IDIR]

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

    """


if __name__ == "__main__":
    main(sys.argv[1:])
