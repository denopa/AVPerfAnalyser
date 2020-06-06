import pandas as pd
from libs.utils import haversine, loadBook, getPerf, isaDiff, calcWindComponents
from configuration.units import runwayUnits

def findStop(flight):
    return flight[flight.IAS>20].index.max()

def isStable(approach, modelConfig, approachType, runwayTrack):
    VRef = float(modelConfig.loc['stallSpeed','Value'])*1.3
    stable = True
    reasons = []
    stableTable = pd.DataFrame(columns=['Actual','Book','Stability', 'Units'])
    stableTable.loc['Max IAS'] = [int(approach.IAS.max()), int(VRef+20),approach.IAS.max()>VRef+20, 'knots' ]
    stableTable.loc['Min IAS'] = [int(approach.IAS.min()), int(VRef),approach.IAS.min()<VRef, 'knots' ]
    stableTable.loc['Max Sink Rate'] = [int(approach.VSpd.min()), -1000,approach.VSpd.min()<-1000, 'fpm' ]
    if approachType == 'IFR':
        stableTable.loc['Loc deviation'] = [round(approach.HCDI.abs().max(),1), 1,approach.HCDI.abs().max()>1, '-' ]
        stableTable.loc['Glide deviation'] = [round(approach.VCDI.abs().max(),1), 1,approach.VCDI.abs().max()>1, '-' ]
    else:
        stableTable.loc['Approach Track'] = [int((approach.TRK - runwayTrack).abs().max()), 10,(approach.TRK - runwayTrack).abs().max()>10, 'degrees' ]
    stableTable.loc['Overall'] = [stableTable['Stability'].all(), 'True',not(stableTable['Stability'].all()),'-']
    stableTable['Stability'] =stableTable['Stability'].apply(lambda x: "Unstable" if x else "Stable")
    return stableTable

def calcLandingWeight(flight, modelConfig, takeoffWeight, threshold):
    startFuel = flight["FQtyL"].max() +flight["FQtyR"].max()
    landingFuel = flight.loc[threshold-10:threshold+10,"FQtyL"].mean() +flight.loc[threshold-10:threshold+10,"FQtyR"].mean()
    fuelWeightPerUSG = float(modelConfig.loc['fuelWeightPerUSG','Value'])
    return takeoffWeight - (startFuel - landingFuel) * fuelWeightPerUSG

def approachPerformance(flight,model, modelConfig,approachType, takeoffWeight):
    stop = findStop(flight)
    landingAltitude = flight.loc[stop,'AltB']
    runwayTrack = flight.loc[stop-10:stop+10,'TRK'].mean()
    threshold = flight[flight.AltB>(landingAltitude+50)].index.max()
    thresholdIAS = flight.loc[threshold,'IAS']
    if approachType == 'IFR':
        gateHeight = 1000
    else:
        gateHeight = 500
    gate = flight[flight.AltB>(landingAltitude+gateHeight)].index.max() #stabilised approach gate
    stableTable = isStable(flight.loc[gate:threshold], modelConfig, approachType, runwayTrack)
    thresholdIASBook = float(modelConfig.loc['thresholdIAS','Value'])
    approachTable = pd.DataFrame(columns=['Actual','Book','Variance%','Units'])
    approachTable.loc['IAS over threshold'] = [int(thresholdIAS),int(thresholdIASBook), round(100*(thresholdIAS/thresholdIASBook-1)),'knots']
    landingDistance = haversine(flight.loc[threshold, 'Longitude'],flight.loc[threshold, 'Latitude'], flight.loc[stop, 'Longitude'],flight.loc[stop, 'Latitude'],runwayUnits)
    landingDistanceBook = loadBook('landing', model)
    tempVISA = isaDiff(flight.loc[threshold,'OAT'], flight.loc[threshold,'AltPress']) 
    windSpeed = flight.loc[threshold,'WndSpd']
    windDirection = flight.loc[threshold,'WndDr']
    headwind, crosswind = calcWindComponents(windSpeed, windDirection, runwayTrack)
    landingWeight = round(calcLandingWeight(flight, modelConfig, takeoffWeight, threshold))
    landingWeightBook = float(modelConfig.loc['maxLandingWeight','Value'])
    bookLandingDistance = getPerf(landingDistanceBook,[tempVISA,flight.loc[threshold,'AltPress'], landingWeight, headwind],runwayUnits)
    approachTable.loc['Landing Distance'] = [int(landingDistance),int(bookLandingDistance), round(100*(landingDistance/bookLandingDistance-1)),runwayUnits]
    approachTable.loc['Headwind'] = [int(headwind),'-', '-','knots']
    bookCrosswind = float(modelConfig.loc['maxCrosswind','Value'])
    approachTable.loc['Crosswind'] = [int(abs(crosswind)),int(bookCrosswind), round(100*(abs(crosswind)/bookCrosswind-1)),'knots']
    approachTable.loc['Landing Weight'] = [int(landingWeight),int(landingWeightBook), round(100*(landingWeight/landingWeightBook-1)),'lbs']
    return approachTable, stableTable