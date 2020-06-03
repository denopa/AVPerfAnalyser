import pandas as pd 
from libs.utils import haversine, calcWindComponents, isaDiff, getPerf, loadBook
from configuration.units import runwayUnits


# definitions


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
    with open('models/'+model+'/config.csv') as dataFile:
        modelConfig = pd.read_csv(dataFile, index_col='Variable')
    engineType = modelConfig.loc['engineType','Value']
    if engineType == 'piston':
        bookTakeoffMAP = float(modelConfig.loc['takeoffMAP','Value'])
        bookTakeoffRPM = float(modelConfig.loc['takeoffRPM','Value'])
        bookminTakeoffFFlow = float(modelConfig.loc['minTakeoffFFlow','Value'])
        takeoffMAP = flight['E1 MAP'][fiftyfeetPoint-10:fiftyfeetPoint].mean().round(1)
        takeoffRPM = flight['E1 RPM'][fiftyfeetPoint-10:fiftyfeetPoint].mean().round(0)
        takeoffFFlow = flight['E1 FFlow'][fiftyfeetPoint-10:fiftyfeetPoint].mean().round(1)
        engineInfo = pd.DataFrame([[takeoffMAP,bookTakeoffMAP, "inches"],[takeoffRPM,bookTakeoffRPM],[takeoffFFlow,bookminTakeoffFFlow, "gph"]],index=["Take off MAP","Take off RPM","Take off Fuel Flow"], columns=["Flight", "Book","Units"])
        engineInfo["Variance"] = ( engineInfo.Flight / engineInfo.Book -1)
    else:
        engineInfo = pd.DataFrame(columns=["Flight", "Book", "Variance", "Units"])

    return dist, flight['IAS'][fiftyfeetPoint], engineInfo

# MAIN
def takeOffPerformance(flight, model, takeoffMethod, takeoffWeight):
    takeOffRollBook = loadBook('takeOffRoll', model, takeoffMethod)
    distanceOver50Book = loadBook('distanceOver50', model, takeoffMethod)
    takeOffRoll, takeOffAIS, temp, pressAlt,  windSpeed, windDirection, track = calcGroundRoll(flight, model)
    fiftyFeetDistance, barrierIAS, engineInfo = calc50feetDistance(flight, model)
    headwind, crosswind = calcWindComponents(windSpeed, windDirection, track)
    bookTakeOffRoll = getPerf(takeOffRollBook, [isaDiff(temp, pressAlt), pressAlt, takeoffWeight, headwind], runwayUnits)
    bookDistanceOver50 = getPerf(distanceOver50Book, [isaDiff(temp, pressAlt), pressAlt, takeoffWeight, headwind], runwayUnits)
    # load book speeds
    with open('models/'+model+'/config.csv') as dataFile:
        modelConfig = pd.read_csv(dataFile, index_col='Variable')
    bookTakeOffIAS = float(modelConfig.loc['takeoffIAS'+takeoffMethod,'Value'])
    bookBarrierIAS = float(modelConfig.loc['barrierIAS'+takeoffMethod,'Value'])
    takeoffTable = pd.DataFrame(columns=['Flight','Book','Variance', 'Units'])
    takeoffTable.loc['Take off Roll'] = [int(takeOffRoll), int(bookTakeOffRoll),takeOffRoll/bookTakeOffRoll-1, runwayUnits]
    takeoffTable.loc['Take off IAS'] = [int(takeOffAIS), int(bookTakeOffIAS),takeOffAIS/bookTakeOffIAS-1, 'knots']
    takeoffTable.loc['Distance over 50 feet'] = [int(fiftyFeetDistance), int(bookDistanceOver50), fiftyFeetDistance/bookDistanceOver50-1, runwayUnits]
    takeoffTable.loc['AIS over Barrier'] = [int(barrierIAS), int(bookBarrierIAS), barrierIAS/bookBarrierIAS-1, "knots"]
    takeoffTable.loc['Headwind'] = [round(headwind), '-','-','knots']
    takeoffTable.loc['Crosswind'] = [round(crosswind), '-','-','knots']
    takeoffTable.loc['ISA Deviation'] = [round(isaDiff(temp, pressAlt)), '-','-','degrees C']
    takeoffTable.loc['Pressure Altitude'] = [pressAlt, '-','-','feet']
    if len(engineInfo)>0:
        takeoffTable = pd.concat([takeoffTable, engineInfo])
    

    return takeoffTable

