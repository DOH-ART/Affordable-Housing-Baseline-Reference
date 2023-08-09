library(tidyverse)

read_geos <- function(end_year,n_year,excluded_suffixes){

geo_url <-
paste0('https://www2.census.gov/programs-surveys/acs/summary_file/',
        end_year,
        '/table-based-SF/documentation/Geos',
        end_year,
        n_year,
        'YR.txt')

data_geo <-
read_delim(geo_url) %>%
  transmute(sumlevel=SUMLEVEL,
            geoid = GEO_ID,
            geography_name = NAME)

data_geo_w_uninc <-
data_geo %>%
  filter(sumlevel=='050',
         !geoid %in% c('0500000US08014',
                       '0500000US08031')
         ) %>%
              mutate(sumlevel='055',
                     geoid = paste0(sumlevel,str_sub(geoid,4)),
                     geography_name = str_replace(geography_name,
                                                'County',
                                                'County (Unincorporated)')
                     )


data_geo_w_muni <-
data_geo %>%  
            filter(sumlevel=='160',
                   !str_detect(geography_name,'CDP')) %>%
              mutate(sumlevel='162',
                     geoid = paste0(sumlevel,str_sub(geoid,4)),
                     geography_name = case_when(geography_name == 'Denver city, Colorado' ~ 'Denver City and County, Colorado',
                                                 geography_name == 'Broomfield city, Colorado' ~  'Broomfield City and County, Colorado' ,
                                                 TRUE ~ geography_name)
                     )
                               
data_geo_w_reservation <-
  data_geo %>%  
  filter(sumlevel=='250',
         str_detect(geography_name,'CO'))
               
                 


results <- bind_rows(data_geo,
                     data_geo_w_uninc,
                     data_geo_w_muni,
                     data_geo_w_reservation) %>% 
  mutate(geography_name = str_remove_all(geography_name,str_c(excluded_suffixes,
                                                               collapse = '|')
                                          )
         )

return(results)
}