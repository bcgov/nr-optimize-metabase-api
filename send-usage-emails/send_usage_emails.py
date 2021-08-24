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
import send_usage_emails_constants as constants
import sys
import smtplib
import psycopg2
import calendar
# import glob
import time
# import os
# import matplotlib.pyplot as plt

from datetime import datetime
from email.mime.multipart import MIMEMultipart
# from email.mime.image import MIMEImage
from email.mime.text import MIMEText


"""
q = pyad.adquery.ADQuery()
q.default_ldap_server = "ldaps://plywood.idir.bcgov:636"

# Update a user dictionary with AD information
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


# Get a simple formatted "sample" object
def get_sample(gb: float, sample_datetime: datetime):

    # Calculate and Format $ cost by GB
    cost = round((gb - 1.5) * 2.7, 2)
    if cost < 0:
        cost = 0

    return {
        "gb": gb,
        "sample_datetime": sample_datetime,
        "month": calendar.month_name[sample_datetime.month],
        "cost": cost
    }


# Send an email to the admin with error message
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


# Query metabase db for h drive table, return data dictionary by idir
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


"""
# Generate an graph image's bytes using idir info
def get_graph_bytes(idir_info):
    samples = idir_info["samples"]
    idir = idir_info["name"]
    # Select plot theme
    plt.style.use("seaborn-whitegrid")
    fig = plt.figure()
    ax1 = plt.axes()

    dates = []
    gb = []
    label_names = []
    for sample in samples:
        dates.append(sample["sample_datetime"])
        gb.append(sample["gb"])
        label_names.append(sample["month"])
    # Build bar chart with a colour array
    x = dates
    y = gb
    plt.bar(x, y, color=["#e3a82b", "#234075"], alpha=0.9)

    # Apply labels, legends and alignments
    plt.title(f"{idir} - H: Drive Data Usage", fontsize=14)
    plt.ylabel("Data size (GB)", fontsize=10)
    x_axis = ax1.axes.get_xaxis()
    x_axis.set_visible(False)

    plt.legend(
        title="Month",
        fontsize="small",
        fancybox=True,
        framealpha=1,
        shadow=True,
        bbox_to_anchor=(1.01, 1),
        labels=label_names,
        borderaxespad=0
    )
    caption = " "
    fig.text(0.5, 0.01, caption, ha="center")
    plt.tight_layout()

    # Save the plot to file
    plt.savefig(os.path.join(os.getcwd(), 'graph.png'))
    # open image and read as binary
    fp = open(os.path.join(os.getcwd(), "graph.png"), "rb")
    image_bytes = fp.read()
    fp.close()

    return image_bytes
"""


# Send an email to the user containing usage information
def send_idir_email(idir_info):
    samples = idir_info["samples"]
    name = idir_info["name"]
    recipient = idir_info["email"]
    msg = MIMEMultipart("related")

    # last_month is the most recent reporting month
    # month_before_last is the month before last_month
    # copy out values for use in fstrings
    last_month_sample = samples[len(samples)-1]
    last_month_name = last_month_sample["month"]
    last_month_gb = last_month_sample["gb"]
    last_month_cost = last_month_sample["cost"]
    month_before_last_sample = None
    if len(samples) > 1:
        month_before_last_sample = samples[len(samples)-2]
        month_before_last_name = month_before_last_sample["month"]
        month_before_last_gb = month_before_last_sample["gb"]
        month_before_last_cost = last_month_sample["cost"]

    # build email content and metadata
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
        In {month_before_last_name}, you used {month_before_last_gb} GB at a cost of
        ${month_before_last_cost}.
        """
    html_img = """<br><br><img src="cid:image1" alt="Graph" style="width:250px;height:50px;">"""
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
    # msgImage = MIMEImage(get_graph_bytes(idir_info))
    # msgImage.add_header("Content-ID", "<image1>")
    # msg.attach(msgImage)
    html = (html_intro + html_snapshot_taken + html_img + html_why_important + html_footer)

    # attach and send email
    msg.attach(MIMEText(html, "html"))
    s = smtplib.SMTP(constants.SMTP_SERVER)
    s.sendmail(msg["From"], recipient, msg.as_string())
    s.quit()

    # log send complete
    print(f"Email sent to {recipient}.")


def main(argv):
    # get a dictionary, format:
    # { idir : {
    #       name, email, idir, samples : [{
    #           gb, sample_datetime, month, cost
    #       }]
    #   }
    # }
    data = get_hdrive_data()
    if data is None:
        return

    for idir in data:
        # print the samples for development
        for sample in data[idir]["samples"]:
            gb = sample["gb"]
            sample_datetime = sample["sample_datetime"]
            month = sample["month"]
            print(f"GB: {gb}, Datetime: {sample_datetime}, Month: {month}")
        # send email to user
        print(idir)
        if idir == "PPLATTEN":
            send_idir_email(data[idir])
        # follow smtp server guidelines of max 30 emails/minute
        time.sleep(2)


if __name__ == "__main__":
    main(sys.argv[1:])
