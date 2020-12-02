# -*- coding: utf-8 -*-
"""
Created on Mon Nov 30 21:37:25 2020

@author: andre_000
"""

############################################################################
# Processing of fitbit sleep exports: Reformatting, Visualizing, Statistics#
# Date: 2020 July                                                          #
# Author: Andreas Baumer - baumer.andreas@gmx.ch                           #
############################################################################

import json
import pandas as pd
import os
from pathlib import Path
from datetime import datetime


export_empty_timestamps = True


# This whole thing is a preliminary version
# Correct directory setting before running the code.
# Set the directory to the same folder as the patient exports.
base_cwd = "C:\\Users\\andre_000\\Desktop\\Projects\\Fitbit\\fitbit"

os.chdir(os.path.join(base_cwd, "export-patients", "heart-rate"))

Path(os.path.join(base_cwd, "Heart-Rate")).mkdir(parents=True, exist_ok=True)
Path(os.path.join(base_cwd, "Heart-Rate", "Heart-Rate_Exports")).mkdir(parents=True, exist_ok=True)


# This takes every  File in the folder.
folders = os.listdir()



for folder in folders:
    os.chdir(os.path.join(base_cwd, "export-patients", "heart-rate", folder))
    filenames = os.listdir()
    comb_df = pd.DataFrame(columns= ["Datetime", "Heart-Rate"])
    for file in filenames:
        with open(file) as f:
            day_file = json.loads(f.read())
            heart_rate_values = [time['value'] for time in day_file["activities-heart-intraday"]["dataset"]]
            timestamps = [time['time'] for time in day_file["activities-heart-intraday"]["dataset"]]
            date_time = [day_file["activities-heart"][0]['dateTime'] + " " + t for t in timestamps]
            date_time_dt = [datetime.strptime(t, '%Y-%m-%d %H:%M:%S') for t in date_time]
            
            day_dict = {'Datetime': date_time_dt, 'Heart-Rate': heart_rate_values}
            day_df = pd.DataFrame(day_dict)
            comb_df = pd.concat([comb_df, day_df])
            
    if export_empty_timestamps==True:
        minutes_range = pd.date_range(start=comb_df.iloc[0,0], end=comb_df.iloc[-1,0], freq='1min')
        comb_df = comb_df.set_index('Datetime').reindex(minutes_range).rename_axis('Datetime').reset_index()

    comb_df.to_csv(os.path.join(base_cwd, 'Heart-Rate', 'Heart-Rate_Exports', 'Heartrate_Export_' + folder + '.csv'), index = False)
    comb_df.to_excel(os.path.join(base_cwd, 'Heart-Rate', 'Heart-Rate_Exports','Heartrate_Export_' + folder + '.xlsx'), index = False)
