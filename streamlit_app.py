import streamlit as st 
import pandas as pd 
import numpy as np
from re import findall
st.set_page_config(layout="wide")
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

acs_data['geography_name'] = acs_data['geography_name'].astype(str)

avail_counties = (acs_data.query('geography_name.str.contains("Unincorporated")')
                            .query('not geoid == "0550000US08014"')
                            .query('not geoid == "0550000US08031"')
                            .loc[:, 'geography_name']
                            .drop_duplicates()
                            .dropna()
                            .to_list())

avail_munis = (acs_data.query('not geography_name.str.contains("Unincorporated")')
                            .query('not geography_name == "nan"')
                            .loc[:, 'geography_name']
                            .drop_duplicates()
                            .dropna()
                            .to_list())

avil_jurisdictions = dict(County = [''] + avail_counties,
                          Municipality = [''] + avail_munis,
                          space = '')

avail_names = income_data['il_name'].drop_duplicates().to_list()

#Input widgets for sidebar
with st.sidebar:
    with st.expander("Start here", expanded = True):

        juris_type_selection = st.radio('Select a jurisdiction type',['County','Municipality'], horizontal=True)

        location = st.selectbox('Select a jurisdiction',avil_jurisdictions[juris_type_selection])
        if location == '':
            st.stop()

        geoid_location = (acs_data.query("geography_name == @location")
                                .loc[:, 'geoid']
                                .drop_duplicates()
                                .to_list())


        name = st.selectbox('Income Limit Type',avail_names, index=1)

        avail_years = (income_data.query("geoid == @geoid_location")
                                .query("il_name == @name")
                                .loc[:, 'il_year']
                                .drop_duplicates()
                                .sort_values(ascending = False)
                                .to_list())
        ILY = st.selectbox('Income Limit Year',avail_years)

        if name == '' or ILY == '':
            st.stop()
        
        avail_adjacency = (income_data.query("geoid == @geoid_location")
                                .query("il_name == @name")
                                .loc[:, 'il_type']
                                .drop_duplicates()
                                .to_list())
        
        if name == 'State Median Income':
            adjacency = 'State Median Income'
            
        else:
            adjacency = st.selectbox('Select Income Limit',avail_adjacency)

        if name == 'Area Median Income':
            HH_size = st.slider('Household Size',1,8,3)
        else: 
            HH_size = 0



        median_income = (income_data.query("geoid == @geoid_location")
                    .query("il_name == @name")
                    .query("il_type == @adjacency")
                    .query("il_hh_size == @HH_size")
                    .query('il_year == @ILY')
                    .loc[:, 'income_limit']
                    .to_list()[0])
        calculate_button = st.button('Calculate Median Income')

    
        st.metric(label = 'Selected Median income',value = f"${median_income:,}")

    with st.expander('Optional variables', expanded = True):
        SaleUnitAvailabilityRateDefault = (acs_data.query("geoid == @geoid_location")
                                                .query('title == "VALUE"')
                                                .loc[:, 'proration_available_units']
                                                .drop_duplicates()
                                                .to_list())
        SaleUnitAvailabilityRate = st.slider('Sale unit Availability Rate',0.0,1.0,SaleUnitAvailabilityRateDefault,.01)
        SaleUnitAvailabilityRateDefault = (acs_data.query("geoid == @geoid_location")
                                                .query('title == "GROSS RENT"')
                                                .loc[:, 'proration_available_units']
                                                .drop_duplicates()
                                                .to_list())
        RentalUnitAvailabilityRate = st.slider('Rental Unit Availability Rate',0.0,1.0,SaleUnitAvailabilityRateDefault,.01)
        HVtoIncome_slider = st.slider('Home Value to Income Ratio',2.5,4.5,3.5,.01)









renter_income_limit = round(median_income * .6)

owner_income_limit = median_income

max_affordable_rent = round((renter_income_limit/12)*.3)
max_affordable_price = round(owner_income_limit * HVtoIncome_slider)



col3, col4 = st.columns((1,1))
with col3:
    st.metric(label = 'Homeowner/Homebuyer Income Limit',
              value = f"${owner_income_limit:,}",
              help='Your selected Median Income of 'f"${median_income:,}" + ' x 1.0')

with col4:    
    st.metric(label = 'Renter Income Limit',
              value = f"${renter_income_limit:,}",
              help='Your selected Median Income of 'f"${median_income:,}" + ' x 0.6')

col5, col6 = st.columns((1,1))
with col5:
    st.metric(label = 'Max Affordable For-Sale Price',
              value = f"${max_affordable_price:,}",
              help = 'Homeowner/Homebuyer Income Limit of ' + f"${owner_income_limit:,}" + ' x ' + f"{HVtoIncome_slider:}")
    
with col6:
    st.metric(label = 'Max Affordable Rent',
              value = f"${max_affordable_rent:,}",
              help = 'Renter Income Limit of (' + f"${renter_income_limit:,}" + '/12) x 0.3')
    


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
locality_submittedOwner['Range'] = locality_submittedOwner['range_min'].map('${:,.0f}'.format) + '  to ' + locality_submittedOwner['range_max'].map('${:,.0f}'.format)
locality_submittedRenter['Range'] = locality_submittedRenter['range_min'].map('${:,.0f}'.format) + '  to ' + locality_submittedRenter['range_max'].map('${:,.0f}'.format)
locality_submittedOwner['Occupied Units'] = locality_submittedOwner['estimate']
locality_submittedRenter['Occupied Units'] = locality_submittedRenter['estimate']

# CSS to inject contained in a string
hide_table_row_index = """
            <style>
            thead tr th:first-child {display:none}
            tbody th {display:none}
            </style>
            """

# Inject CSS with Markdown
st.markdown(hide_table_row_index, unsafe_allow_html=True)

col10, col11 = st.columns((1,1))

with col10:
    st.table(locality_submittedOwner[['Range', 'Occupied Units', 'Available Units', 'Affordable Units']])
with col11:
    st.table(locality_submittedRenter[['Range', 'Occupied Units', 'Available Units', 'Affordable Units']])
LocalitySubmittedSum_Owner = sum(locality_submittedOwner['Affordable Units'])
LocalitySubmittedSum_Rent = sum(locality_submittedRenter['Affordable Units'])
result =  round(LocalitySubmittedSum_Rent + LocalitySubmittedSum_Owner)
st.metric(label = 'Baseline Estimate', value = f'{result:,}' )

st.latex(r'\frac{'+f"{renter_income_limit:}" + r'}{12_{months}}\times .3')
