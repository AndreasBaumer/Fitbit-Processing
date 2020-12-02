##########################################################################
# Retrieval of Sleep Related Data from Fitbit accounts of multiple users #
# Date: 2020 May                                                         #
# Author: Jozef Jarosciak - jozef@jarosciak.com / https://joe0.com       #
# Licensing: MIT license: https://choosealicense.com/licenses/mit/       #
##########################################################################

import json
import requests
import os
import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.abspath("__file__"))
DRIVER_BIN = os.path.join(PROJECT_ROOT, "chromedriver.exe")
os.chdir("C:\\Users\\andre_000\\Desktop\\Projects\\Fitbit\\fitbit")
cwd = os.getcwd()
options = webdriver.ChromeOptions()
options.add_argument("headless")

# This determins if you export heart-rate data as well.
# WARNING: This sends a separate request to the API for every day between the
# start and end date. The limit per patient is 150 requests per hour.
# If the start and end date are more than 5 months apart, run the export code 
# multiple times with subsets of the total timeframe
get_heart_rate_data = True

# Initialize Variables
count = 0
number_of_patients = 0
delay = 30  # seconds

# Process Patients specified in the list-of-patients.json file
with open('list-of-patients.json') as json_file:
    patient_data = json.load(json_file)
    number_of_patients = str(len(patient_data['patients']))
    for patient in patient_data['patients']:
        count = count + 1

        print('Processing Patient ' + str(count) + ' of ' + number_of_patients + ' - ' + patient['First Name'] + " " +
              patient['Last Name'])

        # Get Patient's Login Name and Password from the patients.json file
        usernameStr = patient['Login Name']
        passwordStr = patient['Password']
        # Get Patient's start and end date ranges
        startDate = patient['Start Date']
        endDate = patient['End Date']

        #browser = webdriver.Chrome("chromedriver.exe") # VISIBLE BROWSER
        browser = webdriver.Chrome("chromedriver.exe", options=options)  # HIDDEN BROWSER
        # First log off the current patient from fitbit
        browser.get('https://www.fitbit.com/logout')
        # Go to Fitbit login screen
        browser.get('https://accounts.fitbit.com/login')

        try:
            myElem = WebDriverWait(browser, delay).until(EC.presence_of_element_located((By.ID, 'ember652')))
        except TimeoutException:
            print("Unable to Login to Fitbit")
            exit(0)

        # DELETE ME
        #usernameStr = 'joeykossowsky@gmail.com'
        #passwordStr = 'fovJah-muzku5-dogtet'
        # Login as current User on fitbit website
        username = browser.find_element_by_id('ember651')
        password = browser.find_element_by_id('ember652')
        username.send_keys(usernameStr)
        password.send_keys(passwordStr)
        signInButton = browser.find_element_by_id('ember692')
        signInButton.click()
        
        

        try:
            myElem = WebDriverWait(browser, delay).until(EC.presence_of_element_located((By.ID, 'container')))
        except TimeoutException:
            pass

        # Extract OAuth Access Token from the Fitbit website
        cookies_list = browser.get_cookies()
        for cookie in cookies_list:
            if cookie['name'] == "oauth_access_token":
                oauth_access_token = cookie['value']
                break

        # Get Sleep Data JSON Files
        response = requests.get("https://api.fitbit.com/1.2/user/-/sleep/date/" + startDate + "/" + endDate + ".json",
                                headers={"Authorization": "Bearer " + oauth_access_token})


        Path(os.path.join(cwd, 'export-patients')).mkdir(parents = True, exist_ok = True)

        # Save files into export-patients folder
        saveToFile = os.path.join(cwd, "export-patients", patient['First Name'] + "-" + patient[
            'Last Name'] + "__" + startDate + "-to-" + endDate + ".json")
        mydata = json.loads(json.dumps(response.json()))

        DataFile = open(saveToFile, "w")
        DataFile.write(response.text)
        DataFile.close()
        
        if get_heart_rate_data == True:
            # Get heart-rate Data JSON Files
            # Make directories
            Path(os.path.join(cwd, 'export-patients')).mkdir(parents = True, exist_ok = True)
            Path(os.path.join(cwd, 'export-patients', 'heart-rate')).mkdir(parents = True, exist_ok = True)
            Path(os.path.join(cwd, 'export-patients', 'heart-rate', str(patient['Last Name'] + "-" + str(patient['First Name'])))).mkdir(parents = True, exist_ok = True)
            
            # Generate all the dates between start and end
            all_days = pd.date_range(startDate, endDate, freq='d')
            all_days = [str(d)[:10] for d in all_days]
            # Send an API request for each day
            for day in all_days:
                response = requests.get("https://api.fitbit.com/1/user/-/activities/heart/date/" + str(day) + "/1d/1min/time/00:00/23:59.json",
                                       headers={"Authorization": "Bearer " + oauth_access_token})
                
        
                # Save the file for every day into the patients folder
                saveToFile = os.path.join(cwd, "export-patients", 'heart-rate', str(patient['Last Name']), patient['First Name'] + "-" + patient[
                    'Last Name'] + str(day) + ".json")
                mydata = json.loads(json.dumps(response.json()))
        
                DataFile = open(saveToFile, "w")
                DataFile.write(response.text)
                DataFile.close()
# Finish program
print("Processing of all patients completed!")
