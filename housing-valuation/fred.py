
'''
fetch, reshape, and save macro indicators from sources. 
for indicators.csv:
    every record has (date, value)
'''
import requests, pandas as pd

us_macro_series = {
    "fred_api_key": "88b9092ad3db013e454ea78d5a1084c9",
    "fred_endpoint": "https://api.stlouisfed.org/fred/series/observations",
    "fred_file_type": "json",
    "fred_series": { 
        "high yield spread": {
            "source": "FRED",
            "id": "BAMLH0A0HYM2EY",
            "title": "High Yield Spread",
            "subtitle": "10 year treasury yield minus 2 year treasury yield",
            "unit": "Percent",
            "frequency": "date"
        },
        "treasury yield spread": {
            "id": "T10Y2Y",
            "title": "Treasury Yield Spread" ,
            "source": "FRED",
            "frequency": "date",
            "unit": "Percent",
            "subtitle": "Risky Corporate Bond Yield minus Treasury Bond Yield"
        },
        "consumer sentiment": {
            "id": "UMCSENT",
            "title": "Consumer Sentiment",
            "source": "FRED",
            "unit": "index (1966:Q1=100)",
            "frequency": "quarter",
            "subtitle": "Consumer Sentiment Index"
        },
        "investment to gdp": {
            "id": "A006RE1Q156NBEA",
            "title": "Investment To GDP",
            "source": "FRED",
            "unit": "Percent",
            "frequency": "quarter",
            "subtitle": "Share of Investment from GDP in Percent"
        },
        "gdp": {
            "id": "GDP",
            "source": "FRED",
            "title": "US Nominal GDP",
            "unit": "Billions of USD",
            "subtitle": "Nominal Gross Domestic Product",
            "frequency": "quarter",
            "adjusted": "Seasonally Adjusted"
        },
        "nominal gdp growth": {
            "id": "A191RP1Q027SBEA",
            "source": "FRED",
            "title": "US Nominal GDP Growth",
            "unit": "Percent",
            "subtitle": "Real GDP Annual Change in Percent",
            "frequency": "quarter",
            "adjusted": "Seasonally Adjusted"
        },
        "real gdp growth": {
            "id": "A191RO1Q156NBEA",
            "source": "FRED",
            "title": "US Real GDP Growth",
            "unit": "Percent",
            "subtitle": "Real GDP Annual Change in Percent",
            "frequency": "quarter",
            "adjusted": "From A Year Ago"
        },
        "real gdp per capita": {
            "id": "A939RX0Q048SBEA",
            "source": "FRED",
            "title": "US Real GDP Growth",
            "unit": "USD",
            "subtitle": "US GDP Per Capita in 2012 Chained Dollar",
            "frequency": "quarter",
            "adjusted": "Seasonally Adjusted"
        },
        "mortgage rate 30 year fixed": {
            "id": "MORTGAGE30US",
            "source": "FRED",
            "title": "30 Year Fixed Mortgage Rate Average",
            "frequency": "date",
            "unit": "Percent",
            "adjusted": "Seasonally Adjusted",
            "subtitle": ""
        },
        "mortgage rate 15 year fixed": {
            "id": "MORTGAGE15US",
            "source": "FRED",
            "title": "15 Year Fixed Mortgage Rate Average",
            "frequency": "date",
            "unit": "Percent",
            "adjusted": "Seasonally Adjusted",
            "subtitle": ""
        },
        "mortgage rate 5_1 year adjusted": {
            "id": "MORTGAGE5US",
            "source": "FRED",
            "title": "5/1 Year Adjusted Mortgage Rate Average",
            "frequency": "date",
            "unit": "Percent",
            "adjusted": "Seasonally Adjusted",
            "subtitle": ""
        },
    }
}


freq = {"date": "D", "month": "M", "quarter": "Q", "D": "D", "W": "D", "Q": "Q", "M": "M", "Y": "Y"}

def fetch_fred_series (fred_series):
    url = us_macro_series['fred_endpoint'] + "?series_id=" + fred_series['id'] + "&api_key=" + us_macro_series["fred_api_key"] + "&file_type=" + us_macro_series["fred_file_type"]
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()['observations']
    df = pd.DataFrame(data)
    df['date'] = pd.PeriodIndex(df['date'], freq=freq[fred_series['frequency']]).to_timestamp(how="end")
    return df[['date', 'value']]

def fetch_all_fred_series ():
    for fred_Series_name, fred_series in us_macro_series['fred_series'].items():
        try:
            output = fetch_fred_series (fred_series)
            output.columns = ["date", fred_Series_name]
            output.to_csv(config["macro path"]+fred_Series_name+".csv", index=False)
        except Exception as e:
            print("ERROR! cound not fetch fred series ", fred_Series_name, " because ", e)

