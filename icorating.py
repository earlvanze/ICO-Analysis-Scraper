from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pathlib
import traceback
import shutil
import json
import glob
import re
from pprint import pprint
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from functions import *

chrome_options = Options()
chrome_options.add_experimental_option('useAutomationExtension', False)
#browser = webdriver.Chrome('./chromedriver')
browser = webdriver.Chrome('./chromedriver.exe', options=chrome_options, desired_capabilities=chrome_options.to_capabilities())

# Google Sheets stuff

# You should change these to match your own spreadsheet
GSHEET_ID = '1GaBugNpNK-_4YI8hVc1JV-jrgWDXLbCYddXPlTjEcRA'
RANGE_NAME = 'ICORating Analysis!A:X'
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]

delay = 30

ICOS_FOLDER = "icorating"


# Get all ICOs from ICORating
def get_icorating_list():
    ico_list = []
    browser.get('https://icorating.com/ico/all')
    # Clicks the "Show more..." button a bunch of times, and waits for more ICOs to load before clicking again
    try:
        while(WebDriverWait(browser, delay).until(EC.presence_of_element_located((By.CLASS_NAME, "c-show-more")))):
    #    for i in range(0,100):
            # As long as ... ellipses are shown, wait for more ICOs to load before clicking again
            if not WebDriverWait(browser, delay).until(EC.presence_of_element_located((By.CLASS_NAME, "c-show-more"))):
                print("'Show more' button no longer present")
                break

            # Exception raised when Show more button is not clickable
            try:
                while (not browser.find_element_by_class_name('c-ellipsis-loading').is_displayed()):
                    WebDriverWait(browser, delay).until(EC.presence_of_element_located((By.CLASS_NAME, "c-show-more"))).click()
            except:
    #            traceback.print_exc()
                continue   # Show more button fails to click, try again
    except:
        traceback.print_exc()
        print("exited show more loop")
        pass

    # Everything has loaded, now save each row into a dictionary and save all dictionaries to a list
    ico_table = WebDriverWait(browser, delay).until(EC.presence_of_element_located((By.CLASS_NAME, 'c-table__body')))
    ico_rows = ico_table.find_elements_by_tag_name('tr')
    print(str(len(ico_rows)), "rows found")
    try:
        for ico in ico_rows:
            data = {}
            url = ico.find_element_by_tag_name('a').get_attribute('href')
            html = ico.get_attribute('outerHTML')
            row = BeautifulSoup(html, 'html.parser').text.strip()
            row = re.sub(' +', ' ', row).split("\n")
            data["Name"] = row[0]
            data["URL"] = url
            data["Status"] = row[2].strip()
            data["Hype score"] = row[4].strip()
            data["Risk score"] = row[6].strip()
            data["Rating"] = row[7].strip("NA ")
            if data["Rating"] == "Vote for...":
                data["Rating"] = row[6].strip("NA ")
            print(row)
            try:
                raised_percent = row[-1].strip('$ %').split()
                data["Raised"] = raised_percent[0]
                try:
                    data["Percent"] = float(raised_percent[1])/100
                except IndexError:
                    data["Percent"] = "NA"
                    traceback.print_exc()
                    continue
        #            print(raised_percent)
            except:
                data["Raised"] = str(row)
                traceback.print_exc()
                continue
            finally:
                json_str = json.dumps(data)
    #            print(json_str)
                ico_list.append(json_str)
    except:
        traceback.print_exc()
        pass

    print("saving file...")
    # save all rows to a file
    with open("icorating_list.txt", 'w+') as file:
        for ico in ico_list:
            print(ico)
            file.write("%s\n" % ico)

def get_icorating_info(icos_folder = ICOS_FOLDER):
    ico_list = []
    # Prepare list of lists from list of dictionaries, then upload to Google Sheet
    with open("icorating_list.txt", 'r') as file:
        lines = file.readlines()

        output_data = [[None] * 24 for i in range(len(lines))]

        for i in range(len(lines)):
#        for i in range(5):
            json_repr = lines[i]
            data = json.loads(json_repr)

            browser.get(data["URL"])
            ico_link = '=HYPERLINK("{0}","{1}")'.format(data["URL"], data["Name"])

            try:
                # Token Sale Table
                info_table = WebDriverWait(browser, delay).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'c-info-table')))
                info_table_rows = info_table.find_elements_by_tag_name('tr')
                #            print(str(len(info_table_rows)), "rows found")
                for row in info_table_rows:
                    text = BeautifulSoup(row.get_attribute('outerHTML'), 'html.parser').text.split()
                    text = " ".join(text)
                    if "token supply" in text:
                        data["Token supply"] = text.split()[-1]
                    elif "Soft cap" in text:
                        data["Soft cap"] = " ".join(text.split()[2:])
                    elif "Hard cap size" in text:
                        data["Hard cap"] = " ".join(text.split()[3:])
                    else:
                        print(text)
            except:
                traceback.print_exc()
                pass

            try:
                # Trading Data
                trading_data = browser.find_elements_by_class_name('pt0')
                for item in trading_data:
                    text = BeautifulSoup(item.get_attribute('outerHTML'), 'html.parser').text.split()
                    text = " ".join(text)
                    if "$" in text:
                        data["Trading price"] = text.split()[0].strip('$')
                    elif "return" in text:
                        data["ETH ROI"] = text.split()[-1].strip('x')
                    else:
                        print(text)
            except:
#                traceback.print_exc()
                pass

            try:
                # Summary Table
                card_info_table = WebDriverWait(browser, delay).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'c-card-info__table')))
                card_info_rows = card_info_table.find_elements_by_tag_name('tr')
                #            print(str(len(card_info_rows)), "rows found")
                for row in card_info_rows:
                    text = BeautifulSoup(row.get_attribute('outerHTML'), 'html.parser').text.split()
                    text = " ".join(text)
                    if "Start ICO" in text:
                        data["ICO start"] = " ".join(text.split()[2:])
                    elif "End ICO" in text:
                        data["ICO end"] = " ".join(text.split()[2:])
                        data["Type"] = "Utility"
                    elif "Start STO" in text:
                        data["ICO start"] = " ".join(text.split()[2:])
                    elif "End STO" in text:
                        data["ICO end"] = " ".join(text.split()[2:])
                        data["Type"] = "STO"
                    elif "Price" in text:
                        data["Price"] = text.split("=")[1].strip(" USD")
                    elif "MVP" in text:
                        data["MVP"] = " ".join(text.split()[1:]).strip()
                    elif "Token" in text:
                        data["Token"] = " ".join(text.split()[1:])
                    elif "Product Type" in text:
                        data["Product type"] = " ".join(text.split()[2:])
                    elif "Registration Country" in text:
                        data["Country"] = " ".join(text.split()[2:])
                    elif "KYC" in text:
                        data["KYC"] = " ".join(text.split()[1:])
                    elif "Whitepaper" in text:
                        data["Whitepaper"] = "Yes"
                    elif "Country Limitations" in text:
                        data["Restrictions"] = " ".join(text.split()[2:])
                    else:
                        print(text)
            except:
                traceback.print_exc()
                pass

            print(data)

            # Save data to JSON file
            out_json = "%s.json" % data["Name"].replace('/', '-').replace('>', '-').replace('<', '-')
            with open("{0}/{1}".format(icos_folder, out_json), 'w+') as outfile:
                outfile.write(json.dumps(data))

            # Parse JSON and append to Google Sheet
            parse_icorating_json(out_json)


def parse_icorating_json(out_json = "", icos_folder = ICOS_FOLDER):
    filenames = []
    if not out_json:
        # Parse the json files saved in icos_folder and returns 2D array of properties
        for filename in glob.iglob('{}/*.json'.format(icos_folder)):
             filenames.append(filename)
    else:
        filenames.append('{0}/{1}'.format(icos_folder, out_json))
    print(filenames)
    output_data = [[None] * 24 for i in range(len(filenames))]

    for i in range(len(filenames)):
        with open(filenames[i], 'r') as file:
            json_repr = file.read()
            data = json.loads(json_repr)

            # Save data to output table
            try:
                output_data[i][0] = DictQuery(data).get("Name").split('(')[0].strip()
                output_data[i][1] = DictQuery(data).get("Status")
                output_data[i][2] = DictQuery(data).get("Hype score")
                output_data[i][3] = DictQuery(data).get("Risk score")
                output_data[i][4] = DictQuery(data).get("Rating")
                output_data[i][5] = DictQuery(data).get("Raised")
                output_data[i][6] = DictQuery(data).get("Percent")
                output_data[i][7] = DictQuery(data).get("URL")
                output_data[i][8] = DictQuery(data).get("Token")
                output_data[i][9] = DictQuery(data).get("Soft cap")
                output_data[i][10] = DictQuery(data).get("Hard cap")
                output_data[i][11] = DictQuery(data).get("Token supply")
                output_data[i][12] = DictQuery(data).get("Trading price")
                output_data[i][13] = DictQuery(data).get("ETH ROI")
                output_data[i][14] = DictQuery(data).get("ICO start")
                output_data[i][15] = DictQuery(data).get("ICO end")
                output_data[i][16] = DictQuery(data).get("Type")
                output_data[i][17] = DictQuery(data).get("Product type")
                output_data[i][18] = DictQuery(data).get("Price")
                output_data[i][19] = DictQuery(data).get("MVP")
                output_data[i][20] = DictQuery(data).get("Whitepaper")
                output_data[i][21] = DictQuery(data).get("Country")
                output_data[i][22] = DictQuery(data).get("Restrictions")
                output_data[i][23] = DictQuery(data).get("KYC")
            except:
                traceback.print_exc()
                pass

            result = append_to_gsheet(output_data, GSHEET_ID, RANGE_NAME)
            print(result)


def main(gsheet_id = GSHEET_ID, range_name = RANGE_NAME):
# ICORating.com scraping
    try:
        pathlib.Path(ICOS_FOLDER).mkdir(exist_ok=True)  # create temporary ICOs folder if nonexistent
#        get_icorating_data()
#        get_icorating_info()
        result = parse_icorating_json()
#        empty_folder()
        return result
        browser.quit()
    except:
        tb = traceback.format_exc()
        return tb

if __name__ == "__main__":
    main()