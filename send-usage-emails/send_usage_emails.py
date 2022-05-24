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
#   2.) A .env file or environment variables set with values. See the constants.py for the required values.
# -------------------------------------------------------------------------------


import calendar
import constants
import multiprocessing as mp
import ldap_helper as ldap
import math
import os
import psycopg2
import re
import seaborn as sns
import socket
import sys
import smtplib
import time
import matplotlib.ticker as mticker
import matplotlib.pyplot as plt

from datetime import datetime
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from log_helper import LOGGER


# Get a simple formatted "sample" object
def get_sample(gb, sample_datetime: datetime):
    gb = float(gb)
    # METHOD 1: Calculate and Format $ cost by GB, encouraging users to have "up to" 1.5gb
    # cost = round((gb - 1.5) * 2.7, 2)
    # if cost < 0:
    #    cost = 0
    # METHOD 2: Calculate and Format $ cost by GB, with 1.5gb discount applied at ministry level
    cost = round(gb * 2.7, 2)

    return {
        "gb": gb,
        "sample_datetime": sample_datetime,
        "month": calendar.month_name[sample_datetime.month],
        "cost": cost
    }


# Send an email to the admin with a message
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

        LOGGER.debug('H Drive data from the last six months, but only for idirs which have data last month:')
        sql_expression = """
        SELECT idir, datausage, date, ministry FROM hdriveusage WHERE (date_trunc('month',
         CAST(date AS timestamp)) BETWEEN date_trunc('month', CAST((CAST(now()
         AS timestamp) + (INTERVAL '-6 month')) AS timestamp)) AND
         date_trunc('month', CAST(now() AS timestamp))) AND IDIR IN (

            SELECT idir FROM hdriveusage WHERE (date_trunc('month',
            CAST(date AS timestamp)) BETWEEN date_trunc('month', CAST((CAST(now()
            AS timestamp) + (INTERVAL '-1 month')) AS timestamp)) AND
            date_trunc('month', CAST(now() AS timestamp)) AND idir <> 'Soft
            deleted Home Drives'))
          ORDER BY idir ASC;
        """
        cur.execute(sql_expression)
        all_results = cur.fetchall()
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

    try:
        # Attempt to sign into AD using LDAP credentials
        ldap_util = ldap.LDAPUtil(constants.LDAP_USER, constants.LDAP_PASSWORD)
    except (Exception) as error:
        LOGGER.info(error)
        message_detail = "The send_usage_emails script failed to connect or log in to LDAP. " \
            + "<br />Username: " + constants.LDAP_USER \
            + "<br />Message Detail: " + str(error)
        send_admin_email(message_detail)
        quit()

    data = {}
    attribute_error_idirs = []
    other_error_idirs = []
    conn = ldap_util.getLdapConnection()
    # For each H: Drive row, Add new user to "data" dictionary if not there, and add a data sample.
    for result in all_results:
        idir = result[0]
        # Filter out all IDIRs that don't start with C and P for quicker Dev iterations.
        # if not (idir[0] == "S"):
        #     continue
        gb = result[1]
        sample_datetime = result[2]
        ministry = result[3]
        if ministry == "FPRO" or ministry == "BCWS":
            ministry = "FLNR"
        if idir not in attribute_error_idirs and idir not in other_error_idirs:
            if idir not in data:
                # User is not in the "data" dictionary yet, create user entry while adding first sample.
                try:
                    # Connect to AD to get user info
                    ad_info = ldap_util.getADInfo(idir, conn)
                except (Exception, AttributeError) as error:
                    if AttributeError:
                        print(f"Unable to find {idir} due to error {error}")
                        attribute_error_idirs.append(idir)
                    else:
                        print(f"Unable to find {idir} due to error {error}")
                        other_error_idirs.append(idir)
                    continue

                if ad_info is None or ad_info["mail"] is None or ad_info["givenName"] is None:
                    other_error_idirs.append(idir)
                else:
                    # Create user entry, add first sample
                    data[idir] = {
                        "idir": idir,
                        "samples": [
                            get_sample(gb, sample_datetime)
                        ],
                        "mail": ad_info["mail"],
                        "name": ad_info["givenName"],
                        "ministry": ministry
                    }
            else:
                # Add sample to existing user data, handling edge case:
                # Users who transfer ministry get two records in a single month, so flatten those.
                duplicate_found = False
                new_sample = get_sample(gb, sample_datetime)
                for sample in data[idir]["samples"]:
                    if sample["sample_datetime"] == new_sample["sample_datetime"]:
                        sample['gb'] += new_sample['gb']
                        sample['cost'] += new_sample['cost']
                        duplicate_found = True
                if not duplicate_found:
                    data[idir]["samples"].append(new_sample)

    # Sort the samples
    for idir in data:
        data[idir]["samples"].sort(
            key=lambda s: s["sample_datetime"]
        )

    # If errors existed, email them to the admin.
    # (There will always be errors, due to service accounts or employees who have left during the month)
    if len(attribute_error_idirs) > 0 or len(other_error_idirs) > 0:
        message_detail = "The send_usage_emails script failed to find all IDIRs. " \
            + "<br /><br />IDIRs not found due to attribute error: " + ",".join(attribute_error_idirs) \
            + "<br /><br />IDIRs not found due to other issue: " + ",".join(other_error_idirs)
        LOGGER.info(message_detail)
        send_admin_email(message_detail)
    return data


# Query metabase database to simply get ministry-wide metrics
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

        LOGGER.debug('Get summarized H: Drive counts by ministry from the last month:')
        sql_expression = """
        SELECT count(*) AS "COUNT", sum(datausage) AS "DATAUSAGE", ministry AS "MINISTRY" FROM hdriveusage WHERE (date_trunc('month',
         CAST(date AS timestamp)) BETWEEN date_trunc('month', CAST((CAST(now()
         AS timestamp) + (INTERVAL '-1 month')) AS timestamp)) AND
         date_trunc('month', CAST(now() AS timestamp)) AND idir <> 'Soft
         deleted Home Drives')
         GROUP BY MINISTRY;
        """
        cur.execute(sql_expression)
        all_results = cur.fetchall()
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

    nrm_metrics = {
        "total_h_drive_count": 0,
        "total_gb": 0
    }

    # For each ministry record, aggregate data in dictionary
    for result in all_results:
        nrm_metrics["total_h_drive_count"] += result[0]
        nrm_metrics["total_gb"] += result[1]
        ministry = result[2]
        nrm_metrics[ministry] = {
            "h_drive_count": result[0],
            "gb": result[1]
        }
    return nrm_metrics


# Generate an graph image's bytes using idir info
def get_graph_bytes(idir_info):
    samples = idir_info["samples"]
    idir = idir_info["name"]

    # Select plot theme, with seaborn
    sns.set(rc={'figure.figsize': (9, 4.5)})
    sns.set_theme(style="whitegrid")
    fig = plt.figure()

    # Set custom colour palette and build bar chart "#2E8540"  # green
    color_under = "#003366"  # blue
    color_over = "#e3a82b"  # yellow
    color_goal = "#D8292F"  # red

    # Add sample dates to graph axis
    axis_dates = []
    for idx, sample in enumerate(samples):
        axis_dates.append(sample["sample_datetime"].strftime("%Y-%m-%d"))

    # Convert samples array into dictionary of arrays
    # To have the graph change color below and above the 1.5GB bar, add them as different datasets
    under_bar = {
        'gb': [],
        'datetime': [],
        'month': [],
        'cost': []
    }

    over_bar = {
        'gb': [],
        'datetime': [],
        'month': [],
        'cost': []
    }

    # Bar/threshold of 1.5GB x 2.7 is actually 4.05, but rounding for ease of consumption
    threshold = 4.00
    # For each month sample, add to data dictionaries
    for sample in samples:
        if sample['cost'] <= threshold:
            # Users month was <= to the bar, so add data under bar, and empty data behind it
            under_bar['gb'].append(sample['gb'])
            under_bar['datetime'].append(sample['sample_datetime'])
            under_bar['month'].append(sample['month'])
            under_bar['cost'].append(sample['cost'])

            over_bar['gb'].append(0)
            over_bar['datetime'].append(sample['sample_datetime'])
            over_bar['month'].append(sample['month'])
            over_bar['cost'].append(0)
        else:
            # Users month was > the bar, so add maximum data under bar, and actual data behind it that looks "over" the bar
            under_bar['gb'].append(1.5)
            under_bar['datetime'].append(sample['sample_datetime'])
            under_bar['month'].append(sample['month'])
            under_bar['cost'].append(4.05)

            over_bar['gb'].append(sample['gb'])
            over_bar['datetime'].append(sample['sample_datetime'])
            over_bar['month'].append(sample['month'])
            over_bar['cost'].append(sample['cost'])

    # Give bars color and plot them
    sns.barplot(
        x="month",
        y="cost",
        data=over_bar,
        color=color_over
    )
    g = sns.barplot(
        x="month",
        y="cost",
        data=under_bar,
        color=color_under
    )

    # Add threshold bar
    g.axhline(threshold, label="$4.00 (1.5 GB)", color=color_goal, linewidth=6)

    # Add legend
    plt.legend(bbox_to_anchor=(1.02, 1), loc=2, borderaxespad=0.)

    # Format y axis labels as dollar values
    # ylabels = []
    # for ytick in g.get_yticks():
    #     ylabels.append(f"${ytick:,.2f}")
    # g.set_yticklabels(ylabels)

    label_format = '{:,.2f}'
    ticks_loc = g.get_yticks().tolist()
    g.yaxis.set_major_locator(mticker.FixedLocator(ticks_loc))
    g.set_yticklabels([label_format.format(x) for x in ticks_loc])

    # Add various text components
    plt.title(f"{idir}'s H: Drive Cost by Month", fontsize=14)
    plt.ylabel("H: Drive Cost", fontsize=13)
    plt.xlabel("", fontsize=10)
    caption = "1.5 GB of Shared\nFile and H: drive\nstorage is allocated\nfor each BCPS\nemployee."
    caption = caption + "\n\nKeeping your digital\nstorage use under\n1.5 GB helps prevent\nadditional costs\nfor your ministry."
    fig.text(0.8, 0.34, caption, ha="left")
    plt.tight_layout()
    plt.ylim(bottom=0)

    # Show the graph in a window on a dev computer
    # plt.show()

    # Save the plot to file
    plt.savefig(constants.GRAPH_FILE_PATH)

    plt.close()

    return


# Get bytes from an image file
def get_gold_star():
    fp = open(constants.GOLD_STAR_FILE_PATH, "rb")
    image_bytes = fp.read()
    fp.close()
    return image_bytes


# Send an email to the user containing usage information
def send_idir_email(idir_info, h_drive_count, total_gb, ministry_name, biggest_drop, biggest_drops):
    # Variable Definitions:
    # idir_info         Dictionary of info for a user
    # h_drive_count     H: drives for the users ministry
    # total_gb          Total gb for the users ministry
    # biggest_drop      Biggest single user reduction last month
    # biggest_drops     Sum of five biggest reductions last month
    # last_month        The most recent reporting month
    # month_before_last The reporting month before last_month

    samples = idir_info["samples"]
    name = idir_info["name"]
    recipient = idir_info["mail"]
    msg = MIMEMultipart("related")

    # Copy out values to variables for use in fstrings
    last_month_sample = samples[len(samples)-1]
    last_month_name = last_month_sample["month"]  # i.e. January
    last_month_gb = last_month_sample["gb"]
    last_month_cost = last_month_sample["cost"]
    year = last_month_sample["sample_datetime"].year
    month_before_last_sample = None
    if len(samples) > 1:
        month_before_last_sample = samples[len(samples)-2]
        month_before_last_gb = month_before_last_sample["gb"]
        month_before_last_cost = month_before_last_sample["cost"]
        month_before_last_name = month_before_last_sample["month"]

    total_gb = float(total_gb)
    h_drive_count = float(h_drive_count)
    # Get the cost of ministry H: Drives and biggest drops
    total_h_drive_cost = (total_gb - (h_drive_count*1.5)) * 2.7
    biggest_drop_cost = biggest_drop * 2.7
    biggest_drops_cost = biggest_drops * 2.7

    # Round down to nearest thousand for legibility
    total_gb = int(math.floor(total_gb/10)*10)
    total_h_drive_cost = int(math.floor(total_h_drive_cost/10)*10)
    h_drive_count = int(math.floor(h_drive_count/10)*10)

    # Build email content and metadata
    msg["Subject"] = f"Transitory: Your H: Drive Usage Report for {last_month_name} {year}"
    msg["From"] = "IITD.Optimize@gov.bc.ca"
    msg["To"] = recipient

    # Greet the user and provide introduction
    html_intro = f"""
    <html><head></head><body><p>
        Hi {name},<br><br>

        This report from the <a href="https://intranet.gov.bc.ca/iit">Information, Innovation and Technology Division</a>
         is provided to help raise awareness of monthly storage costs associated with your personal home (H:) drive."""

    # Reward the user with a gold star if data looks well managed
    if last_month_gb < 1 and month_before_last_sample is not None:
        if month_before_last_gb < 1:
            html_intro += """<br><br><img src="cid:image2" alt="Gold Star">&nbspCongratulations!
                 You've kept your H: Drive under 1GB for at least two months straight, and appear to be managing your storage well.
                 Keep up the great work! <img src="cid:image2" alt="Gold Star">"""

    # Remind user why storage costs are important as a ministry
    html_why_data_important = f"""<br><br><b>Why is knowing my data usage important?</b>
        <ul>
        <li>Storing data on your H: Drive is expensive, costing $2.70 per GB per month.</li>
        <li>There are over {h_drive_count:,} H: Drives in the Ministry of {ministry_name}.</li>
        <li>Your Ministry has over {total_gb:,}GB of data in H: Drives, costing more than ${total_h_drive_cost:,} per month.</li>
        </ul>
        """

    # Inform user of personal metrics
    html_personal_metrics = "<b>What are my personal metrics?</b><br><ul>"

    if month_before_last_sample is None:
        # Only one month of data
        html_personal_metrics += f"<li>In {last_month_name} your H: Drive data usage billed to your ministry was {last_month_gb:,}GB, costing ${last_month_cost:,.2f}.</li>"
    else:
        difference = round(last_month_gb-month_before_last_gb, 2)
        difference_cost = round((last_month_cost-month_before_last_cost), 2)
        if difference == 0:
            html_personal_metrics += f"""<li>In {month_before_last_name} and {last_month_name} your H: Drive data usage billed to your ministry was {last_month_gb:,}GB,
             costing ${last_month_cost:,.2f}.</li>"""
        else:
            html_personal_metrics += f"""<li>In {month_before_last_name} your H: Drive data usage billed to your ministry was {month_before_last_gb:,}GB,
             costing ${month_before_last_cost:,.2f}.</li>"""
            html_personal_metrics += f"""<li>In {last_month_name} your H: Drive data usage billed to your ministry was {last_month_gb:,}GB,
             costing ${last_month_cost:,.2f}.</li>"""
            abs_difference = abs(difference)
            abs_difference_cost = abs(difference_cost)
            if difference > 0:
                # Cost went up
                html_personal_metrics += f"""<li>Between {month_before_last_name} and {last_month_name} your consumption
                <span style="color:#D8292F;"><b>increased</b></span> by <b>{abs_difference:,.3g}GB</b>,
                costing an additional <b>${abs_difference_cost:,.2f}</b> per month.</li>"""
            else:
                # Cost went down
                html_personal_metrics += f"""<li>Between {month_before_last_name} and {last_month_name} your consumption
                <span style="color:#2E8540;"><b>decreased</b></span> by <b>{abs_difference:,.3g}GB</b>, saving <b>${abs_difference_cost:,.2f}</b> per month.</li>"""

    number_names = ["", "two ", "three ", "four ", "five ", "six ", "seven ", " eight"]
    month_count = number_names[len(samples)-1]
    month_plural = ""
    if month_before_last_sample is not None:
        month_plural = "s"
    html_img = f"</ul>Below, you will find a graph highlighting your H: Drive cost for the past {month_count}month{month_plural}:<br>"
    html_img = html_img + """<br><img src="cid:image1" alt="Graph" style="width:250px;height:50px;">"""

    # Provide solutions to the user to help with H: Drive faqs/issues
    html_why_important = """
    <br><br><b>Did the cost of your H: Drive go up this month?</b><br>
    This happens from time to time. Here are three simple actions to help you reduce your storage expense "footprint":
    <ol>
        <li>Move <a href="https://intranet.gov.bc.ca/iit/onedrive/what-not-to-move-onto-onedrive">appropriate</a>
         files to <a href="https://intranet.gov.bc.ca/iit/onedrive">OneDrive</a> (time suggested: 20 mins)</li>
        <li>Delete <a href="https://intranet.gov.bc.ca/assets/intranet/iit/pdfs-and-docs/transitoryrecords.pdf">transitory</a> data (time suggested: 5-10 mins)</li>
        <li><a href="https://intranet.gov.bc.ca/iit/products-services/technical-support/storage-tips-and-info#Emptyyourrecycling">Empty</a>
        your Recycle Bin (time suggested: 1 min)</li>
    </ol>
    More suggestions on how to reduce can be found on our
    <a href="https://intranet.gov.bc.ca/iit/products-services/technical-support/storage-tips-and-info">Storage Tips and Information page</a>."""

    # Share the successes of peers
    html_kudos = f"""
    <br><br><b>Storage Saving Kudos:</b>
    <ul>
        <li>Last month the largest H: Drive savings from a single NRM user was <b>{biggest_drop:,.3g}GB</b> saving <b>${biggest_drop_cost:,.2f}</b> per month!</li>
        <li>Last month five NRM users saved a combined total of <b>${biggest_drops_cost:,.2f}</b> per month!</li>
    </ul>
    """

    # Email sign-off
    html_footer = """
    This email is transitory and can be deleted when no longer needed. Thank you for taking the time to manage your digital storage!<br>
    <br>
    </p>
    <p style="font-size: 10px">H: Drive usage information is captured mid-month from the Office of the Chief Information Officer (OCIO).
     If you do not wish to receive these monthly emails, please reply with the subject line "unsubscribe".
     Users can subscribe or re-subscribe by emailing IITD.Optimize@gov.bc.ca with the subject line "PSR subscribe" and including their email address.</p>
    </body>
    </html>
    """

    # Merge html parts and attach to email
    html = (html_intro + html_why_data_important + html_personal_metrics + html_img + html_why_important + html_kudos + html_footer)
    msg.attach(MIMEText(html, "html"))

    # Get and attach images to email
    proc = mp.Process(target=get_graph_bytes, args=(idir_info,))
    proc.daemon = True
    proc.start()
    proc.join()
    # open image and read as binary data, then close and delete the file
    fp = open(constants.GRAPH_FILE_PATH, "rb")
    image_bytes = fp.read()
    fp.close()
    os.remove(constants.GRAPH_FILE_PATH)

    msgImage = MIMEImage(image_bytes)
    msgImage.add_header("Content-ID", "<image1>")
    msg.attach(msgImage)

    msgImage = MIMEImage(get_gold_star())
    msgImage.add_header("Content-ID", "<image2>")
    msg.attach(msgImage)

    # Add header which suppresses out of office requests
    msg.add_header("X-Auto-Response-Suppress", "OOF, DR, RN, NRN")

    # Send email to recipient
    s = smtplib.SMTP(constants.SMTP_SERVER)
    s.sendmail(msg["From"], recipient, msg.as_string())
    s.quit()

    # Following smtp server guidelines of max 30 emails/minute
    # time.sleep(2)

    # log send complete
    LOGGER.info(f"Email sent to {recipient}.")


# Create fake idir info item for development/testing purposes
def get_fake_idir_info():
    idir_info = {
        'idir': 'PPLATTEN',
        'mail': 'Peter.Platten@gov.bc.ca',
        'name': 'NRM Staff Member',
        'ministry': 'ENV',
        'samples': [
            get_sample(0.74, datetime(2021, 6, 1, 0, 0)),
            get_sample(1.11, datetime(2021, 7, 1, 0, 0)),
            get_sample(1.75, datetime(2021, 8, 1, 0, 0)),
            get_sample(1.25, datetime(2021, 9, 1, 0, 0)),
            get_sample(0.7, datetime(2021, 10, 1, 0, 0))
        ]
    }

    return {'PPLATTEN': idir_info}


# A quickly edited email template to test while developing without needing to gather data
def test_email(recipient, subject):
    msg = MIMEMultipart("related")
    msg["Subject"] = subject
    msg["From"] = "peter.platten@gov.bc.ca"
    msg["To"] = recipient
    html = """<img src="cid:image2" alt="Gold Star">&nbspCongratulations! You seem to be managing your storage well.
         If you feel you do not need this email consider unsubscribing. <img src="cid:image2" alt="Gold Star">"""
    msg.attach(MIMEText(html, "html"))
    s = smtplib.SMTP(constants.SMTP_SERVER)
    msg.add_header("X-Auto-Response-Suppress", "OOF, DR, RN, NRN")
    msgImage = MIMEImage(get_gold_star())
    msgImage.add_header("Content-ID", "<image2>")
    msg.attach(msgImage)
    s.sendmail(msg["From"], recipient, msg.as_string())
    s.quit()


# Handle address formatting, ensure uniqueness, and filter out addresses using omitlist
def refine_sendlist():

    # pattern matches all email addresses between < > with letters, numbers, and the following characters: .-_@
    pattern = re.compile(r'(?<=\<)[a-zA-Z\.\-\_\@\0-9]*(?=\>)')

    email_send_list = []
    idir_send_list = []
    if constants.EMAIL_SENDLIST and constants.EMAIL_SENDLIST != "None":
        for recipient in constants.EMAIL_SENDLIST.split(";"):
            if recipient.endswith(">"):
                # Convert from MS Outlook email format
                recipient = pattern.findall(recipient)[0]
                email_send_list.append(recipient.lower())
            elif recipient.find("@") == -1:
                # Entry isn't an email address, assume IDIR
                idir_send_list.append(recipient.lower())
            else:
                email_send_list.append(recipient.lower())
        return email_send_list, idir_send_list

    else:
        # sendlist is empty
        return [], []


def main(argv):
    emails_sent_to = []
    try:

        # Query db for h drive data dictionary by idir
        data = get_hdrive_data()
        if data is None:
            return

        # Query db to simply get ministry-wide metrics
        nrm_metrics = get_h_drive_summary()
        if nrm_metrics is None:
            return

        # Assign Ministry Names
        long_ministry_names = {
            "AFF": "Agriculture, Food and Fisheries",
            "EMLI": "Energy, Mines and Low Carbon Innovation",
            "ENV": "Environment",
            "FLNR": "Forests, Lands, Natural Resource Operations & Rural Development",
            "LWRS": "Land, Water and Resource Stewardship",
            "IRR": "Indigenous Relations & Reconciliation"
        }

        # Get Biggest Drop (storage reduction) of the month
        biggest_drop = 0
        biggest_drops_list = []
        for idir in data:
            samples = data[idir]["samples"]
            if len(samples) >= 2:
                last_month_gb = samples[len(samples)-1]['gb']
                month_before_last_gb = samples[len(samples)-2]['gb']
                drop = month_before_last_gb - last_month_gb
                # Get biggest drop
                if drop > biggest_drop:
                    biggest_drop = drop
                # Get biggest 5 drops
                if len(biggest_drops_list) < 5:
                    biggest_drops_list.append(drop)
                    biggest_drops_list.sort()
                elif biggest_drops_list[0] < drop:
                    biggest_drops_list[0] = drop
                    biggest_drops_list.sort()

        # Calculate the sum of the 5 biggest drops
        biggest_drops = sum(biggest_drops_list)

        # Split input idirs and email addresses, and handle address formatting
        email_send_list, idir_send_list = refine_sendlist()

        # Filter out non-emails, and if sendlist then also users not on the sendlist
        filtered_data = {}
        for idir in data:
            idir_info = data[idir]
            email = idir_info["mail"]
            if email is not None:
                if constants.EMAIL_SENDLIST and constants.EMAIL_SENDLIST != "None":
                    if idir.lower() in idir_send_list or email.lower() in email_send_list:
                        filtered_data[idir] = idir_info
                else:
                    filtered_data[idir] = idir_info
        data = filtered_data

        # data = get_fake_idir_info()

        # Send email for each user
        omit_list = constants.EMAIL_OMITLIST.split(",")
        for idir in data:
            idir_info = data[idir]
            email = idir_info["mail"]
            if email.lower() not in omit_list:
                ministry_acronym = idir_info["ministry"]
                h_drive_count = nrm_metrics[ministry_acronym]["h_drive_count"]
                ministry_gb = nrm_metrics[ministry_acronym]["gb"]
                if ministry_acronym not in long_ministry_names:
                    send_admin_email(f"New Ministry for user {idir} named {ministry_acronym}")
                else:
                    ministry_name = long_ministry_names[ministry_acronym]
                    send_idir_email(idir_info, h_drive_count, ministry_gb, ministry_name, biggest_drop, biggest_drops)

                    # Track successful send
                    emails_sent_to.append(idir_info["mail"])

    except (Exception, psycopg2.DatabaseError) as error:
        LOGGER.info(error)
        message_detail = "The send_usage_emails script encountered an error sending emails to users. " \
            + "<br />Message Detail: " + str(error)
        send_admin_email(message_detail)
    finally:
        # Report successful sends for tracking purposes, even if the script as a whole had an exception.
        message_detail = "The send_usage_emails script sent emails to the following users: " \
            + "<br />" + ",".join(emails_sent_to)
        LOGGER.info(message_detail)
        send_admin_email(message_detail)


if __name__ == "__main__":
    main(sys.argv[1:])

    # Give developers time to look at OCP pod terminal/details after a failure/success before terminating.
    LOGGER.info("Script Complete, pausing for 5 minutes...")
    time.sleep(300)
