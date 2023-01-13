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

from sharepoint_collections import (
    auth,
    for1,
    for2,
    nrm,
    aff,
    irr,
    env,
    eao,
    crts,
    emli,
    bcws,
    irrcs,
    bcts,
)
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

collection_list = [site for key, site in sharepoint_collection.items()]
collection_list[1:]
print(collection_list)
