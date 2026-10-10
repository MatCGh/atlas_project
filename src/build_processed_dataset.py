#imports

import pandas as pd
from pathlib import Path
import sys
import logging
logger = logging.getLogger(__name__)

#params
PROJECT_ROOT = Path(__file__).resolve().parent.parent

GDP_COLUMNS = ['gdp_per_capita_ppp_current_ppp', 'gdp_per_capita_usd_current_usd']
gdp_column_to_keep = 'gdp_per_capita_ppp_current_ppp'

year_to_keep = 2023
#control functions 


def isna_in_features(df):
    features_columns = [col for col in df.columns if col not in ['ref_area', 'time_period', 'name']]
    has_nan = df[features_columns].isna().any()
    if has_nan.any():
        raise ValueError(f"There are NaN values in the final dataset for these columns: {has_nan[has_nan].index.tolist()}.")

def check_key_unicity(df):
    counts_per_key = df.groupby(['ref_area']).size()
    
    nb_non_unique_key = counts_per_key[counts_per_key > 1].count()
    if nb_non_unique_key !=0:
        raise ValueError(f"A country is repeted. Index : {counts_per_key[counts_per_key > 1].index.tolist()}")

#process fuctions

def select_gdp(df, gdp_column):
    """Keep gdp_column and drop the other GDP columns."""
    other_gdp_columns = [col for col in GDP_COLUMNS if col != gdp_column]
    return df.drop(columns=other_gdp_columns)

def split_by_completeness(df, year, gdp_column):
    """Return (df_full, df_missing) for one year: countries with every feature filled vs the others."""
    df_year = select_gdp(df[df['time_period'] == year], gdp_column)
    is_full = df_year.notna().all(axis=1)
    return df_year[is_full], df_year[~is_full]

def add_country_names(df):
    df_area = pd.read_csv(PROJECT_ROOT / f"data/external/area_data.csv")
    df_countries = df_area[df_area['region.value'] != 'Aggregates']
    df_countries_names = df_countries[['id', 'name']].rename(columns={'id': 'ref_area'})
    df_named = df.merge(df_countries_names, on='ref_area', how='left')
    df_named = df_named[['name'] + list(df_named.columns[:-1])]
    
    #control for missing names
    if df_named['name'].isna().any():
        missing_names = df_named[df_named['name'].isna()]['ref_area'].tolist()
        raise ValueError(f"Missing country names for ref_area: {missing_names}")
    
    return df_named


def main():
    df = pd.read_csv(PROJECT_ROOT / 'data' / 'interim' / 'interim_dataset.csv')
    df_named = add_country_names(df)
    df_final, df_missing = split_by_completeness(df_named, year_to_keep, gdp_column_to_keep)

    #controls
    check_key_unicity(df_final)
    isna_in_features(df_final)

    #write the final dataset
    df_final.to_csv(PROJECT_ROOT / 'data' / 'processed' / f'processed_dataset_{year_to_keep}.csv', index=False)
    logger.info(f"Processed dataset written to {PROJECT_ROOT / 'data' / 'processed' / f'processed_dataset_{year_to_keep}.csv'} with {df_final.shape[0]} rows and {df_final.shape[1]} columns.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        main()
    except Exception as e:
        logger.exception("Run failed")
        sys.exit(1)