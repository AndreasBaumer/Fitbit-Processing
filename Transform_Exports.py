############################################################################
# Processing of fitbit sleep exports: Reformatting, Visualizing, Statistics#
# Date: 2020 July                                                          #
# Author: Andreas Baumer - baumer.andreas@gmx.ch                           #
############################################################################

import json
import pandas as pd
import os
import matplotlib.pyplot as plt
from collections import Counter
from pathlib import Path
from matplotlib import colors
import matplotlib.patches as mpatches

# This whole thing is a preliminary version
# Correct directory setting before running the code.
# Set the directory to the same folder as the patient exports.
os.chdir("C:\\Users\\andre_000\\Desktop\\Projects\\Fitbit\\fitbit\\export-patients")
cwd = os.getcwd()

# This takes every  File in the folder.
filenames = os.listdir()
for item in filenames:
    if not item.endswith(".json"):
        filenames.remove(item)
# This takes just those specified here
# filenames = ['Joe-Kossowsky__2020-05-06-to-2020-05-12.json','Camila-Koike__2020-05-08-to-2020-05-14.json']

# Establish a counter for how many files have been processed. This is used to print progress statements
n_patient = 1

# Creating an array where the percentage of missing data and stage data for every patient is stored.
# This is reported at the very end.
total_stages_missing = []
total_missing = []

# Create a Pandas DF to collect whole sample summary stats
whole_sample_df = pd.DataFrame()


for filename in filenames:
    print('Processing Patient ' + str(n_patient) + ' out of ' + str(len(filenames)))
    patientname = filename.partition('_')[0]
    # Read in the JSON file. It should work with both exports.
    with open(Path(filename)) as f:
        sleep_sample = json.loads(f.read())
    
    # Save how many nights of sleep we look at
    n_nights = len(sleep_sample['sleep'])
    
    # Record how many nights don't have sleep stage data
    stages_missing = 0
    
    # Make a list that will be filled with the longform sleep recordings of all nights
    df_list = list()
    
    
    ######  TRANSFORMING DATA TO LONG FORMAT  ######
    
    
    # This loop turns every recording into long form and adds everything into a single list.
    for i in range(n_nights):
        # Establish the time references in 30 second intervals from beginning to end
        time_template = pd.date_range(sleep_sample['sleep'][i]['startTime'],sleep_sample['sleep'][i]['endTime'], freq='30S')
        # Create an array of the same length, that will be filled with the sleep stages later
        sleep_template = [None] * len(time_template)
        
        # If there are no stages add 1 to the stages missing
        if 'asleep' in sleep_sample['sleep'][i]['levels']['summary']:
            stages_missing += 1
        # This counter marks the start of the sleep segment
        counter = 0
        
        # This loop takes each of the short form entries in the JSON and turns them into the long form.
        for k in sleep_sample['sleep'][i]['levels']['data']:
            # Time is measured in 30 second ticks. How many ticks does this segment last?
            duration = round(k['seconds']/30)
            # Fill the sleep stage array with the value (sleep stage) for that particular segment
            # Start at the counter and continue for the number of 30 second ticks this segment lasts.
            sleep_template[counter:counter+duration] = [k['level']] * duration
            # Increase the counter by however many entries you've made
            counter = counter + duration
        
        # There is something weird about the recording files. Sometimes the specified endTime does not
        # correspond perfectly with the recorded data. The endTime is 30 seconds or more later than the recording ends.
        # I just cut off all entries at the end of my arrays that don't have any recorded that don't have data. The time is removed too.
        while sleep_template[-1] is None:
            sleep_template.pop()
            time_template = time_template[:-1]   
        
        # Create a pandas data frame by combining the time references with the long form sleep stages. Add everything into the big list.
        df = pd.DataFrame()
        df['Time'] = time_template
        df['Stage'] = sleep_template
        df_list.insert(0, df)
    
    # Turn the big list into a pandas data frame and reset the messed up indexes.
    df_complete = pd.concat(df_list)
    df_complete = df_complete.reset_index(drop = True)
    
    # This creates a new folder for the Longform Data, so it doesn't get put between the patient exports.
    Path(os.path.join(os.path.dirname(cwd), 'Longform Data')).mkdir(parents = True, exist_ok = True)

    # Export it into a csv and an excel file. Simply throws it into the working directory specified at the top.
    # The excel file had some slight problems displaying the time for me.
    # Double clicking on one of the Time cells directly solved it for me.
    df_complete.to_csv(os.path.join(os.path.dirname(cwd), 'Longform Data', 'Data Longform ' + patientname + '.csv'), index = False)
    df_complete.to_excel(os.path.join(os.path.dirname(cwd), 'Longform Data', 'Data Longform ' + patientname + '.xlsx'), index = False)


    # The next part calculates the missing nights, and the nights where stage data is unavailable
    # Get the difference between the first and last recording.    
    total_days = (pd.to_datetime(sleep_sample['sleep'][0]['dateOfSleep']) - pd.to_datetime(sleep_sample['sleep'][-1]['dateOfSleep'])).days
    missing_days = total_days - n_nights

    
    # Add the percentage of nights with missing stages for this patient to the total.
    # This is used at the very end to report a sample average.
    total_stages_missing.append(stages_missing/total_days * 100)
    total_missing.append(missing_days/total_days * 100)
    
    
    
    # Calculate how many nights haven't been recorded and for how many sleep stage data is unavailable
    print(patientname + ': Data is missing completely for ' + str(round(missing_days/total_days * 100, 1)) + ' % of all nights (' + str(missing_days) + ')')
    print(patientname + ': Sleep stage data is unavailable for ' + str(round(stages_missing/total_days * 100, 1)) + '% of all nights (' + str(stages_missing) + ')')
    print(patientname + ': Sleep stage data is available for ' + str(round((n_nights - stages_missing)/total_days * 100, 1)) + '% of all nights (' + str(total_days - stages_missing - missing_days) + ')')
    
    
    
  


    ######  SUMMARY STATISTICS  ######
    
    # The next part produces summary statistics and produces and excel worksheet with them.
    # I'm certain this could be done better with a loop. I will probably revisit this at a later point.
    # Setting up empty lists which will be filled with the values for each night.
    # They are gonna be the columns for the summary statistcs table, while each night is a row.
    dos = list()
    efficiency = list()
    tib = list()
    deep = list()
    light = list()
    rem = list()
    wake = list()
    
    # For every night in the data add the summary statistics into the lists we set up.
    # Because of the one weird night in Joe's data, this always checks if that category is present.
    # If it isn't I fill in a [None] to make sure the lengths stay equal.
    for night in sleep_sample['sleep']:
        dos = dos + [night['dateOfSleep']]
        tib = tib + [night['timeInBed']]
        efficiency = efficiency + [night['efficiency']]
        if 'deep' in night['levels']['summary']:
            deep = deep + [night['levels']['summary']['deep']['minutes']]
        else:
            deep = deep + [None]
        if 'light' in night['levels']['summary']:
            light = light + [night['levels']['summary']['light']['minutes']]
        else:
            light = light + [None]
        if 'rem' in night['levels']['summary']:
            rem = rem + [night['levels']['summary']['rem']['minutes']]
        else:
            rem = rem + [None]
        if 'wake' in night['levels']['summary']:
            wake = wake + [night['levels']['summary']['wake']['minutes']]
        else:
            wake = wake + [None]
    
    # This is probably a convoluted way to do this but because the [None] 
    # don't work with zip(), they are replaced by a 0
    light_0 = [0 if x is None else x for x in light]
    deep_0 = [0 if x is None else x for x in deep]
    rem_0 = [0 if x is None else x for x in rem]
    
    # Get the total amount of recorded sleeping data, so we can calculate the relative percentages of each sleep stage.
    total_stage = [0 if x is None else sum(x) for x in zip(light_0, deep_0, rem_0)]
    
    # Calculate the percentages for each sleep stage. Avoid division by 0
    light_per = [None if x == 0 else round(x/y*100, 1) for x, y in zip(light_0, total_stage)]
    deep_per = [None if x == 0 else round(x/y*100, 1) for x, y in zip(deep_0, total_stage)]
    rem_per = [None if x == 0 else round(x/y*100, 1) for x, y in zip(rem_0, total_stage)]
    
    # Add each statistic we want as a column to a pandas Dataframe. 
    # A loop might be a cleaner way to do this.
    df_summary = pd.DataFrame()
    df_summary['Date of Sleep'] = dos
    df_summary['Time in Bed'] = tib
    df_summary['Sleep Efficiency'] = efficiency
    df_summary['Minutes in Light Sleep'] = light
    df_summary['Minutes in REM Sleep'] = rem
    df_summary['Minutes in Deep Sleep'] = deep
    df_summary['Percentage Light Sleep'] = light_per
    df_summary['Percentage REM Sleep'] = rem_per
    df_summary['Percentage Deep Sleep'] = deep_per
    df_summary['Minutes awake'] = wake
    
    
    # Calculating averages and adding in floats seems to make the whole dataframe be float64
    # To avoid displaying things like 418.000000000 this makes sure there are no decimals shown.
    pd.options.display.float_format = '{:,.0f}'.format
    
    # Get the average value for each column. 'Date of Sleep' produces a NaN here.
    # 'Date of Sleep' is intended to be the Index but if it already is the index before this step,
    # it is forced out of it and a new index created.
    mean_row = round(df_summary.mean(), 1)
    
    # In order to add that row to the end of the dataframe it needs a name.
    mean_row.name = patientname

    # Add the row with averages to the end. Date of Sleep now has the average value NaN
    df_summary = df_summary.append(mean_row)
    
    # Add the number of fully recorded nights to the Series with average values
    # This resets the name, so it's added again, so the next append call works.
    n_valid_nights = pd.Series(n_nights - stages_missing, index = ['Correctly Recorded Nights'])
    mean_row = mean_row.append(n_valid_nights)
    mean_row.name = patientname
    
    # Add the row with mean values to the dataframe with the average values for the whole sample
    whole_sample_df = whole_sample_df.append(mean_row)
    
    # Replace that NaN with 'Average Value'
    df_summary.at[patientname, 'Date of Sleep'] = 'Average Value'
    
    # Make Date of Sleep the Index. Now the nights are the Index and the row with Averages is indexed as 'Average Value'
    df_summary = df_summary.set_index('Date of Sleep')
    
    # Create a folder for the summaries
    Path(os.path.join(os.path.dirname(cwd), 'Summary Statistics')).mkdir(parents = True, exist_ok = True)

    # Export the summary table into the working dirctory. I will do something about using a different target directory later.
    df_summary.to_csv(os.path.join(os.path.dirname(cwd), 'Summary Statistics', 'Summary Statistics ' + patientname + '.csv'), index = True)
    df_summary.to_excel(os.path.join(os.path.dirname(cwd), 'Summary Statistics', 'Summary Statistics ' + patientname + '.xlsx'), index = True)
    
    
    
    ######  VISUALIZATIONS  ######

    # Create a folder for visualizations
    Path(os.path.join(os.path.dirname(cwd), 'Visualizations')).mkdir(parents = True, exist_ok = True)

    # The next part creates a rudementary pie chart showing the proportions of the different sleep phases over all.
    # This gets the counts for the different sleep stages over all nights
    counts = Counter(df_complete['Stage'])
    # This removes any of the replacement recordings if no sleep stages are recorded
    counts.pop('awake', None)
    counts.pop('asleep', None)
    counts.pop('restless', None)
    pieCounts_s = sorted(counts.values(), reverse = True)
    pieLabels_s = sorted(counts, key=counts.get, reverse = True)
    
    # This creates a mediocre pie chart. The values Asleep, Awake and Restless are weird.
    # They only show up on night 4 (2020-05-09) in Joe's data and replace the other sleep stages.
    # Looks very weird, and I don't understand that part. I'm just gonna leave it like this for now,
    # until we discuss how we wanna deal with it.
    figureObject, axesObject = plt.subplots()
    axesObject.pie(pieCounts_s, labels = pieLabels_s, startangle=90, autopct = '%1.1f%%')
    axesObject.axis('equal')
    plt.title(patientname + ': Percentages of different sleep stages over all nights')
    axesObject.legend(loc = "upper left")
    plt.savefig(os.path.join(os.path.dirname(cwd), 'Visualizations', patientname + ' Sleep Stage Pie Chart.png'), dpi = 1200)
#    plt.savefig(os.path.join(os.path.dirname(cwd), 'Visualizations', patientname + ' Sleep Stage Pie Chart.jpg'), dpi = 1200)
    plt.close(figureObject)
    
    # This creates a line plot for sleep efficiency and the sleep stage percentages
    fig = plt.figure()
    ax = plt.axes()
    ax.plot(dos, efficiency, label = 'Sleep Efficiency')
    ax.plot(dos, light_per, label = '% Light Sleep')
    ax.plot(dos, rem_per, label = '% REM Sleep')
    ax.plot(dos, deep_per, label = '% Deep Sleep')
    plt.xticks(rotation=90)
    ax.xaxis.set_tick_params(labelsize=6)
    lgd = ax.legend(loc='center left', bbox_to_anchor=(1,0.5))
    plt.grid(True)
    plt.ylim(0,100)
    
    plt.savefig(os.path.join(os.path.dirname(cwd), 'Visualizations', patientname + ' Nightly Efficiency and Stages.png'), dpi = 1200, bbox_extra_artists =(lgd,), bbox_inches = 'tight')
#    plt.savefig(os.path.join(os.path.dirname(cwd), 'Visualizations', patientname + ' Nightly Efficiency and Stages.jpg'), dpi = 1200, bbox_extra_artists =(lgd,), bbox_inches = 'tight')
    plt.close(fig)

    #Experimental plot. I don't even know
    # This creates a dataframe starting at 12:00 on the first recorded day and ends at 11:59:30
    # It uses 15 minute intervals and is populated later 
    oldest = min(df_complete['Time']).replace(hour = 12, minute = 0, second = 0)
    youngest = max(df_complete['Time']).replace(hour = 11, minute = 59, second = 30)
    full_range = pd.date_range(oldest, youngest, freq = '15min')
    all_hours = [0] * len(full_range)
    full_df = pd.DataFrame()
    full_df['Time'] = full_range
    full_df['Stage'] = all_hours
    full_df = full_df.set_index('Time')
    df_complete = df_complete.set_index('Time')
    
    # This is outdated, can probably be deleted
    for i in range(len(full_df)):
        if full_df.index[i] in df_complete.index:
            full_df['Stage'][i] = 1

    # Create Ticks and labels every 7 days starting on the first recorded night.
    all_days = pd.date_range(oldest, youngest, freq='D')
    n_days = len(all_days)
    date_ticks = []
    date_tick_labels = []
    for i in range(0,n_days,7):
        date_ticks.append(i)
        date_tick_labels.append(str(all_days[i]))
    date_tick_labels = [x.split(' ')[0] for x in date_tick_labels]    
    
    # Reshape the stage values it into an array. it has 96 Columns because
    sleep_mat = full_df['Stage'].values.reshape(len(pd.date_range(oldest, youngest)), 96)
    
    
    df_wake = df_complete[df_complete['Stage'] == 'wake']
    df_light = df_complete[df_complete['Stage'] == 'light']
    df_deep = df_complete[df_complete['Stage'] == 'deep']
    df_rem = df_complete[df_complete['Stage'] == 'rem']
    df_awake = df_complete[df_complete['Stage'] == 'awake']
    df_asleep = df_complete[df_complete['Stage'] == 'asleep']
    df_restless = df_complete[df_complete['Stage'] == 'restless']
    
    for i in range(len(full_df)):
        if full_df.index[i] in df_complete.index:
            if full_df.index[i] in df_wake.index:
                full_df['Stage'][i] = 0
            if full_df.index[i] in df_light.index:
                full_df['Stage'][i] = 1
            if full_df.index[i] in df_deep.index:
                full_df['Stage'][i] = 2
            if full_df.index[i] in df_rem.index:
                full_df['Stage'][i] = 3
            if full_df.index[i] in df_awake.index:
                full_df['Stage'][i] = 4
            if full_df.index[i] in df_asleep.index:
                full_df['Stage'][i] = 5
            if full_df.index[i] in df_restless.index:
                full_df['Stage'][i] = 6
    
    fig, ax = plt.subplots(1,1, tight_layout = True)
    light_blue_patch = mpatches.Patch(color = 'lightblue', label = 'Light Sleep')
    dark_blue_patch = mpatches.Patch(color = 'darkblue', label = 'Deep Sleep')
    green_patch = mpatches.Patch(color = 'green', label = 'REM Sleep')
    grey_patch = mpatches.Patch(color = 'grey', label = 'No Stage Data')
    cmap = colors.ListedColormap(['white', 'lightblue', 'darkblue', 'green', 'grey'])
    boundary_norm = colors.BoundaryNorm([-1,0.5,1.5,2.5,3.5,10], cmap.N)
    ax.imshow(sleep_mat, cmap=cmap, norm = boundary_norm)
    ax.set_aspect('equal')
    ax.grid(axis='x', color = 'k')
    ax.yaxis.grid()
    plt.xticks(ticks=[0,24,48,72], labels=['12:00','18:00','24:00', '6:00'])
    plt.yticks(ticks=date_ticks, labels=date_tick_labels)
    plt.legend(handles=[light_blue_patch, dark_blue_patch, green_patch, grey_patch], 
           loc = 'upper left', fontsize = 8)
    plt.savefig(os.path.join(os.path.dirname(cwd), 'Visualizations', patientname + ' Nightly Sleep.png'), dpi = 2400)
    
    
    
    # If all the patients have been processed, calculate missing data and
    # Summary statistics for the whole sample
    if n_patient == len(filenames):
        
        sample_mean_row = round(whole_sample_df.mean(),1)
        sample_mean_row.name = 'Sample Average'
        whole_sample_df = whole_sample_df.append(sample_mean_row)
        whole_sample_df.to_csv(os.path.join(os.path.dirname(cwd), 'Summary Statistics', 'Whole Sample Summary Statistics.csv'), index = True)
        whole_sample_df.to_excel(os.path.join(os.path.dirname(cwd), 'Summary Statistics', 'Whole Sample Summary Statistics.xlsx'), index = True)

        ave_missing = sum(total_missing)/len(total_missing)
        ave_stages_missing = sum(total_stages_missing)/len(total_stages_missing)
        print('On average for each patient data is missing completely for ' + 
              str(round(ave_missing, 1)) + '% of all nights' + 
              '\nOn average for each patient sleep stage data is unavailable for '+ 
              str(round(ave_stages_missing, 1)) + 
              '% of recorded nights.' + '\nOn average for each patient sleep stage data is available for '+
              str(round(100 - ave_stages_missing - ave_missing)) + '% of all nights' +
              '\n\nProcessing Complete! \nFolders containing Longform Data, Summary Statistics and Visualizations have been created in:\n' + 
              os.path.dirname(cwd))
    else:
        # Increase the patient counter by one.
        n_patient += 1
    
    
