
import pandas as pd
from libs.takeoffAnalyser import takeOffPerformance



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
        
    flightDate = flight.loc[0, "  Lcl Date"]
    flight = cleanUp(flight)
    fuelStart = flight.loc[0, "FQtyL"] +flight.loc[0, "FQtyR"]
    fuelEnd = flight.loc[flight.index.max(),"FQtyL"] +flight.loc[flight.index.max(), "FQtyR"]
    maxAltitude = flight['AltMSL'].max()
    maxTAS = flight['TAS'].max()
    maxIAS = flight['IAS'].max()
    maxGS = flight['GndSpd'].max()
    maxCHT = flight[['E1 CHT1','E1 CHT2','E1 CHT3','E1 CHT4','E1 CHT5','E1 CHT6',]].max().max()
    if 'E1 TIT1' in flight.columns:
        maxTIT = flight['E1 TIT1'].max()
    else:
        maxTIT = None
    meta = {"registration":registration, "model":model, "flightDate":flightDate,"fuelStart":fuelStart, "fuelEnd":fuelEnd, "maxAltitude":maxAltitude, "maxTAS":maxTAS,"maxIAS":maxIAS, "maxGS":maxGS, 'maxCHT':maxCHT,'maxTIT':maxTIT  }
    
    # run performnance comparisons
    takeOffAnalysis = takeOffPerformance(flight, model, takeoffMethod, takeoffWeight)
    climbAnalysis = pd.DataFrame()
    cruiseAnalysis = pd.DataFrame()
    approachAnalysis = pd.DataFrame()

    return {"meta":meta, "tables":[takeOffAnalysis,climbAnalysis, cruiseAnalysis, approachAnalysis]}
