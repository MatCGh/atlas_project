# Country Atlas: Clustering Countries on World Bank Indicators

**Question.** Do countries form natural groups across development, health and environment, and do those groups match World Bank regions and income groups?

| | |
|---|---|
| **Data** | World Bank indicators, 217 countries, 2000–2024 |
| **Sample** | 162 countries in 2023 (complete data, at least 300,000 inhabitants) |
| **Method** | Quality-checked pipeline, feature selection, log transform, standardization, clustering |
| **Status** | Data preparation done, clustering in progress. Personal learning project. |

## Start here

| Read | To see |
|---|---|
| [Decision log](docs/decisions.md) | Every methodological choice, with alternatives and costs |
| [Feature distributions](notebooks/04_feature_distributions.ipynb) | Distributions, outliers, micro-states |
| [Feature correlations](notebooks/05_feature_correlations.ipynb) | Redundancy, log transform, CO₂ vs PM2.5 |
| [Clustering input](notebooks/06_clustering_input.ipynb) | Standardization, extreme values, variants |
| [`src/`](src/) | Data pipeline code |

Notebooks 01 to 03 are early prototypes and year selection.

## Data

Source: [World Bank — World Development Indicators](https://data.worldbank.org/), retrieved through the Data360 API. Years 2000–2024.

| Feature | World Bank code | Unit | Role |
|---|---|---|---|
| Population | `SP.POP.TOTL` | persons | Illustrative |
| Land area | `AG.LND.TOTL.K2` | km² | Illustrative |
| GDP per capita, PPP | `NY.GDP.PCAP.PP.CD` | current international $ | **Active** |
| GDP per capita | `NY.GDP.PCAP.CD` | current US$ | Not used (D4) |
| Life expectancy at birth | `SP.DYN.LE00.IN` | years | **Active** |
| CO₂ emissions per capita | `EN.GHG.CO2.PC.CE.AR5` | t CO₂e | **Active** |
| PM2.5 mean annual exposure | `EN.ATM.PM25.MC.M3` | µg/m³ | **Active** |
| Urban population | `SP.URB.TOTL.IN.ZS` | % of total | **Active** |
| Current health expenditure | `SH.XPD.CHEX.GD.ZS` | % of GDP | Variant only (D9) |

Active features build the clusters. Illustrative features only describe them afterwards.

A World Bank country reference table (`data/external/`, from the World Bank v2 `/country` API) separates the **217 countries** from regional and income **aggregates**, which are excluded.

## Pipeline

```text
World Bank API ──► data/raw/            one CSV per indicator, never modified
                     │
                     ▼  src/build_interim_dataset.py
                   data/interim/        217 countries × 25 years = 5,425 rows
                     │
                     ▼  src/build_processed_dataset.py
                   data/processed/      model-ready dataset for a given reference year
```

1. **`src/import_raw_data.py`** — downloads each indicator with pagination. A failure on one indicator is logged and does not block the others.
2. **`src/build_interim_dataset.py`** — validates each indicator, keeps countries only, and joins everything onto a full country × year skeleton.
3. **`src/build_processed_dataset.py`** — selects a reference year and one GDP measure, keeps countries with complete data, adds country names, and checks key uniqueness and the absence of `NaN`.

Exploration is in `notebooks/`. Methodological decisions are in the [decision log](docs/decisions.md).

### Data quality checks

At import, the number of rows downloaded must match the total announced by the API, with no duplicate rows.

Every indicator then goes through these checks before being merged; any failure stops the run with an explicit message:

- expected key and value columns are present;
- every other column holds a single value, so it can be dropped without losing information;
- `TIME_PERIOD` is an integer column;
- the key (country × year) is unique;
- no empty values in the raw observations;
- only aggregates are dropped — never a real country (aggregates come from the reference table, plus a short list of known extras such as `FCS`);
- the left join does not change the number of rows.

The join onto a full country × year skeleton turns **missing rows** into visible `NaN`, so coverage can be measured per indicator rather than hidden.

## Repository structure

```text
├── data/
│   ├── raw/          # World Bank downloads (versioned, never edited)
│   ├── external/     # third-party reference tables
│   ├── interim/      # intermediate outputs (regenerated, not versioned)
│   └── processed/    # model-ready datasets (regenerated, not versioned)
├── docs/             # decision log
├── notebooks/        # exploration and visualisation
├── src/              # reusable pipeline code
└── requirements.txt
```

## Getting started

Requires Python 3.14 (developed on Ubuntu under WSL).

```bash
git clone https://github.com/MatCGh/atlas_project.git
cd atlas_project
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

python src/import_raw_data.py        # optional: raw data is already versioned
python src/build_interim_dataset.py    # builds data/interim/interim_dataset.csv
python src/build_processed_dataset.py  # builds data/processed/processed_dataset_2023.csv
```

## Status

- **Done** — data retrieval, quality-checked country × year panel, data preparation for clustering (feature selection, log transform, correlation analysis).
- **In progress** — clustering: choice of the number of clusters, then validation of the groups against World Bank region and income group.
- **Next** — predicting life expectancy from the other indicators, reusing the same panel.

## Author

**Mathis Coué** — [LinkedIn](https://www.linkedin.com/in/mathis-cou%C3%A9-894264220/)

Data: World Bank, World Development Indicators, licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
