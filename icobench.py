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
RANGE_NAME = 'ICOBench Analysis!A:CT'
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]

delay = 30

ICOS_FOLDER = "icobench"


# Get all links to ICOs on ICOBench
def get_ico_links():
    urls = []
    for i in range(1,446):
        browser.get('https://icobench.com/icos?page={0}'.format(i))

        icos = WebDriverWait(browser, delay).until(EC.presence_of_all_elements_located((By.TAG_NAME, "a")))
        for ico in icos:
            if ("/ico/" in ico.get_attribute('href')):
                print(ico.get_attribute('href'))
                urls.append(ico.get_attribute('href'))

        # save all unique links to a file
        urls = set(urls)
        with open("ico_list.txt", 'a+') as file:
            for url in urls:
                file.write("%s\n" % url)

# Takes in a file name containing a list of ICO Analysis Scraper links to ICOs and outputs a dictionary
def get_ico_info(icos_folder = ICOS_FOLDER):
    # open each link and pull data
    with open("ico_list.txt", 'r') as file:
        for line in file.readlines():
            browser.get(line + '/ratings')
            data = {}

            # ICO Name and URL
            try:
                ico_name_html = browser.find_element_by_class_name('ico_information').find_element_by_class_name(
                    'row').find_element_by_class_name('name').find_element_by_tag_name('h1').get_attribute('outerHTML')
                name = BeautifulSoup(ico_name_html, 'html.parser').text.lstrip('Ratings ')
                data["Name"] = name
                data["URL"] = line
            except:
                traceback.print_exc()
                pass

            # Financial Data
            try:
                financial_data = browser.find_element_by_class_name('financial_data').find_elements_by_class_name('data_row')
                for row in financial_data:
                    attrs = []
                    for elem in row.find_elements_by_class_name('col_2'):
                        html = elem.get_attribute('outerHTML')
                        attrs.append(BeautifulSoup(html, 'html.parser').text.strip())
                    for i in range(0, len(attrs), 2):
                        data[attrs[i]] = attrs[i + 1]
            except:
                traceback.print_exc()
                pass

            # Overall Ratings
            try:
                rating = browser.find_element_by_class_name('rating')
                attrs = []
                rate_html = rating.find_element_by_class_name('rate').get_attribute('outerHTML')
                rate = BeautifulSoup(rate_html, 'html.parser').text.strip()
                data["Rate"] = rate

                num_ratings_html = rating.find_element_by_tag_name('small').get_attribute('outerHTML')
                num_ratings = BeautifulSoup(num_ratings_html, 'html.parser').text.split()[0]
                data["Expert Ratings"] = num_ratings

                for elem in rating.find_elements_by_class_name('col_4'):
                    html = elem.get_attribute('outerHTML')
                    attrs.append(BeautifulSoup(html, 'html.parser').text.strip())
                    for i in range(0, len(attrs)):
                        attr = attrs[i].split('\n\t\t\t\t\t\t\t\t\t\t')
                        data[attr[1]] = attr[0].strip('-')
            except:
                traceback.print_exc()
                pass

            # Expert Ratings
            try:
                ratings_list = browser.find_element_by_class_name('ratings_list').find_elements_by_class_name('row')
                for i in range(0, len(ratings_list)-1):
                    attrs = []
                    row = ratings_list[i]
                    for elem in row.find_elements_by_class_name('rate'):
                        html = elem.get_attribute('outerHTML')
                        attrs = BeautifulSoup(html, 'html.parser').text.split()
                    for j in range(0, len(attrs)):
                        value = attrs[j][0]
                        key = "Expert {0} {1}".format(str(i+1), attrs[j][1:])
                        data[key] = value

                    # Expert Rating Weight
                    html = row.find_element_by_class_name('distribution').get_attribute('outerHTML')
                    weight = float(BeautifulSoup(html, 'html.parser').text.strip().split('%')[0])/100
                    data["Expert {0} Weight".format(str(i + 1))] = weight
            except:
                traceback.print_exc()
                pass

            #Benchy Bot Weight
            try:
                html = ratings_list[len(ratings_list)-1].find_element_by_class_name('distribution').get_attribute('outerHTML')
                weight = float(BeautifulSoup(html, 'html.parser').text.strip().split('%')[0]) / 100
                data["Benchy Weight"] = weight
            except:
                traceback.print_exc()
                pass

            # ICO Status
            try:
                ico_status_html = browser.find_element_by_class_name('financial_data').find_element_by_class_name(
                    'col_2').find_element_by_class_name('number').get_attribute('outerHTML')
                status = BeautifulSoup(ico_status_html, 'html.parser').text.strip()
                data["Status"] = status
            except:
                traceback.print_exc()
                pass

            # ICO Time
            try:
                ico_time_html = browser.find_element_by_class_name('financial_data').find_element_by_class_name(
                    'col_2').find_element_by_tag_name('small').get_attribute('outerHTML')
                ico_start = BeautifulSoup(ico_time_html, 'html.parser').text.split(' - ')[0]
                ico_end = BeautifulSoup(ico_time_html, 'html.parser').text.split(' - ')[1]
                data["ICO start"] = ico_start
                data["ICO end"] = ico_end
            except:
                traceback.print_exc()
                pass

            # Amount Raised
            try:
                raised_html = browser.find_element_by_class_name('raised').get_attribute('outerHTML')
                data["Raised"] = BeautifulSoup(raised_html, 'html.parser').text.strip('~')
            except:
                data["Raised"] = "N/A"
                pass

#                pprint(data)

            # Save data to JSON file
            out_json = "%s.json" % data["Name"]
            with open("{0}/{1}".format(icos_folder,out_json), 'w+') as outfile:
                outfile.write(json.dumps(data))

            # Parse JSON and append to Google Sheet
            parse_json(out_json)


def parse_json(out_json = "", icos_folder = ICOS_FOLDER):
    filenames = []
    if not out_json:
        # Parse the json files saved in icos_folder and returns 2D array of properties
        for filename in glob.iglob('{}/*.json'.format(icos_folder)):
             filenames.append(filename)
    else:
        filenames.append('{0}/{1}'.format(icos_folder, out_json))

    output_data = [[None] * 98 for i in range(len(filenames))]

    for i in range(len(filenames)):
        with open(filenames[i], 'r') as file:
            json_repr = file.read()
            data = json.loads(json_repr)
            ico_link = '=HYPERLINK("{0}","{1}")'.format(data["URL"], data["Name"])
            try:
                output_data[i][0] = ico_link
                output_data[i][1] = DictQuery(data).get("Token")
                output_data[i][2] = DictQuery(data).get("Type")
                output_data[i][3] = DictQuery(data).get("Status")
                output_data[i][4] = DictQuery(data).get("ICO start")
                output_data[i][5] = DictQuery(data).get("ICO end")
                output_data[i][6] = DictQuery(data).get("Raised")
                output_data[i][7] = DictQuery(data).get("Price")
                output_data[i][8] = DictQuery(data).get("Bonus")
                output_data[i][9] = DictQuery(data).get("Bounty")
                output_data[i][10] = DictQuery(data).get("MVP/Prototype")
                output_data[i][11] = DictQuery(data).get("Platform")
                output_data[i][12] = DictQuery(data).get("Accepting")
                output_data[i][13] = DictQuery(data).get("Minimum investment")
                output_data[i][14] = DictQuery(data).get("Soft cap")
                output_data[i][15] = DictQuery(data).get("Hard cap")
                output_data[i][16] = DictQuery(data).get("Country")
                output_data[i][17] = DictQuery(data).get("Whitelist/KYC")
                output_data[i][18] = DictQuery(data).get("Restricted areas")
                output_data[i][19] = DictQuery(data).get("Rate")
                output_data[i][20] = DictQuery(data).get("ICO Profile")
                output_data[i][21] = DictQuery(data).get("Benchy Weight")
                output_data[i][22] = DictQuery(data).get("Team")
                output_data[i][23] = DictQuery(data).get("Vision")
                output_data[i][24] = DictQuery(data).get("Product")
                output_data[i][25] = int(DictQuery(data).get("Expert Ratings"))
                for j in range(1, output_data[i][25]+1):
                    output_data[i][26 + 1*j] = DictQuery(data).get("Expert {0} Team".format(str(j)))
                    output_data[i][27 + 2*j] = DictQuery(data).get("Expert {0} Vision".format(str(j)))
                    output_data[i][28 + 3*j] = DictQuery(data).get("Expert {0} Product".format(str(j)))
                    output_data[i][29 + 4*j] = DictQuery(data).get("Expert {0} Weight".format(str(j)))
            except:
                traceback.print_exc()
                pass
            result = append_to_gsheet(output_data, GSHEET_ID, RANGE_NAME)
            print(result)



def main(gsheet_id = GSHEET_ID, range_name = RANGE_NAME):
# ICO Analysis Scraper.com scraping
    try:
        pathlib.Path(ICOS_FOLDER).mkdir(exist_ok=True)  # create temporary ICOs folder if nonexistent
#        get_ico_links()
        get_ico_info()
        result = parse_json()
#        empty_folder()
        return result
        browser.quit()
    except:
        tb = traceback.format_exc()
        return tb

if __name__ == "__main__":
    main()