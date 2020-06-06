# TODO save results in database
import pandas as pd
from libs.takeoffAnalyser import takeoffPerformance
from libs.climbAnalyser import climbPerformance
from libs.cruiseAnalyser import cruisePerformance
from libs.approachAnalyser import approachPerformance

# takeoffWeight = 4135
# takeoffMethod = 'standard' # 'short`
# approachType = 'IFR' # 'VFR'
# csvFileName = "flights/0ed1a44f-ee75-4f22-8ba3-cdb9a83783cb.csv"

def cleanUp(flight): #put everything in the right format
    flight.columns = flight.columns.str.lstrip()
    numericals = flight.columns.drop(['GPSfix','HSIS','Lcl Date','Lcl Time','UTCOfst','AtvWpt'])
    flight[numericals] = flight[numericals].apply(pd.to_numeric, errors='coerce')
    return flight

def analyseFlight(takeoffWeight,takeoffMethod, approachType, csvFileName):

    # load model and flight data
    with open(csvFileName) as dataFile:
        metaSource = pd.read_csv(dataFile)
    registration = metaSource.columns[7][14:-1]
    model = metaSource.columns[2][16:-1].replace(" ","")
    with open(csvFileName) as dataFile:
        flight = pd.read_csv(dataFile, header=2)
        
    flightDate = flight["  Lcl Date"].max()
    flight = cleanUp(flight)
    fuelStart = flight.loc[0, "FQtyL"] +flight.loc[0, "FQtyR"]
    fuelEnd = flight.loc[flight.index.max(),"FQtyL"] +flight.loc[flight.index.max(), "FQtyR"]
    maxAltitude = flight['AltMSL'].max()
    maxG = flight['NormAc'].max() +1 
    minG = flight['NormAc'].min() +1
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
    flightSummary = pd.DataFrame.from_dict({"Fuel Start":int(fuelStart), "Fuel End":int(fuelEnd), "Max Altitude":int(maxAltitude), "Max Positive Load":round(maxG,2), "Max Negative Load":round(minG,2), "Max IAS":int(maxIAS), "Max TAS":int(maxTAS),"Max GS":int(maxGS), "Max CHT":int(maxCHT),"Max TIT":'-'}, orient='index', columns = [meta['flightDate']])
    flightSummary.index.name = meta['registration']
    flightSummary.loc['Max TIT'] = int(maxTIT)

    #load book limits
    with open('models/'+model+'/config.csv') as dataFile:
        modelConfig = pd.read_csv(dataFile, index_col='Variable')
    bookMaxFuel = int(modelConfig.loc['maxFuel','Value'])
    bookMinFuel = int(modelConfig.loc['minFuel','Value'])
    bookMaxAltitude = int(modelConfig.loc['maxAltitude','Value'])
    bookMaxG = float(modelConfig.loc['maxG','Value'])
    bookMinG = float(modelConfig.loc['minG','Value'])
    bookMaxIAS = int(modelConfig.loc['maxIAS','Value'])
    bookMaxCHT = int(modelConfig.loc['maxCHT','Value'])
    bookMaxTIT = int(modelConfig.loc['maxTIT','Value'])
    flightSummary['Book'] = [bookMaxFuel, bookMinFuel, bookMaxAltitude, bookMaxG, bookMinG, bookMaxIAS,'-','-',bookMaxCHT, bookMaxTIT ]

    # run performnance comparisons
    takeoffAnalysis = takeoffPerformance(flight, model, modelConfig, takeoffMethod, takeoffWeight)
    climbAnalysis = climbPerformance(flight, model, modelConfig)
    cruiseAnalysis = cruisePerformance(flight, model, modelConfig, takeoffWeight)
    approachAnalysis, stabilityAnalysis = approachPerformance(flight, model, modelConfig, approachType, takeoffWeight)

    return {"meta":meta,"tables":[flightSummary, takeoffAnalysis,climbAnalysis, cruiseAnalysis, approachAnalysis, stabilityAnalysis]}
