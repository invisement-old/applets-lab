'''
calculate intrinsic economic value of a property based on buy or rent decision indifference (arbitrage)

Rent = Price*mortgage_rate 
        + DEPRECIATION_RATE*min(Building, Price) 
        - growth * Land 
        + Price*tax 
        - (Price - 24k) * tax_braket
        + Price * mortgage_insurance

'''
def main():
    ''' read all input files, prepare housing table, calculate intrinsic value, add return columns, and save output '''
    housing_table = read_and_join_input_files()
    housing_table = prepare_housing_valuation_table(housing_table)
    housing_table['intrinsic house value'] = calculate_intrinsic_value (housing_table).round()
    housing_table["total return"] = (housing_table['intrinsic house value'] - housing_table['house price'])/housing_table['house price']
    housing_table['net annual return'] = housing_table['total return'] * (housing_table['mortgage rate']+PMI_RATE)
    housing_table['annual return'] = housing_table['net annual return'] + housing_table['mortgage rate'] + PMI_RATE
    return prune_and_save (housing_table)

### LIBRARIES
import datetime, pandas as pd, numpy as np

### HOST ADDRESSES
INPUT_PATH = "data/"
OUTPUT_PATH = "data/"

### CONSTANTS
PMI_RATE = 0.01 # private mortgage insurance rate
FEDERAL_INCOME_TAX_RATE = 0.30 # federal tax bracket rate
DEPRECIATION_RATE = 0.03 # home annual depreciation rate for a base home (building)
STANDARD_TAX_DEDUCTION = 24000
MAX_MORTGAGE_CREDIT = 1000000 # maximum allowance for tax deduction on mortgage
BASE_QUANTILE = 0.3

### INPUTS
PRICE_FILE = INPUT_PATH + "house price by county.csv"
RENT_FILE = INPUT_PATH + "rent by county.csv"
MORTGAGE_FILE = INPUT_PATH + "mortgage rate 30 year fixed.csv"
GROWTH_FILE = INPUT_PATH + "nominal gdp growth.csv" 
TAX_FILE = INPUT_PATH + "property tax by fips.csv"

### OUTPUTS
HOUSING_FILE = OUTPUT_PATH + "housing valuation.csv"
LATEST_HOUSING_FILE = OUTPUT_PATH + "latest housing valuation.csv"

### FUNCTIONS
def read_and_join_input_files (base_quantile=BASE_QUANTILE):
    price = pd.read_csv(PRICE_FILE, dtype=str)
    price['house price'] = pd.to_numeric(price['house price'])
    price['fips'] = price['state fips'].str.zfill(2) + price['county fips'].str.zfill(3)
    price = price.filter(['fips', 'state', 'county', 'date', 'house price'])

    rent = pd.read_csv(RENT_FILE, dtype=str)
    rent['rent'] = pd.to_numeric(rent['rent']) * 12 # convert to annual
    rent['fips'] = rent['state fips'].str.zfill(2) + rent['county fips'].str.zfill(3)
    rent = rent.filter(["fips", "date", "rent"])

    rate = (pd.read_csv(MORTGAGE_FILE)
        .set_index('date')
        .rename(columns = {"mortgage rate 30 year fixed": "mortgage rate"})
        .filter(["mortgage rate"])
    )
    rate = rate/100
    rate.index = pd.to_datetime(rate.index)

    average_growth = (
        pd.read_csv (GROWTH_FILE, index_col="date")#["nominal gdp growth"]
        .rename(columns = {"nominal gdp growth": "growth"})
        .sort_index()
        .filter(["growth"])
        .rolling(80)
        .mean() # moving average of nominal growth with 80 quarters
    )
    average_growth = average_growth/100
    average_growth.index = pd.to_datetime(average_growth.index)

    #fips_to_zipcode = pd.read_csv(config['map path']+"zipcode fips mapping.csv")
    property_tax = pd.read_csv(TAX_FILE).filter(["fips", "property tax rate"])
    property_tax['fips'] = property_tax['fips'].astype(str).str.zfill(5)
    #property_tax_by_zipcode = pd.merge(fips_to_zipcode, property_tax, on=["fips"]).drop_duplicates(subset=['zipcode']).set_index(['zipcode'])['property tax rate']

    table = price.merge(rent, how="inner", on=["fips", "date"], suffixes=["", "2"]).sort_values("date")
    table['date'] = pd.to_datetime(table['date'])
    table = pd.merge_asof(table, average_growth, on="date", direction="backward")
    table = pd.merge_asof(table, rate, on="date", direction="backward")
    table = table.merge(property_tax, on="fips", how="left")
    quantiles = table[["house price", "rent", "date"]].groupby(["date"]).quantile(base_quantile)
    table = table.join(quantiles, on="date", how="left", rsuffix=" base")

    return table

def calculate_intrinsic_value (housing_valuation_table):
    intrinsic_value = (
            housing_valuation_table['rent'] 
            + housing_valuation_table['extra tax deduction'] * FEDERAL_INCOME_TAX_RATE
            - housing_valuation_table['house price base']*DEPRECIATION_RATE
        )/(
            housing_valuation_table['mortgage rate']
            + PMI_RATE
            + housing_valuation_table['property tax rate']
            #+ DEPRECIATION_RATE
            - housing_valuation_table['rent growth']
        )
    return intrinsic_value

def prepare_housing_valuation_table (housing_table):
    ''' prepares the housing valuation table the intrinsic value of houses with given data in housing_table '''
    housing_table['rent growth'] = housing_table['growth']*(housing_table['rent']-housing_table['rent base'])/housing_table['rent']
    housing_table['rent growth'][housing_table['rent growth']<0] = 0 
    housing_table['extra tax deduction'] = 0
    housing_table['extra tax deduction'][
        housing_table['house price'] * housing_table['mortgage rate'] > STANDARD_TAX_DEDUCTION
        ] = housing_table['house price'] * housing_table['mortgage rate']
    housing_table['extra tax deduction'][
        housing_table['house price'] > MAX_MORTGAGE_CREDIT
    ] = MAX_MORTGAGE_CREDIT * housing_table['mortgage rate'] - STANDARD_TAX_DEDUCTION
    return housing_table

def prune_and_save (housing_table):
    ''' to pretify the housing table and save in destination'''
    housing_table.to_csv(HOUSING_FILE, index=False)
    name_change = {"fips": "Fips", "state": "State", "county": "County", 
        "house price": "$ Average House Price", 
        "rent": "$ Average Rent", 
        "intrinsic house value": "$ Intrinsic Value of Average House",
        "property tax rate": "% Property Tax Rate", 
        "rent growth": "% Rent Growth Forecast",
        "total return": "% Total Return",
        "annual return": "% Annual Return",
        "net annual return": "% Net Annual Return"}
    date = housing_table['date'].value_counts()
    max_date = date[date > 1000].index.max()
    housing_table = (housing_table
        .query('date == @max_date') 
        .filter(name_change.keys())
        .rename(columns=name_change)
        .rename(str.title, axis= 'columns')
    )
    percentage_columns = [col for col in housing_table.columns if col.startswith('%')]
    housing_table[percentage_columns] = housing_table[percentage_columns] * 100
    housing_table[percentage_columns] = housing_table[percentage_columns].round(1)
    money_columns = [col for col in housing_table.columns if col.startswith('$')]
    housing_table[money_columns] = housing_table[money_columns].round()
    housing_table.to_csv(LATEST_HOUSING_FILE, index=False)
    return True

def try_or_skip(func, **kwargs):
    try:
        return func(**kwargs)
    except Exception as e:
        args = {**kwargs}
        print('WARNING!!: Skipped executing function "{}" with given arguments {} because of the follwoing error:'.format(func.__name__, args))
        print(e)
        return False

if __name__ == '__main__': try_or_skip(main, **{})


#a = pd.read_csv(config['map path']+"buy or rent.csv")

#table.query('fips == "06075"').tail()[["fips", "county", "date", "house price", "rent", "rent growth", "expected home price", "expected return"]]
