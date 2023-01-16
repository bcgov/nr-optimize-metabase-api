# -------------------------------------------------------------------------------
# Name:        scrape_sp_site_collection.py
# Purpose:     the purpose of the script is to web-scrape all the SharePoint collection sites that belong to the Natural Resource Ministries
#              1.) Log into main page of SharePoint site
#              2.) Scrape data from all pages of the Site Collection table
#              3.) Drop row that are not SharePoint sites
#              4.) Drop unnecessary columns
#              5.) Add columns for Collection Name, URL of each page in Collection
#              6.) Write the data from each collection into one Excel file
#
# Author:      HHAY, PPLATTEN
#
# Created:     2023
# Copyright:   (c) Optimization Team 2023
# Licence:     mine
#
#
# usage: scrape_sp_site_collection.py
# example: scrape_sp_site_collection.py
# -------------------------------------------------------------------------------

from sharepoint_collections import auth, site_collections
import sp_constants as constants
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from chromedriver_py import binary_path
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# SharePoint credentials
username = constants.USER_NAME
password = constants.PASSWORD

# initialize the Chrome driver
options = webdriver.ChromeOptions()
options.add_experimental_option("excludeSwitches", ["enable-logging"])
options.add_argument("--ignore-certificate-errors")
options.add_argument("--headless")
service_object = Service(binary_path)
driver = webdriver.Chrome(options=options, service=service_object)


def scrape_page():
    # empty lists & dictionaries
    headers = []
    columns = dict()

    # get table
    table_id = driver.find_element(
        By.XPATH, """/html/body/form/div[12]/div/div[2]/div[2]/div[3]/table[3]"""
    )
    all_rows = table_id.find_elements(By.TAG_NAME, "tr")

    # get headers
    row = all_rows[0]
    all_items = row.find_elements(By.TAG_NAME, "th")
    for item in all_items:
        name = item.text
        columns[name] = []
        headers.append(name)

    print(headers)

    # get URL for new column
    find_href = row.find_elements(
        By.XPATH,
        """/html/body/form/div[12]/div/div[2]/div[2]/div[3]/table[3]/tbody/tr[*]/td[2]/a""",
    )
    links = [i.get_attribute("href") for i in find_href]

    # get Last modified data for existing column
    find_lm = row.find_elements(
        By.XPATH,
        """/html/body/form/div[12]/div/div[2]/div[2]/div[3]/table[3]/tbody/tr[*]/td[8]""",
    )
    lm = [d.text for d in find_lm]

    # append data to rows
    for row in all_rows[1:]:
        all_items = row.find_elements(By.TAG_NAME, "td")
        for name, item in zip(headers, all_items):
            value = item.text
            columns[name].append(value)

    return row


for s in site_collections.values():
    # go to SharePoint login page
    driver.get(s)
    # find username/email field and send the username itself to the input field
    driver.find_element(By.ID, "userNameInput").send_keys(username)
    # find password input field and insert password as well
    driver.find_element(By.ID, "passwordInput").send_keys(password)
    # click login button
    driver.find_element(By.ID, "submitButton").click()
    # get URL of page after login
    strUrl = driver.current_url
    print("Current Url is:" + strUrl + "\n" * 2)
    # scrape the page
    scrape_page()

    # find the collection based on the URL
    collection = strUrl[31:-36]

    # build pandas dataframe
    df = pd.DataFrame.from_dict(columns, orient="index")
    df = df.transpose()
    df = df.drop(df.columns[[0, 3, 4, 5]], axis=1)
    df["Last Modified"] = pd.Series(lm)
    df["URL"] = pd.Series(links)
    df["Collection"] = pd.Series(collection)

    # show the dataframe
    print(df)
