# MBTA Arrival time prediction

## Objective
The objective of this project is to predict train arrival times in the boston subway. I developed 4 models (OLS, GLM, XGBoost and a Dense Neural Network) to make the travel time predictions. All 4 models predict the segment route travel time with features computed directly from the train GPS data collected over a week, weather information and prior knowledge. The aim was to use limited information and implement innovative feature engineering methods from the existing data. This was done with the vision to scale the project easily to other cities and transportation mediums like buses.

## Overall Design
![alt text](https://github.com/amalrkrishna/subway_time_prediction/blob/master/images/DataPipeline.png)
1. **MBTA Data Collector** - cronjob that was run over the first week of November, 2018. The task of the Collector was to ping the MBTA servers for vehicle locations once every minute and save that data. 
2. **The Real-time MBTA feed** -  real-time feed of the vehicle location.
3. **OpenWeatherMap API** - is an API for accessing realtime and historical weather data.

## Feature Engineering

Initial features - 
1. **current_stop_sequence** - current stop sequence of the train
2. **direction_id** - direction of the train, 0 - outbound, 1 - inbound
3. **longitude** - current latitude location of the train
4. **latitude** - current longitude location of the train
5. **route_id** - route ID of the train
6. **server_time** - last updated time from the server
7. **system_time** - last pinged time from the system
8. **vehicle_id** - train ID
9. **trip_id** - trip ID in which the train is currently in
10. **schedule_realtionship** - 
11. **curr_status** - status of the train. incoming, at_station.

Final features after interpolation and weather data integration -
1. **current_stop_sequence** - stop sequence at the start of the segment 
2. **direction_id** (0,1) - direction of the train, 0 - outbound, 1 - inbound
3. **stop_id**- ID of nearest stop to the starting location
4. **end_stop** - ID of the nearest stop to the ending location
5. **temp** - temparature at the start for the segment travelled
6. **humidity** - humidity at the start of the segment
7. **wind_speed** - wind speed at the start of the segment
8. **clouds_all** - intensity of clouds at the start of the segment
9. **weather_main** - Main weather condition at the start of the segment. Rain, Mist, Clear, Drizzle, Fog, Haze
10. **day** - Monday ... Sunday
11. **route_id** - Route of the segment. Red, Green-B, Green-C, Green-D, Green-E, Blue or Orange
12. **time_of_day** - starting time of the day for the segment travelled
13. **distance** - distance travelled by the train during the segment
14. **start_CC** - distance from the city center at the start of the segment
15. **end_CC** - distance from the city center at the end of the segment
16. **velocity** - velocity of the train during the segment
17. **travel_time** - time it took for the train to travel the segment

## Model Designs
1. **Ordinary Least Squares** - In statistics, OLS is a type of linear least squares method for estimating the unknown parameters in a linear regression model. OLS from statsmodel is used for this project. OLS is a bit sensitive to the outliers. 
2. **Generalized Linear Model** - In statistics, the generalized linear model (GLM) is a flexible generalization of ordinary linear regression that allows for response variables that have error distribution models other than a normal distribution. 
3. **Dense Neural Network** - The DNN is created using 3 layers. Model is compiled using mean absolute error as the loss function and adam as the optimizer. Also, between each two layer a dropout layer is added RELU and softmax are used as the activation functions. The following hyperparameters are passed on to the model –  
    a.    **Loss** – mean absolute error  
    b.    **Optimizer** – adam  
    c.    **Activation functions** – relu & soft_max  
    d.    **Dropout** – 0.5  
    e.    **Validation Split** – 0.2  
    f.    **epochs** – 100  
    g.    **Batch Size** – 100  
    Keras library is used to build the model. Keras is an open source neural network library written in Python. It is capable of running on top of TensorFlow, Microsoft Cognitive Toolkit, or Theano.
![alt text](https://github.com/amalrkrishna/subway_time_prediction/blob/master/images/Models.png)

4. **XGBoost Regressor** - XGBoost is an optimized distributed gradient boosting library designed to be highly efficient, flexible and portable. It implements machine learning algorithms under the Gradient Boosting framework. XGBoost provides a parallel tree boosting (also known as GBDT, GBM) that solve many data science problems in a fast and accurate way. The following parameters are passed on to the model –  
    a.    **n estimators** – 100 (number of trees)  
    b.    **Learning rate** – 0.05 (step size shrinkage used in update to prevent overfitting)  
    c.    **Max depth** – 6 (maximum depth of a tree)  
    Xgboost library is used to build the model. 

## Result Analysis
### Predict vs y_test comparison
1. **OLS**
![alt text](https://github.com/amalrkrishna/subway_time_prediction/blob/master/images/OLS.png)
2. **GLM**
![alt text](https://github.com/amalrkrishna/subway_time_prediction/blob/master/images/GLM.png)
3. **Dense Neural Network**
<img src="https://github.com/amalrkrishna/subway_time_prediction/blob/master/images/DNN.png" width="425"/> <img src="https://github.com/amalrkrishna/subway_time_prediction/blob/master/images/dnn_loss.png" width="100"/> 
![alt text](https://github.com/amalrkrishna/subway_time_prediction/blob/master/images/DNN.png) ![alt text](https://github.com/amalrkrishna/subway_time_prediction/blob/master/images/dnn_loss.png)
4. **XGBoost Regressor**
![alt text](https://github.com/amalrkrishna/subway_time_prediction/blob/master/images/XGB.png)

From the above graphs we can note that OLS is a bit sensitive to the outliers. It cannot describe non-linear relationships. Major shortcoming of GLM from the results is that it failed to identify the outliers in the data-points. Not detecting extreme travel-times is really bad for this case scenario where we don’t want the traveler to miss the train. The shortcoming of the DNN was it failed to recognize the time series nature of the data. Better models like LSTM would ideally be a better fit for the given problem statement. XGBoost Regressor performed resonably well with the hold-out test dataset.
### Error metrics
1.   **MEANy** – Mean of the y_test values.
2.   **MBE** - Mean Bias Error measures the average difference between predict travel time and real travel time. Positive error and negative error will cancel out. 
3.   **MAE** - Mean Absolute Error measures the average derivation of prediction from real travel time. 
4.   **MAPE** - Mean Absolute Percentage Error measures the average percentage derivation from real travel time. 
5.   **RMSE** - Root Mean Squared Error measures average derivation. Compared to Mean Absolute Error, RMSE puts large weights on large errors.



## Implementation
Shiny is an open source R package that provides an elegant and powerful web framework for building web applications using R. Here, shiny integrates the real-time MBTA predictions to show real time locations and next expected inbound and outbound arrival times using the implemented machine learning models.
![alt text](https://github.com/amalrkrishna/subway_time_prediction/blob/master/images/implementation.png)
    a. **Route** – Gives you an option to filter based on MBTA Rapid transit routes. Example – Green-B, Red, Orange etc.  
    b. **Select your stop** – Gives you the option to select the stop for which you want to see the next inbound and outbound arrival times. Example – Boston University West, Park Street etc.  
    c. **Refresh Interval** – Update frequency for the map and the arrival times.  
    d. **Inbound, Outbound filters** – filters the map based on the entry.  


## References
[1] Dynamic Bus Arrival Time Prediction with Artificial Neural Networks, Journal of Transportation Engineering  
[2] Bus-Arrival-Time Prediction Models Link-Based and Section-Based. Journal of transportation engineering  
[3] Kalaputa, R. and Demetsky, M. (1995). Application of artificial neural networks and anutomatic vehicle location data for bus transit schedule behavior modelling  
[4] Xu. Jing Ying. Bus arrival time prediction with real-time and historic data  
[5] Tingting Yin , Gang Zhong , Jian Zhang , Shanglu He , Bin Ran. A prediction model of bus arrival time at stops with multi-routes multi-routes  
[6] Mei Chen, Xiaobo Liu, Jingxin Xia & Steven I. Chien A Dynamic Bus-Arrival Time Prediction Model Based on APC Data  
[7] Tingting Yin, Gang Zhong, Jian Zhang, Shanglu He, Bin Ran. School of Transportation, Southeast University, World Conference on Transport research. WTRC 2016 – Shanghai  
[8] Bus Transit Time Prediction using GPS Data with Artificial Neural Networks, Fan Jiang, Carnegie Mellon University (Thesis) – 2017  
[9] A prediction model of bus arrival time at stops with multi-routes. Tingting Yin, Gang Zhong, Jian Zhang, Shanglu He, Bin Ran. School of Transportation, Southeast University, World Conference on Transport research. WTRC 2016 - Shanghai  
