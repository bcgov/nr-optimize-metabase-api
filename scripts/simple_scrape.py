from sharepoint_collections import site_collections
import sp_constants as constants
import pandas as pd
import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from chromedriver_py import binary_path
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# SharePoint credentials
username = constants.USER_NAME
password = constants.PASSWORD

# initialize the Chrome options & service
options = webdriver.ChromeOptions()
options.add_experimental_option("excludeSwitches", ["enable-logging"])
options.add_argument("--ignore-certificate-errors")
options.add_argument("--headless")
service_object = Service(binary_path)

for s in site_collections.values():
    # initialize the Chrome driver
    driver = webdriver.Chrome(options=options, service=service_object)

    # go to SharePoint login page
    driver.get(s)

    # defining a locator for the HTML element with userID
    locator = By.ID, ("userNameInput")

    # wait for the log on option to be available
    WebDriverWait(driver=driver, timeout=10).until(
        EC.presence_of_element_located(locator)
    )

    # define log in variables
    user = driver.find_element(By.ID, "userNameInput")
    pw = driver.find_element(By.ID, "passwordInput")
    login = driver.find_element(By.ID, "submitButton")

    # find username/email field and send the username itself to the input field
    user.send_keys(username)
    # find password input field and insert password as well
    pw.send_keys(password)
    # click login button
    login.click()
    # get URL of page after login

    strUrl = driver.current_url
    # find the collection based on the URL
    collection = strUrl[31:-25]
    print("Accessing " + collection + " site collection, current URL is: " + strUrl)

    # empty lists & dictionaries
    headers = []
    columns = dict()

    # get table
    driver.implicitly_wait(5)
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

    print("Scraping page 1...")

    find_type = row.find_elements(
        By.XPATH,
        """/html/body/form/div[12]/div/div[2]/div[2]/div[3]/table[3]/tbody/tr[*]/td[1]/img[1]""",
    )
    type = [t.get_attribute("alt") for t in find_type]

    # get URL for new column
    find_href = row.find_elements(
        By.XPATH,
        """/html/body/form/div[12]/div/div[2]/div[2]/div[3]/table[3]/tbody/tr[*]/td[2]/a""",
    )
    links = [i.get_attribute("href") for i in find_href]
    # print(links)

    # get Last modified data for existing column
    find_lm = row.find_elements(
        By.XPATH,
        """/html/body/form/div[12]/div/div[2]/div[2]/div[3]/table[3]/tbody/tr[*]/td[8]""",
    )
    lm = [d.text for d in find_lm]
    # print(lm)

    # append data to rows
    for row in all_rows[1:]:
        all_items = row.find_elements(By.TAG_NAME, "td")
        for name, item in zip(headers, all_items):
            value = item.text
            columns[name].append(value)

    # build pandas dataframe
    df1 = pd.DataFrame.from_dict(columns, orient="index")
    df1 = df1.transpose()
    df1 = df1.drop(df1.columns[[0, 3, 4, 5]], axis=1)
    df1.rename(columns={"Name": "sitename", "Total Size": "datausage"}, inplace=True)
    df1["Type"] = pd.Series(type)
    # Selecting only the rows that are SharePoint sites
    df1 = df1.loc[df1["Type"] == "Type Web"]
    df1["unit"] = df1.datausage.str[-2:]
    df1["datausage"] = df1["datausage"].str[:-3]
    df1["lastmodified"] = pd.Series(lm)
    df1["url"] = pd.Series(links)
    df1["collection"] = ""
    df1["collection"] = df1["collection"].str.replace("", collection)
    # Replacing empty string with np.NaN
    df1["url"] = df1["url"].replace("", np.nan)
    df1["sitename"] = df1["sitename"].replace("", np.nan)
    df1["date"] = pd.to_datetime("today").normalize()
    # Dropping rows where NaN is present
    df2 = df1.dropna(subset=["url", "sitename"])
    df2["datausage"] = df2["datausage"].astype(float)
    # convert all data sizes to GB
    df2.loc[df2["unit"] == "MB", "datausage"] = df2["datausage"] / 1000
    df2.loc[df2["unit"] == "KB", "datausage"] = df2["datausage"] / 1000000
    # calculate data cost
    df2["datacost"] = df2.datausage.mul(60).round(2)
    df2 = df2[
        [
            "collection",
            "sitename",
            "url",
            "datausage",
            "datacost",
            "lastmodified",
            "date",
        ]
    ]

    # move to next page
    while True:
        try:
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "/html/body/form/div[12]/div/div[2]/div[2]/div[3]/table[4]/tbody/tr/td/a[contains(.,'Next')]",
                    )
                )
            ).click()
        except TimeoutException:
            print("Reached Last Page")
            break

        # empty lists & dictionaries
        headers = []
        columns = dict()

        # get table
        driver.implicitly_wait(5)
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

        print("Scraping page 2...")

        find_type = row.find_elements(
            By.XPATH,
            """/html/body/form/div[12]/div/div[2]/div[2]/div[3]/table[3]/tbody/tr[*]/td[1]/img[1]""",
        )
        type = [t.get_attribute("alt") for t in find_type]

        # get URL for new column
        find_href = row.find_elements(
            By.XPATH,
            """/html/body/form/div[12]/div/div[2]/div[2]/div[3]/table[3]/tbody/tr[*]/td[2]/a""",
        )
        links = [i.get_attribute("href") for i in find_href]
        # print(links)

        # get Last modified data for existing column
        find_lm = row.find_elements(
            By.XPATH,
            """/html/body/form/div[12]/div/div[2]/div[2]/div[3]/table[3]/tbody/tr[*]/td[8]""",
        )
        lm = [d.text for d in find_lm]
        # print(lm)

        # append data to rows
        for row in all_rows[1:]:
            all_items = row.find_elements(By.TAG_NAME, "td")
            for name, item in zip(headers, all_items):
                value = item.text
                columns[name].append(value)

        # build pandas dataframe
        df3 = pd.DataFrame.from_dict(columns, orient="index")
        df3 = df3.transpose()
        df3 = df3.drop(df3.columns[[0, 3, 4, 5]], axis=1)
        df3.rename(
            columns={"Name": "sitename", "Total Size": "datausage"}, inplace=True
        )
        df3["Type"] = pd.Series(type)
        # Selecting only the rows that are SharePoint sites
        df3 = df3.loc[df3["Type"] == "Type Web"]
        df3["unit"] = df3.datausage.str[-2:]
        df3["datausage"] = df3["datausage"].str[:-3]
        df3["lastmodified"] = pd.Series(lm)
        df3["url"] = pd.Series(links)
        df3["collection"] = ""
        df3["collection"] = df3["collection"].str.replace("", collection)
        # Replacing empty string with np.NaN
        df3["url"] = df3["url"].replace("", np.nan)
        df3["sitename"] = df3["sitename"].replace("", np.nan)
        df3["date"] = pd.to_datetime("today").normalize()
        # Dropping rows where NaN is present
        df4 = df3.dropna(subset=["url", "sitename"])
        df4["datausage"] = df4["datausage"].astype(float)
        # convert all data sizes to GB
        df4.loc[df4["unit"] == "MB", "datausage"] = df4["datausage"] / 1000
        df4.loc[df4["unit"] == "KB", "datausage"] = df4["datausage"] / 1000000
        # Calculate data cost
        df4["datacost"] = df4.datausage.mul(60).round(2)
        df4 = df4[
            [
                "collection",
                "sitename",
                "url",
                "datausage",
                "datacost",
                "lastmodified",
                "date",
            ]
        ]

        # concatenate dataframes
        frames = [df2, df4]
        df = pd.concat(frames)

        # output to csv
        df.to_csv("./SharePoint_Scrape_" + (collection) + ".csv", index=False)

        # wait for the ready state to be complete
        WebDriverWait(driver=driver, timeout=10).until(
            lambda x: x.execute_script("return document.readyState === 'complete'")
        )

    # wait, and go to the next site
    driver.implicitly_wait(5)
