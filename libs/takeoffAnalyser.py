import pandas as pd 
from libs.utils import haversine, calcWindComponents, isaDiff, getPerf, loadBook
from configuration.units import runwayUnits


# definitions


def findTakeoff(flight): #returns the row of the takeoff point
    garminGround = flight[flight['OnGrnd'] == 0].index.min() #Garmin Ground indicator
    startAltitude = flight.loc[garminGround,'AltGPS']
    return flight[(flight.index>garminGround)&(flight.AltGPS>startAltitude+3)&(flight.VSpd>100)].index.min()

def find50feet(flight): #returns the row of the takeoff point
    garminGround = flight[flight['OnGrnd'] == 0].index.min() #Garmin Ground indicator
    startAltitude = flight.loc[garminGround,'AltGPS']
    return flight[(flight.index>garminGround)&(flight.AltGPS>startAltitude+50)].index.min()

def takeoffStability(flight,modelConfig): #returns the row of the takeoff point
    garminGround = flight[flight['OnGrnd'] == 0].index.min() #Garmin Ground indicator
    startAltitude = flight.loc[garminGround,'AltGPS']
    takeoff = findTakeoff(flight)
    fivehundred = flight[(flight.index>garminGround)&(flight.AltGPS>startAltitude+500)].index.min()
    maxPitch = int(flight.loc[takeoff:fivehundred, 'Pitch'].max())
    minPitch = int(flight.loc[takeoff:fivehundred, 'Pitch'].min())
    maxRoll = int(flight.loc[takeoff:fivehundred, 'Roll'].abs().max())
    continuousClimb = (flight.loc[takeoff:fivehundred, 'VSpd'].min()>0)
    bookMaxPitch = int(modelConfig.loc['takeoffMaxPitch','Value'])
    bookMinPitch = int(modelConfig.loc['takeoffMinPitch','Value'])
    bookMaxRoll = int(modelConfig.loc['takeoffMaxRoll','Value'])
    stableTable = pd.DataFrame(columns=['Actual', 'Book', 'Stability', 'Units'])
    stableTable.loc['Takeoff Max Pitch'] = [maxPitch,bookMaxPitch,maxPitch>bookMaxPitch, 'degrees']
    stableTable.loc['Takeoff Min Pitch'] = [minPitch,bookMinPitch,minPitch<bookMinPitch, 'degrees']
    stableTable.loc['Takeoff Max Roll'] = [maxRoll,bookMaxRoll,maxRoll>bookMaxRoll, 'degrees']
    stableTable.loc['Takeoff Continuous Climb'] = [continuousClimb,'True',not continuousClimb, '-']
    stableTable['Stability'] = stableTable['Stability'].apply(lambda x: "Unstable" if x else "Stable")
    stableTable.loc['Takeoff Stability'] = ['Stable' if (stableTable['Stability']=='Stable').all() else 'Unstable', 'True','-','-']
    return stableTable

def findGroundRollStart(groundPortion, modelConfig): #finds the row where take off roll started. This is model dependent
    takeoffPowerTreshold =  float(modelConfig.loc['takeoffPowerTreshold','Value']) #indicates the POWER above which we consider the ground roll to start
    takeoffPowerIndicator = modelConfig.loc['takeoffPowerIndicator','Value']
    return groundPortion[groundPortion[takeoffPowerIndicator]>takeoffPowerTreshold].index.min()

def calcGroundRoll(flight, modelConfig):
    garminGround = flight[flight['OnGrnd'] == 0].index.min() #Garmin Ground indicator
    takeoffPoint = findTakeoff(flight)
    rollStart = findGroundRollStart(flight[:takeoffPoint], modelConfig)
    dist = haversine(flight['Longitude'][rollStart], flight['Latitude'][rollStart],flight['Longitude'][takeoffPoint], flight['Latitude'][takeoffPoint], runwayUnits)
    ais = flight.loc[takeoffPoint, 'IAS']
    temp = flight.loc[rollStart, 'OAT']
    pressAlt = flight.loc[rollStart, 'AltPress']
    windSpeed = flight.loc[garminGround:takeoffPoint, 'WndSpd'].mean()
    windDirection = flight.loc[garminGround:takeoffPoint, 'WndDr'].mean()
    track = flight.loc[garminGround:takeoffPoint, 'TRK'].mean()
    return dist, ais, temp, pressAlt, windSpeed, windDirection, track

def calc50feetDistance(flight, modelConfig):
    fiftyfeetPoint = find50feet(flight)
    rollStart = findGroundRollStart(flight[:fiftyfeetPoint], modelConfig)
    dist = haversine(flight['Longitude'][rollStart], flight['Latitude'][rollStart],flight['Longitude'][fiftyfeetPoint], flight['Latitude'][fiftyfeetPoint], runwayUnits)
    engineType = modelConfig.loc['engineType','Value']
    if engineType == 'piston':
        bookTakeoffMAP = float(modelConfig.loc['takeoffMAP','Value'])
        bookTakeoffRPM = float(modelConfig.loc['takeoffRPM','Value'])
        bookminTakeoffFFlow = float(modelConfig.loc['minTakeoffFFlow','Value'])
        takeoffMAP = flight['E1 MAP'][fiftyfeetPoint-10:fiftyfeetPoint].mean().round(1)
        takeoffRPM = flight['E1 RPM'][fiftyfeetPoint-10:fiftyfeetPoint].mean().round(0)
        takeoffFFlow = flight['E1 FFlow'][fiftyfeetPoint-10:fiftyfeetPoint].mean().round(1)
        engineInfo = pd.DataFrame([[takeoffMAP,bookTakeoffMAP, "inches"],[takeoffRPM,bookTakeoffRPM],[takeoffFFlow,bookminTakeoffFFlow, "gph"]],index=["Take off MAP","Take off RPM","Take off Fuel Flow"], columns=["Actual", "Book","Units"])
        engineInfo["Variance"] = round(100*( engineInfo.Actual / engineInfo.Book -1))
        engineInfo = engineInfo[['Actual','Book','Variance','Units']]
    else:
        engineInfo = pd.DataFrame(columns=["Actual", "Book", "Variance", "Units"])

    return dist, flight['IAS'][fiftyfeetPoint], engineInfo

# MAIN
def takeoffPerformance(flight, model, modelConfig, takeoffMethod, takeoffWeight):
    # load book 
    takeoffRollBook = loadBook('takeoffRoll', model, configuration=takeoffMethod)
    distanceOver50Book = loadBook('distanceOver50', model, configuration=takeoffMethod)
    bookTakeoffIAS = float(modelConfig.loc['takeoffIAS'+takeoffMethod,'Value'])
    bookBarrierIAS = float(modelConfig.loc['barrierIAS'+takeoffMethod,'Value'])
    # actual flight performance
    takeoffRoll, takeoffAIS, temp, pressAlt,  windSpeed, windDirection, track = calcGroundRoll(flight, modelConfig)
    fiftyFeetDistance, barrierIAS, engineInfo = calc50feetDistance(flight, modelConfig)
    headwind, crosswind = calcWindComponents(windSpeed, windDirection, track)
    bookTakeoffRoll = getPerf(takeoffRollBook, [isaDiff(temp, pressAlt), pressAlt, takeoffWeight, headwind], runwayUnits)
    bookDistanceOver50 = getPerf(distanceOver50Book, [isaDiff(temp, pressAlt), pressAlt, takeoffWeight, headwind], runwayUnits)
    
# summary table
    takeoffTable = pd.DataFrame(columns=['Actual','Book','Variance', 'Units'])
    takeoffTable.loc['Takeoff IAS'] = [int(takeoffAIS), int(bookTakeoffIAS),round(100*(takeoffAIS/bookTakeoffIAS-1)), 'knots']
    takeoffTable.loc['Takeoff Roll'] = [int(takeoffRoll), int(bookTakeoffRoll),round(100*(takeoffRoll/bookTakeoffRoll-1)), runwayUnits]
    takeoffTable.loc['Takeoff Dist. over 50 feet'] = [int(fiftyFeetDistance), int(bookDistanceOver50), round(100*(fiftyFeetDistance/bookDistanceOver50-1)), runwayUnits]
    takeoffTable.loc['Takeoff AIS over Barrier'] = [int(barrierIAS), int(bookBarrierIAS), round(100*(barrierIAS/bookBarrierIAS-1)), "knots"]
    takeoffTable.loc['Takeoff Headwind'] = [round(headwind),'-','-','knots']
    takeoffTable.loc['Takeoff Crosswind'] = [round(crosswind), '-','-','knots']
    takeoffTable.loc['Takeoff Temp vs ISA'] = [round(isaDiff(temp, pressAlt)), '-','-','degrees C']
    takeoffTable.loc['Takeoff Pressure Altitude'] = [pressAlt, '-','-','feet']
    if len(engineInfo)>0:
        takeoffTable = pd.concat([takeoffTable, engineInfo])
    return takeoffTable, takeoffStability(flight,modelConfig)

