library(tidyverse)
library(readxl)

il_urls <- c('https://www.huduser.gov/portal/datasets/il/il22/Section8-FY22.xlsx',
             'https://www.huduser.gov/portal/datasets/il/il21/Section8-FY21.xlsx',
             'https://www.huduser.gov/portal/datasets/il/il20/Section8-FY20.xlsx',
             'https://www.huduser.gov/portal/datasets/il/il19/Section8-FY19.xlsx',
             'https://www.huduser.gov/portal/datasets/il/il18/Section8-FY18.xlsx',
             'https://www.huduser.gov/portal/datasets/il/il17/Section8-FY17.xlsx')

il_files <- paste(tempdir(),str_remove(il_urls,".*/"),sep = '\\')

walk2(.x = il_urls,.y = il_files,~download.file(url = .x,destfile = .y,method = 'curl'))


ami_dl <- map_dfr(.x= il_files,~read_excel(.x) %>%
                    filter(str_sub(fips2010,-5)=='99999') %>% 
                    select(contains(c('l50','median','fips','County_Name'))) %>%
                    mutate(fiscal_year = str_extract(.x,'-.*') %>% 
                             str_remove_all('-|.xlsx') %>% 
                             str_c('F',.)) %>% 
                    pivot_longer(!contains(c('fips','year','County_Name'))) %>% 
                    mutate(il_hh_size = as.integer(str_remove(str_extract(name,'_.*'),'_'))) %>% 
                    transmute(il_name = if_else(str_detect(name,'median'),
                                                          'Median Family Income',
                                                           'Area Median Income'),
                              fiscal_year,
                              il_year = as.integer(paste0('20',str_sub(fiscal_year,-2))),
                              geoid = str_sub(fips2010,1,5),
                              il_hh_size = replace_na(il_hh_size,0), 
                              income_limit = if_else(str_detect(name,'median'),
                                                  value,
                                                  value*2),
                           )
                  )



county_ami <- function(county_geoid,year,hh_size) {
  
   
  il <- ami_dl %>%
    filter(geoid == as.character(county_geoid),
           il_year == as.integer(year),
           il_hh_size == as.integer(hh_size)) %>% 
    pull(income_limit)
  
    
    return(il)
  
  
}

county_ami_df <- function(county_geoids) {
  
  
  il <- ami_dl %>%
    filter(geoid %in% county_geoids)
  
  
  return(il)
  
  
}

