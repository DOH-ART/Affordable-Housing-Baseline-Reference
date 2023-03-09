import streamlit as st 
from streamlit_embedcode import github_gist
import pandas as pd 
import numpy as np

st.title('Baseline App')
datasets = st.container()

acs_data_url = (r'C:\Users\bmadalon\Documents\GitHub\Affordable-Housing-Baseline-Reference\acs.csv')
income_data_url = (r'C:\Users\bmadalon\Documents\GitHub\Affordable-Housing-Baseline-Reference\income_limits.csv')
acs_baseline_options_url = (r'C:\Users\bmadalon\Documents\GitHub\Affordable-Housing-Baseline-Reference\ACS Baseline Options.csv')

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
    acs_baseline_options = load_data(acs_baseline_options_url)
    st.write(acs_baseline_options.head())
    HVtoIncome_slider = st.slider('Home Value to Income Ratio',2.5,4.5)
    
col1, col2 = st.columns((1,1))
with col1:
    SaleUnitAvailabilityRate = st.slider('Sale unit Availability Rate',0,100)
with col2:
    RentalUnitAvailabilityRate = st.slider('Rental Unit Availability Rate',0,100)

#Input widgets for sidebar
with st.sidebar:
    location = st.selectbox('County or Municipality',list(set(acs_baseline_options['locality name'].tolist())))
    adjacency = st.selectbox('County or Municipality Adjacency',acs_baseline_options['income limit type'][acs_baseline_options['locality name'] == location].tolist())
    HH_size = st.slider('Household Size',1,5)
    ILY = st.selectbox('Income Limit Year',['2015','2016','2017'])
    IL = st.selectbox('Income Limit',['limit 1','limit 2'])


