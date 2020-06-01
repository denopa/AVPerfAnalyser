import pandas as pd 
from libs.utils import haversine, calcWindComponents, isaDiff, getPerf, loadBook
from configuration.units import runwayUnits


takeOffWeight = 4135
takeOffMethod = 'standard' # 'short`

# LOAD FLIGHT DATA, INCLUDING PLANE MODEL
with open("flights/0ed1a44f-ee75-4f22-8ba3-cdb9a83783cb.csv") as dataFile:
    model = pd.read_csv(dataFile).columns[2][16:-1]

with open("flights/0ed1a44f-ee75-4f22-8ba3-cdb9a83783cb.csv") as dataFile:
    flight = pd.read_csv(dataFile, header=2)



# DEFINITIONS
def cleanUp(flight): #put everything in the right format
    flight.columns = flight.columns.str.lstrip()
    numericals = flight.columns.drop(['GPSfix', 'HSIS'])
    flight[numericals] = flight[numericals].apply(pd.to_numeric, errors='coerce')
    return flight

def findTakeoff(flight): #returns the row of the takeoff point
    garminGround = flight[flight['OnGrnd'] == 0].index.min() #Garmin Ground indicator
    startAltitude = flight.loc[garminGround,'AltGPS']
    return flight[(flight.index>garminGround)&(flight.AltGPS>startAltitude+3)].index.min()

def find50feet(flight): #returns the row of the takeoff point
    garminGround = flight[flight['OnGrnd'] == 0].index.min() #Garmin Ground indicator
    startAltitude = flight.loc[garminGround,'AltGPS']
    return flight[(flight.index>garminGround)&(flight.AltGPS>startAltitude+50)].index.min()

def findGroundRollStart(groundPortion, model): #finds the row where take off roll started. This is model dependent
    with open('models/'+model+'/config.csv') as dataFile:
        modelConfig = pd.read_csv(dataFile, index_col='Variable')
    takeoffPowerTreshold =  float(modelConfig.loc['takeoffPowerTreshold','Value']) #indicates the POWER above which we consider the ground roll to start
    takeoffPowerIndicator = modelConfig.loc['takeoffPowerIndicator','Value']
    return groundPortion[groundPortion[takeoffPowerIndicator]>takeoffPowerTreshold].index.min()

def calcGroundRoll(flight, model):
    garminGround = flight[flight['OnGrnd'] == 0].index.min() #Garmin Ground indicator
    takeoffPoint = findTakeoff(flight)
    rollStart = findGroundRollStart(flight[:takeoffPoint], model)
    dist = haversine(flight['Longitude'][rollStart], flight['Latitude'][rollStart],flight['Longitude'][takeoffPoint], flight['Latitude'][takeoffPoint], runwayUnits)
    ais = flight.loc[takeoffPoint, 'IAS']
    temp = flight.loc[rollStart, 'OAT']
    pressAlt = flight.loc[rollStart, 'AltPress']
    windSpeed = flight.loc[garminGround:takeoffPoint, 'WndSpd'].mean()
    windDirection = flight.loc[garminGround:takeoffPoint, 'WndDr'].mean()
    track = flight.loc[garminGround:takeoffPoint, 'TRK'].mean()
    return dist, ais, temp, pressAlt, windSpeed, windDirection, track

def calc50feetDistance(flight, model):
    fiftyfeetPoint = find50feet(flight)
    rollStart = findGroundRollStart(flight[:fiftyfeetPoint], model)
    dist = haversine(flight['Longitude'][rollStart], flight['Latitude'][rollStart],flight['Longitude'][fiftyfeetPoint], flight['Latitude'][fiftyfeetPoint], runwayUnits)
    return dist, flight['IAS'][fiftyfeetPoint]

# MAIN
def takeOffPerformance(flight, model, takeOffMethod):
    takeOffRollBook = loadBook('takeOffRoll', model, takeOffMethod)
    distanceOver50Book = loadBook('distanceOver50', model, takeOffMethod)
    flight = cleanUp(flight)
    takeOffRoll, takeOffAIS, temp, pressAlt,  windSpeed, windDirection, track = calcGroundRoll(flight, model)
    fiftyFeetDistance, fiftyFeetIAS = calc50feetDistance(flight, model)
    headwind, crosswind = calcWindComponents(windSpeed, windDirection, track)
    bookTakeOffRoll = getPerf(takeOffRollBook, [isaDiff(temp, pressAlt), pressAlt, takeOffWeight, headwind], runwayUnits)
    bookDistanceOver50 = getPerf(distanceOver50Book, [isaDiff(temp, pressAlt), pressAlt, takeOffWeight, headwind], runwayUnits)
    # load book speeds
    with open('models/'+model+'/config.csv') as dataFile:
        modelConfig = pd.read_csv(dataFile, index_col='Variable')
    bookTakeOffIAS = float(modelConfig.loc['takeoffIAS'+takeOffMethod,'Value'])
    bookBarrierIAS = float(modelConfig.loc['barrierIAS'+takeOffMethod,'Value'])
    return takeOffRoll, takeOffRollBook, takeOffAIS, bookTakeOffIAS, fiftyFeetDistance, bookDistanceOver50, fiftyFeetIAS, bookBarrierIAS 
