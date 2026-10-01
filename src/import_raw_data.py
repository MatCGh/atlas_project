#imports
import requests
import pandas as pd
import math
from pathlib import Path
import logging
logging.basicConfig(level=logging.INFO)

#parameters
start_year = 2000
end_year = 2024
pagination_limit = 1000  # Limite de pagination pour les requêtes

#Dictionnaire des indicateurs
indicators = {
    "population": "SP_POP_TOTL",
    "land_area_km2": "AG_LND_TOTL_K2",
    "gdp_per_capita_ppp_current": "NY_GDP_PCAP_PP_CD",
    "gdp_per_capita_usd_current": "NY_GDP_PCAP_CD",
    "life_expectancy": "SP_DYN_LE00_IN",
    "co2_emissions_per_capita": "EN_GHG_CO2_PC_CE_AR5",
    "pm2_5_exposure": "EN_ATM_PM25_MC_M3",
    'urban_population_percentage': "SP_URB_TOTL_IN_ZS",
    'health_expenditure_percentage_of_gdp': "SH_XPD_CHEX_GD_ZS",
}

#database_id
database_id = "WB_WDI"


#fonctions
def get_page(url, params):
    response = requests.get(url, params, timeout=10)
    response.raise_for_status()
    return response.json()

def get_indicator_data(url, nom, pagination_limit):
    # first page data
    data = get_page(url, params={"skip": 0})

    # Test if we have data
    if data["count"] == 0:
        raise ValueError(f"No data found for {nom}")

    n = math.ceil(data["count"]/pagination_limit)
    logging.info(f"Number of pages for {nom} : {n}")
    
    # other pages data
    for i in range(1,n):
        skip = i * pagination_limit
        data_page =get_page(url, params={"skip": skip})
        data['value'].extend(data_page['value'])

    # catch the case where the number of items returned does not match the expected count
    if len(data['value']) != data['count']:
        raise ValueError(f"Expected {data['count']} items, but got {len(data['value'])}")

    # Transform into a DataFrame and select the desired columns
    df=pd.DataFrame(data['value'])
    nb_duplicates = df.duplicated().sum()
    if nb_duplicates != 0:
        raise ValueError(f"Doublons trouvés pour l'indicateur {nom} : {nb_duplicates}")

    return df


def indicators_loop():
    for nom, code in indicators.items():

        url = f"https://data360api.worldbank.org/data360/data?DATABASE_ID={database_id}&INDICATOR={database_id}_{code}&timePeriodFrom={start_year}&timePeriodTo={end_year}"

        try:
            df = get_indicator_data(url, nom, pagination_limit)
            df.to_csv(Path(__file__).resolve().parent.parent / f"data/raw/{nom}_{start_year}-{end_year}_raw.csv", index=False)
                    
        except (requests.exceptions.RequestException, ValueError) as e:
            logging.error(f"Error for {nom}: {e}")
            continue

def area_to_csv():
    try:
        per_page = 400 # a huge number in order have everything in 1 call : if total < per_page
        area_data = get_page(url = "https://api.worldbank.org/v2/country?", params = {"format":"json", "per_page": per_page})
        df_area = pd.json_normalize(area_data[1])
        if area_data[0]['total'] != df_area.shape[0]:
            raise ValueError(f"Area total written in the json does not match the actual number of ids.  area_data[0]['total'] = {area_data[0]['total']} and df_area.shape[0] = {df_area.shape[0]}")

        df_area.to_csv(Path(__file__).resolve().parent.parent / f"data/external/area_data.csv", index=False)
    except (requests.exceptions.RequestException, ValueError) as e:
            logging.error(f"Error in get_countries: {e}")

# Main loop
def main() :
    indicators_loop()
    area_to_csv()


if __name__ == "__main__":
    main()