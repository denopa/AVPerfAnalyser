# TODO 
import pandas as pd
import sqlalchemy, os
from libs.takeoffAnalyser import takeoffPerformance
from libs.climbAnalyser import climbPerformance
from libs.cruiseAnalyser import cruisePerformance
from libs.approachAnalyser import approachPerformance

# takeoffWeight = 4135
# takeoffMethod = 'standard' # 'short`
# approachType = 'IFR' # 'VFR'
# csvFileName = "flights/08934f46-0f14-4bdf-8c7c-5ce4f75d46f7.csv"

def cleanUp(flight): #put everything in the right format
    flight.columns = flight.columns.str.lstrip()
    numericals = flight.columns.drop(['GPSfix','HSIS','Lcl Date','Lcl Time','UTCOfst','AtvWpt'])
    flight[numericals] = flight[numericals].apply(pd.to_numeric, errors='coerce')
    flight['year'] = flight['Lcl Date'].apply(lambda x: x[:4])
    flight['month'] = flight['Lcl Date'].apply(lambda x: x[5:7])
    flight['day'] = flight['Lcl Date'].apply(lambda x: x[8:10])
    flight['hour'] = pd.to_numeric(flight['Lcl Time'].apply(lambda x: x[:3]), errors='coerce') - pd.to_numeric(flight['UTCOfst'].apply(lambda x: x[:5]), errors='coerce')
    flight['minute'] = flight['Lcl Time'].apply(lambda x: x[4:6])
    flight['second'] = flight['Lcl Time'].apply(lambda x: x[7:9])
    flight['datetime'] = pd.to_datetime(flight[['year','month','day','hour','minute','second']], errors='coerce')
    flight.drop(columns=['year','month','day','hour','minute','second'], inplace=True)
    return flight

def transform(csvFileName, meta, tables): #linearise tables
    linearTable = pd.DataFrame.from_dict(meta, orient='index')
    for table in tables:
        lt = pd.Series()
        for column in table.columns:
            addUpLt = table[column]
            addUpLt.index = addUpLt.index + " " + column
            lt = pd.concat([lt, addUpLt])
        linearTable = pd.concat([linearTable, lt])
    linearTable = linearTable.transpose()
    linearTable.index = [os.path.basename(csvFileName)]
    linearTable.index.name = 'file'
    return linearTable

def saveToDB(linearTable):
    try:
        sqlURL =  os.environ['DATABASE_URL']
    except:
        sqlURL = "postgresql://localhost/AVPerformance"
    engine = sqlalchemy.create_engine(sqlURL)
    conn = engine.connect()
    frame = linearTable.to_sql('analysed_flights', conn, if_exists='append')
    conn.close()

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
    flightDuration = round((flight['datetime'].max() - flight['datetime'].min()).seconds / 3600,1)
    continousData = 0.97*len(flight)/3600 < flightDuration < 1.03*len(flight)/3600
    meta = {"registration":registration, "model":model, "flightDate":flightDate, 'flightDuration':flightDuration, 'continuousData':continousData}
    flightSummary = pd.DataFrame.from_dict({"Flight Fuel Start":int(fuelStart), "Flight Fuel End":int(fuelEnd), "Flight Max Altitude":int(maxAltitude), "Flight Max Positive Load":round(maxG,2), "Flight Max Negative Load":round(minG,2), "Flight Max IAS":int(maxIAS), "Flight Max TAS":int(maxTAS),"Flight Max GS":int(maxGS), "Flight Max CHT":int(maxCHT),"Flight Max TIT":'-'}, orient='index', columns = ['Actual'])
    flightSummary.loc['Flight Max TIT'] = int(maxTIT)

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
    try:
        takeoffAnalysis, takeoffStability = takeoffPerformance(flight, model, modelConfig, takeoffMethod, takeoffWeight)
    except:
        takeoffAnalysis = pd.DataFrame()
        takeoffStability = pd.DataFrame()
    try:
        climbAnalysis = climbPerformance(flight, model, modelConfig)
    except:
        climbAnalysis = pd.DataFrame()
    try:
        cruiseAnalysis = cruisePerformance(flight, model, modelConfig, takeoffWeight)
    except:
        cruiseAnalysis = pd.DataFrame()
    try:
        approachAnalysis, approachStability = approachPerformance(flight, model, modelConfig, approachType, takeoffWeight)
    except:
        approachAnalysis = pd.DataFrame()
        approachStability = pd.DataFrame()
    tables = [flightSummary, takeoffAnalysis,takeoffStability, climbAnalysis, cruiseAnalysis, approachAnalysis, approachStability]

    # transform and save to DB
    linearTable = transform(csvFileName, meta, tables)
    linearTable.loc[linearTable.index[0],'Flight'] = flight.to_json()
    # saveToDB(linearTable)

    return {"meta":meta,"tables":tables}
