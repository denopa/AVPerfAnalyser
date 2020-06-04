import pandas as pd 
from libs.utils import haversine, calcWindComponents, isaDiff, getPerf, loadBook

def findClimb(flight, model): #select only datapoints where the power indicates a climb
    with open('models/'+model+'/config.csv') as dataFile:
        modelConfig = pd.read_csv(dataFile, index_col='Variable')
    climbPowerTreshold = modelConfig.loc['climbPowerTreshold','Value']
    climbPowerIndicator = modelConfig.loc['climbPowerIndicator','Value']
    return flight[flight[climbPowerIndicator]>float(climbPowerTreshold)]

def climbPerformance(flight, model):
    # actual flight performance
    climb = findClimb(flight, model)
    climbStartAlt = climb['AltPress'].min()
    climbEndAlt = climb['AltPress'].max()
    climbAlt = climbEndAlt - climbStartAlt
    climbUsedFuel = climb['E1 FFlow'].sum() / 3600 #this assumes 1 second measure intervals
    taxiFuel = flight.loc[:climb.index.min()]['E1 FFlow'].sum() /3600
    totalClimbFuel = climbUsedFuel + taxiFuel  #book table includes taxi and takeoff, so needs to be included here
    climbTime = len(climb) / 60 #assumes 1 second measure interval
    with open('models/'+model+'/config.csv') as dataFile:
        modelConfig = pd.read_csv(dataFile, index_col='Variable')
    climbPowerIndicator = modelConfig.loc['climbPowerIndicator','Value']
    climbISA = (isaDiff(climb.loc[climb.index.min(),'OAT'], climb.loc[climb.index.min(),'AltPress']) + isaDiff(climb.loc[climb.index.max(),'OAT'], climb.loc[climb.index.max(),'AltPress'])) #taking the average ISA variation across the climb
    climbPower = climb[climbPowerIndicator].mean()
    # book performance
    climbBook = loadBook('climb', model)
    base = getPerf(climbBook, [climbPower,climbISA, climbStartAlt], ['time','fuel','distance'])
    top = getPerf(climbBook, [climbPower,climbISA, climbEndAlt], ['time','fuel','distance'])
    bookClimbPerf = top - base
    # summary table
    climbTable = pd.DataFrame(columns=['Actual','Book','Variance %','Units'])
    climbTable.loc['Time'] = [round(climbTime), round(bookClimbPerf[0]), round(100*(climbTime/bookClimbPerf[0]-1)), 'minutes']
    climbTable.loc['Fuel Used'] = [round(totalClimbFuel,1),round(bookClimbPerf[1],1), round(100*(totalClimbFuel/bookClimbPerf[1]-1)), "USG"]
    climbTable.loc['Fuel Used per 10k feet'] = [round(totalClimbFuel/climbAlt*10000,1),round(bookClimbPerf[1]/climbAlt*10000,1), round(100*(totalClimbFuel/bookClimbPerf[1]-1)), "USG"]
    climbTable.loc['Average Vertical Speed'] = [round(climbAlt/climbTime),round(climbAlt/bookClimbPerf[0]),round(100*(1-climbTime/bookClimbPerf[0])),'fpm']
    climbTable.loc['Average IAS'] = [round(climb['IAS'].mean()),'-','-','knots']
    climbTable.loc['Average Power'] = [round(climbPower,1),str(climbBook.index.get_level_values(0).min())+'-'+str(climbBook.index.get_level_values(0).max()),'-',climbPowerIndicator]
    climbTable.loc['Average Fuel Flow'] = [round(climb['E1 FFlow'].mean()),'-','-','USG']
    climbTable.loc['Average temp vs ISA'] = [round(climbISA,1),'-','-','degrees C']
    return(climbTable)

