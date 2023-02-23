ami_dir <- tempfile(fileext = ".xlsx")


download.file('https://www.huduser.gov/portal/datasets/il/il22/Section8-FY22.xlsx',
              ami_dir,
              method = 'curl')

ami_dl <- read_excel(ami_dir) %>%
  transmute(county = str_sub(fips2010,1,5),
            ami = l50_3*2)


county_ami <- function(county_geoid) {
  
  county_ami <- 
  ami_dl %>%
    filter(county == county_geoid) %>% 
    pull(ami)
  
    
    return(county_ami)
  
  
}
