'''
extract real estate data like zillow, rent, housing price, property tax

zillow[data_sources] are zillow files, zillow[datasets] are inVisement files.
we want to grab from data sources, transform them, and save the result in datasets.

'''

import pandas as pd, requests, zipfile, io

zillow = {
        "data_source": {
                'zillow by county': "http://files.zillowstatic.com/research/public/County.zip",
                'zillow by zipcode': "http://files.zillowstatic.com/research/public/Zip.zip",
                'zillow by city': "http://files.zillowstatic.com/research/public/City.zip",
        },
        "datasets": {
                "rent by county": {
                        "source": "County/County_Zri_AllHomes.csv",
                        "frequency": "M",
                        "index_cols": ['RegionName', 'State', 'Metro', 'StateCodeFIPS', 'MunicipalCodeFIPS'],
                        "col_names": ['county', 'state', 'metro', 'state fips', 'county fips', 'date', 'rent']
                },
'''
                "house price by county": {
                        "source": "County/County_Zhvi_AllHomes.csv",
                        "frequency": "M",
                        "index_cols": ['RegionName', 'State', 'Metro', 'StateCodeFIPS', 'MunicipalCodeFIPS'],
                        "col_names": ['county', 'state', 'metro', 'state fips', 'county fips', 'date', 'house price']
                },
                "priceToRent ratio by county": {
                        "source": "County/County_PriceToRentRatio_AllHomes.csv",
                        "frequency": "M",
                        "index_cols": ['RegionName', 'State', 'Metro', 'StateCodeFIPS', 'MunicipalCodeFIPS'],
                        "col_names": ['county', 'state', 'metro', 'state fips', 'county fips', 'date', 'price to rent']
                },
                "priceToRent ratio by zipcode": {
                        "source": "Zip/Zip_PriceToRentRatio_AllHomes.csv",
                        "frequency": "M",
                        "index_cols": ['RegionName', 'City','State', 'Metro', 'CountyName'],
                        "col_names": ['zipcode', 'city', 'state', 'metro', 'county', 'date', 'price to rent']
                },
'''
        },
        "housing table": {
                #"location": config['map path'] + "housing.csv"
        }
}

def fetch_zip (url):
        ''' fetch a zip file from url and extract it to config['archive path']'''
        r = requests.get(url)
        r.raise_for_status()
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall(config['archive path'])

def fetch ():
        ''' fetch all datasets from zillow data source and extract all in config['archive path']'''
        for dataset, url in zillow['data_source'].items():
                r = requests.get(url)
                r.raise_for_status()
                z = zipfile.ZipFile(io.BytesIO(r.content))
                z.extractall(config['archive path'])

def extract ():
        for indicator, vars in zillow['datasets'].items():
                input = pd.read_csv(config['archive path'] + vars["source"]) 
                month_regex = "[0-9]{4}-[0-9]{2}.*"
                output = (input
                        .set_index(vars["index_cols"])
                        .filter(regex=month_regex)
                        .stack()
                        .reset_index()
                )
                output.columns = vars["col_names"] 
                output['date'] = pd.PeriodIndex(output['date'], freq=vars["frequency"]).to_timestamp(how="end")
                output.to_csv (config['map path'] + indicator + ".csv"  , index=False)

def create_housing_table ():
        rent = pd.read_csv(config['map path']+ "rent.csv")  
        price = pd.read_csv(config['map path']+ "house price.csv" )
        housing = pd.merge(rent, price, on=['zipcode', 'date'])
        housing.to_csv(config['map path']+ "housing.csv", index=False)

def extract_property_tax_by_state ():
        tax_by_state = pd.read_excel (config['archive path']+"property_tax_2017.xlsx", sheet_name="States", skiprows=2, header=None)
        tax_by_state.columns = ["state", "house value", "property tax", "property tax rate"]
        tax_by_state["property tax rate"] = tax_by_state["property tax rate"]/1000 # converting to per dollar
        tax_by_state = tax_by_state.dropna(subset=["property tax rate"])
        tax_by_state.to_csv(config['map path']+"property tax by state.csv", index = False)

def extract_property_tax_by_fips ():
        tax_by_fips = pd.read_excel (config['archive path']+"property_tax_2017.xlsx", sheet_name=None, skiprows=3, header=None)
        del tax_by_fips["States"]
        tax_by_fips = pd.concat(tax_by_fips).reset_index()
        tax_by_fips.columns = ["state", "0", "fips", "county", "house value", "property tax", "property tax rate", "lowest tract tax rate", "highest tract tax rate", "high-low"]
        tax_by_fips.drop("0", axis=1, inplace=True)
        tax_by_fips["property tax rate"] = tax_by_fips["property tax rate"]/1000
        tax_by_fips = tax_by_fips.dropna(subset=["property tax rate"])
        tax_by_fips.to_csv(config['map path']+"property tax by fips.csv", index = False)

pass
