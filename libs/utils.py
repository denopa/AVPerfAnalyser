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
    return interpMatrix(points, values, np.array(x))[0]

def loadBook(flightPart, model, takeOffMethod):
    if takeOffMethod == 'standard':
        with open('models/'+model+'/'+flightPart+'Standard.csv') as dataFile:
            book = pd.read_csv(dataFile, index_col=['tempVISA','pressAlt','weight','headwind'])
    else:
        with open('models/'+model+'/'+flightPart+'Short.csv') as dataFile:
            book = pd.read_csv(dataFile, index_col=['tempVISA','pressAlt','weight','headwind'])
    return book
# interpMatrix(takeOffRollBook.index.values, takeOffRollBook['metres'].values, np.array([isaDiff(temp, pressAlt), pressAlt, takeOffWeight, headwind]))