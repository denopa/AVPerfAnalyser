from math import radians, cos, sin, asin, sqrt
from scipy.interpolate import griddata as interpMatrix
import numpy as np
import pandas as pd

def haversine(lon1, lat1, lon2, lat2, units): #great circle distance between two points 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2]) # convert decimal degrees to radians 
    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    if units == 'kilometres': 
        r = 6371 # Radius of earth in kilometres. 
    elif units == 'nautical miles':
        r = 3440 # Radius of earth in nautical miles. 
    elif units == 'metres':
        r = 6371000 # Radius of earth in meters. 
    elif units == 'feet':
        r = 20902231 # Radius of earth in feet. 
    return c * r 

def calcWindComponents(windSpeed, windDirection, track):
    headwind = windSpeed * cos(radians(windDirection - track)) 
    crosswind = windSpeed * sin(radians(windDirection - track))
    return headwind, crosswind

def isaDiff(temp, pressAlt):
    isaTemp = 15 - 2 * pressAlt/1000
    return temp - isaTemp

def getPerf(book, x, units):
    indexColumns = book.index.names
    points = book.reset_index()[indexColumns].values
    values = book[units].values
    i=0
    for ix in x: #make sure the value to look in the book for is inded in the book, replace by the limit otherwise
        x[i] = min(book.index.get_level_values(i).max(), max(ix,book.index.get_level_values(i).min()))
        i = i+1
    return interpMatrix(points, values, np.array(x))[0]

def loadBook(flightPart, model, **configuration):
    if flightPart == 'climb':
        with open('models/'+model+'/'+flightPart+'.csv') as dataFile:
                book = pd.read_csv(dataFile, index_col=['power','tempVISA','pressAlt'])
    elif flightPart == 'cruise':
        with open('models/'+model+'/'+flightPart+'.csv') as dataFile:
                book = pd.read_csv(dataFile, index_col=['cruisePowerVariable1','cruisePowerVariable2','tempVISA','pressAlt'])
    elif flightPart == 'landing':
        with open('models/'+model+'/'+flightPart+'.csv') as dataFile:
                book = pd.read_csv(dataFile, index_col=['tempVISA','pressAlt','weight','headwind'])
    else:
        configuration = kwargs.get('configuration', 'standard')
        if configuration == 'standard':
            with open('models/'+model+'/'+flightPart+'Standard.csv') as dataFile:
                book = pd.read_csv(dataFile, index_col=['tempVISA','pressAlt','weight','headwind'])
        else:
            with open('models/'+model+'/'+flightPart+'Short.csv') as dataFile:
                book = pd.read_csv(dataFile, index_col=['tempVISA','pressAlt','weight','headwind'])
    return book

def c2f(temp): #convert celsius to farenheit
    return float(temp)*1.8+32

def maxSpread(cylinders):#find the max temp diff between cylinders
    return cylinders.max()-cylinders.min()

def engineMetrics(flight, flightTable, modelConfig):
    flightTable.loc['Average Fuel Flow'] = [round(flight['E1 FFlow'].mean(),1),'-','-','USG']
    if 'E1 CHT1' in flight.columns:
        maxCHT = flight[['E1 CHT1','E1 CHT2','E1 CHT3','E1 CHT4','E1 CHT5','E1 CHT6']].max().max()
        highestAverageCHT = flight[['E1 CHT1','E1 CHT2','E1 CHT3','E1 CHT4','E1 CHT5','E1 CHT6']].mean().max()
        highestAverageCylinder = flight[['E1 CHT1','E1 CHT2','E1 CHT3','E1 CHT4','E1 CHT5','E1 CHT6']].mean().idxmax()
        maxCHTSpread = flight[['E1 CHT1','E1 CHT2','E1 CHT3','E1 CHT4','E1 CHT5','E1 CHT6']].apply(maxSpread).max()
        maxEGTSpread = flight[['E1 EGT1','E1 EGT2','E1 EGT3','E1 EGT4','E1 EGT5','E1 EGT6']].apply(maxSpread).max()
        flightTable.loc['Max CHT'] = [round(maxCHT),round(float(modelConfig.loc['maxCHT','Value'])), round(100*(maxCHT/float(modelConfig.loc['maxCHT','Value'])-1)),'degrees F'  ]
        flightTable.loc['Highest Average CHT'] = [round(highestAverageCHT),'-','-','degrees F']
        flightTable.loc['Hottest Average Cylinder'] = [highestAverageCylinder,'-','-','-']
        flightTable.loc['Max CHT Spread'] = [round(maxCHTSpread),'-','-','degrees F']
        flightTable.loc['Max EGT Spread'] = [round(maxEGTSpread),'-','-','degrees F']
    if 'E1 OilT' in flight.columns:
        flightTable.loc['Average Oil Temp'] = [round(flight['E1 OilT'].mean()),'-','-','degrees F']
    if 'E1 OilP' in flight.columns:
        flightTable.loc['Average Oil Press'] = [round(flight['E1 OilP'].mean()),'-','-','PSI']
    if 'E1 FPres' in flight.columns:
        flightTable.loc['Average Fuel Press'] = [round(flight['E1 FPres'].mean()),'-','-','PSI']
    if 'E1 CDT' in flight.columns:
        averageICEfficiency = 100*((flight['E1 CDT']-flight['E1 IAT'])/(flight['E1 CDT']-flight['OAT'].apply(c2f))).mean()
        flightTable.loc['Intercooler Efficiency'] = [round(averageICEfficiency),'-','-','%']
    return flightTable

# interpMatrix(takeOffRollBook.index.values, takeOffRollBook['metres'].values, np.array([isaDiff(temp, pressAlt), pressAlt, takeOffWeight, headwind]))