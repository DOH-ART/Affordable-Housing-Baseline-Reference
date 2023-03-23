import streamlit as st
import pandas as pd

st.set_page_config(layout="centered")
st.title("Baseline App")
st.write('Fill out the select boxes to the left and your results will be posted here')
#"st.session_state values:", st.session_state

acs_data_url = "./acs.csv"
income_data_url = "./income_limits.csv"


def load_data(data_url):
    data = pd.read_csv(
        data_url,
        dtype={
            "geoid": "object",
            "geography_name": "object",
            "title": "object",
            "range_min": "float64",
            "range_max": "float64",
            "estimate": "float64",
            "margin_of_error": "float64",
            "proration_available_units": "float64",
        },
    )
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis="columns", inplace=True)
    return data


acs_data = load_data(acs_data_url)
income_data = load_data(income_data_url)

acs_data["geography_name"] = acs_data["geography_name"].astype(str)

county_options = (
    acs_data.query('geography_name.str.contains("Unincorporated")')
    .query('not geoid == "0550000US08014"')
    .query('not geoid == "0550000US08031"')
    .loc[:, "geography_name"]
    .drop_duplicates()
    .dropna()
    .to_list()
)

municipality_options = (
    acs_data.query('not geography_name.str.contains("Unincorporated")')
    .query('not geography_name == "nan"')
    .loc[:, "geography_name"]
    .drop_duplicates()
    .dropna()
    .to_list()
)

jursidiction_options = dict(
    County=[""] + county_options, Municipality=[""] + municipality_options, space=""
)

income_limit_name_options = income_data["il_name"].drop_duplicates().to_list()
income_limit_name_options.insert(0,"")

# Input widgets for sidebar
with st.sidebar:
    with st.expander("Start here", expanded=True):
        st.write('Step 1: Pick whether you wish to report on a County or Municipality')
        jurisdiction_type_selection = st.radio(
            "Select a jurisdiction type", ["County", "Municipality"], horizontal=True,
            key = 'Select a jurisdiction type'
        )
        st.write('Step 2: Pick which locality you are located in')
        jurisdiction_name_selection = st.selectbox(
            "Select a jurisdiction", jursidiction_options[jurisdiction_type_selection],
            key = 'Select a jurisdiction', help = 'If your specific locality is not found try changing your jurisdiction type.'
        )
        
        if jurisdiction_name_selection == "":
            st.stop()

        jurisdiction_geoid_selection = (
            acs_data.query("geography_name == @jurisdiction_name_selection")
            .loc[:, "geoid"]
            .drop_duplicates()
            .to_list()
        )

        st.write('Step 3: Income limit type has three unique options each with different variables associated with them')
        income_limit_name_selection = st.selectbox(
            "Income Limit Type", income_limit_name_options, index = 0,
            key = 'Income Limit Type', help = 'Area Median Income allows you to pick your preferred household size and adjacent county Income Limits, Median Family Income allows you to only pick adjacent Income Limits, and State Median Income allows you only to pick the year in which that median income existed.'
        )

        if income_limit_name_selection == '':
            st.stop()

        year_options = (
            income_data.query("geoid == @jurisdiction_geoid_selection")
            .query("il_name == @income_limit_name_selection")
            .loc[:, "il_year"]
            .drop_duplicates()
            .sort_values(ascending=False)
            .to_list()
        )

        year_options.insert(0,"")

        st.write('Step 4: pick which year you would like your income limit to report from')
        year_selection = st.selectbox("Income Limit Year", year_options,index=0,key = 'Income Limit year')

        if income_limit_name_selection == "" or year_selection == "":
            st.stop()

        adjacency_options = (
            income_data.query("geoid == @jurisdiction_geoid_selection")
            .query("il_name == @income_limit_name_selection")
            .loc[:, "il_type"]
            .drop_duplicates()
            .to_list()
        )

        adjacency_options.insert(0,'')

        
        if income_limit_name_selection == "State Median Income":
            adjacency_selection = "State Median Income"

        else:
            st.write('Step 5: Select where you want your Income Limit is reporting from')
            adjacency_selection = st.selectbox("Select Income Limit", adjacency_options, key = 'Select Income Limit')



        if income_limit_name_selection == "Area Median Income":
            household_size_selection = st.slider("Household Size", 1, 8, 3, key = 'Household Size')
        else:
            household_size_selection = 0

        if adjacency_selection == '':
            st.stop()
        
        median_income_selection = (
                income_data.query("geoid == @jurisdiction_geoid_selection")
                .query("il_name == @income_limit_name_selection")
                .query("il_type == @adjacency_selection")
                .query("il_hh_size== @household_size_selection")
                .query("il_year == @year_selection")
                .loc[:, "income_limit"]
                .to_list()
            )
        st.write('This number is affected from the options you chose from above')
        st.metric(label="Selected Median income", value=f"${median_income_selection[0]:,}")

        

    with st.expander("Optional variables", expanded=True):
        ownership_unit_availability_rate_default = (
            acs_data.query("geoid == @jurisdiction_geoid_selection")
            .query('title == "VALUE"')
            .loc[:, "proration_available_units"]
            .drop_duplicates()
            .to_list()
        )
        sale_unit_availibility_rate_selection = st.slider(
            "Sale unit Availability Rate",
            0.0,
            1.0,
            ownership_unit_availability_rate_default,
            0.01,
            key = 'Sale unit Availability Rate'
        )
        rental_unit_availability_rate_default = (
            acs_data.query("geoid == @jurisdiction_geoid_selection")
            .query('title == "GROSS RENT"')
            .loc[:, "proration_available_units"]
            .drop_duplicates()
            .to_list()
        )
        rental_unit_availibility_rate_selection = st.slider(
            "Rental Unit Availability Rate",
            0.0,
            1.0,
            ownership_unit_availability_rate_default,
            0.01,
            key = 'Rental Unit Availability Rate'
        )
        home_value_to_income_ratio_selection = st.slider(
            "Home Value to Income Ratio", 2.5, 4.5, 3.5, 0.01,
            key = 'Home Value to Income Ratio'
        )

st.markdown(
"""
<style>
[data-testid="stSidebar"][aria-expanded="true"] > div:first-child {
width: 500px;
}
[data-testid="stExpander"][aria-expanded="true"] > div:first-child {
width: 500px;
margin-left: -500px;
}
</style>
""",
unsafe_allow_html=True
)

renter_income_limit = round(median_income_selection[0] * 0.6)
owner_income_limit = median_income_selection[0]
max_affordable_rent = round((renter_income_limit / 12) * 0.3)
max_affordable_price = round(owner_income_limit * home_value_to_income_ratio_selection)


owner_results = (
    acs_data.query("geoid == @jurisdiction_geoid_selection")
    .query('title == "VALUE"')
    .loc[:, ["range_min", "range_max", "estimate"]]
)

owner_results['range_max'][owner_results['range_max'] < 200000] = 199999
owner_results['range_min'][owner_results['range_max'] < 200000] = 0
owner_results = pd.pivot_table(owner_results, values = 'estimate', index = ['range_max','range_min'], aggfunc=sum).reset_index()

renter_results = (
    acs_data.query("geoid == @jurisdiction_geoid_selection")
    .query('title == "GROSS RENT"')
    .loc[:, ["range_min", "range_max", "estimate"]]
)

renter_results['range_max'][renter_results['range_max'] < 800] = 799
renter_results['range_min'][renter_results['range_max'] < 800] = 0
renter_results = pd.pivot_table(renter_results, values = 'estimate', index = ['range_max','range_min'], aggfunc=sum).reset_index()


owner_results["Available Units"] = round(
    owner_results["estimate"] * sale_unit_availibility_rate_selection
)
renter_results["Available Units"] = round(
    renter_results["estimate"] * rental_unit_availibility_rate_selection
)

# 800 rental side, 200,000 ownership bucket

owner_results["Percent of Units Affordable"] = 0
for idx, rows in owner_results.iterrows():
    if rows["range_max"] <= max_affordable_price:
        owner_results.at[idx, "Percent of Units Affordable"] = 1
    elif (
        rows["range_min"] <= max_affordable_price
        and rows["range_max"] >= max_affordable_price
    ):
        owner_results.at[idx, "Percent of Units Affordable"] = (
            max_affordable_price / rows["range_max"]
        )
    else:
        owner_results.at[idx, "Percent of Units Affordable"] = 0

renter_results["Percent of Units Affordable"] = 0
for idx, rows in renter_results.iterrows():
    if rows["range_max"] <= max_affordable_rent:
        renter_results.at[idx, "Percent of Units Affordable"] = 1
    elif (
        rows["range_min"] <= max_affordable_rent
        and rows["range_max"] >= max_affordable_rent
    ):
        renter_results.at[idx, "Percent of Units Affordable"] = (
            max_affordable_rent / rows["range_max"]
        )
    else:
        renter_results.at[idx, "Percent of Units Affordable"] = 0


owner_percent_affordable = sum(
    owner_results["Available Units"][owner_results["range_max"] <= max_affordable_price]
) / sum(owner_results["estimate"])
renter_percent_affordable = sum(
    renter_results["Available Units"][
        renter_results["range_max"] <= max_affordable_rent
    ]
) / sum(renter_results["estimate"])

owner_results["Affordable Units"] = round(
    owner_results["Percent of Units Affordable"] * owner_results["Available Units"]
)
renter_results["Affordable Units"] = round(
    renter_results["Percent of Units Affordable"] * renter_results["Available Units"]
)


owner_results["Range"] = (
    owner_results["range_min"].map("${:,.0f}".format)
    + "  to "
    + owner_results["range_max"].map("${:,.0f}".format)
)
renter_results["Range"] = (
    renter_results["range_min"].map("${:,.0f}".format)
    + "  to "
    + renter_results["range_max"].map("${:,.0f}".format)
)
owner_results["Occupied Units"] = owner_results["estimate"]
renter_results["Occupied Units"] = renter_results["estimate"]

owner_total_affordable_units = sum(owner_results["Affordable Units"])
renter_total_affordable_units = sum(renter_results["Affordable Units"])
total_affordable_units = round(
    renter_total_affordable_units + owner_total_affordable_units
)

# CSS to inject contained in a string
hide_table_row_index = """
            <style>
            thead tr th:first-child {display:none}
            tbody th {display:none}
            </style>
            """

# Inject CSS with Markdown
st.markdown(hide_table_row_index, unsafe_allow_html=True)

with st.container():

    st.subheader('Baseline and Goal Results')

    col1a,col1b,col1c = st.columns(3, gap="large")
    with col1a:
        st.metric(label="Baseline Estimate", value=f"{total_affordable_units:,}")
        
    with col1b:
        st.metric(label="Annual Goal", value=f"{round(total_affordable_units*0.03):,}")

    with col1c:
        st.metric(label="Three Year Cycle Goal", value=f"{round(total_affordable_units*0.09):,}")

with st.expander("Income Limits and Max Prices/Rates Based on Your Selections"):
    st.write(
        "These income limits have been calculated based on your selections in the sidebar:"
    )
    col3, col4 = st.columns(2, gap="large")
    with col3:
        st.metric(
            label="Homeowner/Homebuyer Income Limit",
            value=f"${owner_income_limit:,}",
            help="Your selected Median Income of "
            f"${median_income_selection[0]:,}" + " x 1.0",
        )

    with col4:
        st.metric(
            label="Renter Income Limit",
            value=f"${renter_income_limit:,}",
            help="Your selected Median Income of "
            f"${median_income_selection[0]:,}" + " x 0.6",
        )
    st.write(
        "---"
    )
    st.write(
        "These Max Affordable For-Sale Prices and Rental Rates are calculated based on the income limits above:"
    )
    col5, col6 = st.columns(2, gap="large")
    with col5:
        st.metric(
            label="Max Affordable For-Sale Price",
            value=f"${max_affordable_price:,}",
            help="Homeowner/Homebuyer Income Limit of "
            + f"${owner_income_limit:,}"
            + " x "
            + f"{home_value_to_income_ratio_selection:}",
        )

    with col6:
        st.metric(
            label="Max Affordable Rent",
            value=f"${max_affordable_rent:,}",
            help="Renter Income Limit of ("
            + f"${renter_income_limit:,}"
            + "/12) x 0.3",
        )
owner_results['Occupied Units'] = owner_results['Occupied Units'].astype(int)
owner_results['Available Units'] = owner_results['Available Units'].astype(int)
owner_results['Affordable Units'] = owner_results['Affordable Units'].astype(int)

renter_results['Occupied Units'] = renter_results['Occupied Units'].astype(int)
renter_results['Available Units'] = renter_results['Available Units'].astype(int)
renter_results['Affordable Units'] = renter_results['Affordable Units'].astype(int)

with st.expander("Housing Affordability by Range"):
    col10, col11 = st.columns(2)
    with col10:
        st.table(
            owner_results[
                ["Range", "Occupied Units", "Available Units", "Affordable Units"]
            ]
        )
    with col11:
        st.table(
            renter_results[
                ["Range", "Occupied Units", "Available Units", "Affordable Units"]
            ]
        )

col7, col8 = st.columns((1, 1))
with col7:
    st.metric(
        label="Percent of Ownership Stock Included in Baseline",
        value=f"{owner_percent_affordable:.1%}",
    )
with col8:
    st.metric(
        label="Percent of Rental Stock Included in Baseline",
        value=f"{renter_percent_affordable:.1%}",
    )
st.experimental_get_query_params()

Downloadable_file = owner_results[["Range", "Occupied Units", "Available Units", "Affordable Units"]].append(renter_results[["Range", "Occupied Units", "Available Units", "Affordable Units"]])

st.download_button('Download Your Baseline Results',Downloadable_file.to_csv(), file_name = 'BaselineReults.csv')