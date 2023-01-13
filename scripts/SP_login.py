import sp_constants as constants
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from chromedriver_py import binary_path
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# from selenium.common.exceptions import TimeoutException, WebDriverException

# SharePoint credentials
username = constants.USER_NAME
password = constants.PASSWORD

# SharePoint Collections
auth = "https://sts.gov.bc.ca/adfs/ls?wa=wsignin1.0&wtrealm=urn%3asp.gov.bc.ca&wctx=https%3a%2f%2fnrm.sp.gov.bc.ca%2fsites%2f"
for1 = (
    auth
    + "flnr%2f_layouts%2f15%2fAuthenticate.aspx%3fSource%3d%252Fsites%252FFLNR%252F%255Flayouts%252F15%252Fstorman%252Easpx&wreply=https%3a%2f%2fnrm.sp.gov.bc.ca%2f_trust%2fDefault.aspx&client-request-id=243e6be9-e8b8-466f-ce8e-00800100008f&RedirectToIdentityProvider=AD+AUTHORITY"
)
for2 = (
    auth
    + "FLNR2%2f_layouts%2f15%2fAuthenticate.aspx%3fSource%3d%252Fsites%252FFLNR2%252F%255Flayouts%252F15%252Fstorman%252Easpx&wreply=https%3a%2f%2fnrm.sp.gov.bc.ca%2f_trust%2fDefault.aspx&client-request-id=d53ecc37-da64-4797-4d43-008001000001&RedirectToIdentityProvider=AD+AUTHORITY"
)
nrm = (
    auth
    + "NRM%2f_layouts%2f15%2fAuthenticate.aspx%3fSource%3d%252Fsites%252FNRM%252F%255Flayouts%252F15%252Fstorman%252Easpx&wreply=https%3a%2f%2fnrm.sp.gov.bc.ca%2f_trust%2fDefault.aspx&client-request-id=ea5d285a-f056-4a04-00bd-0080010400d1&RedirectToIdentityProvider=AD+AUTHORITY"
)
aff = (
    auth
    + "AGRI%2f_layouts%2f15%2fAuthenticate.aspx%3fSource%3d%252Fsites%252FAGRI%252F%255Flayouts%252F15%252Fstorman%252Easpx&wreply=https%3a%2f%2fnrm.sp.gov.bc.ca%2f_trust%2fDefault.aspx&client-request-id=b1599f7c-dce9-440a-5089-0080010000b7&RedirectToIdentityProvider=AD+AUTHORITY"
)
irr = (
    auth
    + "IRR%2f_layouts%2f15%2fAuthenticate.aspx%3fSource%3d%252Fsites%252FIRR%252F%255Flayouts%252F15%252Fstorman%252Easpx&wreply=https%3a%2f%2fnrm.sp.gov.bc.ca%2f_trust%2fDefault.aspx&client-request-id=935d16a0-f66c-466b-f991-0080010400f1&RedirectToIdentityProvider=AD+AUTHORITY"
)
env = (
    auth
    + "ENV%2f_layouts%2f15%2fAuthenticate.aspx%3fSource%3d%252Fsites%252FENV%252F%255Flayouts%252F15%252Fstorman%252Easpx&wreply=https%3a%2f%2fnrm.sp.gov.bc.ca%2f_trust%2fDefault.aspx&client-request-id=15460ce6-01a4-4083-b51d-0080000000bd&RedirectToIdentityProvider=AD+AUTHORITY"
)
eao = (
    auth
    + "EAO%2f_layouts%2f15%2fAuthenticate.aspx%3fSource%3d%252Fsites%252FEAO%252F%255Flayouts%252F15%252Fstorman%252Easpx&wreply=https%3a%2f%2fnrm.sp.gov.bc.ca%2f_trust%2fDefault.aspx&client-request-id=66dc3ac6-7e51-4897-4ce7-008001000030&RedirectToIdentityProvider=AD+AUTHORITY"
)
crts = (
    auth
    + "CRTS%2f_layouts%2f15%2fAuthenticate.aspx%3fSource%3d%252Fsites%252FCRTS%252F%255Flayouts%252F15%252Fstorman%252Easpx&wreply=https%3a%2f%2fnrm.sp.gov.bc.ca%2f_trust%2fDefault.aspx&client-request-id=907d272e-56b2-4116-5a95-0080010400ea&RedirectToIdentityProvider=AD+AUTHORITY"
)
emli = (
    auth
    + "EMPR%2f_layouts%2f15%2fAuthenticate.aspx%3fSource%3d%252Fsites%252FEMPR%252F%255Flayouts%252F15%252Fstorman%252Easpx&wreply=https%3a%2f%2fnrm.sp.gov.bc.ca%2f_trust%2fDefault.aspx&client-request-id=8541b346-e768-452b-4bba-00800100002d&RedirectToIdentityProvider=AD+AUTHORITY"
)
bcws = (
    auth
    + "Wildfire%2f_layouts%2f15%2fAuthenticate.aspx%3fSource%3d%252Fsites%252FWILDFIRE%252F%255Flayouts%252F15%252Fstorman%252Easpx&wreply=https%3a%2f%2fnrm.sp.gov.bc.ca%2f_trust%2fDefault.aspx&client-request-id=ea8dbfe5-a803-4de6-41bd-0080010000c6&RedirectToIdentityProvider=AD+AUTHORITY"
)
irrcs = (
    auth
    + "irrcs%2f_layouts%2f15%2fAuthenticate.aspx%3fSource%3d%252Fsites%252FIRRCS%252F%255Flayouts%252F15%252Fstorman%252Easpx&wreply=https%3a%2f%2fnrm.sp.gov.bc.ca%2f_trust%2fDefault.aspx&client-request-id=303265df-c6b6-434d-feab-0080010400ce&RedirectToIdentityProvider=AD+AUTHORITY"
)
bcts = (
    auth
    + "BCTS%2f_layouts%2f15%2fAuthenticate.aspx%3fSource%3d%252Fsites%252FBCTS%252F%255Flayouts%252F15%252Fstorman%252Easpx&wreply=https%3a%2f%2fnrm.sp.gov.bc.ca%2f_trust%2fDefault.aspx&client-request-id=87d2a718-04fd-43d9-b331-0080010400db&RedirectToIdentityProvider=AD+AUTHORITY"
)

sp_collections = [for1, for2, nrm, aff, irr, env, eao, crts, emli, bcws, irrcs, bcts]

# initialize the Chrome driver
options = webdriver.ChromeOptions()
options.add_experimental_option("excludeSwitches", ["enable-logging"])
options.add_argument("--ignore-certificate-errors")
options.add_argument("--headless")
# driver = webdriver.Chrome(r"chromedriver", options=options)
service_object = Service(binary_path)
driver = webdriver.Chrome(options=options, service=service_object)

################## for testing one site
# go to SharePoint login page
driver.get(for1)
# find username/email field and send the username itself to the input field
driver.find_element(By.ID, "userNameInput").send_keys(username)
# find password input field and insert password as well
driver.find_element(By.ID, "passwordInput").send_keys(password)
# click login button
driver.find_element(By.ID, "submitButton").click()
# get URL of page after login
strUrl = driver.current_url
print("Current Url is:" + strUrl)

# move to next page
while True:
    try:
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "/html/body/form/div[12]/div/div[2]/div[2]/div[3]/table[4]/tbody/tr/td/a",
                )
            )
        ),
        driver.find_element(
            By.XPATH,
            "/html/body/form/div[12]/div/div[2]/div[2]/div[3]/table[4]/tbody/tr/td/a[contains(.,'Next')]",
        ).click()
        print("Navigating to Next Page")
    except:
        print("Last page reached")
        break

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

# find the collection based on the URL
collection = strUrl[31:-36]
# print(collection)

# build pandas dataframe
df = pd.DataFrame.from_dict(columns, orient="index")
df = df.transpose()
df = df.drop(df.columns[[0, 3, 4, 5]], axis=1)
df["Last Modified"] = pd.Series(lm)
df["URL"] = pd.Series(links)
df["Collection"] = pd.Series(collection)

# show the dataframe
print(df)

with pd.ExcelWriter(".\SharePoint_Scrape.xlsx") as writer:
    df.to_excel(writer, sheet_name="FOR", index=False)

# wait for the ready state to be complete
WebDriverWait(driver=driver, timeout=10).until(
    lambda x: x.execute_script("return document.readyState === 'complete'")
)

# DRAFT for looping through each site
# def sp_login():
#    for i in sp_collections:
#        # go to SharePoint login page
#        driver.get(i)
#        # find username/email field and send the username itself to the input field
#        driver.find_element(By.ID, "userNameInput").send_keys(username),
#        # find password input field and insert password as well
#        driver.find_element(By.ID, "passwordInput").send_keys(password),
#        # click login button
#        driver.find_element(By.ID, "submitButton").click(),
#        # wait for the ready state to be complete
#        WebDriverWait(driver=driver, timeout=10).until(
#            lambda x: x.execute_script("return document.readyState === 'complete'")
#        )
#
#
# sp_login()

# Opens a new tab and switches to new tab
# driver.switch_to.new_window('tab')

# close the driver
# driver.close()
