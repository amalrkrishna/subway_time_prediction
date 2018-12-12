#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec  9 10:35:12 2018

@author: amal
"""

import time
import task
import model
import helpers
import numpy as np
import pandas as pd
from geopy.distance import vincenty
import threading 

VEHICLE_POSITIONS = "https://cdn.mbta.com/realtime/VehiclePositions.pb"

q = []
vv = None

def moving_window():
    print("Inside moving_window")
    global vv
    while True:
        if len(q) == 5:
            right_most = q[len(q)-1]
            data = pd.DataFrame(columns=list(right_most))
            for i in range(len(q)):
                data = pd.concat([data, q[i]])
            for index, row in data.iterrows():
                for i in range(index+1, len(data)):
                    if(row['vehicle_id'] == data["vehicle_id"].iloc[i]):
                        source = (row['latitude'], row['longitude'])
                        dest = ( data["latitude"].iloc[i] , data["longitude"].iloc[i] )
                        distance = vincenty(source, dest).miles
                        t = row['server_time']-data["server_time"].iloc[i]
                        if(t!=0): data.at[index, 'velocity'] = abs(distance/(t/3600))
            if 'velocity' in data.columns:
                data = data[['vehicle_id','velocity']]
                vv = data.groupby(['vehicle_id'], as_index=False).mean()
            del q[0]
            
        real_time_data = helpers.get_gtfs_realtime_vehicle_positions(VEHICLE_POSITIONS)
        q.append(real_time_data)
        print(len(q), ' elements in moving window')
        time.sleep(30)
        
def start_realtimefeed():
    print("Inside start_realtimefeed")
    while True:
        print('...collecting feed data')
        X_test_variables = ['curr_stop_sequence',
                            'direction_id',
                            'stop_id',
                            'start_lat',
                            'start_long',
                            'end_lat',
                            'end_long',
                            'temp',
                            'pressure',
                            'humidity',
                            'wind_speed',
                            'clouds_all',
                            'weather_main_Clear',
                            'weather_main_Clouds',
                            'weather_main_Drizzle',
                            'weather_main_Fog',
                            'weather_main_Haze',
                            'weather_main_Mist',
                            'weather_main_Rain',
                            'day_Friday',
                            'day_Monday',
                            'day_Saturday',
                            'day_Sunday',
                            'day_Tuesday',
                            'day_Wednesday',
                            'route_id_Blue',
                            'route_id_Green-B',
                            'route_id_Green-C',
                            'route_id_Green-D',
                            'route_id_Green-E',
                            'route_id_Orange',
                            'route_id_Red',
                            'time_of_day',
                            'distance',
                            'start_CC',
                            'end_CC']
        
        real_time_data = helpers.get_gtfs_realtime_vehicle_positions(VEHICLE_POSITIONS)
        real_time_data = pd.merge(real_time_data, vv, on=['vehicle_id'])
        real_time_data = real_time_data.fillna(np.mean(vv['velocity']))
        print(real_time_data['velocity'])
        pre_prediction_data = task.add_prediction_features(real_time_data)
        pre_prediction_data=task.realtime_prediction_add_other_features(pre_prediction_data)
        pre_prediction_data=task.realtime_prediction_add_weather(pre_prediction_data)
    
        rem_variables = list(set(X_test_variables) - set(pre_prediction_data))
        
        pre_prediction_data=task.add_remaining_variables_and_drop(pre_prediction_data, rem_variables)
        data = pre_prediction_data.drop(["curr_status", 'system_time', 'server_time', 
                                                        'stop_name', 'vehicle_id', 'stop_sequence', 
                                                        'schedule_relationship', 'start_lat','start_long',
                                                        'end_lat', 'end_long', 'pressure','trip_id'], axis=1)
        
        dNames = ['curr_stop_sequence', 'direction_id', 'stop_id', 'end_stop', 'temp', 'humidity', 
         'wind_speed', 'clouds_all', 'weather_main_Clear', 'weather_main_Clouds', 
         'weather_main_Drizzle', 'weather_main_Fog', 'weather_main_Haze', 
         'weather_main_Mist', 'weather_main_Rain', 'day_Friday', 'day_Monday', 
         'day_Saturday', 'day_Sunday', 'day_Tuesday', 'day_Wednesday', 'route_id_Blue', 
         'route_id_Green-B', 'route_id_Green-C', 'route_id_Green-D', 'route_id_Green-E', 
         'route_id_Orange', 'route_id_Red', 'time_of_day', 'distance', 'start_CC', 
         'end_CC', 'velocity']
        
        data=data.reindex(columns=dNames)
        data=task.scale_realtime_prediction(data)
        XGB_name = 'XGB-58.38-7.64.bin'
        DNN_name = 'DNN-3.27-34.82.h5'
        OLS_name = 'OLS-194.31-44.31.pkl'
        predict_ols = model.OLS_realtime(data, OLS_name)
        predict_dnn = model.DNN_realtime(data, DNN_name)
        predict_xgb = model.XGB_realtime(data, XGB_name)
        
        pre_prediction_data['ols'] = predict_ols
        pre_prediction_data['dnn'] = predict_dnn
        pre_prediction_data['xgb'] = predict_xgb
        pre_prediction_data.to_csv('../dashboard/prediction.csv')
        time.sleep(5)

'''
p1 = Process(target=moving_window)
p1.start()
time.sleep(30)
p2 = Process(target=start_realtimefeed)
p2.start()
p1.join()
p2.join()
'''

t1 = threading.Thread(target=moving_window) 
t2 = threading.Thread(target=start_realtimefeed) 
  
# starting thread 1 
t1.start() 
time.sleep(360)
# starting thread 2 
t2.start() 
  
# wait until thread 1 is completely executed 
t1.join() 
# wait until thread 2 is completely executed 
t2.join()
