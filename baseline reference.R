library(tidyverse)

library(readxl)

library(tidycensus)

library(arrow)

source('./functions/read_geos.R')

source('./functions/read_acs.R')

source('./functions/county_ami.R')


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
  ungroup() %>% 
  select(-margin_of_error)

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


income_limits_hud <- unique(pull(locality_adjacency,county_neighbor)) %>% 
    county_ami_df(county_geoids = .)

amis_adjacency <- locality_adjacency %>%
    mutate(county_name = str_remove(county_name, ', CO')) %>% 
    left_join(income_limits_hud, by = c('county_neighbor'='geoid'),multiple = "all") %>%
    mutate(income_limit_text = as.character(income_limit)) %>%
    group_by(geoid,county,il_name,il_year,il_hh_size,income_limit) %>%
    summarise(county_concat = str_c(county_name, collapse = ', '),
              county_id_concat = str_c(county_neighbor, collapse = ' ')) %>%
    ungroup() %>% 
    rowwise() %>% 
    mutate(il_type = if_else(str_detect(county_id_concat,county),
                             paste0('Own AMI - ', county_concat),
        paste0('Neighboring AMI - ', str_c(county_concat, sep = ', ')))) %>%
    ungroup() %>%
    select(geoid, il_name, il_year,il_hh_size, il_type, income_limit) %>%
    distinct()

state_median_income <- map_dfr(c(2017:2019,2021),
                           ~tidycensus::get_acs(geography = 'state',
                                                variables = 'B19013_001E',
                                                year = .x,
                                                state = '08',
                                                survey = 'acs1') %>% 
                               transmute(il_year = as.integer(.x),
                                         income_limit = estimate))
    
    
    

localities_state_income <- geos_localities %>% 
    filter(str_sub(geoid,10,11)=='08') %>% 
    crossing(il_year = as.integer(c(2017:2019,2021))) %>% 
    left_join(state_median_income, by = 'il_year') %>% 
    transmute(geoid,
              il_name = 'State Median Income',
              il_year,
              il_hh_size = 0,
              il_type = 'State Median Income',
              income_limit)

income_limits_flat <- bind_rows(amis_adjacency,localities_state_income)

income_limits <- bind_rows(amis_adjacency,localities_state_income) %>% 
    filter(il_year==2021 & il_name == 'State Median Income'|
           il_year==2022 & il_name != 'State Median Income'   , 
           il_hh_size==3) %>% 
    select(geoid,il_name,il_type,income_limit) %>% 
    crossing(title = c('VALUE','GROSS RENT')) %>% 
    mutate(income_limit = if_else(title == 'VALUE',
                                  income_limit,
                                  income_limit*.6))

affordable_to <-  function(amount,tenure){
    
    result <- if_else(tenure=='VALUE',
                      amount/3.5,
                      (amount*3.333)*12)
    
}

results_acs <- bind_rows(acs_own,acs_rent) %>% 
    left_join(acs_available_units, by = c('geoid','title')) %>% 
    mutate(range_min = as.numeric(range_min),
           range_max = as.numeric(range_max),
           margin_of_error = abs(margin_of_error)) %>% 
  filter(!geoid %in% c('0550000US08031',
                      '0550000US08014'))

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
             `Income Limit Type` = il_type) %>% 
    summarise(`Affordable Housing Baseline Estimate` = sum(affordable_units)) %>% 
    ungroup() %>% 
    mutate(`Three Year Commitment Estimate` = ceiling(`Affordable Housing Baseline Estimate`*0.09),
           `Annualized Commitment Estimate` = ceiling(`Affordable Housing Baseline Estimate`*0.03)) %>% 
    arrange(`Locality Name`,`Income Limit Type`)

write_csv(baseline,'ACS Baseline Options.csv')

write_csv(income_limits_flat,'income_limits.csv')

write_feather(income_limits_flat,'income_limits.feather')

write_csv(results_acs,'acs.csv')

write_feather(results_acs,'acs.feather')

