# import
import pandas as pd
import numpy as np
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

import sys

#parameters
from import_raw_data import start_year, end_year, indicators

key = {"REF_AREA", "TIME_PERIOD"}
value = 'OBS_VALUE'
unit_measure = 'UNIT_MEASURE'
value_related_columns = {value, unit_measure}
Allow_non_unique_columns = {"LATEST_DATA"} #Just true or false if it is the latest data that the world bank have for a country or aggregate
KNOWN_EXTRA_AGGREGATES = ['FCS'] # FCS = Fragile and Conflict-Affected Situations


# Functions

def check_year_type(df,indicator):
    if not isinstance(df['TIME_PERIOD'].iloc[0], (int, np.integer)):
        raise ValueError(f"For indicator {indicator}: TIME_PERIOD column should contain integer values")

def check_columns_presence(df,indicator):
    key.issubset(df.columns)
    missing_key = key - set(df.columns)
    if len(missing_key)!=0:
        raise ValueError(f"For indicator {indicator}: Missing key column(s) : {missing_key}") #probleme : ne dit pas exactement quelle valeur de la clé manque
    
    value_related_columns.issubset(df.columns)
    missing_value_related = value_related_columns - set(df.columns)
    if len(missing_value_related)!=0:
        raise ValueError(f"For indicator {indicator}: Missing value column(s) : {missing_value_related}")  #probleme : ne dit pas exactement quelle valeur manque

    # Checking if columns have only 1 value and so, can be dropped
    set_columns_to_check = set(df.columns) - key - set([value]) - Allow_non_unique_columns
    nu = df[list(set_columns_to_check)].nunique()
    if not (nu <= 1).all():
        raise ValueError(f"For indicator {indicator}: Non key or value columns have more than 1 value. They should be checked before dropping. Columns : {nu[nu > 1].to_dict()}")

def check_key_unicity(df,indicator):

    counts_per_key = df.groupby(['TIME_PERIOD', 'REF_AREA']).size()
    
    nb_non_unique_key = counts_per_key[counts_per_key > 1].count()
    if nb_non_unique_key !=0:
        raise ValueError(f"For indicator {indicator}: A key (TIME_PERIOD x REF_AREA) is repeted. Index : {counts_per_key[counts_per_key > 1].index.tolist()}")

def check_missing_values(df,indicator):
    if df['OBS_VALUE'].isnull().sum()!=0:
        index_null= df[df['OBS_VALUE'].isnull()].index
        raise ValueError(f"For indicator {indicator}: OBS_VALUE is null for at this index : {index_null.tolist()}")

def check_aggregates_dropping(df, df_area, df_countries, indicator):
    df_dropped = df[~df['REF_AREA'].isin(df_countries['id'])] # IDs dropped
    df_aggegates_from_area = df_area[df_area['region.value'] == 'Aggregates']
    df_dropped_countries= df_dropped[
        ~df_dropped['REF_AREA'].isin(df_aggegates_from_area['id'])
        &
        ~df_dropped['REF_AREA'].isin(KNOWN_EXTRA_AGGREGATES)
        ]
    if df_dropped_countries['REF_AREA'].nunique() != 0:
        raise ValueError(f"For indicator {indicator}: Countries were dropped, not only aggregates")

def dataset_squeleton(df_countries):
    # df_all_indicators : squeleton for the merged dataset (all indicators)
    df_countries_id = df_countries[['id']]
    df_years= pd.DataFrame([k for k in range(start_year,end_year+1)],dtype=np.dtype("int64"))
    df_all_indicators = df_countries_id.merge(df_years, how='cross')
    df_all_indicators = df_all_indicators.rename(columns={'id' : 'REF_AREA', 0 : 'TIME_PERIOD',})

    return df_all_indicators

def merging(df_all_indicators, df_filtre, indicator):
    #Renaming columns
    new_col = f"{indicator}_{df_filtre['UNIT_MEASURE'].iloc[0]}"
    df_to_merge = df_filtre.rename(columns={'OBS_VALUE': new_col})
    df_to_merge = df_to_merge.drop(['UNIT_MEASURE'], axis=1)

    #Merging and controling size of the merged dataframe
    shape_0_before_merge = df_all_indicators.shape[0]
    df_all_indicators = df_all_indicators.merge(df_to_merge,how='left', on=['REF_AREA', 'TIME_PERIOD'])
    if df_all_indicators.shape[0] !=shape_0_before_merge :
        raise ValueError(f"For indicator {indicator}: merge error : the number of row has changed")

    #Calculating coverage of the indicator in the final dataset
    coverage = df_all_indicators[new_col].notna().mean()
    logger.info(f"{indicator} : couverture {coverage:.1%}")

    return df_all_indicators

def create_interim_dataset(df_all_indicators):
    df_all_indicators.columns = [x.lower() for x in df_all_indicators.columns]
    df_all_indicators = df_all_indicators.rename(columns={'land_area_km2_km2' : 'land_area_km2'})

    df_all_indicators.to_csv(Path(__file__).resolve().parent.parent / f"data/interim/interim_dataset.csv", index=False)
        
# Main
def main():

    # Reading the area data and filtering out aggregates to keep only countries
    #df_countries will be used to filter the dataframes of each indicator to keep only countries and not aggregates
    df_area = pd.read_csv(Path(__file__).resolve().parent.parent /f"data/external/area_data.csv")
    df_countries = df_area[df_area['region.value']!= 'Aggregates']

    # Creating the squeleton of the final dataset (all indicators)
    df_all_indicators = dataset_squeleton(df_countries)

    for indicator, code in indicators.items():
        df = pd.read_csv(Path(__file__).resolve().parent.parent /f"data/raw/{indicator}_{start_year}-{end_year}_raw.csv")

        #Controls on the data before merging it to the final dataset
        check_year_type(df, indicator)
        check_columns_presence(df, indicator)
        check_key_unicity(df, indicator)
        check_missing_values(df, indicator)
        check_aggregates_dropping(df, df_area, df_countries, indicator)    
         
        # Droping useless columns
        df = df[['REF_AREA', 'TIME_PERIOD', 'OBS_VALUE', 'UNIT_MEASURE']]
            
        # Dropping aggregates to conserve countries only
        df_filtre = df[df['REF_AREA'].isin(df_countries['id'])]
        df_all_indicators = merging(df_all_indicators,df_filtre, indicator)

    create_interim_dataset(df_all_indicators)




if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        main()
    except Exception as e:
        logger.exception("Run failed")
        sys.exit(1)