from __future__ import division
from sqlalchemy import create_engine, MetaData, Table
import json
import math
import re
import csv
from itertools import izip_longest
from collections import Counter
import pandas as pd
import numpy as np
from .egg import Egg

def load(dbpath=None, recpath=None, remove_subs=None, wordpool=None, groupby=None, experiments=None):
    '''
    Function that loads sql files generated by autoFR Experiment
    '''

    assert (dbpath is not None), "You must specify a db file or files."
    assert (recpath is not None), "You must specify a recall folder."
    assert (wordpool is not None), "You must specify a wordpool file."
    assert (experiments is not None), "You must specify a list of experiments"

    ############################################################################
    # subfunctions #############################################################

    def db2df(db, filter_func=None):
        '''
        Loads db file and converts to dataframe
        '''
        db_url = "sqlite:///" + db
        table_name = 'turkdemo'
        data_column_name = 'datastring'

        # boilerplace sqlalchemy setup
        engine = create_engine(db_url)
        metadata = MetaData()
        metadata.bind = engine
        table = Table(table_name, metadata, autoload=True)

        # make a query and loop through
        s = table.select()
        rows = s.execute()

        data = []
        for row in rows:
            data.append(row[data_column_name])

        # parse each participant's datastring as json object
        # and take the 'data' sub-object
        data = [json.loads(part)['data'] for part in data if part is not None]

        # insert uniqueid field into trialdata in case it wasn't added
        # in experiment:
        for part in data:
            for record in part:
        #         print(record)
                if type(record['trialdata']) is list:

                    record['trialdata'] = {record['trialdata'][0]:record['trialdata'][1]}
                record['trialdata']['uniqueid'] = record['uniqueid']

        # flatten nested list so we just have a list of the trialdata recorded
        # each time psiturk.recordTrialData(trialdata) was called.
        def isNotNumber(s):
            try:
                float(s)
                return False
            except ValueError:
                return True

        data = [record['trialdata'] for part in data for record in part]

        # filter out fields that we dont want using isNotNumber function
        filtered_data = [{k:v for (k,v) in part.items() if isNotNumber(k)} for part in data]

        # Put all subjects' trial data into a dataframe object from the
        # 'pandas' python library: one option among many for analysis
        data_frame = pd.DataFrame(filtered_data)

        data_column_name = 'codeversion'

        # boilerplace sqlalchemy setup
        engine = create_engine(db_url)
        metadata = MetaData()
        metadata.bind = engine
        table = Table(table_name, metadata, autoload=True)

        # make a query and loop through
        s = table.select()
        rows = s.execute()

        versions = []
        version_dict = {}
        for row in rows:
            version_dict[row[0]]=row[data_column_name]

        version_col = []
        for idx,sub in enumerate(data_frame['uniqueid'].unique()):
            for i in range(sum(data_frame['uniqueid']==sub)):
                version_col.append(version_dict[sub])
        data_frame['exp_version']=version_col

        if filter_func:
            data_frame = filter_func(data_frame)

        return data_frame

    # custom filter to clean db file
    def filter_func(data_frame):
        data=[]
        indexes=[]
        for line in data_frame.iterrows():
            try:
                if json.loads(line[1]['responses'])['Q1'].lower() in ['kirsten','allison','marisol','maddy','campbell']:
                    delete = False
                else:
                    delete = True
            except:
                pass

            if delete:
                indexes.append(line[0])

        return data_frame.drop(data_frame.index[indexes])


    # this function takes the data frame and returns subject specific data based on the subid variable
    def filterData(data_frame,subid):
        filtered_stim_data = data_frame[data_frame['stimulus'].notnull() & data_frame['listNumber'].notnull()]
        filtered_stim_data = filtered_stim_data[filtered_stim_data['trial_type']=='single-stim']
        filtered_stim_data =  filtered_stim_data[filtered_stim_data['uniqueid']==subid]
        return filtered_stim_data

    # this function parses the data creating an array of dictionaries, where each dictionary represents a trial (word presented) along with the stimulus attributes
    def createStimDict(data):
        stimDict = []
        for index, row in data.iterrows():
            stimDict.append({
                    'text': str(re.findall('>(.+)<',row['stimulus'])[0]),
                    'color' : { 'r' : int(re.findall('rgb\((.+)\)',row['stimulus'])[0].split(',')[0]),
                               'g' : int(re.findall('rgb\((.+)\)',row['stimulus'])[0].split(',')[1]),
                               'b' : int(re.findall('rgb\((.+)\)',row['stimulus'])[0].split(',')[2])
                               },
                    'location' : {
                        'top': float(re.findall('top:(.+)\%;', row['stimulus'])[0]),
                        'left' : float(re.findall('left:(.+)\%', row['stimulus'])[0])
                        },
                    'category' : wordpool['CATEGORY'].iloc[list(wordpool['WORD'].values).index(str(re.findall('>(.+)<',row['stimulus'])[0]))],
                    'size' : wordpool['SIZE'].iloc[list(wordpool['WORD'].values).index(str(re.findall('>(.+)<',row['stimulus'])[0]))],
                    'wordLength' : len(str(re.findall('>(.+)<',row['stimulus'])[0])),
                    'firstLetter' : str(re.findall('>(.+)<',row['stimulus'])[0])[0],
                    'listnum' : row['listNumber']
                })
        return stimDict

    # this function loads in the recall data into an array of arrays, where each array represents a list of words
    def loadRecallData(subid):
        recalledWords = []
        for i in range(0,16):
            try:
                f = open(recpath + subid + '/' + subid + '-' + str(i) + '.wav.txt', 'rb')
                spamreader = csv.reader(f, delimiter=' ', quotechar='|')
            except (IOError, OSError) as e:
                print(e)
            for row in spamreader:
                recalledWords.append(row[0].split(','))
        return recalledWords

    # this function computes accuracy for a series of lists
    def computeListAcc(stimDict,recalledWords):
        accVec = []
        for i in range(0,16):
            stim = [stim['text'] for stim in stimDict if stim['listnum']==i]
            recalled= recalledWords[i]

            acc = 0
            tmpstim = stim[:]
            for word in recalled:
                if word in tmpstim:
                    tmpstim.remove(word)
                    acc+=1
            accVec.append(acc/len(stim))
        return accVec

    def getFeatures(stimDict):
        stimDict_copy = stimDict[:]
        for item in stimDict_copy:
            item['location'] = [item['location']['top'], item['location']['left']]
            item['color'] = [item['color']['r'], item['color']['g'], item['color']['b']]
            item.pop('text', None)
            item.pop('listnum', None)
        stimDict_copy = [stimDict_copy[i:i+16] for i in range(0, len(stimDict_copy), 16)]
        return stimDict_copy

    ############################################################################
    # main program #############################################################

    # if its not a list, make it one
    if type(dbpath) is not list:
        dbpath = [dbpath]

    # read in stimulus library
    wordpool = pd.read_csv(wordpool)

    # load in dbs and convert to df, and filter
    dfs = [db2df(db, filter_func=filter_func) for db in dbpath]

    # concatenate the db files
    df = pd.concat(dfs)

    # subjects who have completed the exp
    subids = list(df[df['listNumber']==15]['uniqueid'].unique())

    # remove problematic subjects
    if remove_subs:
        for sub in remove_subs:
            subids.remove(sub)

    # set up data structure to load in subjects
    if groupby:
        pres = [[] for i in range(len(groupby['exp_version']))]
        rec = [[] for i in range(len(groupby['exp_version']))]
        features = [[] for i in range(len(groupby['exp_version']))]

        # make each groupby item a list
        groupby = [exp if type(exp) is list else [exp] for exp in groupby['exp_version']]

    else:
        pres = [[]]
        rec = [[]]
        features = [[]]

    # for each subject that completed the experiment
    for idx,sub in enumerate(subids):

        # get the subjects data
        filteredStimData = filterData(df,sub)

        if filteredStimData['exp_version'].values[0] in experiments:

            # create stim dict
            stimDict = createStimDict(filteredStimData)

            sub_data = pd.DataFrame(stimDict)
            sub_data['subject']=idx
            sub_data['experiment']=filteredStimData['exp_version'].values[0]
            sub_data = sub_data[['experiment','subject','listnum','text','category','color','location','firstLetter','size','wordLength']]

            # get features from stim dict
            feats = getFeatures(stimDict)

            # load in the recall data
            recalledWords = loadRecallData(sub)

            # get experiment version
            exp_version = filteredStimData['exp_version'].values[0]

            # find the idx of the experiment for this subjects
            if groupby:
                exp_idx = list(np.where([exp_version in item for item in groupby])[0])
            else:
                exp_idx = [0]

            if exp_idx != []:
                pres[exp_idx[0]].append([list(sub_data[sub_data['listnum']==lst]['text'].values) for lst in sub_data['listnum'].unique()])
                rec[exp_idx[0]].append(recalledWords)
                features[exp_idx[0]].append(feats)

    eggs = [Egg(pres=ipres, rec=irec, features=ifeatures) for ipres,irec,ifeatures in zip(pres,rec,features)]

    if len(eggs)>1:
        return eggs
    else:
        return eggs[0]
