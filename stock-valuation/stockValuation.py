'''
Calculates the stock valuation based on growth to margin conversion
assumption:
- The firm current situation lasts forever because it is driven by core competency
- Revenue Growth can be converted to Net Profit Margin in future

Formula:
netValue = baseValue + growthPotential + extraCash + debtCoverage
baseValue = Revenue * netMargin / discount
growthValue = years * growthRate * Revenue / discount
extraCash = currentAsset - currentDebt
debtCoverage = years * debtGrowth * debt

- every value will be transformed with Sigmoid (logistic function) to convert to return
- growth will be calculated base on "growth-averageGrowth"

expected return = netReturn + discount + averageGrowth
'''
import requests
import pandas as pd
import numpy as np
import math
import time

base = "https://api.iextrading.com/1.0/stock/"

def getTickers (isEnabled = True):
    r = requests.get('https://api.iextrading.com/1.0/ref-data/symbols')
    r.raise_for_status()
    return pd.DataFrame(r.json()
        ).query('type == "cs" & isEnabled == ' + str(isEnabled)
        )['symbol']

def getCompanies (companies=[]): # run occasionally to create dataframe of companies
    tickers = getTickers()
    s = requests.Session()
    for ticker in tickers:
        try:
            r = s.get(base + ticker + '/company')
        except Exception:
            print('could not make get connection with server at ticker ', ticker)
            time.sleep(5)
            s = requests.Session()
            r = s.get(base + ticker + '/company')
        if r.ok:
            print(ticker)
            companies.append(r.json())
        else:
            print('Could not fetch', ticker)
    out = pd.DataFrame(companies)
    out.to_csv("./stock-valuation/companies.csv", index=False)

def getQuotes (quotes=[]): # runs daily
    ## parse price and market cap from quote request
    tickers = getTickers()
    s = requests.Session()
    for ticker in tickers:
        try:
            r = s.get(base + ticker + '/quote')
        except Exception:
            print ('could not make connection with iex server at ticker', ticker)
            time.sleep(5)
            s = requests.Session()
            r = s.get(base + ticker + '/quote')
        if r.ok:
            quotes.append(r.json())
            print(ticker)
        else:
            print ('did not find quote information on iex for', ticker)
    quotesDF = pd.DataFrame.from_records(quotes)
    quotesDF.to_csv('./stock-valuation/quotes.csv', index=False)
    return quotesDF

def getFinancials (period = 'quarterly', financials={}): # or period = annual
    tickers = getTickers()
    s = requests.Session()
    for symbol in tickers: 
        try:   
            r = s.get(base + symbol + '/financials?period=' + period)
            if r.ok and r.text!='{}':
                financials[symbol] = pd.DataFrame(r.json()['financials'])
                print(symbol)
            else:
                print('iex did not respond to request or no data available for ', symbol)
        except Exception:
            print('something went wrong either connection or extract dataframe for ', symbol)
            time.sleep(5)
            s = requests.Session() # renew the session
            r = s.get(base + symbol + '/financials?period=' + period)
    out = pd.concat(financials).reset_index(level=1, drop=True)
    out.index.name = 'symbol'
    out.to_csv('./stock-valuation/financials-' + period + '.csv')
    return out

def sum4quarters (quarters):
    try:
        return quarters.iloc[[0,1,2,3]].sum(skipna=False)
    except:
        print(quarters.index, 'does not have 4 quarters')


def score(x, x0=0.1): # transform return to buy (+1) or hold (0) or sell (-1)
    if x > x0:
        return 1
    elif x < -x0:
        return -1
    elif x is np.nan:
        return np.nan
    else:
        return 0

def logistic (x, x0=1, L=2, k=4): # k=4 means in middle it has slope of 1
    try:
        return L/(1+math.exp(k*(x0-x)))
    except:
        return np.nan

def annual_percent_change (df):
    df = df.drop_duplicates(subset=['reportDate'], keep='last').sort_values(['reportDate'], ascending=False)
    df = df.set_index('reportDate')
    annual_time_delta = pd.to_datetime(df.index).to_series().diff(-1).apply(lambda x: x.days)/365
    df = df.pct_change(-1)
    return df.multiply(annual_time_delta, axis=0)

def weightedMean(df, weightCol='Market Cap'):
    w = df[weightCol]
    total = w.sum()
    w = w/total
    df2 = df.drop(weightCol, axis=1).multiply(w, axis=0).sum()
    df2[weightCol] = total
    return df2

def prepare_input_dataset_for_stock_valuation ():
    #Read Datasets
    quotes = pd.read_csv('./stock-valuation/quotes.csv'
        ).set_index('symbol')[['companyName', 'sector', 'latestPrice', 'marketCap']]
    quarterly = pd.read_csv('./stock-valuation/financials-quarterly.csv'
        ).set_index('symbol')
    annual = pd.read_csv('./stock-valuation/financials-annual.csv'
        ).set_index('symbol')

    # calculate input datasets for each company: lastest, margin, growth
    income_variables = ['operatingRevenue', 'operatingGainsLosses', 'researchAndDevelopment', 'totalRevenue', 'costOfRevenue', 'grossProfit', 'operatingExpense', 'operatingIncome', 'netIncome', 'cashChange', 'cashFlow'] # cashChange is net cash change, cash flow is net operating cash flow
    trailing_income = quarterly.sort_values('reportDate', ascending=False
        )[income_variables
        ].groupby('symbol'
        ).agg(sum4quarters)

    balance_variables = [var for var in quarterly.columns if var not in income_variables]
    trailing_balance = quarterly.sort_values('reportDate', ascending=False
        )[balance_variables
        ].groupby('symbol'
        ).head(1)

    last_year_trailing = trailing_income.join(trailing_balance) # I have no idea what total cash is: !!!!!!! NEVER USE IT

    fundamentals = pd.concat([last_year_trailing, annual], sort=False)
    margin =  fundamentals[['netIncome', 'operatingIncome', 'grossProfit', 'cashFlow', 'operatingExpense', 'costOfRevenue', 'totalAssets'] #_temp[['netIncome', 'grossProfit']
        ].div(fundamentals['totalRevenue'], axis=0
        ).groupby('symbol'
        ).median(
        ).rename(columns = lambda colname: colname+'Margin')

    growth = fundamentals.groupby('symbol'
        )[['reportDate', 'totalRevenue', 'totalLiabilities', 'cashFlow', 'totalDebt', 'netIncome', 'shareholderEquity', 'grossProfit', 'operatingIncome', 'operatingExpense', 'costOfRevenue', 'totalAssets']
        ].apply(annual_percent_change
        ).groupby('symbol'
        ).median(
        ).rename(columns = lambda colname: colname+'Growth')

    # get the latest valid number from fundamentals as the latest
    latest = fundamentals.groupby('symbol').first()

    # merge all to make input dataset
    inputData = latest.join(growth).join(margin).join(quotes)
    #inputData['capitalReturn'] = inputData['netIncome'] / inputData['marketCap']
    #inputData['capitalReturn'] = inputData['capitalReturn'].where(inputData['capitalReturn']>0, 0)
    #or use margin medians: inputData['netIncomeMargin'] * inputData['totalRevenue'] / inputData['marketCap']
    return inputData


########## Financial Modeling thorugh year by year
## Growth decays, Growth means revenue growth as it is reliable trend with min disparity and consumer channel
## Gross profit is marginal profit (variable costs) and depends directly on Revenue
## Operating Expense in fixed cost and remains constant
## Tax depends on Operating income
## Tax credit and Interest works the same way and they are proportional to Revenue
def flow (incomes, DecayRate=0.8, TaxRate=0.21):
    Growth = incomes['Growth'] * DecayRate
    #Growth = Growth.where(Growth>0, 0)
    Revenue = incomes['Revenue'] * (1 + Growth)
    grossMargin = incomes['GrossIncome']/incomes['Revenue']
    GrossIncome =  Revenue * grossMargin
    #GrossIncome = GrossIncome.where(GrossProfit>0, 0)
    fixedCost = incomes['GrossIncome'] - incomes['OperatingIncome']
    OperatingIncome = GrossIncome - fixedCost
    ExpectedIncome = OperatingIncome * (1-TaxRate) # expected income is what goes to financial stakeholders and share holders
    taxAndInterestCreditRate = (incomes['NetIncome'] - incomes['ExpectedIncome'])/incomes['Revenue']
    NetIncome = ExpectedIncome + taxAndInterestCreditRate * Revenue #* DecayRate
    nextYearIncomes = pd.concat([NetIncome, ExpectedIncome, OperatingIncome, GrossIncome, Revenue, Growth], axis=1)
    return nextYearIncomes


def transform_returns (col):
    m = col.median()
    return col.apply(lambda x: logistic(x, m, 2, 4))


def intrinsic_value (DecayRate = 0.8):
    inputData = prepare_input_dataset_for_stock_valuation()
    Names = ['NetIncome', 'ExpectedIncome', 'OperatingIncome', 'GrossIncome', 'Revenue', 'Growth']
    ## create the starter dataset
    Growth = inputData['totalRevenueGrowth']
    Revenue = inputData['totalRevenue']
    GrossIncome = inputData['grossProfitMargin'] * Revenue
    OperatingIncome = GrossIncome - inputData['operatingExpense']
    ExpectedIncome = OperatingIncome.where(OperatingIncome<0, OperatingIncome * (1 - 0.21)) # tax rate = 0.21 for positive operating income
    NetIncome = (inputData['netIncomeMargin'] / inputData['operatingIncomeMargin']) * OperatingIncome
    incomes = pd.concat([NetIncome, ExpectedIncome, OperatingIncome, GrossIncome, Revenue, Growth], axis=1
        ).set_axis(Names, axis='columns', inplace=False)
    ## create future incomes
    futureAnnualIncomes = {}
    for year in range(50):
        incomes = flow(incomes, DecayRate).set_axis(Names, axis='columns', inplace=False)
        futureAnnualIncomes[year+1] = incomes
    FutureIncomes = pd.concat(futureAnnualIncomes, names=['year', 'symbol'])
    ## create the discount rates along dataset rows and then divide to get present value of incomes which gives economic value of companies
    snp500 = inputData.drop_duplicates('companyName').sort_values('totalRevenue', ascending=False)[:500]
    averageGrowth = weightedMean(snp500[['totalRevenueGrowth', 'totalRevenue']], weightCol='totalRevenue')['totalRevenueGrowth']
    bondYield = requests.get("https://api.iextrading.com/1.0/stock/jnk/stats").json()['dividendYield']/100
    DiscountRate = bondYield + averageGrowth * DecayRate
    years = FutureIncomes.index.get_level_values('year')
    Discounts = 1/(1+DiscountRate)**years
    FuturesNPV = FutureIncomes.multiply(Discounts, axis=0
        ).groupby('symbol').sum()#skipna=False
    FuturesNPV.to_csv("./stock-valuation/stocks-futuresNPV.csv")
    return DiscountRate


def BuyOrSell (r):
    if r > 0.25:
        return 'Buy'
    elif r >= -0.25:
        return 'Hold'
    elif r < -0.25:
        return 'Sell'
    else:
        return np.nan
        

def adjustedReturn (x, center=1):
    x = x/center
    return np.where(x>1, np.log(x), np.exp(x-1)-1)    




def stock_info ():

inputData = prepare_input_dataset_for_stock_valuation()

DiscountRate = intrinsic_value()

snp500 = inputData.drop_duplicates('companyName').sort_values('totalRevenue', ascending=False)[:500]
averageGrowth = weightedMean(snp500[['totalRevenueGrowth', 'totalRevenue']], weightCol='totalRevenue')['totalRevenueGrowth']
bondYield = requests.get("https://api.iextrading.com/1.0/stock/jnk/stats").json()['dividendYield']/100
DiscountRate = bondYield + averageGrowth * DecayRate


FuturesNPV = pd.read_csv('./stock-valuation/stocks-futuresNPV.csv', index_col='symbol').rename(columns = lambda name: name + 'FuturesNPV')

a = FuturesNPV.drop('GrowthFuturesNPV', axis=1)

a = inputData.join(FuturesNPV)
a['Return'] = b = a['NetIncomeFuturesNPV'] / a['marketCap']
flag = (b>0) & (b<10) 
b = b[flag]
a.loc[flag, 'Expected Net Return'] = adjustedReturn(b, center=1)

a['Fair Price'] = a['latestPrice'] * (1+a['Expected Net Return'])

a['Next Year Return'] = DiscountRate + a['Expected Net Return']
a['BuyOrSell'] = a['Expected Net Return'].apply(BuyOrSell)

a['Direct Cost'] = a['RevenueFuturesNPV']-a['GrossIncomeFuturesNPV']
a['Operating Expense'] = a['GrossIncomeFuturesNPV']-a['OperatingIncomeFuturesNPV']
a['Interest and Tax'] = a['OperatingIncomeFuturesNPV']-a['NetIncomeFuturesNPV']
a['Net Profit'] = a['NetIncomeFuturesNPV']


a.loc[tickers].round(2).reset_index().apply(lambda row: row.to_json('./stock-valuation/stock-json-files/' + row.symbol + '.json'), axis=1)


'''

def sectorsOutlook ():
    stockReturns = pd.read_csv('./stock-valuation/stockValuation.csv').set_index('symbol')
    #stockReturns['Financial Position'] = stockReturns['Liquid Position'].fillna(0) + stockReturns['Debt Position'].fillna(0)
    cols = ['Expected Return', 'Base Return', 'Growth Potential', 'Financial Position', 'Market Cap']
    #stockReturns = stockReturns.join(quotes['companyName']).rename(columns = {'companyName': 'Name'})
    sectors = stockReturns.drop_duplicates('Name').groupby('Sector')[cols].apply(weightedMean)
    sectors = sectors.append(weightedMean(sectors).rename('Total Market'))
    sectors.to_csv('./stock-valuation/sectors.csv')





#idx = ['reportDate',]
#inc = [ 'totalRevenue', 'costOfRevenue', 'grossProfit', 'researchAndDevelopment', 'operatingExpense', 'operatingIncome', 'netIncome' ]
#bs = ['totalAssets', 'currentAssets', 'totalCash', 'totalLiabilities', 'currentDebt', 'totalDebt', 'shareholderEquity']
#cf = ['currentCash', 'cashChange', 'cashFlow', 'operatingGainsLosses']
output = pd.read_csv("./stock-valuation/stockValuation.csv", index_col='symbol')
valuation = output.query('Rating in ["strong buy"]').sort_values('Market Cap', ascending=False).drop(['Fair Price', 'Rating'], axis=1).groupby('Sector').head(2)
tickers = ['INTC', 'NVDA', 'GOOG', 'FB', 'AAPL', 'MSFT', 'CRM', 'ACN', 'MDB', 'AMZN', 'BABA', 'WMT', 'MCD', 'GS', 'BRK.A', 'GE', 'BA', 'TM', 'F', 'TSLA', 'T', 'VZ', 'TWTR', 'SNAP']
output.drop(['Market Cap', 'Fair Price', 'Sector'], axis=1).loc[tickers]

IT NEEDS TEST AND VALIDATION:
def getHistoricalPrices (period='1y', prices = {}):
    tickers = getTickers()
    s = requests.Session()
    for ticker in tickers:
        try:
            r = s.get(base + ticker + '/chart/' + period)
            prices[ticker] = pd.DataFrame(r.json())[['date', 'close']].set_index('date')['close']
            print(ticker, 'done')
        except:
            print('could not download or parse prices of ', ticker)
    prices = pd.DataFrame(prices)
    return prices

# calculate s&p 500 and return
snp500 = valuation.drop_duplicates('Name').sort_values('Market Cap', ascending=False)[:500]
w = snp500['Market Cap']
w = w/w.sum()
SnP_return = 100*(snp500["Expected Return"]*w).sum()
print(f's&p500 Expected Return: {SnP_return:.2f}%')

'''

if __name__ == "__main__":
    getQuotes()
    getFinancials(period='annual')
    getFinancials()
    stockValuation()
    sectorsOutlook()

