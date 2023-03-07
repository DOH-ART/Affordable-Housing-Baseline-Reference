library(tidyverse)

library(readxl)

source('read_geos.R')

source('get_acs.R')

source('county_ami.R')


end_year = 2021
n_year = 5

selected_tables <- c('b25063', 'b25075', 'b25038')

selected_summary_levels <- c('055', '162')


acs_dl <- read_acs(table_name = selected_tables,
                   n_year = 5,
                   end_year = 2021,
                   summary_levels = selected_summary_levels,
                   excluded_cols = c('sumlevel',
                                     'universe')) %>%
  filter(!measure_id %in% c('B25063_027',
                            'B25063_001',
                            'B25063_002',
                            'B25038_001',
                            'B25038_002',
                            'B25038_009',
                            'B25075_001')
  )


acs_own <- acs_dl %>%
  filter(title == 'VALUE') %>%
  mutate(range = case_when(
    str_detect(label, 'Less than') ~ str_replace(label, 'Less than', '$0 to'),
    str_detect(label, 'or more')  ~ str_replace(label, 'or more', 'to $5,252,000'),
    TRUE ~ label)) %>%
  mutate(range = str_remove_all(range, '[^[:digit:]. ]')) %>% 
  separate(range, into = c('range_min','range_max')) %>% 
  select(geoid,geography_name,title,range_min,range_max,estimate,margin_of_error)

acs_rent <- acs_dl %>%
  filter(title == 'GROSS RENT') %>%
  mutate(range = case_when(
    str_detect(label, 'Less than') ~ str_replace(label, 'Less than', '$0 to'),
    str_detect(label, 'or more')  ~ str_replace(label, 'or more', 'to $6,000'),
    TRUE ~ label
  )) %>%
  mutate(range = str_remove_all(range, '[^[:digit:]. ]')) %>% 
  separate(range, into = c('range_min','range_max')) %>% 
  select(geoid,geography_name,title,range_min,range_max,estimate,margin_of_error)

acs_dl$margin_of_error <- acs_dl$margin_of_error / 1.645
acs_dl$margin_of_error <- acs_dl$margin_of_error ^ 2

acs_available_units <- acs_dl %>%
  filter(title == 'TENURE BY YEAR HOUSEHOLDER MOVED INTO UNIT') %>%
  mutate(title = if_else(measure_id %in% c('B25038_003',
                                           'B25038_004',
                                           'B25038_005',
                                           'B25038_006',
                                           'B25038_007',
                                           'B25038_008'),
                         'VALUE',
                         'GROSS RENT'),
         recent_mover = if_else(measure_id %in% c('B25038_003',
                                                  'B25038_004',
                                                  'B25038_010',
                                                  'B25038_011'),
                                estimate,
                                0)) %>%
  group_by(geoid, title) %>%
  summarise(proration_available_units = sum(recent_mover) / sum(estimate),
            margin_of_error = sqrt(sum(margin_of_error))) %>% 
  ungroup()

geos_dl <- read_geos(end_year = end_year,
                     n_year = n_year,
                     excluded_suffixes=c(', Colorado'))

geos_counties <- geos_dl %>%
  filter(sumlevel == '055') %>%
  mutate(county = str_sub(geoid, -5, -1))

geos_place_remainders <- geos_dl %>%
  filter(sumlevel == '155',
         !str_detect(geography_name,'CDP')) %>%
  mutate(county = paste0(str_sub(geoid, 10, 11), str_sub(geoid, -3, -1)),
         geoid = paste0('1620000US', str_sub(geoid, 10, 16))) %>%
  select(geoid, county)

geos_munis <- geos_dl %>%
  filter(sumlevel == '162')

county_adjacency <-
  read_csv(
    'https://data.nber.org/census/geo/county-adjacency/2010/county_adjacency2010.csv'
  ) %>%
  transmute(county = fipscounty,
            county_neighbor = fipsneighbor,
            county_name = neighborname)

geos_localities <- left_join(geos_munis,
                             geos_place_remainders,
                             by = 'geoid') %>%
  bind_rows(geos_counties)

locality_adjacency <- geos_localities %>%
  select(geoid, geography_name, county) %>%
  right_join(county_adjacency, by = 'county') %>%
  filter(str_sub(county, 1, 2) == '08')

amis_adjacency <- locality_adjacency %>%
  rowwise() %>%
  mutate(county_name = str_remove(county_name, ', CO'),
         ami = county_ami(county_neighbor)) %>%
  group_by(geoid, county, ami) %>%
  mutate(income_limit_type = case_when(
    county == county_neighbor ~ paste0('Own AMI - ', county_name),
    TRUE ~ paste0('Neighboring AMI - ', str_c(county_name, collapse = ', '))
  )) %>%
  ungroup() %>%
  select(geoid, income_limit_type, income_limit = ami) %>%
  distinct()

state_median_income <- read_acs(
  table_name = 'b19013',
  n_year = 5,
  end_year = 2021,
  summary_levels = '040',
  excluded_cols = c('sumlevel',
                    'universe')
) %>% 
  filter(geoid == '0400000US08') %>% 
  pull(estimate)

localities_state_income <- geos_localities %>% 
  filter(str_sub(geoid,10,11)=='08') %>% 
  transmute(geoid,
            income_limit_type = 'State Median Income',
            income_limit = state_median_income)

income_limits <- bind_rows(amis_adjacency,localities_state_income) %>% 
  crossing(title = c('VALUE','GROSS RENT')) %>% 
  mutate(income_limit = if_else(title == 'VALUE',
                                income_limit,
                                income_limit*.6))

affordable_to <-  function(amount,tenure){
  
  result <- if_else(tenure=='VALUE',
                    amount/3.5,
                    (amount*3.333)*12)
  
}


#----------------------------------
#For DOH baseline aggregations 

results <- bind_rows(acs_own,acs_rent) %>% 
  left_join(acs_available_units, by = c('geoid','title')) %>% 
  mutate(range_min = as.numeric(range_min),
         range_max = as.numeric(range_max)) %>% 
  mutate(min_affordable_to = affordable_to(amount = range_min,
                                           tenure = title),
         max_affordable_to = affordable_to(amount = range_max,
                                           tenure = title)) %>% 
  inner_join(income_limits, by = c('geoid','title')) %>% 
  mutate(affordable_unit_pct = case_when(max_affordable_to < income_limit ~ 1,
                                         min_affordable_to > income_limit ~ 0,
                                         TRUE ~ (max_affordable_to/income_limit) - (min_affordable_to/income_limit)
  ),
  affordable_units = ceiling(estimate*proration_available_units*affordable_unit_pct))

baseline <- results %>% 
  group_by(`Locality Name` = str_to_title(geography_name),
           `Income Limit Type` = income_limit_type) %>% 
  summarise(`Affordable Housing Baseline Estimate` = sum(affordable_units)) %>% 
  ungroup() %>% 
  mutate(`Three Year Commitment Estimate` = ceiling(`Affordable Housing Baseline Estimate`*0.09),
         `Annualized Commitment Estimate` = ceiling(`Affordable Housing Baseline Estimate`*0.03)) %>% 
  arrange(`Locality Name`,`Income Limit Type`)

write_csv(baseline,'ACS Baseline Options.csv')


