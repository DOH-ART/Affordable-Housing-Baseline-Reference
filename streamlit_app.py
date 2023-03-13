import streamlit as st 
from streamlit_embedcode import github_gist
import pandas as pd 
import numpy as np

st.title('Baseline App')
datasets = st.container()

acs_data_url = (r'C:\Users\bmadalon\Documents\GitHub\Affordable-Housing-Baseline-Reference\acs.csv')
income_data_url = (r'C:\Users\bmadalon\Documents\GitHub\Affordable-Housing-Baseline-Reference\income_limits.csv')

def load_data(data_url):
    data = pd.read_csv(data_url)
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis='columns',inplace=True)
    return data

st.text('Welcome to the data thing that needs a good name!')

with datasets:
    acs_data = load_data(acs_data_url)
    st.write(acs_data.head())
    income_data = load_data(income_data_url)
    st.write(income_data.head())
    HVtoIncome_slider = st.slider('Home Value to Income Ratio',2.5,4.5,3.5,.01)

acs_data['geography_name'] = acs_data['geography_name'].astype(str)

col1, col2 = st.columns((1,1))
with col1:
    SaleUnitAvailabilityRate = st.slider('Sale unit Availability Rate',0,100,100)
with col2:
    RentalUnitAvailabilityRate = st.slider('Rental Unit Availability Rate',0,100,60)

#Input widgets for sidebar
with st.sidebar:
    location = st.selectbox('County or Municipality',list(set(acs_data['geography_name'][~acs_data['geography_name'].str.contains('nan')].tolist())))
    geoid_location = list(set(acs_data['geoid'][acs_data['geography_name'] == location]))
    adjacency = st.selectbox('County or Municipality Adjacency',list(set(income_data['il_type'][income_data['geoid'] == geoid_location[0]].tolist())))
    HH_size = st.slider('Household Size',1,8,3)
    ILY = st.selectbox('Income Limit Year',list(set((income_data['il_year']))))
    IL = st.selectbox('Income Limit',list(set(income_data['income_limit'][income_data['geoid'] == geoid_location[0]].tolist())))


acs_data['range_max'] = acs_data['range_max'].astype(float)
locality_submitted = acs_data[acs_data['geoid'] == geoid_location[0]]
#locality submitted rental and ownership VALUE AND GROSS RENT 
locality_submittedIncome = income_data[income_data['geoid'] == geoid_location[0]]
Income_dataYear = locality_submittedIncome[locality_submittedIncome['il_year'] == ILY]
Income_dataIL_type = Income_dataYear[Income_dataYear['il_type'].str.contains(adjacency)]
Income_data_hhsize = Income_dataIL_type[Income_dataIL_type['il_hh_size'] == HH_size]
st.write(Income_data_hhsize)
Renter_medianIncome = ((Income_data_hhsize['income_limit'].tolist()[0]*.6)//12)*.3
Owner_medianIncome = ((Income_data_hhsize['income_limit'].tolist()[0]*1))*3.5
st.write(Owner_medianIncome)
st.write(Renter_medianIncome)
locality_submittedRenter = locality_submitted[(locality_submitted['range_max'] <= float(Renter_medianIncome)) & (locality_submitted['title'].str.contains('GROSS RENT'))]
locality_submittedOwner = locality_submitted[(locality_submitted['range_max'] <= float(Owner_medianIncome)) & (locality_submitted['title'].str.contains('VALUE'))]
st.write(locality_submittedRenter)
st.write(locality_submittedOwner)
LocalitySubmittedSum_Owner = sum(locality_submittedOwner['estimate'])*HVtoIncome_slider
LocalitySubmittedSum_Rent = sum(locality_submittedRenter['estimate'])*HVtoIncome_slider
result =  (LocalitySubmittedSum_Rent + LocalitySubmittedSum_Owner)* 3.333 * 12
st.metric(label = 'Baseline Estimate', value = result)