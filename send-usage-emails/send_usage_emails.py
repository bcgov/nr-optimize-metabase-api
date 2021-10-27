# -------------------------------------------------------------------------------
# Name:        send_usage_emails.py
# Purpose:     the purpose of the script is to email a list of users a bar chart of their H:drive usage over the past 2 reporting periods:
#                    1.) Connect to the metabase postgres database, querying for all H drives
#                    2.) Get emails and names from active directory
#                    3.) Create a bar chart and send each user their html format report by email
#
# Author:      HHAY, JMONTEBE, PPLATTEN
#
# Created:     2021
# Copyright:   (c) Optimization Team 2021
# Licence:     mine
#
# usage: send_usage_emails.py
# Requires:
#   1.) Postgres database to be "localhost". On Dev PCs this is done using port binding with open_postgres_port_dev.bat
#   2.) A .env file to exist with valid credentials. See the constants.py for the required values.
# -------------------------------------------------------------------------------


import calendar
import constants
import decimal
import ldap_helper as ldap
import math
import os
import psycopg2
import random
import seaborn as sns
import socket
import sys
import smtplib
import time
import matplotlib.pyplot as plt

from datetime import datetime
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from log_helper import LOGGER


# Get a simple formatted "sample" object
def get_sample(gb, sample_datetime: datetime):
    gb = float(gb)
    # Calculate and Format $ cost by GB, encouraging users to have "up to" 1.5gb
    # cost = round((gb - 1.5) * 2.7, 2)
    # if cost < 0:
    #    cost = 0
    # Calculate and Format $ cost by GB, with 1.5gb discount applied at ministry level
    cost = round(gb * 2.7, 2)

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

        LOGGER.debug('H Drive data from the last six months:')
        sql_expression = """
        SELECT idir, datausage, date FROM hdriveusage WHERE (date_trunc('month',
         CAST(date AS timestamp)) BETWEEN date_trunc('month', CAST((CAST(now()
         AS timestamp) + (INTERVAL '-6 month')) AS timestamp)) AND
         date_trunc('month', CAST(now() AS timestamp)) AND idir <> 'Soft
         deleted Home Drives') ORDER BY idir ASC;
        """
        cur.execute(sql_expression)
        all_results = cur.fetchall()

        # close the communication with the PostgreSQL
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        LOGGER.info(error)
        message_detail = "The send_usage_emails script failed to connect or read data from the postgres database. " \
            + "<br />Username: " + constants.POSTGRES_USER \
            + "<br />Message Detail: " + str(error)
        send_admin_email(message_detail)
        quit()
    finally:
        if conn is not None:
            conn.close()
            LOGGER.debug('Database connection closed.')

    data = {}

    try:
        ldap_util = ldap.LDAPUtil(constants.LDAP_USER, constants.LDAP_PASSWORD)
    except (Exception) as error:
        LOGGER.info(error)
        message_detail = "The send_usage_emails script failed to connect or log in to LDAP. " \
            + "<br />Username: " + constants.LDAP_USER \
            + "<br />Message Detail: " + str(error)
        send_admin_email(message_detail)
        quit()

    attribute_error_idirs = []
    other_error_idirs = []
    conn = ldap_util.getLdapConnection()

    # Block which filters results to just one for quick debugging.
    """
    debug_results = []
    for result in all_results:
        idir = result[0]
        if idir.lower() == "pplatten":
            gb = (decimal.Decimal(random.randrange(0, 1000))/100)
            gb = round(gb, 2)
            gb_cost = round(gb*decimal.Decimal(2.7))
            month = calendar.month_name[result[2].month]
            print(f"sample size cost for {month}: ${gb_cost}")
            debug_results.append((idir, gb, result[2]))
    all_results = debug_results
    """

    for result in all_results:
        idir = result[0]
        gb = result[1]
        sample_datetime = result[2]
        if idir not in attribute_error_idirs and idir not in other_error_idirs:
            if idir not in data:
                try:
                    ad_info = ldap_util.getADInfo(idir, conn)
                except (Exception, AttributeError) as error:
                    print(f"Unable to find {idir} due to error {error}")
                    attribute_error_idirs.append(idir)
                    continue
                except (Exception) as error:
                    print(f"Unable to find {idir} due to error {error}")
                    other_error_idirs.append(idir)
                    continue

                if ad_info is None or ad_info["mail"] is None or ad_info["givenName"] is None:
                    other_error_idirs.append(idir)
                else:
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

    if len(attribute_error_idirs) > 0 or len(other_error_idirs) > 0:
        message_detail = "The send_usage_emails script failed to find all IDIRs. " \
            + "<br /><br />IDIRs not found due to attribute error: " + ",".join(attribute_error_idirs) \
            + "<br /><br />IDIRs not found due to other issue: " + ",".join(other_error_idirs)
        LOGGER.info(message_detail)
        send_admin_email(message_detail)
    return data


def get_h_drive_summary():
    conn = None
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

        LOGGER.debug('H Drive data from the last six months:')
        sql_expression = """
        SELECT count(*) AS "COUNT", sum(datausage) AS "DATAUSAGE" FROM hdriveusage WHERE (date_trunc('month',
         CAST(date AS timestamp)) BETWEEN date_trunc('month', CAST((CAST(now()
         AS timestamp) + (INTERVAL '-1 month')) AS timestamp)) AND
         date_trunc('month', CAST(now() AS timestamp)) AND idir <> 'Soft
         deleted Home Drives');
        """
        cur.execute(sql_expression)
        all_results = cur.fetchall()

        # close the communication with the PostgreSQL
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        LOGGER.info(error)
        message_detail = "The send_usage_emails script failed to connect or read data from the postgres database. " \
            + "<br />Username: " + constants.POSTGRES_USER \
            + "<br />Message Detail: " + str(error)
        send_admin_email(message_detail)
        quit()
    finally:
        if conn is not None:
            conn.close()
            LOGGER.debug('Database connection closed.')

    nrm_metrics = {}
    for result in all_results:
        nrm_metrics["total_h_drive_count"] = result[0]
        nrm_metrics["total_gb"] = result[1]
    return nrm_metrics


# Generate an graph image's bytes using idir info
def get_graph_bytes(idir_info):
    samples = idir_info["samples"]
    idir = idir_info["name"]

    # Select plot theme, with seaborn
    sns.set()
    sns.set_theme(style="whitegrid")
    fig = plt.figure()

    # Set custom colour palette and build bar chart
    previous_months_color = "#234075"
    last_month_color = "#e3a82b"
    colors = []
    axis_dates = []
    for idx, sample in enumerate(samples):
        axis_dates.append(sample["sample_datetime"].strftime("%Y-%m-%d"))
        if idx == len(samples) - 1:
            colors.append(last_month_color)
            sample["color"] = last_month_color
        else:
            colors.append(previous_months_color)
            sample["color"] = previous_months_color
    sns.set_palette(sns.color_palette(colors))

    barplot_formatted_samples = {
        'gb': [],
        'datetime': [],
        'month': [],
        'cost': [],
        'color': []
    }
    for sample in samples:
        barplot_formatted_samples['gb'].append(sample['gb'])
        barplot_formatted_samples['datetime'].append(sample['sample_datetime'])
        barplot_formatted_samples['month'].append(sample['month'])
        barplot_formatted_samples['cost'].append(sample['cost'])
        barplot_formatted_samples['color'].append(sample['color'])

    sns.barplot(
        x="month",
        y="cost",
        data=barplot_formatted_samples,
    )

    plt.title(f"{idir} - H: Drive Cost", fontsize=14)
    plt.ylabel("Data Cost ($)", fontsize=10)
    plt.xlabel("Month", fontsize=10)

    caption = " "
    fig.text(0.5, 0.01, caption, ha="center")
    plt.tight_layout()
    plt.ylim(bottom=0)

    # Save the plot to file
    # filepath = '/tmp/graph.png'
    filepath = 'c:/temp/graph.png'
    plt.savefig(filepath)
    # open image and read as binary
    fp = open(filepath, "rb")
    image_bytes = fp.read()
    fp.close()
    os.remove(filepath)

    return image_bytes


# Send an email to the user containing usage information
def send_idir_email(idir_info, total_h_drive_count, total_gb):
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
        month_before_last_gb = month_before_last_sample["gb"]
        month_before_last_cost = month_before_last_sample["cost"]

    total_gb = float(total_gb)
    total_h_drive_count = float(total_h_drive_count)
    total_h_drive_cost = (total_gb - (total_h_drive_count*1.5)) * 2.7
    # round down to nearest thousand
    total_gb = int(math.floor(total_gb/1000)*1000)
    total_h_drive_cost = int(math.floor(total_h_drive_cost/1000)*1000)
    total_h_drive_count = int(math.floor(total_h_drive_count/1000)*1000)

    # build email content and metadata
    year = last_month_sample["sample_datetime"].year
    msg["Subject"] = f"Transitory: Your H: Drive Usage Report for {last_month_name} {year}"
    msg["From"] = "IITD.Optimize@gov.bc.ca"
    msg["To"] = recipient

    html_intro = f"""
    <html><head></head><body><p>
        Hi {name}!<br><br>

        IITD is providing you with personalized H: Drive Usage Reports to raise awareness and encourage you to proactively keep costs down.<br><br>

        <b>Why is My Data Usage Important?</b><br>
        There are over {total_h_drive_count:,} H: Drives, and lots of small actions add up to big savings.
        <ul>
        <li>Data storage on the H: Drive is expensive and billed at $2.70 per GB, per month.</li>
        <li>The NRM has over {total_gb:,}GB of data in H: Drives, billed at over ${total_h_drive_cost:,} per month.</li>
        """

    html_snapshot_taken = ""
    if month_before_last_sample is not None:
        difference = round(last_month_gb-month_before_last_gb, 2)
        difference_cost = round((last_month_cost-month_before_last_cost), 2)
        if difference == 0:
            html_snapshot_taken = html_snapshot_taken + """<li>There was no change to the size of your H: Drive last month.</li>"""
        elif difference > 0:
            html_snapshot_taken = html_snapshot_taken + f"""<li>Your H: Drive consumption <span style="color:#D8292F;">increased</span> by {difference}GB,
            costing an additional ${difference_cost} per month.</li>"""
        elif difference < 0:
            difference = abs(difference)
            difference_cost = abs(difference_cost)
            html_snapshot_taken = html_snapshot_taken + f"""<li>Your H: Drive consumption <span style="color:#2E8540;">decreased</span> by {difference}GB,
            saving ${difference_cost} per month.</li>"""
    html_snapshot_taken = html_snapshot_taken + """</ul>"""

    number_names = ["", "two ", "three ", "four ", "five ", "six ", "seven "]
    month_count = number_names[len(samples)-1]
    month_plural = ""
    if month_before_last_sample is not None:
        month_plural = "s"
    html_img = f"Below, you will find a graph highlighting your H: Drive usage for the past {month_count}month{month_plural}."
    html_img = html_img + """<br><img src="cid:image1" alt="Graph" style="width:250px;height:50px;">
    <p style="font-size: 10px">H: Drive usage information is provided mid-month from the Office of the Chief Information Officer (OCIO).</p>"""
    html_why_important = """
    <b>Did the cost of your H: Drive go up this month?</b><br>
    This happens from time to time. Here are 3 simple actions to help you reduce your storage expense "footprint":
    <ol>
        <li>Delete <a href="https://intranet.gov.bc.ca/assets/intranet/iit/pdfs-and-docs/transitoryrecords.pdf">transitory</a> data (time suggested: 5-10 mins)</li>
        <li><a href="https://intranet.gov.bc.ca/iit/products-services/technical-support/storage-tips-and-info#Emptyyourrecycling">Empty</a>
        your Recycle Bin (time suggested: 1 min)</li>
        <li>Move <a href="https://intranet.gov.bc.ca/iit/onedrive/what-not-to-move-onto-onedrive">appropriate</a> files to OneDrive (time suggested: 20 mins)</li>
    </ol>
    """
    html_footer = """
    More suggestions on how to reduce can be found on our
    <a href="https://intranet.gov.bc.ca/iit/products-services/technical-support/storage-tips-and-info">StorageTips and Information page</a>.<br>
    <br>
    We welcome your questions, comments, and ideas! Connect with us at IITD.Optimize@gov.bc.ca.<br>
    <br>
    Signed,<br>
    Your Friendly Neighbourhood Optimization Team<br>
    (Chris, Hannah, Heather, Joseph, Kristal, Kulbir, Lolanda, and Peter)<br>
    <br>
    <br>
    </p>
    <p style="font-size: 10px">If you do not wish to receive these monthly emails, please reply with the subject line "unsubscribe".</p>
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
    s.sendmail(msg["From"], recipient, msg.as_string())
    s.quit()

    # ensure we're following smtp server guidelines of max 30 emails/minute
    time.sleep(2)

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

    # Get NRM metrics
    nrm_metrics = get_h_drive_summary()
    total_h_drive_count = nrm_metrics["total_h_drive_count"]
    total_gb = nrm_metrics["total_gb"]

    for idir in data:
        # print the samples for development
        for sample in data[idir]["samples"]:
            gb = sample["gb"]
            sample_datetime = sample["sample_datetime"]
            month = sample["month"]
            LOGGER.debug(f"GB: {gb}, Datetime: {sample_datetime}, Month: {month}")
        # send email to user
        LOGGER.debug(idir)

        if constants.EMAIL_WHITELIST and data[idir]["mail"] is not None and data[idir]["mail"].lower() in constants.EMAIL_WHITELIST.split(','):
            send_idir_email(data[idir], total_h_drive_count, total_gb)


if __name__ == "__main__":
    main(sys.argv[1:])
    # time.sleep(300)
