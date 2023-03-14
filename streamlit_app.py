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
    st.write(acs_data.head())
    income_data = load_data(income_data_url)
    st.write(income_data.head())
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

   
median_income = (income_data.query("geoid == @geoid_location")
                   .query("il_name == @name")
                   .query("il_type == @adjacency")
                   .query("il_hh_size == @HH_size")
                   .query('il_year == @ILY')
                   .loc[:, 'income_limit']
                   .to_list()[0])

renter_income_limit = median_income * .6

owner_income_limit = median_income

max_affordable_rent = ((renter_income_limit/12)*.3)
max_affordable_price = owner_income_limit * HVtoIncome_slider

st.metric(label = 'Selected Median income',value = median_income)
st.metric(label = 'Homeowner/Homebuyer Income Limit',value = owner_income_limit)
st.metric(label = 'Renter Income Limit',value = renter_income_limit)
st.metric(label = 'Max Affordable Rent',value = max_affordable_rent)
st.metric(label = 'Max Affordable For-Sale Price',value = max_affordable_price)

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


locality_submittedOwner['Percent of Units Affordable'] = sum(locality_submittedOwner['Available Units'][locality_submittedOwner['range_max'] <= max_affordable_price]) / sum(locality_submittedOwner['estimate'])
locality_submittedRenter['Percent of Units Affordable'] = sum(locality_submittedRenter['Available Units'][locality_submittedRenter['range_max'] <= max_affordable_rent]) / sum(locality_submittedRenter['estimate'])

locality_submittedOwner['Affordable Units'] = round(locality_submittedOwner['Percent of Units Affordable'] * locality_submittedOwner['Available Units'])
locality_submittedRenter['Affordable Units'] = round(locality_submittedRenter['Percent of Units Affordable'] * locality_submittedRenter['Available Units'])

st.write(locality_submittedRenter)
st.write(locality_submittedOwner)
LocalitySubmittedSum_Owner = sum(locality_submittedOwner['Affordable Units'])
LocalitySubmittedSum_Rent = sum(locality_submittedRenter['Affordable Units'])
result =  (LocalitySubmittedSum_Rent + LocalitySubmittedSum_Owner)
st.metric(label = 'Baseline Estimate', value = result)
