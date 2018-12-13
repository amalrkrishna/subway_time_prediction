## MBTA Arrival Time prediction
The objective of this project is to predict train arrival times in the boston subway. I developed 4 models (OLS, GLM, XGBoost and a Dense Neural Network) to make the travel time predictions. All 4 models predict the segment route travel time with features computed directly from the train GPS data collected over a week, weather information and prior knowledge. The aim was to use limited information and implement innovative feature engineering methods from the limited existing data. This was done with the vision to scale the project easily to other cities.

### Design
![alt text](https://github.com/amalrkrishna/subway_time_prediction/blob/master/images/DataPipeline.png)
1. MBTA Data Collector - cronjob that was run over the first week of November, 2018. The task of the Collector was to ping the MBTA servers for vehicle locations once every minute and save that data. 
2. The Real-time MBTA feed -  real-time feed of the vehicle location.
3. OpenWeatherMap API is an API for accessing realtime and historical weather data.

The results show promising observations and insights into the travel time prediction using Global Position System data. XGBoost Regressor had the lowest errors on the hold-out test data with a MAPE of 7.7% and MAE of 59 seconds. The results also give insight into promising trends in errors when filtered by routes and peak/non-peak hours. In the final implementation of the Shiny app, arrival time predictions are made based on OLS, DNN, XGB, Moving average filter (MAV) and finally XGB+MAV. The combination of XGB and MAV seems to give the best results on real time data.
