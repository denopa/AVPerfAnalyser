# this can be used to ingest all the flights in a folder
import os, re
import pandas as pd
from libs.flightAnalyser import analyseFlight, cleanUp

folderPath = '/users/Patrick/Documents/Flights' ###fill this in

# all those values will be set to default:
takeoffMaxWeight = 4135 #an estimate of the weight on those flights if the plane had had full fuel
takeoffMethod = 'standard' # 'short`
approachType = 'IFR' # 'VFR'
maxFuel = 120 #the takeoff weight will be lowered if the fuel is not full
maxWeightFuelDuration = 120 #in minutes, length above which a flight is considered by default to be done at max weight

def allowedFiles(filename): 
    #use this RegEx to grab the file extension and see if it is allowed
        if re.search(r'([^.]*)$', filename).group().upper() in ['CSV']:
            return True
        else:
            return False

def correctWeightForFuel(flight, model):
    startFuel = flight['FQtyL'].max() + flight['FQtyR'].max()
    with open('models/'+model+'/config.csv') as dataFile:
        modelConfig = pd.read_csv(dataFile, index_col='Variable')
    fuelWeightPerUSG = float(modelConfig.loc['fuelWeightPerUSG','Value'])
    return (maxFuel - startFuel) * fuelWeightPerUSG

for file in os.listdir(folderPath):
    if allowedFiles(file):
        csvFileName = folderPath + "/" + file
        with open(csvFileName) as dataFile:
            metaSource = pd.read_csv(dataFile)
            registration = metaSource.columns[7][14:-1]
            model = metaSource.columns[2][16:-1].replace(" ","")
        with open(csvFileName) as dataFile:
            flight = pd.read_csv(dataFile, header=2)
        flight = cleanUp(flight)
        if (flight.datetime.max() - flight.datetime.min()).seconds/60 < maxWeightFuelDuration:
            takeoffWeight = takeoffMaxWeight - correctWeightForFuel(flight, model)
        else:
            takeoffWeight = takeoffMaxWeight
        analyseFlight(takeoffWeight, takeoffMethod, approachType, csvFileName)
