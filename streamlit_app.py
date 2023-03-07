import streamlit as st 
from streamlit_embedcode import github_gist
import pandas as pd 
import numpy as np

st.title('practice app')

acs_data_url = (r'C:\Users\bmadalon\Documents\GitHub\Affordable-Housing-Baseline-Reference\acs.csv')\


def load_data(nrows):
    data = pd.read_csv(data_url, nrows=nrows)
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis='columns',inplace=True)
    return data

data_load = st.text('Loading Data..')
acs_data = load_data(100)
income_data = load_data(100)
data_load.text('Loading Data...done')