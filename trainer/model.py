#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec  7 02:36:03 2018

@author: amal
"""

from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, explained_variance_score, mean_squared_log_error
import statsmodels.api as sm
from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation, Flatten
from keras.layers.normalization import BatchNormalization
from keras.models import load_model
from statsmodels.regression.linear_model import OLSResults
from keras.callbacks import ModelCheckpoint, LearningRateScheduler, CSVLogger, TensorBoard

import matplotlib
import matplotlib.pyplot as plt


from sklearn import preprocessing
import task
import math
import pandas as pd
import numpy as np
import xgboost
import pickle

def prepare_train_test(data):
    data = data.drop(['trip_id', 'vehicle_id', 'server_time',
                      'start_lat','start_long','end_lat', 'end_long',
                      'pressure'], axis=1)

    target = 'travel_time'
    #Define the x and y data
    X = data.drop(target, axis=1)
    
    names = list(data.drop(target, axis=1))
    min_max_scaler = preprocessing.MinMaxScaler()
    np_scaled = min_max_scaler.fit_transform(X)
    X = pd.DataFrame(np_scaled, columns=names)   
    y = list(data[target])
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.30, random_state=42)
    return (X_train, X_test, y_train, y_test, X, y)

def calculate_metrics(predict, y_test):
    
    MEANy = np.mean(y_test)
    SDy = np.std(y_test)
    MSE = mean_squared_error(predict, y_test)
    RMSE = math.sqrt(MSE)
    EVS = explained_variance_score(predict, y_test)
    MAE = mean_absolute_error(predict, y_test)
    MAPE = task.mean_absolute_percentage_error(predict, y_test)
    MBE = task.mean_bias_error(predict, y_test)
    
    metrics = {'MEANy': MEANy,
               'SDy':SDy,
                'MSE':MSE,
               'RMSE':RMSE,
               'EVS':EVS,
               'MAE':MAE,
               'MAPE':MAPE,
               'MBE':MBE
               }
    
    metrics = pd.DataFrame(metrics, index=[0])
    return(metrics)

def ols_model(X_train, X_test, y_train, y_test):
    
    linear_model = sm.OLS(y_train, X_train)
    linear_results = linear_model.fit()
    
    task.coef_plot(linear_results.params)
    
    ols_predict = linear_results.predict(X_test)
    task.time_series_plot(y_test, ols_predict)
    metrics = calculate_metrics(ols_predict, y_test)
    fname = '../datasets.nosync/OLS-' + str(round(metrics['MAE'][0], 2)) + "-" + \
    str(round(metrics['MAPE'][0],2)) + '.pkl'
    linear_results.save(fname)
    return(ols_predict, metrics)
    
def XGB_model(X_train, X_test, y_train, y_test):
    
    xgb_model = xgboost.XGBRegressor(n_estimators=50, 
                                     learning_rate=0.05, 
                                     gamma=0, 
                                     subsample=1,
                                     colsample_bytree=1, 
                                     max_depth=6)
    
    xgb_results = xgb_model.fit(X_train,y_train, verbose=True)
    xgb_predict = xgb_results.predict(X_test)
    
    task.time_series_plot(y_test, xgb_predict)
    metrics = calculate_metrics(xgb_predict, y_test)
    
    fname = '../datasets.nosync/XGB-' + str(round(metrics['MAE'][0], 2)) + \
    "-" + str(round(metrics['MAPE'][0],2)) + '.bin'
    pickle.dump(xgb_model, open(fname, "wb"))
    
    return(xgb_predict, metrics)
    
def glm_model(X_train, X_test, y_train, y_test):
    
    gamma_model = sm.GLM( y_train, X_train,family=sm.families.Gamma())
    gamma_results = gamma_model.fit()
    task.coef_plot(gamma_results.params)
    
    glm_predict = gamma_results.predict(X_test)
    metrics = calculate_metrics(glm_predict, y_test)
    
    fname = '../datasets.nosync/GLM-' + str(round(metrics['MAE'][0], 2)) + "-" + \
    str(round(metrics['MAPE'][0],2)) + '.pkl'
    gamma_results.save(fname)
    return(glm_predict, metrics)
    
def DNN_model(X_train, X_test, y_train, y_test, X):

    DNN_model = Sequential()
    DNN_model.add(Dense(100,input_dim=X_train.shape[1],
                        kernel_initializer='uniform',
                        activation='relu'))
    DNN_model.add(Dropout(0.5))
    DNN_model.add(Dense(50,kernel_initializer='uniform',activation='softmax'))
    DNN_model.add(Dropout(0.5))
    DNN_model.add(Dense(100,kernel_initializer='uniform',activation='relu'))
    DNN_model.add(Dropout(0.5))
    DNN_model.add(Dense(1,kernel_initializer='uniform',activation='relu'))
        
    DNN_model.summary()
    
    mn = X.mean(axis=0) 
    DNN_model.compile(loss='mae',
                      optimizer='adam')
    
    print("...starting modeling")
    
    tensor = TensorBoard(log_dir='./Graph', histogram_freq=0,  
          write_graph=True, write_images=True)
    
    DNN_model.fit(X_train/mn, y_train,  
                  validation_split=0.2,
                  epochs =100,
                  batch_size=100,
                  verbose=1,
                  callbacks=[tensor])
    
    print("DNN Model created")
    
    dnn_predict = DNN_model.predict(X_test)
    
    dnn_predict = pd.Series((v[0] for v in dnn_predict))
    task.time_series_plot(y_test, dnn_predict)
    metrics = calculate_metrics(dnn_predict, y_test)

    
    fname = '../datasets.nosync/DNN-' + str(round(metrics['MAE'][0], 2)) + "-" + \
    str(round(metrics['MAPE'][0],2)) + '.h5'
    DNN_model.save(fname)
    
    return(dnn_predict, metrics)
    
def DNN_realtime(X_test, DNN_name):
    DNN_name = '../datasets.nosync/' + DNN_name
    DNN_model = load_model(DNN_name)
    dnn_predict = DNN_model.predict(X_test)
    dnn_predict = pd.Series((v[0] for v in dnn_predict))
    return(dnn_predict)
    
def OLS_realtime(X_test, OLS_name):
    OLS_name = '../datasets.nosync/' + OLS_name
    linear_results = OLSResults.load(OLS_name)
    ols_predict = linear_results.predict(X_test)
    return(ols_predict)
    
def XGB_realtime(X_test, XGB_name):
    XGB_name = "../datasets.nosync/" + XGB_name
    xgb_results = pickle.load(open(XGB_name, "rb"))
    xgb_predict = xgb_results.predict(X_test)
    return(xgb_predict)

def DNN_epoch_cure(history):
    plt.figure(figsize=(10, 8))
    plt.title("Dense model training", fontsize=12)
    plt.plot(history.history["loss"], label="Train")
    plt.plot(history.history["val_loss"], label="Test")
    plt.grid("on")
    plt.xlabel("Epoch", fontsize=12)
    plt.ylabel("loss", fontsize=12)
    plt.legend(loc="upper right")
    