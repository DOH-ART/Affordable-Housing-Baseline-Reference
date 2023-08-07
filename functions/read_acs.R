library(tidyverse)

read_acs <- function(table_name,
                     n_year,
                     end_year,
                     summary_levels,
                     excluded_cols) {
  data_geo_w_uninc_muni <- read_geos(end_year = end_year,
                                     n_year = n_year,
                                     excluded_suffixes=c(', Colorado'))
  
  url_table_shells <-
    paste0(
      'https://www2.census.gov/programs-surveys/acs/summary_file/',
      end_year,
      '/table-based-SF/documentation/ACS',
      end_year,
      n_year,
      'YR_Table_Shells.txt'
    )
  
  url_acs <-
    c(table_name) %>%
    map(
      ~ paste0(
        'https://www2.census.gov/programs-surveys/acs/summary_file/',
        end_year,
        '/table-based-SF/data/',
        n_year,
        'YRData/acsdt',
        n_year,
        'y',
        end_year,
        '-',
        .,
        '.dat'
      )
    )
    
  
  data_table_shells <-
    read_delim(url_table_shells) %>%
    transmute(
      measure_id = `Unique ID`,
      label = Label,
      title = Title,
      universe = Universe
    )
  
  cdp_geoids <- data_geo_w_uninc_muni %>%
    filter(str_detect(geography_name, 'CDP')) %>%
    pull(geoid)
  
  Reservation <- data_geo_w_uninc_muni %>%
    filter(sumlevel=='250') %>%
    pull(geoid)
  
  data_acs <-
    url_acs %>%
    map_dfr(
      ~ read_delim(.) %>%
        filter(str_sub(GEO_ID, 10, 11) == '08') %>%
        pivot_longer(!GEO_ID,
                     names_to = 'variable',
                     values_to = 'values') %>%
        transmute(
          sumlevel = str_sub(GEO_ID, 1, 3),
          geoid = GEO_ID,
          variable,
          values
        )
    )
  data_acs_tribal <-
    url_acs %>%
    map_dfr(
      ~ read_delim(.) %>%
        filter(str_sub(GEO_ID, 10, 11) == '39') %>%
        pivot_longer(!GEO_ID,
                     names_to = 'variable',
                     values_to = 'values') %>%
        transmute(
          sumlevel = str_sub(GEO_ID, 1, 3),
          geoid = GEO_ID,
          variable,
          values
        )
    )
  
  acs_county <- data_acs %>%
    filter(sumlevel == '050') %>%
    mutate(geoid_county = str_sub(geoid,-5, -1))
  
  acs_county_proration <- data_acs %>% 
    filter(sumlevel == '155', !geoid %in% cdp_geoids) %>%
    group_by(geoid_county = paste0('08', str_sub(geoid,-3, -1)),
             variable) %>%
    summarise(proration = sum(values)) %>% 
    ungroup()
  
  data_acs_uninc <- acs_county %>%
    left_join(acs_county_proration,
              by = c('geoid_county', 'variable')) %>%
    transmute(
      sumlevel = '055',
      geoid = paste0(sumlevel, str_sub(geoid, 4)),
      variable,
      values = values - proration
    )
  
  
  data_acs_munis <-
    data_acs %>%
    filter(sumlevel == '160',!geoid %in% cdp_geoids) %>%
    mutate(sumlevel = '162',
           geoid = paste0(sumlevel, str_sub(geoid, 4)))
  
  data_acs_reservation <- 
    data_acs_tribal %>%
    filter(sumlevel == '250',geoid %in% Reservation) %>%
    mutate(sumlevel = '252',
    geoid = paste0(sumlevel, str_sub(geoid, 4)))
  
  data_acs_uninc_munis <- bind_rows(data_acs,
                                    data_acs_uninc,
                                    data_acs_munis,
                                    data_acs_reservation)
  
  
  data_acs_unpivoted <-
    data_acs_uninc_munis %>%
    mutate(
      measure_id = str_remove(str_remove(variable, 'E'), 'M'),
      measure_type = if_else(str_detect(variable, 'E'),
                             'estimate',
                             'margin_of_error')
    ) %>%
    select(-variable) %>%
    pivot_wider(names_from = measure_type, values_from = values)
  
  
  data_acs_joined <-
    data_acs_unpivoted %>%
    filter(sumlevel %in% selected_summary_levels) %>%
    left_join(data_table_shells, by = 'measure_id') %>%
    left_join(data_geo_w_uninc_muni, by = c('geoid', 'sumlevel'))
  
  results <-
    data_acs_joined %>%
    select(-matches(excluded_cols)) %>%
    mutate(estimate = as.numeric(estimate),
           margin_of_error = as.numeric(margin_of_error))
  
  return(results)
}