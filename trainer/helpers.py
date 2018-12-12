#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 10 00:27:23 2018

@author: amal
"""

import pandas as pd
import os.path
import requests
import time
from google.transit import gtfs_realtime_pb2

route_name_subset = ['Green-B',
                     'Green-C',
                     'Green-D',
                     'Green-E',
                     'Orange',
                     'Red',
                     'Blue']

def make_trip_object(t, updated):
    trip = {}
    trip['trip_id'] = t.trip_id
    trip['start_date'] = t.start_date
    trip['route_id'] = t.route_id
    trip['updated'] = updated

    return trip

def make_stop_time_update_object(t, stu, updated):
    stop_time_update = {}
    stop_time_update['trip_id'] = t.trip_id
    if stu.departure:
        stop_time_update['departure'] = stu.departure.time
    if stu.arrival:
        stop_time_update['arrival'] = stu.arrival.time
    stop_time_update['stop_id'] = stu.stop_id
    stop_time_update['updated'] = updated

    return stop_time_update

def make_vehicle_object(v, updated):
    vehicle = {}
    vehicle['vehicle_id'] = v.vehicle.id
    vehicle['trip_id'] = v.trip.trip_id
    vehicle['schedule_relationship'] = v.trip.schedule_relationship
    vehicle['route_id'] = v.trip.route_id
    vehicle['direction_id'] = v.trip.direction_id
    vehicle['latitude'] = v.position.latitude
    vehicle['longitude'] = v.position.longitude
    #vehicle['bearing'] = v.position.bearing
    vehicle['curr_stop_sequence'] = v.current_stop_sequence
    vehicle['curr_status'] = v.current_status
    vehicle['server_time'] = v.timestamp
    vehicle['stop_id'] = v.stop_id
    vehicle['system_time'] = updated

    return vehicle

def get_gtfs_realtime_vehicle_positions(vehicle_position_url):
    
    feed = gtfs_realtime_pb2.FeedMessage()
    vehicle_position_data = requests.get(vehicle_position_url).content
    feed.ParseFromString(vehicle_position_data)
    
    trips = []
    stop_time_updates = []
    vehicles = []
    
    updated = int(time.time())
    
    for entity in feed.entity:
        if entity.HasField('trip_update'):
            trips.append(make_trip_object(entity.trip_update.trip, updated))
            for s in entity.trip_update.stop_time_update:
                stop_time_updates.append(make_stop_time_update_object(entity.trip_update.trip, s, updated))
    
        elif entity.HasField('vehicle'):
            vehicles.append(make_vehicle_object(entity.vehicle, updated))
    
    current_vehicle_positions = pd.DataFrame(vehicles)
    current_vehicle_positions = current_vehicle_positions.loc[current_vehicle_positions['route_id'].isin(route_name_subset)]
    
    return(current_vehicle_positions)

def get_weather():
    CITY_ID = '4930956'
    START = '1541177994'
    END = '1541625811'

    API_URL = 'http://history.openweathermap.org/data/2.5/history/'
    API_KEY = '&APPID=f2945dde296e86ae509e15d26ded0bb1'
    CITY_COMP = '&city?id=' + CITY_ID
    TYPE_COMP = '&type=hour'
    START_COMP = '&start=' + START
    END_COMP = '&end='+ END

    URL = API_URL + API_KEY + CITY_COMP + TYPE_COMP + START_COMP + END_COMP

    data = pd.read_csv('../datasets.nosync/weather_info.csv')
    
def interpolate_data_intermediate():
    
    one_week_data = pd.read_pickle('../datasets.nosync/data_intermediate.pkl')
    
    interpolated_data = []
    
    for index, row in one_week_data.iterrows():
        if (row['server_time'] > max(one_week_data['server_time'])-3600):
            break
        row['end_stop'] = row['stop_id']
        
        if os.path.isfile('../datasets.nosync/interpolated_data.csv'):
            with open('../datasets.nosync/interpolated_data.csv', 'a+') as f:
                row.to_frame().T.to_csv(f, header=False)
        else:
            with open('../datasets.nosync/interpolated_data.csv', 'a+') as f:
                row.to_frame().T.to_csv(f, header=True)
    
        interpolated_data.append(row)
        start_lat = row['start_lat']
        start_long = row['start_long']
        travel_time = row['travel_time']
        vehicle_id = row['vehicle_id']
        tt = travel_time
        for i in range(index+1, index+1000):
            if(vehicle_id == one_week_data['vehicle_id'].iloc[i]):
                print(index, i, vehicle_id, one_week_data['vehicle_id'].iloc[i])
     
                tt=tt+one_week_data['travel_time'].iloc[i]
                to_append = one_week_data.iloc[i].copy()
                to_append['end_stop'] = to_append['stop_id']
                to_append['stop_id'] = row['stop_id']
                to_append['travel_time'] = tt
                to_append['start_lat'] = start_lat
                to_append['start_long'] = start_long
                    
                with open('../datasets.nosync/interpolated_data.csv', 'a+') as f:
                    to_append.to_frame().T.to_csv(f, header=False)
