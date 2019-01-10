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
        ).query('type == "cs" & isEnabled == ' + isEnabled
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
            quotes.push(r.json())
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
    out.index.name = ['symbol']
    out.to_csv('./stock-valuation/financials-' + period + '.csv')
    return out

'''
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
'''

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

def sigmoid (x, x0=1, L=2):
    try:
        return L/(1+math.exp(x0-x))
    except:
        return np.nan

def stockValuation ():
    #Read Datasets
    quotes = pd.read_csv('./stock-valuation/quotes.csv'
        ).set_index('symbol')[['latestPrice', 'marketCap', 'sector']]
    quarterly = pd.read_csv('./stock-valuation/financials-quarterly.csv'
        ).set_index('symbol')
    annual = pd.read_csv('./stock-valuation/financials-annual.csv'
        ).set_index('symbol')

    # calculate input datasets for each company: lastest, margin, growth
    income = quarterly.sort_values('reportDate', ascending=False
        )[[ 'totalRevenue', 'netIncome', 'grossProfit']
        ].groupby('symbol'
        ).agg(sum4quarters)

    balance = quarterly.sort_values('reportDate', ascending=False
        )[['reportDate', 'totalLiabilities', 'totalAssets', 'totalCash', 'currentDebt', 'totalDebt', 'currentCash', 'currentAssets']
        ].groupby('symbol'
        ).head(1)

    fundamentals = pd.concat([latest, annual])
    margin =  fundamentals[['netIncome', 'grossProfit'] #_temp[['netIncome', 'grossProfit']
        ].div(fundamentals['totalRevenue'], axis=0
        ).groupby('symbol'
        ).median(
        ).rename(columns = lambda colname: colname+'Margin')

    growth = annual.sort_values('reportDate', ascending=False
        )[['totalRevenue', 'totalLiabilities', 'totalAssets', 'totalDebt']
        ].groupby('symbol'
        ).apply(lambda col: col.pct_change(-1).median()
        ).rename(columns = lambda colname: colname+'Growth')

    # merge all to make input dataset
    inputData = income.join(balance).join(growth).join(margin).join(quotes)

    # get model parameters: nominal discount, average growth, years, growth to margin rate
    r = requests.get("https://api.iextrading.com/1.0/stock/jnk/stats") # as a proxy for discount factor
    r.raise_for_status()
    nominalDiscount = r.json()['dividendYield']/100
    years = 5

    #calculate averageGrowth through weighted mean 
    snp500 = inputData.sort_values('totalRevenue', ascending=False)[:500]
    weights = snp500['totalRevenue']
    weights = weights/weights.sum()
    averageGrowth = (snp500["totalRevenueGrowth"]*weights).sum()

    growthToMarginRate = inputData['grossProfitMargin']#.fillna(inputData['netIncomeMargin'])

    # calculate each company parameters: revenue growth, debt growth, net growth, net margin
    revGrowth = inputData['totalRevenueGrowth'] - averageGrowth
    debtGrowth = inputData['totalDebtGrowth'].fillna(inputData['totalLiabilitiesGrowth']) - averageGrowth 
    netRevenueGrowth = inputData['totalRevenueGrowth'] - inputData['totalLiabilitiesGrowth']
    netMargin = inputData['netIncomeMargin'].where(inputData['netIncomeMargin']>0, 0) + growthToMarginRate *netRevenueGrowth.where(netRevenueGrowth>0, 0)

    # calculate values: base value, growth value, extra cash, debt potentials
    inputData['baseValue'] = inputData['totalRevenue'] * netMargin / nominalDiscount
    inputData['growthValue'] = years*revGrowth* inputData['totalRevenue']*netMargin / nominalDiscount
    inputData['extraCash'] = inputData['currentAssets'].fillna(inputData['currentCash']) - inputData['currentDebt'].fillna(0)
    inputData['debtPotential'] = - years * debtGrowth * inputData['totalDebt'].fillna(inputData['totalLiabilities'])
    # for financial frim that have no gross profit, just calculate asset minus debt
    inputData['baseValue'].fillna( inputData['totalAssets'] - inputData['totalLiabilities'], inplace=True) 

    # divide values to market cap to get relative value, then transform to return with sigmoid (logistic) function
    valuation = inputData[['baseValue', 'growthValue', 'extraCash', 'debtPotential']].div(inputData['marketCap'].replace(0, np.nan), axis=0)
    valuation['Base Return'] = valuation['baseValue'].apply(sigmoid)-1
    valuation['Growth Potential'] = (valuation['growthValue']+1).apply(sigmoid)-1
    valuation['Liquid Position'] = (valuation['extraCash']+1).apply(sigmoid)-1
    valuation['Debt Position'] = (valuation['debtPotential']+1).apply(sigmoid)-1

    # calculate final data: far price, net return, expected return, rating
    valuation['netReturn'] = valuation[['Base Return', 'Growth Potential', 'Liquid Position', 'Debt Position']].sum(axis=1)
    valuation['Expected Return'] = valuation['netReturn'] + nominalDiscount + averageGrowth 
    valuation['Market Cap'] = inputData['marketCap']
    valuation['Fair Price'] = inputData['latestPrice'] * (1 + valuation['netReturn'])
    valuation['Sector'] = inputData['sector']

    # transform returns to score and give rating: buy, sell, hold, strong buy, strong sell
    valuation['Rating'] = valuation[['netReturn', 'Base Return', 'Growth Potential', 'Liquid Position', 'Debt Position']
        ].applymap(score
        ).apply(sum, axis=1
        ).replace({-5:'strong sell', -4:'strong sell', -3: 'strong sell', -2: 'sell', -1: 'hold', 0: 'hold', 1: 'hold', 2:'buy', 3:'buy', 4:'strong buy', 5:'strong buy'})

    # write output
    output = valuation[['Rating', 'Fair Price', 'Expected Return', 'Base Return', 'Growth Potential', 'Liquid Position', 'Debt Position', 'Market Cap', 'Sector']]
    output.to_csv('./stock-valuation/stockValuation.csv')

    # calculate s&p 500 and return
    snp500 = valuation.sort_values('Market Cap', ascending=False)[:500]
    w = snp500['Market Cap']
    w = w/w.sum()
    SnP_return = 100*(snp500["Expected Return"]*w).sum()
    print(f's&p500 Expected Return: {SnP_return:.2f}%')
    return SnP_return

'''
tickers = ['NVDA', 'GOOG', 'AAPL', 'MSFT', 'MDB', 'AMZN', 'WMT', 'GS', 'F', 'T', 'BRK.A', 'FB', 'TSLA', 'ACN', 'MCD', 'CRM', 'TWTR', 'SNAP', 'GE', 'BA']
valuation.loc[tickers].iloc[:,5:]

#idx = ['reportDate',]
#inc = [ 'totalRevenue', 'costOfRevenue', 'grossProfit', 'researchAndDevelopment', 'operatingExpense', 'operatingIncome', 'netIncome' ]
#bs = ['totalAssets', 'currentAssets', 'totalCash', 'totalLiabilities', 'currentDebt', 'totalDebt', 'shareholderEquity']
#cf = ['currentCash', 'cashChange', 'cashFlow', 'operatingGainsLosses']
df = pd.read_csv("./stock-valuation/stockValuation.csv", index_col='symbol')
a = df.query('Rating in ["strong buy"]').sort_values('Market Cap', ascending=False).drop(['Fair Price', 'Rating'], axis=1).groupby('Sector').head(2)
'''

if __name__ == "__main__":
    getQuotes()
    getFinancials(period='annual')
    getFinancials()
    stockValuation()

