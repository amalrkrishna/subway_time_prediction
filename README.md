# MBTA Arrival time prediction

## Objective
The objective of this project is to predict train arrival times in the boston subway. I developed 4 models (OLS, GLM, XGBoost and a Dense Neural Network) to make the travel time predictions. All 4 models predict the segment route travel time with features computed directly from the train GPS data collected over a week, weather information and prior knowledge. The aim was to use limited information and implement innovative feature engineering methods from the existing data. This was done with the vision to scale the project easily to other cities and mediums like buses.

## Overall Design
![alt text](https://github.com/amalrkrishna/subway_time_prediction/blob/master/images/DataPipeline.png)
1. MBTA Data Collector - cronjob that was run over the first week of November, 2018. The task of the Collector was to ping the MBTA servers for vehicle locations once every minute and save that data. 
2. The Real-time MBTA feed -  real-time feed of the vehicle location.
3. OpenWeatherMap API is an API for accessing realtime and historical weather data.

## Feature Engineering

Initial features - 
1. current_stop_sequence - current stop sequence of the train
2. direction_id - direction of the train, 0 - outbound, 1 - inbound
3. longitude - current latitude location of the train
4. latitude - current longitude location of the train
5. route_id - route ID of the train
6. server_time - last updated time from the server
7. system_time - last pinged time from the system
8. vehicle_id - train ID
9. trip_id - trip ID in which the train is currently in
10. schedule_realtionship - 
11. curr_status - status of the train. incoming, at_station.

Final features after interpolation and weather data integration -
1. current_stop_sequence - stop sequence at the start of the segment 
2. direction_id (0,1) - direction of the train, 0 - outbound, 1 - inbound
3. stop_id - ID of nearest stop to the starting location
4. end_stop - ID of the nearest stop to the ending location
5. temp - temparature at the start for the segment travelled
6. humidity - humidity at the start of the segment
7. wind_speed - wind speed at the start of the segment
8. clouds_all - intensity of clouds at the start of the segment
9. weather_main - Main weather condition at the start of the segment. Rain, Mist, Clear, Drizzle, Fog, Haze
10. day - Monday ... Sunday
11. route_id - Route of the segment. Red, Green-B, Green-C, Green-D, Green-E, Blue or Orange
12. time_of_day - starting time of the day for the segment travelled
13. distance - distance travelled by the train during the segment
14. start_CC - distance from the city center at the start of the segment
15. end_CC - distance from the city center at the end of the segment
16. velocity - velocity of the train during the segment
17. travel_time - time it took for the train to travel the segment

## Models
1. Ordinary Least Squares
2. Generalized Linear Model
3. XGBoost Regressor
4. Dense Neural Network
