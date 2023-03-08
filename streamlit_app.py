import streamlit as st 
from streamlit_embedcode import github_gist
import pandas as pd 
import numpy as np

st.title('practice app')

acs_data_url = (r'C:\Users\bmadalon\Documents\GitHub\Affordable-Housing-Baseline-Reference\acs.csv')
income_data_url = (r'C:\Users\bmadalon\Documents\GitHub\Affordable-Housing-Baseline-Reference\income_limits.csv')

def load_data(data_url, nrows):
    data = pd.read_csv(data_url, nrows=nrows)
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis='columns',inplace=True)
    return data

st.text('Welcome to the data thing that needs a good name!')
acs_data = load_data(acs_data_url, 100)
income_data = load_data(income_data_url, 100)
HVtoIncome_slider = st.slider('Home Value to Income Ratio',2.5,4.5)
col1, col2 = st.beta_columns((1,1))
with col1:
    SaleUnitAvailabilityRate = st.slider('Sale unit Availability Rate',0,100)
with col2:
    RentalUnitAvailabilityRate = st.slider('Rental Unit Availability Rate',0,100)

#Input widgets for sidebar
with st.sidebar:
    st.selectbox('County or Municipality',['Denver','Aurora'])
    st.selectbox('County or Municipality Adjacency',['Denver','Aurora'])
    st.selectbox('Area Median Income',['100','80','60'])
    st.slider('Household Size',1,5)
    st.selectbox('Income Limit',['limit 1','limit 2'])


