'''
extract zillow datasets related to housing price and rent price
'''
def main():
    fetch_zip(ZILLOW_BY_COUNTY)
    sucess = [try_or_skip(extract_and_save, dataset=d) for d in DATASETS]
    print('successful extracts = ', sucess)

### LIBRARIES
import pandas as pd, requests, zipfile, io

### CONSTANTS
DATASETS = ["rent by county", "house price by county"]

### PATHES
TEMP_PATH = "temp/"
OUTPUT_PATH = "data/"

### INPUTS
ZILLOW_BY_COUNTY = "http://files.zillowstatic.com/research/public/County.zip"
ZILLOW_BY_ZIPCODE = "http://files.zillowstatic.com/research/public/Zip.zip"
ZILLOW_BY_CITY = "http://files.zillowstatic.com/research/public/City.zip"

### OUTPUTS
OUTPUTS = {
    "rent by county": {
        "source": "County/County_Zri_AllHomes.csv",
        "frequency": "M",
        "index_cols": ['RegionName', 'State', 'Metro', 'StateCodeFIPS', 'MunicipalCodeFIPS'],
        "col_names": ['county', 'state', 'metro', 'state fips', 'county fips', 'date', 'rent']
    },
    "house price by county": {
        "source": "County/County_Zhvi_AllHomes.csv",
        "frequency": "M",
        "index_cols": ['RegionName', 'State', 'Metro', 'StateCodeFIPS', 'MunicipalCodeFIPS'],
        "col_names": ['county', 'state', 'metro', 'state fips', 'county fips', 'date', 'house price']
    },
}

### FUNCTIONS
def fetch_zip (url):
    ''' fetch a zip file from url and extract it to config['archive path']'''
    r = requests.get(url)
    r.raise_for_status()
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall(TEMP_PATH)

def extract_and_save (dataset):
    kv = {'date_col': 'date', **OUTPUTS[dataset]}
    input = pd.read_csv(TEMP_PATH + kv['source'], encoding='latin')
    month_regex = "[0-9]{4}-[0-9]{2}.*"
    df = (input
            .set_index(kv['index_cols'])
            .filter(regex=month_regex)
            .stack()
            .reset_index()
    )
    df.columns = kv['col_names']
    df[kv['date_col']] = pd.PeriodIndex(df[kv['date_col']], freq=kv['frequency']).to_timestamp(how="end")
    df.to_csv (OUTPUT_PATH + dataset + ".csv"  , index=False)
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

