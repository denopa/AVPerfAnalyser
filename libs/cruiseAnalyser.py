import pandas as pd
from libs.utils import loadBook, getPerf, isaDiff, c2f, maxSpread

def findCruise(flight, model): #cruise: not a climb power and within 200 feet of the max altitude
    with open('models/'+model+'/config.csv') as dataFile:
        modelConfig = pd.read_csv(dataFile, index_col='Variable')
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

def cruisePerformance(flight, model, takeoffWeight):
    cruise = findCruise(flight, model)
    cruiseWeight = findCruiseWeight(flight, cruise, model, takeoffWeight)
    cruiseBook = loadBook('cruise',model)
    with open('models/'+model+'/config.csv') as dataFile:
        modelConfig = pd.read_csv(dataFile, index_col='Variable')
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
    cruiseTable = pd.DataFrame(columns=['Actual','Book','Variance%','units'])
    cruiseTable.loc['TAS'] = [int(cruiseTAS), int(bookCruiseTAS), round(100*(cruiseTAS/bookCruiseTAS-1)),'knots']
    cruiseTable.loc['Ground Speed'] = [int(cruise['GndSpd'].mean()),int(bookCruiseTAS), round(100*(cruise['GndSpd'].mean()/bookCruiseTAS-1)), 'knots']
    cruiseTable.loc['Temp vs ISA'] = [round(tempVISA),'-','-','degrees C']
    if 'maxTIT' in modelConfig.index:
        maxCruiseTIT = cruise['E1 TIT1'].max()
        cruiseTable.loc['Max TIT'] = [int(maxCruiseTIT), float(modelConfig.loc['maxTIT','Value']), round(100*(maxCruiseTIT/float(modelConfig.loc['maxTIT','Value'])-1)),'degrees F']
    if 'E1 CHT1' in cruise.columns:
        maxCHT = cruise[['E1 CHT1','E1 CHT2','E1 CHT3','E1 CHT4','E1 CHT5','E1 CHT6']].max().max()
        maxCHTSpread = cruise[['E1 CHT1','E1 CHT2','E1 CHT3','E1 CHT4','E1 CHT5','E1 CHT6']].apply(maxSpread).max()
        maxEGTSpread = cruise[['E1 EGT1','E1 EGT2','E1 EGT3','E1 EGT4','E1 EGT5','E1 EGT6']].apply(maxSpread).max()
        cruiseTable.loc['Max CHT'] = [int(maxCHT),round(float(modelConfig.loc['maxCHT','Value'])), round(100*(maxCHT/float(modelConfig.loc['maxCHT','Value'])-1)),'degrees F'  ]
        cruiseTable.loc['Max CHT Spread'] = [int(maxCHTSpread),'-','-','degrees F']
        cruiseTable.loc['Max EGT Spread'] = [int(maxEGTSpread),'-','-','degrees F']
    if 'E1 CDT' in cruise.columns:
        averageICEfficiency = 100*((cruise['E1 CDT']-cruise['E1 IAT'])/(cruise['E1 CDT']-cruise['OAT'].apply(c2f))).mean()
        cruiseTable.loc['Intercooler Efficiency'] = [int(averageICEfficiency),'-','-','%']
    
    return cruiseTable     
