import pandas as pd 
from libs.utils import haversine, calcWindComponents, isaDiff, getPerf, loadBook

def findClimb(flight, model): #select only datapoints where the power indicates a climb
    with open('models/'+model+'/config.csv') as dataFile:
        modelConfig = pd.read_csv(dataFile, index_col='Variable')
    climbPowerTreshold = modelConfig.loc['climbPowerTreshold','Value']
    climbPowerIndicator = modelConfig.loc['climbPowerIndicator','Value']
    return flight[flight[climbPowerIndicator]>float(climbPowerTreshold)]

def analyseClimb(flight, model):
    climb = findClimb(flight, model)
    climbStartAlt = climb['AltPress'].min()
    climbEndAlt = climb['AltPress'].max()
    climbUsedFuel = climb['E1 FFlow'].sum() / 3600 #this assumes 1 second measure intervals
    taxiFuel = flight.loc[:climb.index.min()]['E1 FFlow'].sum() /3600
    totalClimbFuel = climbUsedFuel + taxiFuel  #book table includes taxi and takeoff, so needs to be included here
    with open('models/'+model+'/config.csv') as dataFile:
        modelConfig = pd.read_csv(dataFile, index_col='Variable')
    climbPowerIndicator = modelConfig.loc['climbPowerIndicator','Value']
    climbISA = (isaDiff(climb.loc[climb.index.min(),'OAT'], climb.loc[climb.index.min(),'AltPress']) + isaDiff(climb.loc[climb.index.max(),'OAT'], climb.loc[climb.index.max(),'AltPress'])) #taking the average ISA variation across the climb
    climbPower = climb[climbPowerIndicator].mean()
    climbBook = loadBook('climb', model)
    base = getPerf(climbBook, [climbPower,climbISA, climbStartAlt], ['time','fuel','distance'])
    top = getPerf(climbBook, [climbPower,climbISA, climbEndAlt], ['time','fuel','distance'])