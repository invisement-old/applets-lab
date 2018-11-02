''' extracts property tax datasets for states and counties from excel file "property_tax_2017.xlsx" '''
### PATHES to change
HOST = "/home/invisement/PROJECTS/inVisement2/apps-workshop/"
INPUT_PATH = HOST + "input/"
OUTPUT_PATH = HOST + "data/"

def main():
    success1 = try_or_skip(extract_property_tax_by_state, **{})
    success2 = try_or_skip(extract_property_tax_by_fips, **{})
    print(success1, success2)

### LIBRARIES
import pandas as pd, requests, zipfile, io

### INPUTS
PROPERY_TAX_FILE = "property_tax_2017.xlsx"

## OUTPUTS
PROPERY_TAX_BY_STATE_DATASET = "property tax by state.csv"
PROPERY_TAX_BY_FIPS_DATASET = "property tax by fips.csv"

def extract_property_tax_by_state ():
    tax_by_state = pd.read_excel (INPUT_PATH + PROPERY_TAX_FILE, sheet_name="States", skiprows=2, header=None)
    tax_by_state.columns = ["state", "house value", "property tax", "property tax rate"]
    tax_by_state["property tax rate"] = tax_by_state["property tax rate"]/1000 # converting to per dollar
    tax_by_state = tax_by_state.dropna(subset=["property tax rate"])
    tax_by_state.to_csv(OUTPUT_PATH + PROPERY_TAX_BY_STATE_DATASET, index = False)
    return True

def extract_property_tax_by_fips ():
    tax_by_fips = pd.read_excel (INPUT_PATH + PROPERY_TAX_FILE, sheet_name=None, skiprows=3, header=None)
    del tax_by_fips["States"]
    tax_by_fips = pd.concat(tax_by_fips).reset_index()
    tax_by_fips.columns = ["state", "0", "fips", "county", "house value", "property tax", "property tax rate", "lowest tract tax rate", "highest tract tax rate", "high-low"]
    tax_by_fips.drop("0", axis=1, inplace=True)
    tax_by_fips["property tax rate"] = tax_by_fips["property tax rate"]/1000
    tax_by_fips = tax_by_fips.dropna(subset=["property tax rate"])
    tax_by_fips.to_csv(OUTPUT_PATH + PROPERY_TAX_BY_FIPS_DATASET, index = False)
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


