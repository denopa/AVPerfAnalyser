
import pandas as pd
from libs.takeoffAnalyser import takeOffPerformance
from libs.climbAnalyser import climbPerformance


# takeoffWeight = 4135
# takeoffMethod = 'standard' # 'short`
# csvFileName = "flights/0ed1a44f-ee75-4f22-8ba3-cdb9a83783cb.csv"

def cleanUp(flight): #put everything in the right format
    flight.columns = flight.columns.str.lstrip()
    numericals = flight.columns.drop(['GPSfix', 'HSIS'])
    flight[numericals] = flight[numericals].apply(pd.to_numeric, errors='coerce')
    return flight

def analyseFlight(takeoffWeight,takeoffMethod, csvFileName):

    # load model and flight data
    with open(csvFileName) as dataFile:
        metaSource = pd.read_csv(dataFile)
    registration = metaSource.columns[7][14:-1]
    model = metaSource.columns[2][16:-1]
    with open(csvFileName) as dataFile:
        flight = pd.read_csv(dataFile, header=2)
        
    flightDate = flight["  Lcl Date"].max()
    flight = cleanUp(flight)
    fuelStart = flight.loc[0, "FQtyL"] +flight.loc[0, "FQtyR"]
    fuelEnd = flight.loc[flight.index.max(),"FQtyL"] +flight.loc[flight.index.max(), "FQtyR"]
    maxAltitude = flight['AltMSL'].max()
    maxTAS = flight['TAS'].max()
    maxIAS = flight['IAS'].max()
    maxGS = flight['GndSpd'].max()
    if 'E1 CHT1' in flight.columns:
        maxCHT = flight[['E1 CHT1','E1 CHT2','E1 CHT3','E1 CHT4','E1 CHT5','E1 CHT6',]].max().max()
    else:
        maxCHT = None
    if 'E1 TIT1' in flight.columns:
        maxTIT = flight['E1 TIT1'].max()
    else:
        maxTIT = None
    meta = {"registration":registration, "model":model, "flightDate":flightDate}
    flightSummary = pd.DataFrame.from_dict({"fuelStart":int(fuelStart), "fuelEnd":int(fuelEnd), "maxAltitude":int(maxAltitude), "maxTAS":int(maxTAS),"maxIAS":int(maxIAS), "maxGS":int(maxGS), "maxCHT":int(maxCHT),"maxTIT":int(maxTIT)}, orient='index', columns = [meta['flightDate']])
    flightSummary.index.name = meta['registration']

    # run performnance comparisons
    takeOffAnalysis = takeOffPerformance(flight, model, takeoffMethod, takeoffWeight)
    climbAnalysis = climbPerformance(flight, model)
    cruiseAnalysis = pd.DataFrame()
    approachAnalysis = pd.DataFrame()

    return {"meta":meta,"tables":[flightSummary, takeOffAnalysis,climbAnalysis, cruiseAnalysis, approachAnalysis]}
