import pandas as pd
from libs.utils import loadBook, getPerf, isaDiff, c2f, maxSpread, engineMetrics

def findCruise(flight, modelConfig): #cruise: not a climb power and within 200 feet of the max altitude
    climbPowerTreshold = modelConfig.loc['climbPowerTreshold','Value']
    climbPowerIndicator = modelConfig.loc['climbPowerIndicator','Value']
    cruiseMaxAlt = flight['AltB'].max()
    nonClimb = flight[flight[climbPowerIndicator]<float(climbPowerTreshold)]
    return nonClimb[nonClimb['AltB']> (cruiseMaxAlt-200)]

def findCruiseWeight(flight, cruise, model, takeoffWeight):
    startFuel = flight["FQtyL"].max() +flight["FQtyR"].max()
    cruiseStartFuel = cruise["FQtyL"].max() +cruise["FQtyR"].max()
    cruiseEndFuel = cruise["FQtyL"].min() +cruise["FQtyR"].min()
    with open('models/'+model+'/config.csv') as dataFile:
        modelConfig = pd.read_csv(dataFile, index_col='Variable')
    fuelWeightPerUSG = float(modelConfig.loc['fuelWeightPerUSG','Value'])
    return takeoffWeight - (startFuel - (cruiseStartFuel + cruiseEndFuel)/2) * fuelWeightPerUSG

def cruisePerformance(flight, model, modelConfig, takeoffWeight):
    cruise = findCruise(flight, modelConfig)
    cruiseWeight = findCruiseWeight(flight, cruise, model, takeoffWeight)
    cruiseBook = loadBook('cruise',model)
    cruisePowerVariable1 = modelConfig.loc['cruisePowerVariable1','Value']
    cruisePowerVariable2 = modelConfig.loc['cruisePowerVariable2','Value']
    cruiseReferenceWeight = float(modelConfig.loc['cruiseReferenceWeight','Value'])
    speedGainPer100lbs = float(modelConfig.loc['speedGainPer100lbs','Value'])
    cruisePower1 = cruise[cruisePowerVariable1].mean()
    cruisePower2 = cruise[cruisePowerVariable2].mean()
    pressAlt = cruise['AltPress'].mean()
    tempVISA = isaDiff(cruise['OAT'].mean(), pressAlt)
    bookCruiseTAS = getPerf(cruiseBook, [cruisePower1,cruisePower2,tempVISA, pressAlt], 'TAS') + (cruiseReferenceWeight - cruiseWeight) * speedGainPer100lbs / 100
    cruiseTAS = round(cruise['TAS'].mean(),1)
    cruiseTable = pd.DataFrame(columns=['Actual','Book','Variance','units'])
    cruiseTable.loc['Cruise Average TAS'] = [int(cruiseTAS), int(bookCruiseTAS), round(100*(cruiseTAS/bookCruiseTAS-1)),'knots']
    cruiseTable.loc['Cruise Average Ground Speed'] = [int(cruise['GndSpd'].mean()),int(bookCruiseTAS), round(100*(cruise['GndSpd'].mean()/bookCruiseTAS-1)), 'knots']
    if 'maxTIT' in modelConfig.index:
        maxCruiseTIT = cruise['E1 TIT1'].max()
        cruiseTable.loc['Cruise Max TIT'] = [round(maxCruiseTIT), modelConfig.loc['maxTIT','Value'], round(100*(maxCruiseTIT/float(modelConfig.loc['maxTIT','Value'])-1)),'degrees F']
    cruiseTable = engineMetrics(cruise, cruiseTable, modelConfig, 'Cruise')
    cruiseTable.loc['Cruise TAS Economy'] = [round(cruiseTAS/cruiseTable.loc['Cruise Average Fuel Flow','Actual'],1), round(bookCruiseTAS/cruiseTable.loc['Cruise Average Fuel Flow','Actual'],1), round(100*(1/cruiseTAS*bookCruiseTAS-1)),'nm/g']
    bookMaxAlt  = float(modelConfig.loc['cruiseMaxAlt','Value'])
    cruiseTable.loc['Cruise Max Altitude'] = [int(pressAlt), int(bookMaxAlt), round(100*(pressAlt/bookMaxAlt-1)),'feet']
    
    cruiseTable.loc['Cruise Average Temp vs ISA'] = [round(tempVISA),'-','-','degrees C']
    return cruiseTable     
