#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  7 17:35:50 2018

@author: amal
"""

from __future__ import division
import os.path
import pandas as pd
import numpy as np
from datetime import datetime
from geopy.distance import vincenty
import matplotlib.pyplot as plt
import seaborn as sns
import json
import urllib.request as urllib2
from sklearn import preprocessing
from plotly.offline import plot
import plotly.graph_objs as go


def fetch_one_week_data(URL):
    one_week_data = pd.read_csv(URL,
                            sep=",",
                            header=None,
                            names=[
                                  "curr_status",
                                  "curr_stop_sequence",
                                  "direction_id",
                                  "latitude",
                                  "longitude",
                                  "route_id",
                                  "schedule_realtionship",
                                  "stop_id",
                                  "server_time",
                                  "trip_id",
                                  "system_time",
                                  "vehicle_id"])
    
    one_week_data = one_week_data[["server_time",
                                   "route_id",
                                   "curr_stop_sequence",
                                  "latitude",
                                  "longitude",
                                  "direction_id",
                                  "curr_status",
                                  "schedule_realtionship",
                                  "stop_id",
                                  "trip_id",
                                  "vehicle_id",
                                  "system_time",
                                  ]]
    
    one_week_data['curr_status'] = pd.to_numeric(one_week_data['curr_status'])
    one_week_data['curr_stop_sequence'] = pd.to_numeric(one_week_data['curr_stop_sequence'])
    one_week_data['direction_id'] = pd.to_numeric(one_week_data['direction_id'])
    one_week_data['latitude'] = pd.to_numeric(one_week_data['latitude'])
    one_week_data['longitude'] = pd.to_numeric(one_week_data['longitude'])
    one_week_data['schedule_realtionship'] = pd.to_numeric(one_week_data['schedule_realtionship'])
    one_week_data['stop_id'] = pd.to_numeric(one_week_data['stop_id'])
    one_week_data['latitude'] = pd.to_numeric(one_week_data['latitude'])
    
    one_week_data = one_week_data.drop(['curr_status', 'schedule_realtionship'], axis=1)
    return(one_week_data)
    
def day_of_week(ep):
    return datetime.fromtimestamp(ep).strftime("%A")

def time_of_day(ep):
    ref = datetime(2018, 1, 1, 0, 0, 0)
    sec = (datetime.fromtimestamp(ep)- ref).seconds
    return sec

def distance(row):
    source = (row['start_lat'], row['start_long'])
    dest = ( row['end_lat'], row['end_long'])
    return vincenty(source,dest).miles

Boston = (42.3601, -71.0589)

def start_to_CC(row):
    '''find the distance between pick up point and Manhattan center'''
    source = (row['start_lat'], row['start_long'])
    return vincenty(source,Boston).miles

def end_to_CC(row):
    '''find the distance between dropoff point and Manhattan center'''
    dest = ( row['end_lat'], row['end_long'])
    return vincenty(dest,Boston).miles  

def weather(data):
    wdata = pd.read_csv('../datasets.nosync/weather_info.csv')
    wdata = wdata[wdata['dt'] >= 1541177994 ]
    wdata = wdata[wdata['dt'] < 1541625811 ]
    
    for index, row in data.iterrows():
        #print(index)
        wrow = wdata.iloc[(wdata['dt']-row['server_time']).abs().argsort()[:1]]
        #print(list(wrow['temp'])[0])
        data.at[index,'temp'] = list(wrow['temp'])[0]
        data.at[index,'pressure'] = list(wrow['pressure'])[0]
        data.at[index,'humidity'] = list(wrow['humidity'])[0]
        data.at[index,'wind_speed'] = list(wrow['wind_speed'])[0]
        data.at[index,'clouds_all'] = list(wrow['wind_speed'])[0]
        data.at[index,'weather_main'] = list(wrow['weather_main'])[0]
    return(data)

def remove_outliers(data):
    data = data[data['travel_time']<2000]
    #data = data[data['travel_time']>120]
    #data['travel_time'] = data['travel_time']/60
    
    data=data[data['stop_id'] != data['end_stop']]
    #data2=data[data['stop_id'] == data['end_stop']].sample(frac=0.25, replace=False)
    #data = pd.concat([data1, data2])
    #print(data)
    return(data)
    
def add_other_features(data):
    # Add day of the week and the dummy variable
    
    data = weather(data)
    data = pd.get_dummies(data, columns=['weather_main'])
    DD  = data['server_time'].map(day_of_week)
    data['day'] = DD
    DD  = pd.get_dummies(DD,prefix='day')
    data = pd.concat([data, DD], axis =1)
    data = pd.get_dummies(data, columns=['route_id'])
    data = data.drop(['day'], axis=1)
    data['time_of_day']  = data['server_time'].map(time_of_day)
    # distance between start and end of the trip
    data['distance']   = data.apply(lambda x :distance(x), axis=1 )
    #data['distance2'] = data['distance']**2
    # distance between start, end, and center of City 
    data['start_CC']  = data.apply(start_to_CC, axis=1 )
    data['end_CC'] = data.apply(end_to_CC, axis=1 )
    data['velocity'] = np.array(data['distance']/(data['travel_time']/3600))
    #Replace this part with IQR
    data = data[data['velocity']<100]
    data = data[data['velocity']>.5]
    #data = data[data['travel_time']<300]
    #data = data[data['travel_time']>10]
    
    return(data)

def realtime_prediction_add_weather(data):
    API_ENDPOINT = 'http://api.openweathermap.org/data/2.5/weather'
    CITY_ID = '?q=Boston,US'
    API_TOKEN = '&appid=f2945dde296e86ae509e15d26ded0bb1'
    
    URL = API_ENDPOINT+CITY_ID+API_TOKEN
    r = urllib2.urlopen(URL)
    r = json.load(r)
    #print(r['weather'][0]['main'])
    
    t = r['main']['temp']
    p = r['main']['pressure']
    w = r['wind']['speed']
    h = r['main']['humidity']
    #v = r['visibility']
    c = r['clouds']['all']
    
    wm = 'weather_main_' + str(r['weather'][0]['main'])
    data[wm] = 1
    data['temp'] = t
    data['pressure'] = p
    data['wind_speed'] = w
    data['humidity'] = h
    data['clouds_all'] = c
    
    return(data)
    
    
    
def realtime_prediction_add_other_features(data):
    # Add day of the week and the dummy variable
    #data = pd.get_dummies(data, columns=['weather_main'])
    #print(data)
    #print(list(data))
    DD  = data['server_time'].map(day_of_week)
    data['day'] = DD
    
    DD  = pd.get_dummies(DD,prefix='day')
    data = pd.concat([data, DD], axis =1)
    #print(list(data))
    data = pd.get_dummies(data, columns=['route_id'])
    #print(list(data))
    
    data = data.drop(['day'], axis=1)
    data['time_of_day']  = data['server_time'].map(time_of_day)
    # distance between start and end of the trip
    data['distance']   = data.apply(lambda x :distance(x), axis=1 )
    #data['distance2'] = data['distance']**2
    
    # distance between start, end, and center of Boston 
    data['start_CC']  = data.apply(start_to_CC, axis=1 )
    data['end_CC'] = data.apply(end_to_CC, axis=1 )
    
    return(data)
    
def add_main_features_cords_tt(data):
    for index, row in data.iterrows():
        vid = row['vehicle_id']
        rid = row['route_id']
        start_lat = row['latitude']
        start_long = row['longitude']
        start_time = row['server_time']
        for i in range(index+1, index+500):
            if (i < data.shape[0] and vid == data["vehicle_id"].iloc[i] and rid == data["route_id"].iloc[i]):
                print(index, i)
                end_lat = data["latitude"].iloc[i]
                end_long = data["longitude"].iloc[i]
                end_time = data["server_time"].iloc[i]
                
                data.at[index,'start_lat'] = start_lat
                data.at[index,'start_long'] = start_long
                data.at[index,'end_lat'] = end_lat
                data.at[index,'end_long'] = end_long
                data.at[index,'travel_time'] = end_time - start_time
                break
            
    data = data.drop(['system_time', 'latitude', 'longitude'], axis=1)
    data = data.dropna()
    
    data = data[data['travel_time'] != 0]
    
    data.to_pickle('../datasets.nosync/data_intermediate.pkl')
    
    return(data)
def add_remaining_variables_and_drop(data, rv):
    
    for item in rv:
        data[item] = 0
        
    return(data)
    
def scale_realtime_prediction(data):
    names = list(data)
    min_max_scaler = preprocessing.MinMaxScaler()
    np_scaled = min_max_scaler.fit_transform(data)
    np_scaled = pd.DataFrame(np_scaled, columns=names)
    
    return (np_scaled)

def add_prediction_features(data):
    print("Inside add_prediction_features")
    
    fresult = []
    owd=pd.read_csv('../datasets.nosync/one_week_dataset.csv')
    owd=owd[owd.columns[8]].drop_duplicates()
    
    if os.path.isfile('../datasets.nosync/stop_sequence.csv'):
        stops=pd.read_csv('../datasets.nosync/stop_sequence.csv')
    else:
        stops=pd.read_csv('../datasets.nosync/MBTA_GTFS/stops+.csv')
        stops = stops[['Route Id', 'Stop Name', 'Stop Code','Direction Id', 'Stop Lat', 'Stop Lon','Stop Sequence']]
        stops.rename(columns={'Direction Id': 'direction_id', 
                                      'Route Id': 'route_id',
                                      'Stop Code': 'stop_id',
                                      'Stop Lat': 'stop_lat',
                                      'Stop Lon': 'stop_long',
                                      'Stop Name': 'stop_name',
                                      'Stop Sequence': 'stop_sequence'}, inplace=True)
    
        stops=stops.loc[stops['stop_id'].isin(owd)]
        stops=stops.drop_duplicates()
        stops = stops.sort_values(['route_id', 'stop_sequence'])
        stops.to_csv('../datasets.nosync/stop_sequence.csv')

    for data_index, data_row in data.iterrows():
        rid = data_row['route_id']
        sid = data_row['stop_id']
        did = data_row['direction_id']
        #print(data_row['route_id'], data_row['stop_id'], data_row['direction_id'])
        subset=stops[stops['route_id'] == rid].sort_values('stop_id')
        subset=subset[subset['direction_id'] == did].sort_values('stop_id')
        #print(list(subset))
        #print(subset)
        for s_index, s_row in subset.iterrows(): 
            #print(did, sid, s_row['stop_id'])
            if (did == 0):
                if (int(sid) >= int(s_row['stop_id'])):
                    result = data_row.append(s_row)
                    result = list(result)
                    fresult.append(result)
            else:
                if (int(sid) <= int(s_row['stop_id'])):
                    result = data_row.append(s_row)
                    result = list(result)
                    fresult.append(result)
        
    names = list(data) + list(stops)
    #print(names)
    
    #have to update 2nd stop_id -> end_stop, lat,long -> start respectively
    names = ['curr_status', 'curr_stop_sequence', 'direction_id', 'start_lat', 'start_long', 
             'route_id', 'schedule_relationship', 'server_time', 'stop_id', 'system_time', 
             'trip_id', 'vehicle_id', 'velocity', 'route_id1', 'stop_name', 'end_stop', 
             'direction_id1', 'end_lat', 'end_long', 'stop_sequence']
    
    
    new_data = pd.DataFrame(fresult, columns=names)
    
    new_data = new_data.drop(['route_id1','direction_id1'], axis=1)
    print(list(new_data))
    return(new_data)
    
def mean_absolute_percentage_error(y_pred, y_true): 
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100

def mean_bias_error(y_pred, y_true): 
    error = np.array(y_true) - np.array(y_pred)
    return np.mean(error)

def corr_plot(data):
    data = data.drop(['trip_id', 'vehicle_id', 'server_time'], axis=1)
    corr = data.corr()
    
    # generate a mask for the lower triangle
    mask = np.zeros_like(corr, dtype=np.bool)
    mask[np.triu_indices_from(mask)] = True
    
    # set up the matplotlib figure
    f, ax = plt.subplots(figsize=(18, 18))
    
    # generate a custom diverging colormap
    cmap = sns.diverging_palette(220, 10, as_cmap=True)
    
    # draw the heatmap with the mask and correct aspect ratio
    sns.heatmap(corr, mask=mask, cmap=cmap, vmax=.3,
                square=True, 
                linewidths=.5, cbar_kws={"shrink": .5}, ax=ax)
    
    plt.show()
    
def coef_plot(params):
    params = params.to_frame().reset_index()
    data = [go.Bar(
            x=params[params.columns[1]],
            y=params[params.columns[0]],
            orientation = 'h'
    )]
    layout = go.Layout(
        title='GLM Coefficients',
        margin=go.layout.Margin(
            l=200
        )
    )
    
    #py.iplot(data, filename='horizontal-bar')
    fig = go.Figure(data=data, layout=layout)
    plot(fig)
    
def time_series_plot(y_test, predict):
    
    xv = list(range(1,len(y_test)))
    
    trace_high = go.Scatter(
                x=xv[1:150],
                y=predict[1:150],
                name = "Prediction",
                line = dict(color = 'red'),
                opacity = 0.8)

    trace_low = go.Scatter(
                    x=xv[1:150],
                    y=y_test[1:150],
                    name = "Ground truth",
                    line = dict(color = 'orange'),
                    opacity = 0.8)
    
    data = [trace_high, trace_low]
    
    layout = dict(
        title = "predict vs y_test : GLM",
        yaxis=dict(
                title='Travel times')
    )
    
    fig = dict(data=data, layout=layout)
    plot(fig)