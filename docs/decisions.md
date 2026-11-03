# Decision log

Methodological decisions taken in this project, with the evidence behind them. Each decision was taken **before** looking at any clustering result, to avoid shaping the data to fit a desired outcome.

Evidence lives in the notebooks; this file only summarises it.

| # | Decision | Notebook |
|---|---|---|
| D1 | Data source: World Bank WDI as the single base | — |
| D2 | Raw and reference data are committed | — |
| D3 | Reference year: 2023 | `03_clustering_dataset` |
| D4 | GDP per capita in PPP, not current US$ | `03_clustering_dataset` |
| D5 | Complete-case analysis, no imputation | `03_clustering_dataset` |
| D6 | Clustering question and active vs illustrative features | `04_feature_distributions` |
| D7 | Exclusion of micro-states (< 300,000 inhabitants) | `04_feature_distributions` |
| D8 | Log transform of four features | `05_feature_correlations` |
| D9 | Removal of health spending features | `05_feature_correlations` |
| D10 | Standardization, extreme values kept | `06_clustering_input` |
| D11 | Robustness variants fixed in advance | `06_clustering_input` |

---

## D1 — World Bank WDI as the single data source

- **Context.** Indicators can come from several providers (World Bank, Our World in Data, UN).
- **Decision.** Use the World Bank World Development Indicators only.
- **Why.** Country codes, units and definitions are consistent across indicators, which makes joins safe.
- **Consequence.** Region and income group come from the World Bank country table; continents are not available from this source.

## D2 — Raw and reference data are committed

- **Decision.** `data/raw/` and `data/external/` are versioned; `data/interim/` and `data/processed/` are not.
- **Why.** The API may return different data later (revisions), so raw downloads cannot be rebuilt identically. Interim and processed data can always be rebuilt from raw data and code.

## D3 — Reference year: 2023

- **Context.** The clustering uses one cross-section; coverage varies by year and indicator.
- **Decision.** 2023.
- **Alternatives rejected.**
  - 2024: structural gaps (no land area, no PM2.5).
  - 2020–2021: Covid years, not representative.
  - 2022: closer to Covid, for a gain of one country only (Syria).
- **Risk.** As the latest complete year, 2023 may still be revised by the World Bank.

## D4 — GDP per capita in PPP

- **Decision.** Keep `NY.GDP.PCAP.PP.CD` (PPP), drop GDP in current US$.
- **Why.** PPP measures what an income actually buys locally; exchange-rate GDP underestimates living standards in low-income countries. The question compares living standards, not weight in world markets.
- **Cost.** One country lost compared with current US$ (Venezuela).

## D5 — Complete-case analysis, no imputation

- **Result.** 38 of 217 countries are incomplete in 2023; 179 remain.
- **Accepted cost.** Ukraine and Puerto Rico are excluded only because health spending (% of GDP) is missing, even though D9 removes this feature from the main version. They stay excluded so that the main version and the health variant (D11, variant A) are compared on the same 162 countries.
- **Alternatives rejected.**
  - Neighbour average: neighbouring countries can differ sharply (politics, economy, environment).
  - Carrying past values forward: likely missing too (not verified), and would erase recent shocks.
- **Limitation.** Missing data is probably not random:
  - 23 of the 38 excluded countries have < 300,000 inhabitants.
  - Others: conflict or sanctions (Yemen, Syria, North Korea).
  - Exceptions: Serbia, Montenegro (no CO₂), Hong Kong, Macao (no PM2.5).
  - About 2.6 % of the world population is excluded, so the clusters do not describe these countries.

## D6 — Clustering question and feature roles

- **Question.** Group countries by development profile: wealth, health, environment.
- **Active features** (build the groups): GDP per capita, life expectancy, CO₂ per capita, PM2.5, urbanisation.
- **Illustrative features** (describe the groups afterwards): population, land area, World Bank region, income group.
- **Why size is not active.** Grouping by size teaches nothing about development, and population and land area are linked, so size would weigh almost twice.
- **Why illustrative features matter.** Features that build the groups cannot validate them (circular reasoning). External variables are the check.

## D7 — Exclusion of micro-states

- **Decision.** Exclude countries with fewer than 300,000 inhabitants in 2023 (17 countries): 179 → 162.
- **Why.** Their per-capita ratios are dominated by a single facility, foreign aid or an estimated value. Evidence: Nauru and Tuvalu report zero CO₂ every year since 2000; Palau reports 64–203 t CO₂ per capita depending on the year; Tuvalu and Nauru top health spending as % of GDP.
- **Effect.** CO₂ skew drops from 5.83 to 3.59 and zeros disappear, so a log transform becomes possible.
- **Cost.** The atlas describes countries of at least 300,000 inhabitants only. The 179-country set is kept as a robustness variant (D11).

## D8 — Log transform of four features

- **Principle.** A log keeps the ranking of countries but changes what distances measure: ratios instead of absolute gaps. Candidates are strictly positive features with max/min above ~10. The domain argument decides; skewness confirms.

| Feature | Max/min | Choice | Domain argument |
|---|---|---|---|
| GDP per capita | 131 | log | Diminishing returns: the same absolute gap matters more for poor countries |
| CO₂ per capita | 1,051 | log | 0.1 → 1 t marks a development step, 10 → 11 t does not |
| PM2.5 | 24 | log | Concave health effect: strong at low concentrations, flattening above |
| Life expectancy | 1.5 | raw | Small range, symmetric |
| Urbanisation | 6.6 | raw | Small range, symmetric |

- **Fourth feature.** Health spending per capita: also logged, then removed from the main version (D9).
- **Check.** After log, all transformed features have |skew| < 0.5.

## D9 — Removal of health spending features

- **Health spending per capita** (derived: % of GDP × GDP per capita) — **removed.** Spearman 0.96 with GDP per capita, largely by construction: given GDP, it only adds health spending as % of GDP.
- **Health spending as % of GDP** — **removed from the main version**, kept as a variant. The feature is ambiguous: the same value can mean a costly developed health system (Germany) or an aid-dependent small economy (Liberia), so poor countries appear at both extremes. Health is still represented by life expectancy (an outcome rather than spending effort).
- **Method.** Pearson and Spearman matrices on the transformed features differ by at most 0.08: relationships are roughly linear and no single country drives them.

## D10 — Standardization, extreme values kept

- **Decision.** Log first, then z-score standardization so every feature weighs the same in distances. Standardization happens at modelling time and is not stored in `data/processed/`.
- **Check.** Only 3 countries exceed |z| > 2.5, each on a single feature (Nigeria, Somalia, Qatar). All countries are kept. Qatar is the most isolated country overall: watch whether it forms a cluster on its own.

## D11 — Robustness variants fixed in advance

Clusters from the main version will be compared with these variants, defined before any clustering:

| Variant | Change from the main version |
|---|---|
| A | + health spending as % of GDP |
| B | Pollution only: log CO₂ + log PM2.5 |
| C | CO₂ and PM2.5 without log |
| D | 177 countries: micro-states put back, except Nauru and Tuvalu (zero CO₂, log impossible) |
| E1 / E2 | Without CO₂ / without urbanisation |

- **Known risk.** Four of the five active features are strongly correlated (Spearman 0.67–0.89), so clusters may mostly split a poor → rich axis. Variants E1/E2 and a PCA (principal component analysis) are planned to measure this.

---

## Open decisions

- Number of clusters K and the range to test.
- Validation of clusters against World Bank region and income group.
