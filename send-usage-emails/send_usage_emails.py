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


import calendar
import constants
import ldap_helper as ldap
import os
import psycopg2
import seaborn as sns
import socket
import sys
import smtplib
import time
# import glob
import matplotlib.pyplot as plt
# import os

from datetime import datetime
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from log_helper import LOGGER


# Get a simple formatted "sample" object
def get_sample(gb, sample_datetime: datetime):
    gb = float(gb)
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
def send_admin_email(message_detail):
    msg = MIMEMultipart("related")
    msg["Subject"] = "Script Report"
    if constants.DEBUG_EMAIL == "":
        msg["From"] = "IITD.Optimize@gov.bc.ca"
        msg["To"] = "IITD.Optimize@gov.bc.ca"
    else:
        msg["To"] = constants.DEBUG_EMAIL
        msg["From"] = constants.DEBUG_EMAIL

    dir_path = os.path.dirname(os.path.realpath(__file__))
    host_name = socket.gethostname()
    html = "<html><head></head><body><p>" \
        + "A scheduled script relay_bucket_data.py has sent an automated report email." \
        + "<br />Server: " + str(host_name) \
        + "<br />File Path: " + dir_path + "<br />" \
        + str(message_detail) \
        + "</p></body></html>"
    msg.attach(MIMEText(html, "html"))
    s = smtplib.SMTP(constants.SMTP_SERVER)
    s.sendmail(msg["From"], msg["To"], msg.as_string())
    s.quit()


# Query metabase db for h drive table, return data dictionary by idir
def get_hdrive_data():
    conn = None
    data = None
    try:
        # Open a connection
        conn = psycopg2.connect(
            host=constants.POSTGRES_HOST,
            database="metabase",
            user=constants.POSTGRES_USER,
            password=constants.POSTGRES_PASSWORD
        )
        # create a cursor
        cur = conn.cursor()

        LOGGER.debug('H Drive data from the last two months:')
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
        ldap_util = ldap.LDAPUtil(constants.LDAP_USER, constants.LDAP_PASSWORD)
        for result in all_results:
            idir = result[0]
            gb = result[1]
            if constants.DEBUG_IDIR is not None:
                if idir == constants.DEBUG_IDIR:
                    gb = 12.456
                else:
                    continue
            sample_datetime = result[2]
            if idir not in data:
                ad_info = ldap_util.getADInfo(idir)
                data[idir] = {
                    "idir": idir,
                    "samples": [
                        get_sample(gb, sample_datetime)
                    ],
                    "mail": ad_info["mail"],
                    "name": ad_info["givenName"]
                }
            else:
                data[idir]["samples"].append(get_sample(gb, sample_datetime))
        for idir in data:
            # sort the samples
            data[idir]["samples"].sort(
                key=lambda s: s["sample_datetime"]
            )

    # close the communication with the PostgreSQL
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        LOGGER.warning(error)
        message_detail = "The send_usage_emails script failed to connect or read data from the postgres database. " \
            + "<br />Username: " + constants.POSTGRES_USER \
            + "<br />Message Detail: " + str(error)
        send_admin_email(message_detail)
    finally:
        if conn is not None:
            conn.close()
            LOGGER.debug('Database connection closed.')
    return data


# Generate an graph image's bytes using idir info
def get_graph_bytes(idir_info):
    samples = idir_info["samples"]
    idir = idir_info["name"]

    # Select plot theme, without seaborn
    """
    plt.style.use("seaborn-whitegrid")
    fig = plt.figure()
    ax1 = plt.axes()

    # Build bar chart with a colour array
    colors = ["#e3a82b", "#234075"]
    axis_dates = []
    for idx, sample in enumerate(samples):
        plt.bar(sample["sample_datetime"], sample["gb"], color=colors[idx], alpha=0.9, label=sample["month"])
        axis_dates.append(sample["sample_datetime"].strftime('%Y-%m-%d'))
        """

    # Select plot theme, with seaborn
    sns.set()
    sns.set_theme(style="whitegrid")
    fig = plt.figure()
    ax1 = plt.axes()
    # Create a colour array
    colors = ["#e3a82b", "#234075"]
    # Set custom colour palette
    sns.set_palette(sns.color_palette(colors))
    # Build bar chart
    axis_dates = []
    for idx, sample in enumerate(samples):
        sns.barplot(
            x=sample["sample_datetime"],
            y=sample["gb"],
            color=colors[idx],
            width=1,
            space=1,
            ci=None,
            dodge=False,
            alpha=0.9,
            estimator=min,
            label=sample["month"]
        )
        axis_dates.append(sample["sample_datetime"].strftime("%Y-%m-%d"))

    # Apply labels, legends and alignments
    plt.legend(
        title="Month",
        fontsize="small",
        fancybox=True,
        framealpha=1,
        shadow=True,
        bbox_to_anchor=(1.01, 1),
        borderaxespad=0
    )
    """
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
    plt.legend(
        title="Month",
        fontsize="small",
        fancybox=True,
        framealpha=1,
        shadow=True,
        bbox_to_anchor=(1.01, 1),
        labels=label_names,
        borderaxespad=0
    )"""

    plt.title(f"{idir} - H: Drive Data Usage", fontsize=14)
    plt.ylabel("Data size (GB)", fontsize=10)
    x_axis = ax1.axes.get_xaxis()
    x_axis.set_visible(False)

    caption = " "
    fig.text(0.5, 0.01, caption, ha="center")
    plt.tight_layout()

    # Save the plot to file
    plt.savefig('/tmp/graph.png')
    # open image and read as binary
    fp = open('/tmp/graph.png', "rb")
    os.remove('/tmp/graph.png')
    image_bytes = fp.read()
    fp.close()

    return image_bytes


# Send an email to the user containing usage information
def send_idir_email(idir_info):
    samples = idir_info["samples"]
    name = idir_info["name"]
    recipient = idir_info["mail"]
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
    html = (html_intro + html_snapshot_taken + html_img + html_why_important + html_footer)
    msg.attach(MIMEText(html, "html"))

    msgImage = MIMEImage(get_graph_bytes(idir_info))
    msgImage.add_header("Content-ID", "<image1>")
    msg.attach(msgImage)

    # send email
    s = smtplib.SMTP(constants.SMTP_SERVER)
    LOGGER.debug(f"Sending to: {recipient} if == peter.platten@gov.bc.ca")
    if (recipient.upper() == constants.DEBUG_EMAIL.upper()):
        s.sendmail(msg["From"], recipient, msg.as_string())
    s.quit()

    # log send complete
    LOGGER.info(f"Email sent to {recipient}.")


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
            LOGGER.info(f"GB: {gb}, Datetime: {sample_datetime}, Month: {month}")
        # send email to user
        LOGGER.debug(idir)
        if idir == "PPLATTEN":
            send_idir_email(data[idir])
        # follow smtp server guidelines of max 30 emails/minute
        time.sleep(2)


if __name__ == "__main__":
    main(sys.argv[1:])
    time.sleep(300)
