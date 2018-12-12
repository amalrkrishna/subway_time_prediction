#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec  5 17:48:38 2018

@author: amal
"""

import os.path
import pandas as pd
import task
import model

VEHICLE_POSITIONS = "https://cdn.mbta.com/realtime/VehiclePositions.pb"
ONE_WEEK_DATA_LINK = '../datasets.nosync/one_week_dataset.csv'

if os.path.isfile('../datasets.nosync/data_intermediate.pkl'):
    one_week_data = pd.read_pickle('../datasets.nosync/data_intermediate.pkl')
else:
    one_week_data = task.fetch_one_week_data(ONE_WEEK_DATA_LINK)
    one_week_data = one_week_data.reset_index(drop=True)
    one_week_data = task.add_main_features_cords_tt(one_week_data)

if os.path.isfile('../datasets.nosync/data_intermediate_01.pkl'):   
    one_week_data = pd.read_pickle('../datasets.nosync/data_intermediate_01.pkl')
else:    
    if os.path.isfile('../datasets.nosync/intrapolated_data.csv'):
        one_week_data = pd.read_csv('../datasets.nosync/intrapolated_data.csv')
        one_week_data = one_week_data.drop(['Unnamed: 0'], axis=1)
        one_week_data = task.add_other_features(one_week_data)
        one_week_data.to_pickle('../datasets.nosync/data_intermediate_01.pkl')

one_week_data = task.remove_outliers(one_week_data)

##Data Exploration
#one_week_data.info()
#one_week_data['velocity'].hist(bins=1000)
#print("Average Travel Time = ", np.mean(np.array(one_week_data['travel_time'])))
one_week_data['travel_time'].hist(bins=100)
#one_week_data['time_of_day'].hist(bins=100)
#one_week_data[['distance', 'travel_time','velocity']].describe()
#task.corr_plot(one_week_data) 
#owd_describe = one_week_data.describe()  

MODEL = 'XGB'
FRACTION = 1

#one_week_data = one_week_data[one_week_data['time_of_day'].isin(list(range(20*60*60, 24*60*60)))]
one_week_data = one_week_data.sample(frac=FRACTION, replace=False)

print(list(one_week_data))


X_train, X_test, y_train, y_test, X, y = model.prepare_train_test(one_week_data)

print(list(X_test))
if MODEL == 'OLS':
    ols_predict, ols_errors = model.ols_model(X_train, X_test, y_train, y_test)
if MODEL == 'GLM':
    glm_predict, glm_errors = model.glm_model(X_train, X_test, y_train, y_test)
if MODEL == 'DNN':
    dnn_predict, dnn_errors = model.DNN_model(X_train, X_test, y_train, y_test, X)
if MODEL == 'XGB':
    xgb_predict, xgb_errors = model.XGB_model(X_train, X_test, y_train, y_test)