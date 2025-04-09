# -------------------------------------------------------------------------------
# Name:        send_usage_emails.py
# Purpose:     the purpose of the script is to email a list of users a bar chart of their H drive usage over the past 2 reporting periods:
#                    1.) Connect to the metabase postgres database, querying for all H drives
#                    2.) Get emails and names from active directory
#                    3.) Create a bar chart and send each user their html format report by email
#
# Author:      HHAY, JMONTEBE, PPLATTEN, KMWILKIN
#
# Created:     2021
# Copyright:   (c) Optimization Team 2025
# Licence:     mine
#
# usage: send_usage_emails.py
# Requires:
#   1.) Postgres database to be "localhost". On Dev PCs this is done using port binding with open_postgres_port_dev.bat
#   2.) A .env file or environment variables set with values. See the constants.py for the required values.
# -------------------------------------------------------------------------------


import multiprocessing as mp
import calendar
import math
import os
import re
import socket
import sys
import smtplib
import time
from datetime import datetime, timedelta
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import ldap_helper_v2 as ldap
import constants
import matplotlib.ticker as mticker
import matplotlib.pyplot as plt
import seaborn as sns
from log_helper import LOGGER
import psycopg2


# Get a simple formatted "sample" object
def get_sample(gb, sample_datetime: datetime, ministry):
    gb = float(gb)
    # METHOD 1: Calculate and Format $ cost by GB, encouraging users to have "up to" 1.5gb
    # cost = round((gb - 1.5) * 2.7, 2)
    # if cost < 0:
    #    cost = 0
    # METHOD 2: Calculate and Format $ cost by GB, with 1.5gb discount applied at ministry level
    cost = round(
        (gb - 1.5) * 2.7, 2
    )  # cost updated to account for the first 1.5 GB being $0 charge, anything after that is $2.70 per GB

    return {
        "gb": gb,
        "sample_datetime": sample_datetime,
        "month": calendar.month_name[sample_datetime.month],
        "cost": cost,
        "ministry": ministry,
    }


# Send an email to the admin with a message
def send_admin_email(message_detail):
    msg = MIMEMultipart("related")
    msg["Subject"] = "Script Report"
    if constants.DEBUG_EMAIL == "":
        msg["From"] = "NRIDS.Optimize@gov.bc.ca"
        msg["To"] = "NRIDS.Optimize@gov.bc.ca"
    else:
        msg["To"] = constants.DEBUG_EMAIL
        msg["From"] = constants.DEBUG_EMAIL

    dir_path = os.path.dirname(os.path.realpath(__file__))
    host_name = socket.gethostname()
    html = (
        "<html><head></head><body><p>"
        + "A scheduled script send_usage_emails.py has sent an automated report email."
        + "<br />Server: "
        + str(host_name)
        + "<br />File Path: "
        + dir_path
        + "<br />"
        + str(message_detail)
        + "</p></body></html>"
    )
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
            # port="5431",
            database="metabase",
            user=constants.POSTGRES_USER,
            password=constants.POSTGRES_PASSWORD,
        )
        # create a cursor
        cur = conn.cursor()

        LOGGER.debug(
            "H Drive data from the last three months, but only for idirs which have data last month:"
        )  # update from six to three months
        sql_expression = """
        SELECT idir, datausage, date, ministry FROM hdriveusage WHERE (date_trunc('month',
         CAST(date AS timestamp)) BETWEEN date_trunc('month', CAST((CAST(now()
         AS timestamp) + (INTERVAL '-3 month')) AS timestamp)) AND
         date_trunc('month', CAST(now() AS timestamp))) AND IDIR IN (

            SELECT idir FROM hdriveusage WHERE (date_trunc('month',
            CAST(date AS timestamp)) BETWEEN date_trunc('month', CAST((CAST(now()
            AS timestamp) + (INTERVAL '-1 month')) AS timestamp)) AND
            date_trunc('month', CAST(now() AS timestamp)) AND idir <> 'Soft
            deleted Home Drives'))
          ORDER BY idir ASC;
        """  # update from six to three months
        cur.execute(sql_expression)
        all_results = cur.fetchall()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        LOGGER.info(error)
        message_detail = (
            "The send_usage_emails script failed to connect or read data from the postgres database. "
            + "<br />Username: "
            + constants.POSTGRES_USER
            + "<br />Message Detail: "
            + str(error)
        )
        send_admin_email(message_detail)
        quit()
    finally:
        if conn is not None:
            conn.close()
            LOGGER.debug("Database connection closed.")

    try:
        # Attempt to sign into AD using LDAP credentials
        ldap_util = ldap.LDAPUtil(constants.LDAP_USER, constants.LDAP_PASSWORD)
    except Exception as error:
        LOGGER.info(error)
        message_detail = (
            "The send_usage_emails script failed to connect or log in to LDAP. "
            + "<br />Username: "
            + constants.LDAP_USER
            + "<br />Message Detail: "
            + str(error)
        )
        send_admin_email(message_detail)
        quit()

    data = {}
    attribute_error_idirs = []
    other_error_idirs = []
    inactive_idirs = []
    conn = ldap_util.getLdapConnection()
    # For each H Drive row, add new user to "data" dictionary if not there and add a data sample.
    for result in all_results:
        idir = result[0]
        # Filter out all IDIRs that don't start with C and P for quicker Dev iterations.
        # if not (idir[0] == "S"):
        #     continue
        gb = result[1]
        sample_datetime = result[2]
        ministry = result[3]
        if ministry == "FPRO" or ministry == "BCWS" or ministry == "FLNR":
            ministry = "FOR"
        if ministry == "AFF":
            ministry = "AF"
        if ministry == "LWRS":
            ministry = "WLRS"

        if (
            idir not in attribute_error_idirs
            and idir not in other_error_idirs
            and idir not in inactive_idirs
        ):
            if idir not in data:
                # User is not in the "data" dictionary yet, create user entry while adding first sample.
                try:
                    # Connect to AD to get user info
                    ad_info = ldap_util.getADInfo(
                        idir, conn, ["givenName", "mail", "userAccountControl"]
                    )
                except (Exception, AttributeError) as error:
                    if AttributeError:
                        print(f"Unable to find {idir} due to error {error}")
                        attribute_error_idirs.append(idir)
                    else:
                        print(f"Unable to find {idir} due to error {error}")
                        other_error_idirs.append(idir)
                    continue

                if (
                    ad_info is None
                    or "mail" not in ad_info
                    or "givenName" not in ad_info
                    or "userAccountControl" not in ad_info
                ):
                    other_error_idirs.append(idir)
                elif ad_info["userAccountControl"] in [1, 256, 514, 546, 66050, 66082]:
                    inactive_idirs.append(idir)
                else:
                    # Create user entry, add first sample
                    data[idir] = {
                        "idir": idir,
                        "samples": [get_sample(gb, sample_datetime, ministry)],
                        "mail": ad_info["mail"],
                        "name": ad_info["givenName"],
                    }
            else:
                # Add sample to existing user data, handling edge case:
                # Users who transfer ministry get two records in a single month, so flatten those.
                duplicate_found = False
                new_sample = get_sample(gb, sample_datetime, ministry)
                for sample in data[idir]["samples"]:
                    if sample["sample_datetime"] == new_sample["sample_datetime"]:
                        sample["gb"] += new_sample["gb"]
                        sample["cost"] += new_sample["cost"]
                        duplicate_found = True
                if not duplicate_found:
                    data[idir]["samples"].append(new_sample)

    # Sort the samples
    for idir in data:
        data[idir]["samples"].sort(key=lambda s: s["sample_datetime"])
        samples_length = len(data[idir]["samples"])
        data[idir]["ministry"] = data[idir]["samples"][samples_length - 1]["ministry"]

    # If errors existed, email them to the admin.
    # (There will always be errors, due to service accounts or employees who have left during the month)
    if len(attribute_error_idirs) > 0 or len(other_error_idirs) > 0:
        message_detail = (
            "The send_usage_emails script failed to find all IDIRs. "
            + "<br /><br />IDIRs not found due to attribute error: "
            + ",".join(attribute_error_idirs)
            + "<br /><br />IDIRs excluded due to inactive status: "
            + ",".join(inactive_idirs)
            + "<br /><br />IDIRs not found due to other issue: "
            + ",".join(other_error_idirs)
        )
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
            # port="5431",
            database="metabase",
            user=constants.POSTGRES_USER,
            password=constants.POSTGRES_PASSWORD,
        )
        # create a cursor
        cur = conn.cursor()

        LOGGER.debug("Get summarized H Drive counts by ministry from the last month:")
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
        message_detail = (
            "The send_usage_emails script failed to connect or read data from the postgres database. "
            + "<br />Username: "
            + constants.POSTGRES_USER
            + "<br />Message Detail: "
            + str(error)
        )
        send_admin_email(message_detail)
        quit()
    finally:
        if conn is not None:
            conn.close()
            LOGGER.debug("Database connection closed.")

    nrm_metrics = {"total_h_drive_count": 0, "total_gb": 0}

    # For each ministry record, aggregate data in dictionary
    for result in all_results:
        nrm_metrics["total_h_drive_count"] += result[0]
        nrm_metrics["total_gb"] += result[1]
        ministry = result[2]
        nrm_metrics[ministry] = {"h_drive_count": result[0], "gb": result[1]}
    return nrm_metrics


# Generate graph image's bytes using idir info
def get_graph_bytes(idir_info):
    samples = idir_info["samples"]
    idir = idir_info["name"]

    # Select plot theme, with seaborn
    sns.set_theme(rc={"figure.figsize": (9, 4.5)})
    sns.set_theme(style="whitegrid")
    fig = plt.figure()

    # Set custom colour palette and build bar chart "#2E8540"  # green
    color_under = "#003366"  # blue
    color_goal = "#D8292F"  # red

    # Add sample dates to graph axis
    axis_dates = []
    for idx, sample in enumerate(samples):
        axis_dates.append(sample["sample_datetime"].strftime("%Y-%m-%d"))

    # Convert samples array into dictionary of arrays
    gb_bar = {"gb": [], "datetime": [], "month": [], "cost": []}

    # Bar/threshold of 1.5 GB
    threshold = 1.5
    # For each month sample, add to data dictionaries
    for sample in samples:
        if sample["gb"] <= threshold:
            # Users month was <= the bar, so the cost was zero
            gb_bar["gb"].append(sample["gb"])
            gb_bar["datetime"].append(sample["sample_datetime"])
            gb_bar["month"].append(sample["month"])
            gb_bar["cost"].append(0.00)
        else:
            # Users month was > the bar, so use the calculated cost
            gb_bar["gb"].append(sample["gb"])
            gb_bar["datetime"].append(sample["sample_datetime"])
            gb_bar["month"].append(sample["month"])
            gb_bar["cost"].append(sample["cost"])

    # function to convert float to currency
    def to_currency(x):
        return "${:,.2f}".format(x)

    # convert cost list to float, then currency
    gb_bar_cost_float = [float(v) for v in gb_bar["cost"]]
    gb_bar_cost_label = [to_currency(val) for val in gb_bar_cost_float]

    # Give bars color and plot theme
    g = sns.barplot(x="month", y="gb", data=gb_bar, color=color_under)

    # label top of each bar with cost
    for i in g.containers:
        if sample["gb"] <= threshold:
            g.bar_label(i, labels=gb_bar_cost_label, color="#003366")
        else:
            g.bar_label(i, labels=gb_bar_cost_label, color="#000000")

    # Add threshold bar
    g.axhline(threshold, label="Limit of 1.5 GB", color=color_goal, linewidth=6)

    # Add legend
    plt.legend(bbox_to_anchor=(1.02, 1), loc=2, borderaxespad=0.0)

    ticks_loc = g.get_yticks().tolist()
    g.yaxis.set_major_locator(mticker.FixedLocator(ticks_loc))

    # Add various text components
    plt.title(f"{idir}'s H Drive Cost by Month", fontsize=14, color="#141414")
    plt.ylabel("H Drive Size (GB)", fontsize=13)
    plt.xlabel("", fontsize=10)
    caption = "BCPS employees are\nallocated 1.5 GB of\nH drive storage."
    caption = (
        caption
        + "\n\nStaying under the limit\nreduces unnecessary\ncosts to your Ministry"
    )

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
def send_idir_email(idir_info, h_drive_count, total_gb, ministry_name, biggest_drop):
    # Variable Definitions:
    # idir_info         Dictionary of info for a user
    # h_drive_count     H drives for the users ministry
    # total_gb          Total gb for the users ministry
    # biggest_drop      Biggest single user reduction last month
    # last_month        The most recent reporting month
    # month_before_last The reporting month before last_month

    samples = idir_info["samples"]
    name = idir_info["name"]
    recipient = idir_info["mail"]
    msg = MIMEMultipart("related")

    # Copy out values to variables for use in fstrings
    last_month_sample = samples[len(samples) - 1]
    last_month_name = last_month_sample["month"]  # i.e. January
    last_month_gb = last_month_sample["gb"]
    last_month_cost = max(0, last_month_sample["cost"])
    year = last_month_sample["sample_datetime"].year
    month_before_last_sample = None
    if len(samples) > 1:
        month_before_last_sample = samples[len(samples) - 2]
        month_before_last_gb = month_before_last_sample["gb"]
        # month_before_last_cost = max(0, month_before_last_sample["cost"])
        # month_before_last_name = month_before_last_sample["month"]
    else:
        month_before_last_gb = None

    total_gb = float(total_gb)
    h_drive_count = float(h_drive_count)
    # Get the cost of ministry H Drives and biggest drops
    total_h_drive_cost = (total_gb - (h_drive_count * 1.5)) * 2.7

    # Round down to nearest thousand for legibility
    total_gb = int(math.floor(total_gb / 10) * 10)
    total_h_drive_cost = int(math.floor(total_h_drive_cost / 10) * 10)
    h_drive_count = int(math.floor(h_drive_count / 10) * 10)

    # Build email content and metadata
    msg["Subject"] = (
        f"Transitory: Your {last_month_name} 15th {year} Personal Storage Report"
    )
    msg["From"] = "NRIDS.Optimize@gov.bc.ca"
    msg["To"] = recipient

    # Greet the user
    if last_month_gb <= 1.5:
        html_greeting = f"""<span style="font-family:Aptos; font-size: 16px">Hi {name},<br><br>
        Your H drive is under the 1.5 GB limit - great job!<br><br>
        <p><em>You will not receive this monthly report again unless you go over the 1.5 GB limit.</em></p></span>"""
    else:
        html_greeting = f"""<span style="font-family:Aptos; font-size: 16px">Hi {name},</span><br><br>
        <p><span style="background-color: #FFFF00; font-family:Aptos; font-size: 16px">You've exceeded the 1.5 GB H drive storage limit.</span></p>"""

    # Prepare user storage snapshot
    if month_before_last_gb is not None:
        difference = round(last_month_gb - month_before_last_gb, 2)
    else:
        difference = 0

    abs_difference = abs(difference)

    if last_month_gb > 1.5 and difference == 0:
        html_snapshot = f"""<div>
        <!--[if gte mso 16]>
        <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" 
        style="height:220px; v-text-anchor:middle; width:675px;" arcsize="5%" strokecolor="#666666" fill="t" strokeweight="1px" fillcolor="#EF5350">     
            <w:anchorlock/>
            <left style="color:#000;font-family:Aptos;font-weight:light;">
            <span style="font-size:16pt"><b><u>Your storage snapshot for {last_month_name} 15th, {year}</b></u><br></span>
            <span style="font-size:16pt"><p><b>Storage used: </b></b><span style="font-weight:bold">{last_month_gb:,} GB of 1.5 GB</p></span>
        	<span style="font-size:16pt"><p><b>Monthly cost: </b></b><span style="font-weight:bold">${last_month_cost:,.2f}</p></span>
        	<span style="font-size:10pt">Your storage has not changed since last month.</span>
            </left>
        </v:roundrect>
        <![endif]-->
        <!--[if !mso]> <!-->
        <table cellspacing="0" cellpadding="0"> <tr>
        <td align="left" width="675" height="220" bgcolor="#EF5350" <a style="-webkit-border-radius5px; -moz-border-radius: 5px; border-radius: 5px; color: #000; display: block;">
            <a style="color: #ffffff; font-size:18pt; font-weight: light; font-family: Aptos; text-decoration: none; line-height:220px; width:100%; display:inline-block">
            <span style="font-size:16pt"><b><u>Your storage snapshot for {last_month_name} 15th, {year}</b></u><br></span>
            <span style="font-size:16pt"><p><b>Storage used: </b>{last_month_gb:,} GB of 1.5 GB</p></span>
        	<span style="font-size:16pt"><p><b>Monthly cost: </b>${last_month_cost:,.2f}</p></span>
        	<span style="font-size:10pt; color: #000">Your storage has not changed since last month.span>
            </a>
        </td>
        </tr> </table>
        <!-- <![endif]-->
        </div>"""
    elif last_month_gb > 1.5 and difference < 0:
        html_snapshot = f"""<div>
        <!--[if gte mso 16]>
        <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" 
        style="height:220px; v-text-anchor:middle; width:675px;" arcsize="5%" strokecolor= "#666666" fill="t" #strokeweight="1px" fillcolor="#EF5350">
            <w:anchorlock/>
            <left style="color:#000;font-family:Aptos;font-weight:light;">
            <span style="font-size:16pt"><b><u>Your storage snapshot for {last_month_name} 15th, {year}</b></#u><br></span>
		    <span style="font-size:16pt"><p><b>Storage used: </b><span style="font-weight:bold">{last_month_gb:,} GB</span> of 1.5 GB</p></span>
        	<span style="font-size:16pt"><p><b>Monthly cost: </b><span style="font-weight:bold">${last_month_cost:,.2f}</span></p></span>
        	<span style="font-size:10pt">Your storage decreased by {abs_difference:,.3g} GB since last month.</span>
            </left>
        </v:roundrect>
        <![endif]-->
        <!--[if !mso]> <!-->
        <table cellspacing="0" cellpadding="0"> <tr>
        <td align="left" width="675" height="220" bgcolor="#EF5350" <a style="-webkit-border-radius: 5px; -moz-border-radius: 5px; border-radius: 5px; color: #000; display: block;">
            <a style="color: #ffffff; font-size:18pt; font-weight: light; font-family: Aptos; text-decoration: none; line-height:220px; width:100%; display:inline-block">
            <span style="font-size:16pt"><b><u>Your storage snapshot for {last_month_name} 15th, {year}</b></#u><br></span>
		    <span style="font-size:16pt"><p><b>Storage used: </b><span style="font-weight:bold">{last_month_gb:,} GB</span> of 1.5 GB</p></span>
        	<span style="font-size:16pt"><p><b>Monthly cost: </b><span style="font-weight:bold">${last_month_cost:,.2f}</span></p></span>
        	<span style="font-size:10pt; color: #000">Your storage decreased by {abs_difference:,.3g} GB since last month.</span>
            </a>
        </td>
        </tr> </table>
        <!-- <![endif]-->
        </div>"""
    elif last_month_gb > 1.5 and difference > 0:
        html_snapshot = f"""<div>
        <!--[if gte mso 16]>
        <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" mlns:w="urn:schemas-microsoft-com:office:word" 
        style="height:220px; v-text-anchor:middle; width:675px;" arcsize="5%" strokecolor= "#666666" fill="t" #strokeweight="1px" fillcolor="#EF5350">
            <w:anchorlock/>
            <left style="color:#000;font-family:Aptos;font-weight:light;">
            <span style="font-size:16pt"><b><u>Your storage snapshot for {last_month_name} 15th, {year}</b></#u><br></span>
		    <span style="font-size:16pt"><p><b>Storage used: </b><span style="font-weight:bold">{last_month_gb:,} GB</span> of 1.5 GB</p></span>
        	<span style="font-size:16pt"><p><b>Monthly cost: </b><span style="font-weight:bold">${last_month_cost:,.2f}</span></p></span>
        	<span style="font-size:10pt">Your storage increased by {abs_difference:,.3g} GB since last month.</span>
            </left>
        </v:roundrect>
        <![endif]-->
        <!--[if !mso]> <!-->
        <table cellspacing="0" cellpadding="0"> <tr>
        <td align="left" width="675" height="220" bgcolor="#EF5350" <a style="-webkit-border-radius: 5px; -moz-border-radius: 5px; border-radius: 5px; color: #000; display: block;">
            <a style="color: #ffffff; font-size:18pt; font-weight: light; font-family: Aptos; text-decoration: none; line-height:220px; width:100%; display:inline-block">
            <span style="font-size:16pt"><b><u>Your storage snapshot for {last_month_name} 15th, {year}</></#u><br></span>
		    <span style="font-size:16pt"><p><b>Storage used: </b><span style="font-weight:bold">{last_month_gb:,} GB</span> of 1.5 GB</p></span>
        	<span style="font-size:16pt"><p><b>Monthly cost: </b><span style="font-weight:bold">${last_month_cost:,.2f}</span></p></span>
        	<span style="font-size:10pt; color: #000">Your storage increased by {abs_difference:,.3g} GB since last month.</span>
            </a>
        </td>
        </tr> </table>
        <!-- <![endif]-->
        </div>"""
    elif last_month_gb > 1.5 and month_before_last_sample is None:
        html_snapshot = f"""<div>
        <!--[if gte mso 16]>
        <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" 
        style="height:220px; v-text-anchor:middle; width:675px;" arcsize="5%" strokecolor= "#666666" fill="t" #strokeweight="1px" fillcolor="#EF5350">
            <w:anchorlock/>
            <left style="color:#000;font-family:Aptos;font-weight:light;">
            <span style="font-size:16pt"><b><u>Your storage snapshot for {last_month_name} 15th, {year}</b></#u><br></span>
		    <span style="font-size:16pt"><b><p>Storage used: </b><span style="font-weight:bold">{last_month_gb:,} GB</span> of 1.5 GB</p></span>
        	<span style="font-size:16pt"><b><p>Monthly cost: </b><span style="font-weight:bold">${last_month_cost:,.2f}</span></p></span>
            </left>
        </v:roundrect>
        <![endif]-->
        <!--[if !mso]> <!-->
        <table cellspacing="0" cellpadding="0"> <tr>
        <td align="left" width="675" height="220" bgcolor="#EF5350" <a style="-webkit-border-radius: 5px; -moz-border-radius: 5px; border-radius: 5px; color: #000; display: block;">
            <a style="color: #ffffff; font-size:18pt; font-weight: light; font-family: Aptos; text-decoration: none; line-height:220px; width:100%; display:inline-block">
            <span style="font-size:16pt"><b><u>Your storage snapshot for {last_month_name} 15th, {year}</></u><br></span>
		    <span style="font-size:16pt"><b><p>Storage used: </b><span style="font-weight:bold">{last_month_gb:,} GB</span> of 1.5 GB</p></span>
        	<span style="font-size:16pt"><b><p>Monthly cost: </b><span style="font-weight:bold">${last_month_cost:,.2f}</span></p></span>
            </a>
        </td>
        </tr> </table>
        <!-- <![endif]-->
        </div>"""
    elif last_month_gb <= 1.5:
        pass
    else:
        pass

    # if last_month_gb <= 1.5 and difference == 0:
    #    html_snapshot = f"""<div>
    #    <!--[if gte mso 16]>
    #    <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word"
    #    style="height:220px; v-text-anchor:middle; width:675px;" arcsize="5%" strokecolor="#666666" fill="t" #strokeweight="1px" fillcolor="#43A047">
    #    <style type="text/css">
    #        <w:anchorlock/>
    #        <left style="color:#000 !important;font-family:Aptos;font-weight:light;">
    #        <span style="font-size:16pt;"><b><u>Your storage snapshot for {last_month_name} 15th, {year}</b></#u><br></span>
    #        <span style="font-size:16pt;"><p><b>Storage used: </b>{last_month_gb:,} GB of 1.5 GB</p></span>
    #    	<span style="font-size:16pt;"><p><b>Monthly cost: </b>${last_month_cost:,.2f}</p></span>
    #    	<span style="font-size:10pt;">Your storage has not changed since last month.</span>
    #        </left>
    #    </v:roundrect>
    #    </style>
    #    <![endif]-->
    #    <!--[if !mso]> <!-->
    #    <table cellspacing="0" cellpadding="0"> <tr>
    #    <td align="left" width="675" height="220" bgcolor="#43A047" <a style="-webkit-border-radius5px; #-moz-border-radius: 5px; border-radius: 5px; color: #000; display: block;">
    #        <a style="color: #ffffff; font-size:18pt; font-weight: light; font-family: Aptos; #text-decoration: none; line-height:220px; width:100%; display:inline-block">
    #        <span style="font-size:16pt"><b><u>Your storage snapshot for {last_month_name} 15th, {year}</b></ #u><br></span>
    #        <span style="font-size:16pt"><p><b>Storage used: </b>{last_month_gb:,} GB of 1.5 GB</p></span>
    #    	<span style="font-size:16pt"><p><b>Monthly cost: </b>${last_month_cost:,.2f}</p></span>
    #    	<span style="font-size:10pt; color: #000">Your storage has not changed since last month.span>
    #        </a>
    #    </td>
    #    </tr> </table>
    #    <!-- <![endif]-->
    #    </div>"""
    # elif last_month_gb <= 1.5 and difference < 0:
    #    html_snapshot = f"""<div>
    #    <!--[if gte mso 16]>
    #    <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word"
    #    style="height:220px; v-text-anchor:middle; width:675px;" arcsize="5%" strokecolor= "#666666" fill="t" #strokeweight="1px" fillcolor="#43A047">
    #        <w:anchorlock/>
    #        <left style="color:#000;font-family:Aptos;font-weight:light;">
    #        <span style="font-size:16pt"><b><u>Your storage snapshot for {last_month_name} 15th, {year}</b></#u><br></span>
    # 	    <span style="font-size:16pt"><p><b>Storage used: </b>{last_month_gb:,} GB of 1.5 GB</p></span>
    #    	<span style="font-size:16pt"><p><b>Monthly cost: </b>${last_month_cost:,.2f}</p></span>
    #    	<span style="font-size:10pt">Your storage decreased by {abs_difference:,.3g} GB since last month.#</span>
    #        </left>
    #    </v:roundrect>
    #    <![endif]-->
    #    <!--[if !mso]> <!-->
    #    <table cellspacing="0" cellpadding="0"> <tr>
    #    <td align="left" width="675" height="220" bgcolor="#43A047" <a style="-webkit-border-radius: 5px; #-moz-border-radius: 5px; border-radius: 5px; color: #000; display: block;">
    #        <a style="color: #ffffff; font-size:18pt; font-weight: light; font-family: Aptos; #text-decoration: none; line-height:220px; width:100%; display:inline-block">
    #        <span style="font-size:16pt"><b><u>Your storage snapshot for {last_month_name} 15th, {year}</b></#u><br></span>
    # 	    <span style="font-size:16pt"><p><b>Storage used: </b>{last_month_gb:,} GB of 1.5 GB</p></span>
    #    	<span style="font-size:16pt"><p><b>Monthly cost: </b>${last_month_cost:,.2f}</p></span>
    #    	<span style="font-size:10pt; color: #000">Your storage decreased by {abs_difference:,.3g} GB #since last month.</span>
    #        </a>
    #    </td>
    #    </tr> </table>
    #    <!-- <![endif]-->
    #    </div>"""
    # elif last_month_gb <= 1.5 and difference > 0:
    #    html_snapshot = f"""<div>
    #    <!--[if gte mso 16]>
    #    <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word"
    #    style="height:220px; v-text-anchor:middle; width:675px;" arcsize="5%" strokecolor= "#666666" fill="t" #strokeweight="1px" fillcolor="#43A047">
    #        <w:anchorlock/>
    #        <left style="color:#000;font-family:Aptos;font-weight:light;">
    #        <span style="font-size:16pt"><b><u>Your storage snapshot for {last_month_name} 15th, {year}</b></#u><br></span>
    # 	    <span style="font-size:16pt"><p><b>Storage used: </b>{last_month_gb:,} GB of 1.5 GB</p></span>
    #    	<span style="font-size:16pt"><p><b>Monthly cost: </b>${last_month_cost:,.2f}</p></span>
    #    	<span style="font-size:10pt">Your storage increased by {abs_difference:,.3g} GB since last month.#</span>
    #        </left>
    #    </v:roundrect>
    #    <![endif]-->
    #    <!--[if !mso]> <!-->
    #    <table cellspacing="0" cellpadding="0"> <tr>
    #    <td align="left" width="675" height="220" bgcolor="#43A047" <a style="-webkit-border-radius: 5px; #-moz-border-radius: 5px; border-radius: 5px; color: #000; display: block;">
    #        <a style="color: #ffffff; font-size:18pt; font-weight: light; font-family: Aptos; #text-decoration: none; line-height:220px; width:100%; display:inline-block">
    #        <span style="font-size:16pt"><b><u>Your storage snapshot for {last_month_name} 15th, {year}</b></#u><br></span>
    # 	    <span style="font-size:16pt"><p><b>Storage used: </b>{last_month_gb:,} GB of 1.5 GB</p></span>
    #    	<span style="font-size:16pt"><p><b>Monthly cost: </b>${last_month_cost:,.2f}</p></span>
    #    	<span style="font-size:10pt; color: #000">Your storage increased by {abs_difference:,.3g} GB #since last month.</span>
    #        </a>
    #    </td>
    #    </tr> </table>
    #    <!-- <![endif]-->
    #    </div>"""
    # elif last_month_gb <= 1.5 and month_before_last_sample is None:
    #    html_snapshot = f"""<div>
    #    <!--[if gte mso 16]>
    #    <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word"
    #    style="height:220px; v-text-anchor:middle; width:675px;" arcsize="5%" strokecolor= "#666666" fill="t" #strokeweight="1px" fillcolor="#43A047">
    #        <w:anchorlock/>
    #        <left style="color:#000;font-family:Aptos;font-weight:light;">
    #        <span style="font-size:16pt"><b><u>Your storage snapshot for {last_month_name} 15th, {year}</b></#u><br></span>
    # 	    <span style="font-size:16pt"><b><p>Storage used: </b>{last_month_gb:,} GB of 1.5 GB</p></span>
    #    	<span style="font-size:16pt"><b><p>Monthly cost: </b>${last_month_cost:,.2f}</p></span>
    #        </left>
    #    </v:roundrect>
    #    <![endif]-->
    #    <!--[if !mso]> <!-->
    #    <table cellspacing="0" cellpadding="0"> <tr>
    #    <td align="left" width="675" height="220" bgcolor="#43A047" <a style="-webkit-border-radius: 5px; #-moz-border-radius: 5px; border-radius: 5px; color: #000; display: block;">
    #        <a style="color: #ffffff; font-size:18pt; font-weight: light; font-family: Aptos; #text-decoration: none; line-height:220px; width:100%; display:inline-block">
    #        <span style="font-size:16pt"><b><u>Your storage snapshot for {last_month_name} 15th, {year}</b></#u><br></span>
    # 	    <span style="font-size:16pt"><p><b>Storage used: </b>{last_month_gb:,} GB of 1.5 GB</p></span>
    #    	<span style="font-size:16pt"><p><b>Monthly cost: </b>${last_month_cost:,.2f}</p></span>
    #        </a>
    #    </td>
    #    </tr> </table>
    #    <!-- <![endif]-->
    #    </div>"""

    number_names = ["", "two ", "three ", "four ", "five ", "six ", "seven ", " eight"]
    month_count = number_names[len(samples) - 1]
    month_plural = ""
    if month_before_last_sample is not None:
        month_plural = "s"

    html_img = (
        """<br><img src="cid:image1" alt="Graph" style="width:250px;height:50px;">"""
    )

    # Provide H drive reduction resources
    html_resources = """<span style="font-family:Aptos; font-size: 16px"><br><p>The NRIDS Optimization Team is dedicated to getting H drive costs down to $0.<br><br>
    For H drive reduction resource materials, including step-by-step guidance and demo session recordings, please visit our <a href="https://apps.nrs.gov.bc.ca/int/confluence/x/pQ1xD">Knowledge Base</a>.</p></span><br>"""

    # Display chart of 3 month trend
    html_trend_chart = f"""<div>
        <!--[if gte mso 16]>
        <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" 
        style="height:40px; v-text-anchor:middle; width:1005px;" arcsize="5%" strokecolor= "#666666" fill="t" strokeweight="1px" fillcolor="#EF5350">
            <w:anchorlock/>
            <left style="font-family:Aptos;font-size:16px;font-weight:light;">
            If you recently updated to Windows 11 on your computer and saw a jump in your H drive storage, <a href="https://apps.nrs.gov.bc.ca/int/confluence/x/pQ1xD#HDrivemigrationtoOneDrive-Win11">learn what to do.</a>
            </left>
        </v:roundrect>
        </style>
        <![endif]-->
        <!--[if !mso]> <!-->
        <table cellspacing="0" cellpadding="0"> <tr>
        <td align="left" width="1005" height="40" bgcolor="#43A047" <a style="-webkit-border-radius: 5px; -moz-border-radius: 5px; border-radius: 5px; color: #000; display: block;">
            <a style="color: #ffffff; 16px; font-weight: light; font-family: Aptos; text-decoration: none; line-height:40px; width:100%; display:inline-block">
            If you recently updated to Windows 11 on your computer and saw a jump in your H drive storage, <a href="https://apps.nrs.gov.bc.ca/int/confluence/x/pQ1xD#HDrivemigrationtoOneDrive-Win11">learn what to do.</a>
            </a>
        </td>
        </tr> </table>
        <!-- <![endif]-->
        </div>
        <br>
        {html_img}<br><br>"""

    # Tell user where to find more PSR info
    html_about = """<span style="font-family:Aptos; font-size: 18px"><b>About this report</b></span><br><br>
    <span style="font-family:Aptos; font-size: 16px"><p>Visit our <a href="https://apps.nrs.gov.bc.ca/int/confluence/x/YxF2Dg">Knowledge Base (PSR) </a>to learn: </p>
    <ul>
        <li>General PSR info</li>
        <li>Why H drive storage reduction matters</li>
        <li>How to reduce your storage</li>
    </ul>
    <span style="color: #000435">This email is transitory and can be deleted when no longer needed. Thank you for taking the time to manage your digital storage.</span></span><br><br>"""

    # Email unsubscribe information
    html_unsub = """<footer><span style="font-family:Aptos; font-size: 9px">To opt out of these monthly emails, reply with the subject line "unsubscribe".<br>
    <em>Note:</em> by unsubscribing, you will not be notified if your H drive goes over the 1.5 GB limit.<br>
    You can re-subscribe at any time by contacting <a href="mailto:NRIDS.Optimize@gov.bc.ca">NRIDSOptimize@gov.bc.ca</a></span></footer>"""

    # Merge html parts and attach to email

    html = (
        html_greeting
        + html_snapshot
        + html_resources
        + html_trend_chart
        + html_about
        + html_unsub
    )

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
    # s.sendmail(msg["From"], recipient, msg.as_string())
    s.sendmail(msg["From"], recipient, msg.as_string())
    s.quit()

    # Following smtp server guidelines of max 30 emails/minute
    # time.sleep(2)

    # log send complete
    LOGGER.info(f"Email sent to {recipient}.")


# Handle address formatting, ensure uniqueness, and filter out addresses using omitlist
def refine_sendlist():

    # pattern matches all email addresses between < > with letters, numbers, and the following characters: .-_@
    pattern = re.compile(r"(?<=\<)[a-zA-Z\.\-\_\@\0-9]*(?=\>)")

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

        # Update ministry names in both sets of data
        ministry_renames = {
            "BCWS": "FOR",
            "FLNR": "FOR",
            "FPRO": "FOR",
            "AFF": "AF",
            "LWRS": "WLRS",
        }

        for idir in data:
            idir_info = data[idir]
            ministry_acronym = idir_info["ministry"]
            if ministry_acronym in ministry_renames:
                idir_info["ministry"] = ministry_renames[ministry_acronym]
        ministry_acronyms_to_remove = []
        for ministry_acronym in nrm_metrics:
            metrics = nrm_metrics[ministry_acronym]
            if ministry_acronym in ministry_renames:
                new_acronym = ministry_renames[ministry_acronym]
                nrm_metrics[new_acronym]["gb"] = (
                    nrm_metrics[new_acronym]["gb"] + metrics["gb"]
                )
                nrm_metrics[new_acronym]["h_drive_count"] = (
                    nrm_metrics[new_acronym]["h_drive_count"] + metrics["h_drive_count"]
                )
                ministry_acronyms_to_remove.append(ministry_acronym)
        for ministry_acronym in ministry_acronyms_to_remove:
            del nrm_metrics[ministry_acronym]

        # Assign Ministry Names, in use they are prefixed with "Ministry of "
        long_ministry_names = {
            "AF": "Agriculture and Food",
            "EMLI": "Energy, Mines and Low Carbon Innovation",
            "ENV": "Environment and Climate Change Strategy",
            "FOR": "Forests",
            "WLRS": "Water, Land and Resource Stewardship",
            "IRR": "Indigenous Relations & Reconciliation",
            "MCM": "Mining and Critical Minerals",
        }

        # Get Biggest Drop (storage reduction) of the month
        biggest_drop = 0
        # biggest_drops_list = []
        for idir in data:
            samples = data[idir]["samples"]
            if len(samples) >= 2:
                last_month = samples[len(samples) - 1]
                month_before_last = samples[len(samples) - 2]
                if last_month["sample_datetime"] - month_before_last[
                    "sample_datetime"
                ] < timedelta(days=35):
                    last_month_gb = last_month["gb"]
                    month_before_last_gb = month_before_last["gb"]
                    drop = month_before_last_gb - last_month_gb
                    # Get biggest drop
                    if drop > biggest_drop:
                        biggest_drop = drop

        # Split input idirs and email addresses, and handle address formatting
        email_send_list, idir_send_list = refine_sendlist()

        # Filter out non-emails, and if sendlist then also users not on the sendlist
        filtered_data = {}
        for idir in data:
            idir_info = data[idir]
            email = idir_info["mail"]
            if email is not None:
                if constants.EMAIL_SENDLIST and constants.EMAIL_SENDLIST != "None":
                    if (
                        idir.lower() in idir_send_list
                        or email.lower() in email_send_list
                    ):
                        filtered_data[idir] = idir_info
                else:
                    filtered_data[idir] = idir_info
        data = filtered_data

        # Send email for each user
        omit_list = constants.EMAIL_OMITLIST.split(",")

        for i in range(len(omit_list)):
            omit_list[i] = omit_list[i].lower()

        for idir in data:
            idir_info = data[idir]
            email = idir_info["mail"]
            if email.lower() not in omit_list:
                ministry_acronym = idir_info["ministry"]
                h_drive_count = nrm_metrics[ministry_acronym]["h_drive_count"]
                ministry_gb = nrm_metrics[ministry_acronym]["gb"]
                if ministry_acronym not in long_ministry_names:
                    send_admin_email(
                        f"New Ministry for user {idir} named {ministry_acronym}"
                    )
                else:
                    ministry_name = long_ministry_names[ministry_acronym]
                    send_idir_email(
                        idir_info,
                        h_drive_count,
                        ministry_gb,
                        ministry_name,
                        biggest_drop,
                        # biggest_drops,
                    )

                    # Track successful send
                    emails_sent_to.append(idir_info["mail"])

    except (Exception, psycopg2.DatabaseError) as error:
        LOGGER.info(error)
        message_detail = (
            "The send_usage_emails script encountered an error sending emails to users. "
            + "<br />Message Detail: "
            + str(error)
        )
        send_admin_email(message_detail)
    finally:
        # Report successful sends for tracking purposes, even if the script as a whole had an exception.
        message_detail = (
            "The send_usage_emails script sent emails to the following users: "
            + ",".join(emails_sent_to)
        )
        LOGGER.info(message_detail)
        send_admin_email(message_detail)


if __name__ == "__main__":
    main(sys.argv[1:])

    # Give developers time to look at OCP pod terminal/details after a failure/success before terminating.
    LOGGER.info("Script Complete, pausing for 5 minutes...")
    time.sleep(300)
