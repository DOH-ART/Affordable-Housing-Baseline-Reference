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
    HH_size = st.slider('Household Size',1,5,3)
    ILY = st.selectbox('Income Limit Year',list(set((income_data['il_year']))))
    IL = st.selectbox('Income Limit',list(set(income_data['income_limit'][income_data['geoid'] == geoid_location[0]].tolist())))


locality_submitted = acs_data[acs_data['geoid'] == geoid_location[0]]
LocalitySubmittedSum = sum(locality_submitted['estimate'])*HVtoIncome_slider
result = LocalitySubmittedSum * 3.333 * 12
st.metric(label = 'Baseline Estimate', value = result)