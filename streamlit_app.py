import streamlit as st 
import pandas as pd 
import numpy as np

st.title('Baseline App')
datasets = st.container()

acs_data_url = "./acs.csv"
income_data_url = "./income_limits.csv"

def load_data(data_url):
    data = pd.read_csv(data_url,dtype = {'geoid':'object',
                                            'geography_name':'object',
                                            'title':'object',
                                            'range_min':'float64',
                                            'range_max':'float64',
                                            'estimate':'float64',
                                            'margin_of_error':'float64',
                                            'proration_available_units':'float64'})
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis='columns',inplace=True)
    return data


with datasets:
    acs_data = load_data(acs_data_url)
    income_data = load_data(income_data_url)
    HVtoIncome_slider = st.slider('Home Value to Income Ratio',2.5,4.5,3.5,.01)

acs_data['geography_name'] = acs_data['geography_name'].astype(str)



#Input widgets for sidebar
with st.sidebar:
    avail_locations = acs_data['geography_name'].drop_duplicates().to_list()
    location = st.selectbox('County or Municipality',avail_locations)

    geoid_location = list(set(acs_data['geoid'][acs_data['geography_name'] == location]))

    avail_names = income_data['il_name'].drop_duplicates().to_list()
    name = st.selectbox('Income Limit Type',avail_names)

    avail_adjacency = (income_data.query("geoid == @geoid_location")
                              .query("il_name == @name")
                              .loc[:, 'il_type']
                              .drop_duplicates()
                              .to_list())
    adjacency = st.selectbox('Select Income Limit',avail_adjacency)

    if name == 'Area Median Income':
        HH_size = st.slider('Household Size',1,8,3)
    else: 
        HH_size = 0

    avail_years = (income_data.query("geoid == @geoid_location")
                              .query("il_name == @name")
                              .loc[:, 'il_year']
                              .drop_duplicates()
                              .sort_values(ascending = False)
                              .to_list())
    ILY = st.selectbox('Income Limit Year',avail_years)

    median_income = (income_data.query("geoid == @geoid_location")
                   .query("il_name == @name")
                   .query("il_type == @adjacency")
                   .query("il_hh_size == @HH_size")
                   .query('il_year == @ILY')
                   .loc[:, 'income_limit']
                   .to_list()[0])
    st.metric(label = 'Selected Median income',value = f"${median_income:,}")
    

col1, col2 = st.columns((1,1))
with col1:
    SaleUnitAvailabilityRateDefault = (acs_data.query("geoid == @geoid_location")
                                               .query('title == "VALUE"')
                                               .loc[:, 'proration_available_units']
                                               .drop_duplicates()
                                               .to_list())
    SaleUnitAvailabilityRate = st.slider('Sale unit Availability Rate',0.0,1.0,SaleUnitAvailabilityRateDefault,.01)
with col2:
    SaleUnitAvailabilityRateDefault = (acs_data.query("geoid == @geoid_location")
                                               .query('title == "GROSS RENT"')
                                               .loc[:, 'proration_available_units']
                                               .drop_duplicates()
                                               .to_list())
    RentalUnitAvailabilityRate = st.slider('Rental Unit Availability Rate',0.0,1.0,SaleUnitAvailabilityRateDefault,.01)




renter_income_limit = round(median_income * .6)

owner_income_limit = median_income

max_affordable_rent = round((renter_income_limit/12)*.3)
max_affordable_price = round(owner_income_limit * HVtoIncome_slider)



col3, col4 = st.columns((1,1))
with col3:
    st.metric(label = 'Homeowner/Homebuyer Income Limit',value = f"${owner_income_limit:,}")

with col4:    
    st.metric(label = 'Renter Income Limit',value = f"${renter_income_limit:,}")

col5, col6 = st.columns((1,1))
with col5:
    st.metric(label = 'Max Affordable For-Sale Price',value = f"${max_affordable_price:,}")
    
with col6:
    st.metric(label = 'Max Affordable Rent',value = f"${max_affordable_rent:,}")



acs_data['range_max'] = acs_data['range_max'].astype(float)
locality_submitted = acs_data[acs_data['geoid'] == geoid_location[0]]
locality_submittedIncome = income_data[income_data['geoid'] == geoid_location[0]]
Income_dataYear = locality_submittedIncome[locality_submittedIncome['il_year'] == ILY]
Income_dataIL_type = Income_dataYear[Income_dataYear['il_type'].str.contains(adjacency)]
Income_data_hhsize = Income_dataIL_type[Income_dataIL_type['il_hh_size'] == HH_size]

locality_submittedOwner = (acs_data
                            .query('geoid == @geoid_location')
                            .query('title == "VALUE"')
                            .loc[:, ['range_min','range_max','estimate']])

locality_submittedRenter = (acs_data
                            .query('geoid == @geoid_location')
                            .query('title == "GROSS RENT"')
                            .loc[:, ['range_min','range_max','estimate']])



locality_submittedOwner['Available Units'] = round(locality_submittedOwner['estimate'] * SaleUnitAvailabilityRate)
locality_submittedRenter['Available Units'] = round(locality_submittedRenter['estimate'] * RentalUnitAvailabilityRate)

##these newly created columns still need to be populated
##the percent of units that are affordable should be calculated by comparing the
##range_min and range_max to either max_affordable_rent or max_affordable_price to
##this is already set up to feed into Affordable Units once it is populated

#800 rental side, 200,000 ownership bucket 
locality_submittedOwner['Percent of Units Affordable'] = 0
for idx, rows in locality_submittedOwner.iterrows():
    if rows['range_max'] <= max_affordable_price:
        locality_submittedOwner.at[idx,'Percent of Units Affordable'] = 1
    elif rows['range_min'] <= max_affordable_price and rows['range_max'] >= max_affordable_price:
        locality_submittedOwner.at[idx,'Percent of Units Affordable'] = max_affordable_price / rows['range_max']
    else:
        locality_submittedOwner.at[idx,'Percent of Units Affordable'] = 0

locality_submittedRenter['Percent of Units Affordable'] = 0
for idx, rows in locality_submittedRenter.iterrows():
    if rows['range_max'] <= max_affordable_rent:
        locality_submittedRenter.at[idx,'Percent of Units Affordable'] = 1
    elif rows['range_min'] <= max_affordable_rent and rows['range_max'] >= max_affordable_rent:
        locality_submittedRenter.at[idx,'Percent of Units Affordable'] = max_affordable_rent / rows['range_max']
    else:
        locality_submittedRenter.at[idx,'Percent of Units Affordable'] = 0
        
percent_affordable_owner = sum(locality_submittedOwner['Available Units'][locality_submittedOwner['range_max'] <= max_affordable_price]) / sum(locality_submittedOwner['estimate'])
percent_affordable_rental = sum(locality_submittedRenter['Available Units'][locality_submittedRenter['range_max'] <= max_affordable_rent]) / sum(locality_submittedRenter['estimate'])

col7, col8 = st.columns((1,1))
with col7:
    st.metric(label = 'Percent Ownership Stock Included in Baseline',value = f"{percent_affordable_owner:.1%}")
with col8:
    st.metric(label = 'Percent of Rental Stock Included in Baseline',value = f"{percent_affordable_rental:.1%}" )

locality_submittedOwner['Affordable Units'] = round(locality_submittedOwner['Percent of Units Affordable'] * locality_submittedOwner['Available Units'])
locality_submittedRenter['Affordable Units'] = round(locality_submittedRenter['Percent of Units Affordable'] * locality_submittedRenter['Available Units'])

#st.write(locality_submittedRenter)
#st.write(locality_submittedOwner)
LocalitySubmittedSum_Owner = sum(locality_submittedOwner['Affordable Units'])
LocalitySubmittedSum_Rent = sum(locality_submittedRenter['Affordable Units'])
result =  round(LocalitySubmittedSum_Rent + LocalitySubmittedSum_Owner)
st.metric(label = 'Baseline Estimate', value = f'{result:,}' )
