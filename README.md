# Country Atlas — Data Science on World Bank Indicators

> 🚧 **Work in progress.** This is a personal learning project, built step by step. The data pipeline is in place; the modelling stages are under way.

A country-level dataset built from World Bank indicators, designed as a reusable base: one cleaned country × year panel, from which each analysis derives its own model-ready dataset.

One row = one country × one year. One column = one indicator.

---

## Question

**Do countries form natural groups across development, health and environmental indicators — and do those groups match continents and income levels, or cut across them?**

The current analysis works on a 2023 cross-section of countries with complete data. Skewed features are log-transformed, and Pearson and Spearman correlations are used to assess redundancy between features before clustering.

## Data

Source: [World Bank — World Development Indicators](https://data.worldbank.org/), retrieved through the Data360 API. Years 2000–2024.

| Feature | World Bank code | Unit |
|---|---|---|
| Population | `SP.POP.TOTL` | persons |
| Land area | `AG.LND.TOTL.K2` | km² |
| GDP per capita, PPP | `NY.GDP.PCAP.PP.CD` | current international $ |
| GDP per capita | `NY.GDP.PCAP.CD` | current US$ |
| Life expectancy at birth | `SP.DYN.LE00.IN` | years |
| CO₂ emissions per capita | `EN.GHG.CO2.PC.CE.AR5` | t CO₂e |
| PM2.5 mean annual exposure | `EN.ATM.PM25.MC.M3` | µg/m³ |
| Urban population | `SP.URB.TOTL.IN.ZS` | % of total |
| Current health expenditure | `SH.XPD.CHEX.GD.ZS` | % of GDP |

A World Bank country reference table (`data/external/`) separates the **217 countries** from regional and income **aggregates**, which are excluded.

## Pipeline

```text
World Bank API ──► data/raw/            one CSV per indicator, never modified
                     │
                     ▼  src/build_interim_dataset.py
                   data/interim/        217 countries × 25 years = 5,425 rows
                     │
                     ▼  notebooks/
                   data/processed/      model-ready dataset for a given analysis and reference year
```

1. **`src/import_raw_data.py`** — downloads each indicator with pagination. A failure on one indicator is logged and does not block the others.
2. **`src/build_interim_dataset.py`** — validates each indicator, keeps countries only, and joins everything onto a full country × year skeleton.

### Data quality checks

Every indicator goes through these checks before being merged; any failure stops the run with an explicit message:

- expected key and value columns are present;
- `TIME_PERIOD` is an integer column;
- the key (country × year) is unique;
- no empty values in the raw observations;
- only aggregates are dropped — never a real country;
- the left join does not change the number of rows.

The join onto a full country × year skeleton turns **missing rows** into visible `NaN`, so coverage can be measured per indicator rather than hidden.

## Repository structure

```text
├── data/
│   ├── raw/          # World Bank downloads (versioned, never edited)
│   ├── external/     # third-party reference tables
│   ├── interim/      # intermediate outputs (regenerated, not versioned)
│   └── processed/    # model-ready datasets (regenerated, not versioned)
├── notebooks/        # exploration and visualisation
├── src/              # reusable pipeline code
└── requirements.txt
```

## Getting started

Requires Python 3.14 (developed on Ubuntu under WSL).

```bash
git clone <repo-url>
cd atlas_project
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

python src/import_raw_data.py        # optional: raw data is already versioned
python src/build_interim_dataset.py  # builds data/interim/interim_dataset.csv
```

## Status

- **Done** — data retrieval, quality-checked country × year panel, data preparation for clustering (feature selection, log transform, correlation analysis).
- **In progress** — clustering: choice of the number of clusters, then validation of the groups against continent and income group.
- **Next** — predicting life expectancy from the other indicators, reusing the same panel.

## Author

**Mathis Coué** — [LinkedIn](https://www.linkedin.com/in/mathis-cou%C3%A9-894264220/)

Data: World Bank, World Development Indicators, licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
