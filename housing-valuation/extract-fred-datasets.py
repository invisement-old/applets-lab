'''
fetch, reshape, extract, and save FRED series. 
for each indicators.csv every record has (date, value)
'''
### PATHES
HOST = "/home/invisement/PROJECTS/inVisement2/apps-workshop/"
OUTPUT_PATH = HOST + "data/"
FRED_ENDPOINT= "https://api.stlouisfed.org/fred/series/observations"

def main():
    sucess = [try_or_skip(fetch_and_save_fred_dataset, dataset=d) for d in FRED_SERIES.keys()]
    print('successful extracts = ', sucess)

### LIBRARIES
import requests, pandas as pd

### CONSTANTS
FRED_API_KEY= "88b9092ad3db013e454ea78d5a1084c9"
FRED_FILE_TYPE= "json"


### DATASETS: INPUTS and OUTPUTS
FRED_SERIES= { 
    "high yield spread": {
        "source": "FRED",
        "id": "BAMLH0A0HYM2EY",
        "title": "Corporate Yield Spread",
        "subtitle": "Risky Corporate Bond Yield minus Treasury Bond Yield"
        "unit": "Percent",
        "frequency": "D"
    },
    "fed total assets": {
        "source": "FRED",
        "id": "WALCL",
        "title": "Federal Reserve Total Assets",
        "subtitle": "Fed Balance Sheet Total Assets in Millions of Dollar",
        "unit": "Millions of USD",
        "frequency": "D"
    },
    "treasury yield spread": {
        "id": "T10Y2Y",
        "title": "Treasury Bond Spread" ,
        "source": "FRED",
        "frequency": "D",
        "unit": "Percent",
        "subtitle": "10 year treasury yield minus 2 year treasury yield",
    },
    "consumer sentiment": {
        "id": "UMCSENT",
        "title": "Consumer Sentiment",
        "source": "FRED",
        "unit": "index (1966:Q1=100)",
        "frequency": "Q",
        "subtitle": "Consumer Sentiment Index"
    },
    "investment to gdp": {
        "id": "A006RE1Q156NBEA",
        "title": "Investment To GDP",
        "source": "FRED",
        "unit": "Percent",
        "frequency": "Q",
        "subtitle": "Share of Investment from GDP in Percent"
    },
    "gdp": {
        "id": "GDP",
        "source": "FRED",
        "title": "US Nominal GDP",
        "unit": "Billions of USD",
        "subtitle": "Nominal Gross Domestic Product",
        "frequency": "Q",
        "adjusted": "Seasonally Adjusted"
    },
    "nominal gdp growth": {
        "id": "A191RP1Q027SBEA",
        "source": "FRED",
        "title": "US Nominal GDP Growth",
        "unit": "Percent",
        "subtitle": "Real GDP Annual Change in Percent",
        "frequency": "Q",
        "adjusted": "Seasonally Adjusted"
    },
    "real gdp growth": {
        "id": "A191RO1Q156NBEA",
        "source": "FRED",
        "title": "US Real GDP Growth",
        "unit": "Percent",
        "subtitle": "Real GDP Annual Change in Percent",
        "frequency": "Q",
        "adjusted": "From A Year Ago"
    },
    "real gdp per capita": {
        "id": "A939RX0Q048SBEA",
        "source": "FRED",
        "title": "US Real GDP Growth",
        "unit": "USD",
        "subtitle": "US GDP Per Capita in 2012 Chained Dollar",
        "frequency": "Q",
        "adjusted": "Seasonally Adjusted"
    },
    "mortgage rate 30 year fixed": {
        "id": "MORTGAGE30US",
        "source": "FRED",
        "title": "30 Year Fixed Mortgage Rate Average",
        "frequency": "D",
        "unit": "Percent",
        "adjusted": "Seasonally Adjusted",
        "subtitle": ""
    },
    "mortgage rate 15 year fixed": {
        "id": "MORTGAGE15US",
        "source": "FRED",
        "title": "15 Year Fixed Mortgage Rate Average",
        "frequency": "D",
        "unit": "Percent",
        "adjusted": "Seasonally Adjusted",
        "subtitle": ""
    },
    "mortgage rate 5_1 year adjusted": {
        "id": "MORTGAGE5US",
        "source": "FRED",
        "title": "5/1 Year Adjusted Mortgage Rate Average",
        "frequency": "D",
        "unit": "Percent",
        "adjusted": "Seasonally Adjusted",
        "subtitle": ""
    },
}

def fetch_and_save_fred_dataset (dataset):
    series = FRED_SERIES[dataset]
    url = FRED_ENDPOINT + "?series_id=" + series['id'] + "&api_key=" + FRED_API_KEY + "&file_type=" + FRED_FILE_TYPE
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()['observations']
    df = pd.DataFrame(data)
    df['date'] = pd.PeriodIndex(df['date'], freq=series['frequency']).to_timestamp(how="end")
    df = df[['date', 'value']]
    df.columns = ['date', dataset]
    df.to_csv(OUTPUT_PATH + dataset +'.csv', index=False)
    return True

def try_or_skip(func, **kwargs):
    try:
        return func(**kwargs)
    except Exception as e:
        args = {**kwargs}
        print('WARNING!!: Skipped executing function "{}" with given arguments {} because of the follwoing error:'.format(func.__name__, args))
        print(e)
        return False

if __name__ == '__main__': main()

