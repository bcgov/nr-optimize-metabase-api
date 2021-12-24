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
import matplotlib.pyplot as plt
import numpy

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

    for result in all_results:
        idir = result[0]
        # Filter out all IDIRs that don't start with A and B for quick Dev.
        # if not (idir[0] == "A" or idir[0] == "B"):
        #     continue
        gb = result[1]
        sample_datetime = result[2]
        ministry = result[3]
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
                        "name": ad_info["givenName"],
                        "ministry": ministry
                    }
            else:
                data[idir]["samples"].append(get_sample(gb, sample_datetime))
    for idir in data:
        # sort the samples
        data[idir]["samples"].sort(
            key=lambda s: s["sample_datetime"]
        )
    # fakedata = get_fake_idir_info()
    # data = fakedata

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
        SELECT count(*) AS "COUNT", sum(datausage) AS "DATAUSAGE", ministry AS "MINISTRY" FROM hdriveusage WHERE (date_trunc('month',
         CAST(date AS timestamp)) BETWEEN date_trunc('month', CAST((CAST(now()
         AS timestamp) + (INTERVAL '-1 month')) AS timestamp)) AND
         date_trunc('month', CAST(now() AS timestamp)) AND idir <> 'Soft
         deleted Home Drives')
         GROUP BY MINISTRY;
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

    nrm_metrics = {
        "total_h_drive_count": 0,
        "total_gb": 0
    }
    for result in all_results:
        nrm_metrics["total_h_drive_count"] += result[0]
        nrm_metrics["total_gb"] += result[1]
        nrm_metrics[result[2]] = {
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
    axis_dates = []
    for idx, sample in enumerate(samples):
        axis_dates.append(sample["sample_datetime"].strftime("%Y-%m-%d"))

    # convert samples array into dictionary of arrays
    under_bars = {
        'gb': [],
        'datetime': [],
        'month': [],
        'cost': []
    }

    over_bars = {
        'gb': [],
        'datetime': [],
        'month': [],
        'cost': []
    }

    # 1.5GB x 2.7 is actuall 4.05, but rounding for ease of consumption
    threshold = 4.00
    for sample in samples:
        if sample['cost'] <= threshold:
            under_bars['gb'].append(sample['gb'])
            under_bars['datetime'].append(sample['sample_datetime'])
            under_bars['month'].append(sample['month'])
            under_bars['cost'].append(sample['cost'])

            over_bars['gb'].append(0)
            over_bars['datetime'].append(sample['sample_datetime'])
            over_bars['month'].append(sample['month'])
            over_bars['cost'].append(0)
        else:
            under_bars['gb'].append(1.5)
            under_bars['datetime'].append(sample['sample_datetime'])
            under_bars['month'].append(sample['month'])
            under_bars['cost'].append(4.05)

            over_bars['gb'].append(sample['gb'])
            over_bars['datetime'].append(sample['sample_datetime'])
            over_bars['month'].append(sample['month'])
            over_bars['cost'].append(sample['cost'])

    sns.barplot(
        x="month",
        y="cost",
        data=over_bars,
        color=color_over
    )
    g = sns.barplot(
        x="month",
        y="cost",
        data=under_bars,
        color=color_under
    )

    # add patterns to the bars
    # hatches = ['/', '//', '+', '-', 'x', '\\', '*', 'o', 'O', '.']
    # for i, bar in enumerate(g.patches):
    #     hatch = hatches[i]
    #    bar.set_hatch(hatch)

    g.axhline(threshold, label="$4.00 (1.5 GB)", color=color_goal, linewidth=6)
    plt.legend(bbox_to_anchor=(1.02, 1), loc=2, borderaxespad=0.)
    # Format y axis labels as dollar values
    ylabels = []
    for ytick in g.get_yticks():
        ylabels.append(f"${ytick:,.2f}")
    g.set_yticklabels(ylabels)

    plt.title(f"{idir}'s H: Drive Cost by Month", fontsize=14)

    plt.ylabel("H: Drive Cost", fontsize=13)
    plt.xlabel("", fontsize=10)

    caption = "1.5 GB of Shared\nFile and H: drive\nstorage is allocated\nfor each BCPS\nemployee."
    caption = caption + "\n\nKeeping your digital\nstorage use under\n1.5 GB helps prevent\nadditional costs\nfor your ministry."
    fig.text(0.8, 0.34, caption, ha="left")
    plt.tight_layout()
    plt.ylim(bottom=0)

    # plt.show()
    # Save the plot to file
    filepath = '/tmp/graph.png'
    # filepath = 'c:/temp/graph.png'
    plt.savefig(filepath)
    # open image and read as binary
    fp = open(filepath, "rb")
    image_bytes = fp.read()
    fp.close()
    os.remove(filepath)

    return image_bytes


def get_gold_star():
    filepath = 'gold-star.png'
    # filepath = 'send-usage-emails/gold-star.png'
    fp = open(filepath, "rb")
    image_bytes = fp.read()
    fp.close()
    return image_bytes


# Send an email to the user containing usage information
def send_idir_email(idir_info, total_h_drive_count, total_gb, ministry_name, biggest_drop, biggest_drops):
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
        month_before_last_name = month_before_last_sample["month"]

    total_gb = float(total_gb)
    total_h_drive_count = float(total_h_drive_count)
    total_h_drive_cost = (total_gb - (total_h_drive_count*1.5)) * 2.7
    # round down to nearest thousand
    total_gb = int(math.floor(total_gb/1000)*1000)
    total_h_drive_cost = int(math.floor(total_h_drive_cost/1000)*1000)
    total_h_drive_count = int(math.floor(total_h_drive_count/1000)*1000)
    biggest_drop_cost = biggest_drop * 2.7
    biggest_drops_cost = biggest_drops * 2.7

    # build email content and metadata
    year = last_month_sample["sample_datetime"].year
    msg["Subject"] = f"Transitory: Your H: Drive Usage Report for {last_month_name} {year}"
    msg["From"] = "IITD.Optimize@gov.bc.ca"
    msg["To"] = recipient

    html_intro = f"""
    <html><head></head><body><p>
        Hi {name},<br><br>

        This report from the <a href="https://intranet.gov.bc.ca/iit">Information, Innovation and Technology Division</a>
         is provided to help raise awareness of monthly storage costs associated with your personal home (H:) drive."""

    if last_month_gb < 1 and month_before_last_gb < 1:
        html_intro += """<br><br><img src="cid:image2" alt="Gold Star">&nbspCongratulations! You seem to be managing your storage well. <img src="cid:image2" alt="Gold Star">"""

    html_why_data_important = f"""<br><br><b>Why is knowing my data usage important?</b>
        <ul>
        <li>Storing data on your H: Drive is expensive, costing $2.70 per GB per month.</li>
        <li>There are over {total_h_drive_count:,} H: Drives in the Ministry of {ministry_name}.</li>
        <li>Your Ministry has over {total_gb:,}GB of data in H: Drives, costing more than ${total_h_drive_cost:,} per month.</li>
        </ul>
        """

    html_personal_metrics = f"""<b>What are my personal metrics?</b><br>
    Last month your H: Drive usage was {last_month_gb:,}GB, costing ${last_month_cost:,.2f}. This has """
    if month_before_last_sample is not None:
        difference = round(last_month_gb-month_before_last_gb, 2)
        difference_cost = round((last_month_cost-month_before_last_cost), 2)
        if difference == 0:
            html_personal_metrics = html_personal_metrics + f"""not changed since {month_before_last_name}."""
        elif difference > 0:
            html_personal_metrics = html_personal_metrics + f"""<span style="color:#D8292F;"><b>increased</b></span> by <b>{difference:,.3g}GB</b> since {month_before_last_name},
            costing an additional <b>${difference_cost:,.2f}</b> per month."""
        elif difference < 0:
            difference = abs(difference)
            difference_cost = abs(difference_cost)
            html_personal_metrics = html_personal_metrics + f"""<span style="color:#2E8540;"><b>decreased</b></span> by <b>{difference:,.2g}GB</b> since {month_before_last_name},
            saving <b>${difference_cost:,.2f}</b> per month."""

    number_names = ["", "two ", "three ", "four ", "five ", "six ", "seven "]
    month_count = number_names[len(samples)-1]
    month_plural = ""
    if month_before_last_sample is not None:
        month_plural = "s"
    html_img = f"<br>Below, you will find a graph highlighting your H: Drive cost for the past {month_count}month{month_plural}:"
    html_img = html_img + """<br><img src="cid:image1" alt="Graph" style="width:250px;height:50px;">"""
    html_why_important = f"""
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
    <a href="https://intranet.gov.bc.ca/iit/products-services/technical-support/storage-tips-and-info">Storage Tips and Information page</a>.<br><br>
    <b>Storage Saving Kudos:</b>
    <ul>
        <li>Last month the largest H: Drive savings from a single user was <b>{biggest_drop:,.3g}GB</b> saving <b>${biggest_drop_cost:,.2f}</b> per month!</li>
        <li>Last month five users saved a combined total of <b>${biggest_drops_cost:,.2f}</b> per month!</li>
    </ul>
    """
    html_footer = """
    This email is transitory and can be deleted when no longer needed. Thank you for taking the time to manage your digital storage!<br>
    <br>
    Questions? Comments? Ideas? Connect with the Optimization Team at <a href="mailto:IITD.Optimize@gov.bc.ca">IITD.Optimize@gov.bc.ca</a>.<br>
    <br>
    </p>
    <p style="font-size: 10px">H: Drive usage information is captured mid-month from the Office of the Chief Information Officer (OCIO).
     If you do not wish to receive these monthly emails, please reply with the subject line "unsubscribe".
     Users can subscribe or re-subscribe by emailing IITD.Optimize@gov.bc.ca with the subject line "PSR subscribe" and including their email address.</p>
    </body>
    </html>
    """
    html = (html_intro + html_why_data_important + html_personal_metrics + html_img + html_why_important + html_footer)
    msg.attach(MIMEText(html, "html"))

    msgImage = MIMEImage(get_graph_bytes(idir_info))
    msgImage.add_header("Content-ID", "<image1>")
    msg.attach(msgImage)

    msgImage = MIMEImage(get_gold_star())
    msgImage.add_header("Content-ID", "<image2>")
    msg.attach(msgImage)

    # add header which suppresses out of office requests
    msg.add_header("X-Auto-Response-Suppress", "OOF, DR, RN, NRN")

    # send email
    s = smtplib.SMTP(constants.SMTP_SERVER)
    s.sendmail(msg["From"], recipient, msg.as_string())
    s.quit()

    # ensure we're following smtp server guidelines of max 30 emails/minute
    time.sleep(2)

    # log send complete
    LOGGER.info(f"Email sent to {recipient}.")


def get_fake_idir_info():
    idir_info = {
        'idir': 'PPLATTEN',
        'mail': 'Peter.Platten@gov.bc.ca',
        'name': 'Peter',
        'ministry': 'ENV',
        'samples': [
            get_sample(0.0, datetime(2021, 6, 1, 0, 0)),
            get_sample(0, datetime(2021, 7, 1, 0, 0)),
            get_sample(0, datetime(2021, 8, 1, 0, 0)),
            get_sample(0, datetime(2021, 9, 1, 0, 0)),
            get_sample(0, datetime(2021, 10, 1, 0, 0)),
            get_sample(0, datetime(2021, 11, 1, 0, 0))
        ]
    }

    return idir_info


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


def main(argv):

    data = get_hdrive_data()
    if data is None:
        return

    # Get NRM metrics
    nrm_metrics = get_h_drive_summary()
    if nrm_metrics is None:
        return

    # Assign Ministry Names
    long_ministry_names = {
        "AFF": "Agriculture, Food and Fisheries",
        "EMLI": "Energy, Mines and Low Carbon Innovation",
        "ENV": "Environment",
        "FLNR": "Forests, Lands, Natural Resource Operations & Rural Development",
        "FPRO": "Forest Protection Branch",
        "IRR": "Indigenous Relations & Reconciliation"
    }

    # Get Biggest Drop of the month
    biggest_drop = 0
    biggest_drops_list = []
    for idir in data:
        samples = data[idir]["samples"]
        if len(samples) >= 2:
            last_month = samples[len(samples)-1]['gb']
            month_before_last = samples[len(samples)-2]['gb']
            drop = month_before_last - last_month
            if drop > biggest_drop:
                biggest_drop = drop
            if len(biggest_drops_list) < 5:
                biggest_drops_list.append(drop)
                biggest_drops_list.sort()
            elif biggest_drops_list[0] < drop:
                biggest_drops_list[0] = drop
                biggest_drops_list.sort()

    biggest_drops = sum(biggest_drops_list)
    sendlist = []
    if constants.EMAIL_SENDLIST:
        sendlist = constants.EMAIL_SENDLIST

    for idir in data:
        idir_info = data[idir]
        if idir_info["mail"] is not None:
            if len(sendlist) and idir_info["mail"].lower() in sendlist:
                ministry_acronym = idir_info["ministry"]
                h_drive_count = nrm_metrics[ministry_acronym]["h_drive_count"]
                ministry_gb = nrm_metrics[ministry_acronym]["gb"]
                ministry_name = long_ministry_names[ministry_acronym]
                send_idir_email(data[idir], h_drive_count, ministry_gb, ministry_name, biggest_drop, biggest_drops)


# Handle MS Outlook email format
def convert_email_addresses(long_format_addresses):
    # pattern matches all email addresses between < > with letters, numbers, and the following characters: .-_@
    pattern = re.compile(r'(?<=\<)[a-zA-Z\.\-\_\@\0-9]*(?=\>)')
    short_format_addresses = pattern.findall(long_format_addresses)
    return ",".join(numpy.array(short_format_addresses))


# Handle formatting, ensure uniqueness, and omit emails
def refine_sendlist():
    if constants.EMAIL_SENDLIST.endswith(">"):
        constants.EMAIL_SENDLIST = convert_email_addresses(constants.EMAIL_SENDLIST)
    if constants.EMAIL_OMITLIST.endswith(">"):
        constants.EMAIL_OMITLIST = convert_email_addresses(constants.EMAIL_OMITLIST)
    temp_dict = {}
    if constants.EMAIL_SENDLIST:
        for email in constants.EMAIL_SENDLIST.split(","):
            temp_dict[email.lower()] = True
        if constants.EMAIL_OMITLIST:
            for email in constants.EMAIL_OMITLIST.split(","):
                if email in temp_dict:
                    del temp_dict[email.lower()]
    constants.EMAIL_SENDLIST = []
    for email in temp_dict:
        constants.EMAIL_SENDLIST.append(email)


if __name__ == "__main__":

    # test_email("peter.platten@gov.bc.ca", "test email from Peter!")
    refine_sendlist()

    # get_graph_bytes(get_fake_idir_info())

    main(sys.argv[1:])
    time.sleep(300)
