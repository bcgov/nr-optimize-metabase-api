# -------------------------------------------------------------------------------
# Name:        Update_quarterly_reporting.py
# Purpose:     The purpose of the script is to update the Opt. reporting dashboard for each quarterly report via the metabase api.
#              *Note - variables need to be updated prior to running the script. This could be command line input in future iterations.
#
# Author:      CCOCKER
#
# Created:     2022
# Copyright:   (c) Optimization Team 2022
# Licence:     mine
#
#
# usage: ./update_quarterly_reporting.py
# -------------------------------------------------------------------------------

import requests
import constants

# Define the environment URL

# DEV
# env_url = 'https://iitco-metabase-dev.apps.silver.devops.gov.bc.ca'

# PROD
env_url = "https://iitco-metabase.apps.silver.devops.gov.bc.ca"


# VARS for quarterly report dates (update as needed for each report)
# -------------------------
fy_start = "2021-04-01"
q_start = "2022-01-01"
q_end = "2022-03-31"

# Dictionaries of date replacements KV pairs for each case:
email_replace = {"2021-12-31": "2022-03-31", "2021-04-01": fy_start}
h_since_opt_replace = {"2021-12-31": "2022-03-31", "2021-12-01": "2022-03-01"}
q_compare_replace = {
    "2021-12-31": "2022-03-31",
    "2021-10-01": "2022-01-01",
    "2021-09-30": "2021-12-31",
    "2021-07-01": "2021-10-01",
    "2021-04-01": "2021-07-01",
    "2021-06-30": "2021-09-30",
    "2021-01-01": "2021-04-01",
    "2021-03-31": "2021-06-30",
    "2021/2022 Q3 Spend": "2022/2022 Q4 Spend",
    "2021/2022 Q2 Spend": "2021/2022 Q3 Spend",
    "2021/2022 Q1 Spend": "2021/2022 Q2 Spend",
    "2020/2021 Q4 Spend": "2021/2022 Q1 Spend",
}
# ------------------------

# Query case lists (matching replacement process for each group of cards) *Note - need to test the same in dev*
email_total = [254]
h_since_opt = [263]
q_compare = [
    260,
    262,
    266,
    269,
    268,
    270,
    271,
    272,
    273,
    276,
    277,
    278,
    279,
    281,
    280,
    287,
    286,
    284,
    285,
    282,
    288,
    289,
    290,
    292,
    291,
    298,
    274,
    297,
    294,
    293,
    296,
]

# function to update Metabase Custom questions & native SQL queries (type either 'query' or 'native') .
def put_query(card_id, query, type):
    if type == "query":
        JSON = {"dataset_query": {"database": 2, "query": query, "type": "query"}}

    if type == "native":
        JSON = {
            "dataset_query": {
                "database": 2,
                "type": "native",
                "native": {"query": query},
            }
        }
    url = env_url + "/api/card/" + str(card_id)
    requests.put(url, headers=headers, json=JSON).json()


# get session
session_url = env_url + "/api/session"
response = requests.post(
    session_url, json={"username": constants.USER_NAME, "password": constants.PASSWORD}
)
session_id = response.json()["id"]
headers = {"X-Metabase-Session": session_id}

# get all the reporting dashboard data
dashboard_url = env_url + "/api/dashboard/14"
dashboard = requests.get(dashboard_url, headers=headers).json()

for item in dashboard["ordered_cards"]:

    # Metabase Custom questions - all in the dashboard are fiscal year to date (only need to update last quarter date of filter)
    if "query" in item["card"]["dataset_query"]:
        query = item["card"]["dataset_query"]["query"]

        # catch historical card (only update Quarter end date)
        if item["card"]["id"] == 265:
            query["filter"][3] = q_end
        else:
            # filters slightly different with queries containing "and" statements
            if len(query["filter"]) == 4:
                query["filter"][2] = fy_start
                query["filter"][3] = q_end
            else:
                query["filter"][2][2] = fy_start
                query["filter"][2][3] = q_end

        # update dashboard
        put_query(item["card"]["id"], query, "query")

    elif "native" in item["card"]["dataset_query"]:

        # get the query string
        query = item["card"]["dataset_query"]["native"]["query"]

        # update sdaparty to ministry due to table updates/consistencey 04/2022
        if "sdaparty" in query:
            query = query.replace("sdaparty", "ministry")
            put_query(item["card"]["id"], query, "native")

        # update queries according to card id for each case
        if item["card"]["id"] in email_total:
            for key, value in email_replace.items():
                query = query.replace(key, value)
        elif item["card"]["id"] in h_since_opt:
            for key, value in h_since_opt_replace.items():
                query = query.replace(key, value)
        elif item["card"]["id"] in q_compare:
            for key, value in q_compare_replace.items():
                query = query.replace(key, value)
        else:
            print(
                "Unknown Card Found: " + item["card"]["id"] + " " + item["card"]["name"]
            )
            continue

        # update dashboard
        put_query(item["card"]["id"], query, "native")

    else:
        print("ERROR PARSING DASHBOARD CARDS: QUERY TYPE UNKNOWN")
