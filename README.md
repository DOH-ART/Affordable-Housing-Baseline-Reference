# Affordable Housing Baseline Reference
 
This project provides localities with data they may reference in planning for and developing their affordable housing baselines and annual goals outlined in Proposition 123. Results may be reproduced by downloading these project files and running the script "baseline reference.R". Most tabulations are performed in this script, which calls functions that are created in the "functions" folder; these scripts download and transform data using methods that are lengthy yet uncomplicated and have been excluded from the main script for brevity. 

## Technologies Used

- R
- tidyverse
- readxl

## Data Sources

[U.S. Census Bureau (2022). Table B25063: Gross Rent, 2017-2021 American Community Survey 5-year estimates.](https://www2.census.gov/programs-surveys/acs/summary_file/2021/table-based-SF/data/5YRData/)

[U.S. Census Bureau (2022). Table B25075: Value, 2017-2021 American Community Survey 5-year estimates.](https://www2.census.gov/programs-surveys/acs/summary_file/2021/table-based-SF/data/5YRData/)

[U.S. Census Bureau (2022). Table B25038: Tenure By Year Householder Moved Into Unit, 2017-2021 American Community Survey 5-year estimates.](https://www2.census.gov/programs-surveys/acs/summary_file/2021/table-based-SF/data/5YRData/)

[U.S. Census Bureau (2022). Table B19013: Median Household Income,  2021 American Community Survey 1-year estimates.](https://www2.census.gov/programs-surveys/acs/summary_file/2021/table-based-SF/data/1YRData/)

[U.S. Department of Housing and Urban Development (2022).  Data for Section 8 Income Limits in MS EXCEL.](https://www.huduser.gov/portal/datasets/il/il22/Section8-FY22.xlsx)

[National Bureau of Exonomic Research (2017). County adjacency.](https://data.nber.org/census/geo/county-adjacency/2010/county_adjacency2010.csv)

## Data Wrangling

1. Load data on rents, home values, and years that householders move into units for municipalities and unincorporated areas.
2. Process description columns to transform text such as "$1,000 to $1,249" into numeric columns representing the minimum and maximum of a range, such as 1000 and 1249.
3. Determine which counties each municipality and unincorporated area are adjacent to by identifying what counties they are within, and what counties those counties are adjacent to.
4. Calculate area median income, and income limits, of each county by looking up the HUD median income for a household of 3 in Federal Fiscal Year 2022 for each county.
2. Calculate housing stock turnover by calculating the percent of recent movers, those that have moved in the past 4 years, by municipality and unincorporated area.

## Modeling

1. Join the estimates data with the adjacency and income limit data, enabling stock affordability and turnover to be crossreferenced against buying power using income limits within each juristiction, its neighbors, or the state median income.
2. Prorate the estimated amounts of occupied units to the estimated amount of stock available by multiplying each estimate by the turnover rate of the locality for each tenure type.
3. Calculate the percent of units that are affordable to each income limit within each locality by comparing the minimum and maximum rental rates or home values, if they can be afforded by a buyer at 100% of that incom limit or a renter at 60% of that limit.
4. Calculate the total number of available affordable and available units within each jurisdiction, income limit, and range of rents or home values by multiplying the percent of affordable units within that range by the estimated number of available units.
6. Summarise the affordable housing baseline reference options by summing the total of available affordable units by locality and income limit type, determine the annual and three year goals by multiplying this figure by 3% and 9% respectively.

## Results

A file containing potential baseline oprions by locality and income limit type is contained in the ACS Basline Options.csv file.
