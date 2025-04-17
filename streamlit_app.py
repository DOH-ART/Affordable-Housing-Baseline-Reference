import streamlit as st
import pandas as pd
import time
from json import dumps, loads
import io
import random

st.set_page_config(
    layout="wide",
    menu_items={
        "Report a Bug": "https://dola-doh.atlassian.net/rest/collectors/1.0/template/form/b44faba8"
    },
)
st.image("https://cdola.colorado.gov/sites/dola/files/logo.svg")
st.title("Baseline Assistance Tool")

tab1a, tab1b, tab1c = st.tabs(["Overview", "Definitions", "Help"])
with tab1a:
    """
    Welcome to the State of Colorado's Baseline Assistance Tool. This
    resource can be used to calculate the baseline amount of affordable
    housing within a municipality or county, which can then be incorporated
    into a commitment to annual increases in affordable housing.

    Local governments file a commitment with the Division to unlock funding
    for affordable housing projects and programs made available by Proposition 123.

    To learn more about baselines, commitments, and Proposition 123
    go to [this page](https://engagedola.org/prop-123).
    """
with tab1b:
    """
    - **Affordable Rental Housing**: Rental housing that costs less than 30%
    of the monthly income for a household at or below 60% of the median income.
    - **Affordable For-Sale Housing**: For-sale housing that could be bought
    as such that a mortgage payment costs less than 30% of the monthly income
    for a household at or below 100% of the median income.
    - **Area Median Income**: The median income of households of a given size,
    ranging from 1 to 8 persons, in a county or metropolitan statistical area
    as calculated and published for a given year by the United States
    Department of Housing and Urban Development.
    - **Median Family Income**: The median income of families of all sizes in a
    county or metropolitan statistical area as calculated and published for a
    given year by the United States Department of Housing and Urban Development.
    - **State Median Income**: The median income of all households in the state as
    calculated and published for a given year by the U.S. Census Bureau.
    """
with tab1c:
    """
    Data regarding estimated rents, home values, and unit availability
    rates was obtained from the U.S. Census Bureau American Community Survey
    as 5-year averages from 2017 to 2021. This is the most recently available
    data and can be regarded as from roughly 2019.

    Specific data sources such as data table names and survey vintages
    can be found as captions under tables once the input submissions are complete.

    The results you generate can be saved for later by bookmarking the page,
    or shared by copying and sending the URL in the address bar. Submit a
    bug report by clicking on the navivation menu at the top right if you
    experience an issue.
    """

st.write("---")

st.subheader("Selections")

try:
    if st.session_state["median_income_selection"] != "":
        st.empty()
except KeyError:
    st.write(
        "An analysis of affordable housing stock will be shown below once the selections in the sidebar are complete."
    )

acs_data_url = "./acs.feather"
income_data_url = "./income_limits.feather"

def load_data(data_url):
    data = pd.read_feather(
        data_url
    )
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis="columns", inplace=True)
    return data

#load in data
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

tribal_options = (
    acs_data.query('geography_name.str.contains("Reservation")')
    .loc[:, "geography_name"]
    .drop_duplicates()
    .dropna()
    .to_list()
)

#give options for which jurisdiction
jursidiction_options = dict(
    County=[""] + county_options, Municipality=[""] + municipality_options, Tribe=[""] + tribal_options, space=""
)

income_limit_name_options = income_data["il_name"].drop_duplicates().to_list()
income_limit_name_options.insert(0, "")

# Input widgets for sidebar


params_in = st.query_params


if len(params_in) > 0 and len(st.session_state) == 0:
    try:
        params_dict = loads(params_in.get("query").pop())
        for key in list(params_dict.keys()):
            st.session_state[key] = params_dict[key]
    except AttributeError:
        print('Session has unexpected URL components, clearing URL.')
        st.query_params = {}

#this function allows for the session state to maintain variables
def selection_callback(key):
    print(st.session_state)
    if len(st.session_state) > 0:
        # Update query_params with session state
        for k, v in st.session_state.to_dict().items():
            st.query_params[k] = [str(v)] # Update individual query params
        try:
            # get the current params dict
            params_in = st.query_params
            # set the session state key from the params dict
            st.session_state[key] = params_in[key][0]
        except KeyError:
            print("oops") # if session state key is not in params, handle the KeyError
    elif ValueError and len(st.session_state) > 0:
        st.session_state[key] == ""
        # replace with this line
        for k, v in st.session_state.to_dict().items():
            st.query_params[k] = v  # Update individual query params
        try:
            st.session_state[key] = params_in[key][0]  # changed line
        except KeyError:
            print("New session")
    else:
        print("New session")

#This container is for holding all the variables that different jurisdictions input
with st.container():
    with st.expander("Start here", expanded=True):

        st.selectbox(
            "Step 1: Select a jurisdiction type",
            ["", "County", "Municipality",'Tribe'],
            key="jurisdiction_type",
            on_change=selection_callback("jurisdiction_type"),
        )

        try:
            if st.session_state["jurisdiction_type"] == "":
                st.stop()
        except KeyError:
            st.stop()

        st.selectbox(
            "Step 2: Select a " + st.session_state["jurisdiction_type"],
            jursidiction_options[st.session_state["jurisdiction_type"]],
            key="jurisdiction_name",
            help="Tip: Type in the box to search for a "
            + st.session_state["jurisdiction_type"],
            on_change=selection_callback("jurisdiction_name"),
        )
        st.caption(
            "Tip: Type in the box to search for a "
            + st.session_state["jurisdiction_type"]
        )
        try:
            if st.session_state["jurisdiction_name"] == "":
                st.stop()
        except KeyError:
            st.stop()

        st.session_state["geoid"] = (
            acs_data[
                acs_data["geography_name"] == st.session_state["jurisdiction_name"]
            ]
            .loc[:, "geoid"]
            .drop_duplicates()
            .to_list()
            .pop()
        )

        st.selectbox(
            "Step 3: Income Limit Type",
            income_limit_name_options,
            index=0,
            key="income_limit_type",
            help="Select one of three Income Limit Types, we suggest Median Family Income because it is simplest, and likely most accurate.",
        )

        st.query_params = st.session_state.to_dict()  # replaced here

        try:
            if st.session_state["income_limit_type"] == "":
                st.stop()
        except KeyError:
            st.stop()

        year_options = (
            income_data[
                (income_data["geoid"] == st.session_state["geoid"])
                & (income_data["il_name"] == st.session_state["income_limit_type"])
            ]
            .loc[:, "il_year"]
            .drop_duplicates()
            .sort_values(ascending=False)
            .to_list()
        )

        year_options.insert(0, "")

        st.selectbox(
            "Step 4: Select an Income Limit Year",
            year_options,
            index=0,
            key="year",
            help="Select the year that the income limit data was collected or published in, we recommend "
            + str(year_options[1])
            + " because it is likely most accurate.",
        )

        st.query_params = st.session_state.to_dict()  # replaced here

        try:
            if st.session_state["year"] == "":
                st.stop()
        except KeyError:
            st.stop()

        adjacency_options = (
            income_data[
                (income_data["geoid"] == st.session_state["geoid"])
                & (income_data["il_name"] == st.session_state["income_limit_type"])
                & (income_data["il_year"] == st.session_state["year"])
            ]
            .loc[:, "il_type"]
            .drop_duplicates()
            .to_list()
        )

        adjacency_options.insert(0, "")

        try:
            if st.session_state["income_limit_type"] == "State Median Income":
                adjacency_selection = "income_limit_type"
                st.session_state["income_limit"] = "State Median Income"

            else:
                st.selectbox(
                    "Step 5: Select an Income Limit",
                    adjacency_options,
                    key="income_limit",
                    help="Select the counties that the income limit is taken from, your Own County is likely most appropriate.",
                )

                st.query_params = st.session_state.to_dict()  # replaced here
        except KeyError:
            st.stop()

        if (
            st.session_state["income_limit"] == ""
            and st.session_state["income_limit_type"] != "State Median Income"
        ):
            st.stop()

        if st.session_state["income_limit_type"] == "Area Median Income":
            household_size_selection = st.slider(
                "Household Size",
                1,
                8,
                3,
                key="hh_size",
                help="The average (rounded) size of households in Colorado is 3, and is likely the most appropriate selection.",
            )
            st.query_params = st.session_state.to_dict()  # replaced here
        else:
            st.session_state["hh_size"] = 0
        if (
            st.session_state["hh_size"] == 0
            and st.session_state["income_limit_type"] == "Area Median Income"
        ):
            st.stop()

        median_income_selection = (
            income_data[
                (income_data["geoid"] == st.session_state["geoid"])
                & (income_data["il_name"] == st.session_state["income_limit_type"])
                & (income_data["il_type"] == st.session_state["income_limit"])
                & (income_data["il_hh_size"] == st.session_state["hh_size"])
                & (income_data["il_year"] == st.session_state["year"])
            ]
            .loc[:, "income_limit"]
            .to_list()
            .pop()
        )

        st.session_state["median_income_selection"] = median_income_selection
        selection_callback("median_income_selection")

    with st.expander("Economic Variables", expanded=True):
        st.write('The data collected by the U.S. Census Bureau may have limitations that could prevent it from better illustrating the baseline amount of affordable housing within your jurisdiction. Adjust these economic variables as appropriate to harmonize the data with current economic conditions and the statutory requirements on baseline definitions.')
        st.slider(
            "Sale Unit Availability Rate",
            0.0,
            100.0,
            21.0,
            0.1,
            key="sale_availability_rate",
            help="The percent of home-ownership stock expected to be sold over the commitment period.",
            format="%f%%",
        )
        st.caption('''Only for-sale homes that can be purchased over the commitment period by a household at 100% of the median income are considered affordable.
                   The American Community Survey does not provide data on home sales, but it does provide data on moves into owner-occupied stock housing stock.
                   Roughly 21% of homeowners in Colorado moved into their home from 2019 to 2021, which is provided as the devault value above.''')
        if "sale_availability_rate" not in st.session_state:
            st.session_state[
                "sale_availability_rate"
            ] = 0.21
        st.query_params = st.session_state.to_dict()  # replaced here

        st.slider(
            "Inflation Rate", 0.0, 100.0, 0.0, 0.1, key="inflation_rate", format="%f%%"
        )
        if "inflation_rate" not in st.session_state:
            st.session_state["inflation_rate"] = 0.1
        st.query_params = st.session_state.to_dict()  # replaced here
        st.caption('Adjust the prices of apartments and for-sale stock to correct for price increases caused by inflation. Moving this slider will calculate the movement of units between cost brackets using statistics based on your selection.')
    with st.expander("Homebuyer Variables", expanded=True):
        st.write('Adjust these homebuyer variables to change the price of an affordable for-sale home based on appropriate factors in your jurisdiction. Your choices will be used to calculate the maximum mortgage payment that is affordable at 100% of the median income.')
        st.slider(
            "Mortgage Interest Rate",
            0.0,
            10.0,
            3.0,
            0.1,
            key="interest_rate",
            format="%f%%",
        )
        st.selectbox(
            "Mortgage Term (Years)",
            [15, 20, 30, 40],
            index=2,
            key="mortgage_term",
        )
        st.number_input(
            "Property Tax Amount (Annual)",
            0,
            5000,
            3000,
            1,
            key="property_tax",
        )
        st.number_input(
            "Property/Mortgage Insurance Amount (Annual)",
            0,
            5000,
            1000,
            1,
            key="insurance",
        )
        st.slider(
            "Down Payment", 0.0, 100.0, 5.0, 1.0, key="down_payment", format="%f%%"
        )

#This is where the math from the variables is added to the udnerlying data

renter_income_limit = round(st.session_state["median_income_selection"] * 0.6)
owner_income_limit = st.session_state["median_income_selection"]
max_affordable_rent = round((renter_income_limit / 12) * 0.3)
owner_results = acs_data[
    (acs_data["geoid"] == st.session_state["geoid"]) & (acs_data["title"] == "VALUE")
].loc[:, ["range_min", "range_max", "estimate"]]
owner_results["range_min"][owner_results["range_max"] < 200000] = 0
owner_results["range_max"][owner_results["range_max"] < 200000] = 199999


owner_results = pd.pivot_table(
    owner_results, values=["estimate"], index=["range_min", "range_max"], aggfunc=sum
).reset_index()

owner_max_prices = owner_results["range_max"].to_list()

random.seed(123)
inflation_rate = st.session_state["inflation_rate"] / 100
rand_list = [0] * len(owner_results.index)
for idx, row in owner_results.iterrows():
    row_index = owner_max_prices.index(row["range_max"])
    for i in range(0, int(row["estimate"])):
        x = random.randint(row["range_min"], row["range_max"])
        x = x * (1 + inflation_rate)
        if x > row["range_max"]:
            try:
                rand_list[row_index + 1] = rand_list[row_index + 1] + 1
            except IndexError:
                rand_list[row_index] = rand_list[row_index] + 1
        else:
            rand_list[row_index] = rand_list[row_index] + 1

owner_results["Occupied Units (Inflation Adjusted)"] = rand_list

renter_results = acs_data[
    (acs_data["geoid"] == st.session_state["geoid"])
    & (acs_data["title"] == "CONTRACT RENT")
].loc[:, ["range_min", "range_max", "estimate"]]

renter_results["range_max"][renter_results["range_max"] < 800] = 799
renter_results["range_min"][renter_results["range_max"] < 800] = 0
renter_results = pd.pivot_table(
    renter_results, values="estimate", index=["range_max", "range_min"], aggfunc=sum
).reset_index()

renter_max_prices = renter_results["range_max"].to_list()

rand_list = [0] * len(renter_results.index)
for idx, row in renter_results.iterrows():
    row_index = renter_max_prices.index(row["range_max"])
    for i in range(0, int(row["estimate"])):
        x = random.randint(row["range_min"], row["range_max"])
        x = x * (1 + inflation_rate)
        if x > row["range_max"]:
            try:
                rand_list[row_index + 1] = rand_list[row_index + 1] + 1
            except IndexError:
                rand_list[row_index] = rand_list[row_index] + 1
        else:
            rand_list[row_index] = rand_list[row_index] + 1

renter_results["Occupied Units (Inflation Adjusted)"] = rand_list


owner_results["Available Units"] = round(
    owner_results["Occupied Units (Inflation Adjusted)"]
    * (st.session_state["sale_availability_rate"] / 100)
)
renter_results["Available Units"] = round(
    renter_results["Occupied Units (Inflation Adjusted)"]
)


property_tax = st.session_state["property_tax"]

insurance = st.session_state["insurance"]

A = ((st.session_state["median_income_selection"]) * 0.3) - property_tax - insurance

d = 1 - (st.session_state["down_payment"]) / 100

r = st.session_state["interest_rate"] / 100

n = st.session_state["mortgage_term"]

max_affordable_price = round((A - A * (r + 1) ** (-n)) / (d * r))

#change the units in the range values of the underlying data

owner_results["Percent of Units Affordable"] = 0
for idx, rows in owner_results.iterrows():
    if rows["range_max"] <= max_affordable_price:
        owner_results.at[idx, "Percent of Units Affordable"] = 1
    elif (
        rows["range_min"] <= max_affordable_price
        and rows["range_max"] >= max_affordable_price
    ):
        owner_results.at[idx, "Percent of Units Affordable"] = (
            (max_affordable_price - rows["range_min"]) / (rows["range_max"] - rows["range_min"])
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
            (max_affordable_rent - rows["range_min"]) / (rows["range_max"] - rows["range_min"])
        )
    else:
        renter_results.at[idx, "Percent of Units Affordable"] = 0


#Find the availability of affordable units
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

----


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

st.header("Results")

#this is the final container that holds the result of the baseline calculations
with st.container():

    with st.container():
        with st.spinner("Wait for it..."):
            time.sleep(1)

        st.metric(
            label="Selected Median income",
            value=f"${round(st.session_state['median_income_selection']):,}",
        )
        st.caption(
            "This median income selection was calculated based on your choices above."
        )

    col1a, col1b, col1c, col1d, col1e = st.columns(5, gap="large")
    with col1a:
        st.metric(label="Baseline Estimate", value=f"{total_affordable_units:,}")

    with col1b:
        st.metric(label="Annual Goal", value=f"{round(total_affordable_units*0.03):,}")

    with col1c:
        st.metric(label="One Year Cycle Goal", value=f"{round(total_affordable_units*0.03):,}")

    with col1d:
        st.metric(
            label="Two Year Cycle Goal",
            value=f"{round(total_affordable_units*0.06):,}",
        )

    with col1e:
        st.metric(
            label="Three Year Cycle Goal",
            value=f"{round(total_affordable_units*0.09):,}",
        )


with st.expander(
    "Income Limits and Max Prices/Rates Based on Your Selections", expanded=True
):
    st.write(
        "These income limits have been calculated based on your selections in the sidebar:"
    )
    col3, col4 = st.columns(2, gap="large")
    with col3:
        st.metric(
            label="Homeowner/Homebuyer Income Limit",
            value=f"${round(owner_income_limit):,}",
            help="Your selected Median Income of "
            f"${st.session_state['median_income_selection']:,}" + " x 1.0",
        )

    with col4:
        st.metric(
            label="Renter Income Limit",
            value=f"${round(renter_income_limit):,}",
            help="Your selected Median Income of "
            f"${st.session_state['median_income_selection']:,}" + " x 0.6",
        )
    st.write("---")
    st.write(
        "These Max Affordable For-Sale Prices and Rental Rates are calculated based on the income limits above:"
    )
    col5, col6 = st.columns(2, gap="large")
    with col5:
        st.metric(
            label="Max Affordable For-Sale Price",
            value=f"${max_affordable_price:,}",
        )
        st.caption(
            "Included: mortgage principal, interest, homeowners insurance, and property taxes."
        )
        st.caption(
            "Excluded: utilities payments of any kind, HOA fees, and lot rents for mobile homes."
        )

    with col6:
        st.metric(
            label="Max Affordable Rent",
            value=f"${max_affordable_rent:,}",
            help="Maximum Rent of (" + f"${renter_income_limit:,}" + "/12) x 0.3",
        )
        st.caption("Included: rental payments.")
        st.caption("Excluded: utilities payments of any kind.")

owner_export = owner_results[
    [
        "Range",
        "Occupied Units",
        "Occupied Units (Inflation Adjusted)",
        "Available Units",
        "Affordable Units",
    ]
]

owner_export.loc["Total"] = owner_export[
    [
        "Occupied Units",
        "Occupied Units (Inflation Adjusted)",
        "Available Units",
        "Affordable Units",
    ]
].sum()

renter_export = renter_results[
    [
        "Range",
        "Occupied Units",
        "Occupied Units (Inflation Adjusted)",
        "Available Units",
        "Affordable Units",
    ]
]

renter_export.loc["Total"] = renter_export[
    [
        "Occupied Units",
        "Occupied Units (Inflation Adjusted)",
        "Available Units",
        "Affordable Units",
    ]
].sum()

with st.expander("Housing Affordability by Range", expanded=True):
    tab2a, tab2b = st.tabs(["For-Sale Table", "Rental Table"])
    with tab2a:
        st.dataframe(owner_export, height=425)
        st.caption(
            "Source: U.S. Census Bureau (2022). Table B25075: Value, 2017-2021 American Community Survey 5-year estimates."
        )
    with tab2b:
        st.dataframe(renter_export, height=425)
        st.caption(
            "Source: U.S. Census Bureau (2022). Table B25056: Contract Rent, 2017-2021 American Community Survey 5-year estimates."
        )

state_export = pd.DataFrame(list(st.session_state.to_dict().values()),
                            index = list(st.session_state.to_dict().keys()),
                                              columns =['Selection'])
buffer = io.BytesIO()

"""
You can save your selections and results to revisit them later
by bookmarking this page, and you can share them by copying the URL in the address
bar and pasting it into an email or chat. Click the button below to download your
results as a spreadsheet.
"""

with pd.ExcelWriter(buffer) as writer:
    # Write each dataframe to a different worksheet.
    owner_export.style.to_excel(writer, sheet_name="For-Sale Table", index=False)
    renter_export.to_excel(writer, sheet_name="Rental Table", index=False)
    state_export.to_excel(writer, sheet_name="Selections", index=True)


    # Close the Pandas Excel writer and output the Excel file to the buffer
    writer.close()

    st.download_button(
        label="Download Your Baseline Results",
        data=buffer,
        file_name="baseline_results.xlsx",
        mime="application/vnd.ms-excel",
    )
