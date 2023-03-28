import streamlit as st
import pandas as pd
import time
from json import dumps, loads
import io

st.set_page_config(
    layout="centered",
    menu_items={
        "Report a Bug": "https://dola-doh.atlassian.net/rest/collectors/1.0/template/form/b44faba8"
    },
)
st.title("Baseline Assistance Tool")
st.subheader("Baseline and Goal Results")

try:
    if st.session_state["median_income_selection"] != "":
        st.empty()
except KeyError:
    st.write(
        "An analysis of affordable housing stock will be shown below once the selections in the sidebar are complete."
    )

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
income_limit_name_options.insert(0, "")

# Input widgets for sidebar


params_in = st.experimental_get_query_params()


if len(params_in) > 0 and len(st.session_state) == 0:
    params_dict = loads(params_in.get("query").pop())
    for key in list(params_dict.keys()):
        st.session_state[key] = params_dict[key]


def selection_callback(key):
    print(st.session_state)
    if len(st.session_state) > 0:
        st.experimental_set_query_params(query=dumps(st.session_state.to_dict()))
        print(st.experimental_get_query_params())
        params_in = loads(st.experimental_get_query_params().get("query").pop())
        try:
            st.session_state[key] = params_in[key]
        except KeyError:
            print("New session")
        except AttributeError:
            print("oops")
    else:
        print("New session")


with st.sidebar:
    with st.container():
        st.image("https://cdola.colorado.gov/sites/dola/files/logo.svg")
        st.write(
            "[Submit Feedback](https://dola-doh.atlassian.net/rest/collectors/1.0/template/form/e6a34351?os_authType=none)"
        )
        with st.expander("Start here", expanded=True):

            st.selectbox(
                "Step 1: Select a jurisdiction type",
                ["", "County", "Municipality"],
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

            try:
                if st.session_state["jurisdiction_name"] == "":
                    st.stop()
            except KeyError:
                st.stop()
            

            st.session_state["geoid"] = (
                acs_data[acs_data['geography_name'] == st.session_state['jurisdiction_name']]
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

            st.experimental_set_query_params(query=dumps(st.session_state.to_dict()))

            try:
                if st.session_state["income_limit_type"] == "":
                    st.stop()
            except KeyError:
                st.stop()

            year_options = (
                income_data[(income_data['geoid'] == st.session_state['geoid']) & 
                            (income_data['il_name'] == st.session_state['income_limit_type'])]
                .loc[:, "il_year"]
                .drop_duplicates()
                .sort_values(ascending=False)
                .to_list()
            )

            year_options.insert(0, "")

            st.selectbox(
                "Step 4: Select an income Limit Year",
                year_options,
                index=0,
                key="year",
                help="Select the year that the income limit data was collected or published in, we recommend "
                + str(year_options[1])
                + " because it is likely most accurate.",
            )

            st.experimental_set_query_params(query=dumps(st.session_state.to_dict()))

            try:
                if st.session_state["year"] == "":
                    st.stop()
            except KeyError:
                st.stop()

            adjacency_options = (
                income_data[(income_data['geoid'] == st.session_state['geoid']) & 
                            (income_data['il_name'] == st.session_state['income_limit_type'])]
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

                    st.experimental_set_query_params(
                        query=dumps(st.session_state.to_dict())
                    )
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
                st.experimental_set_query_params(
                    query=dumps(st.session_state.to_dict())
                )
            else:
                st.session_state["hh_size"] = 0
            if (
                st.session_state["hh_size"] == 0
                and st.session_state["income_limit_type"] == "Area Median Income"
            ):
                st.stop()

            median_income_selection = (income_data[(income_data['geoid'] == st.session_state['geoid']) &
                                                   (income_data['il_name'] == st.session_state['income_limit_type']) &
                                                   (income_data['il_type'] == st.session_state['income_limit']) &
                                                   (income_data['il_hh_size'] == st.session_state['hh_size']) &
                                                   (income_data['il_year'] == st.session_state['year'])]
                .loc[:, "income_limit"]
                .to_list()
                .pop()
            )

            st.session_state["median_income_selection"] = median_income_selection
            selection_callback("median_income_selection")

        with st.expander("Optional variables", expanded=False):
            ownership_unit_availability_rate_default = (
                acs_data[(acs_data['geoid'] == st.session_state['geoid']) &
                         (acs_data['title'] == "VALUE")]
                .loc[:, "proration_available_units"]
                .drop_duplicates()
                .to_list()
                .pop()
            )
            st.slider(
                "Sale unit Availability Rate",
                0.0,
                1.0,
                round(ownership_unit_availability_rate_default, 2),
                0.01,
                key="sale_availability_rate",
            )
            if "sale_availability_rate" not in st.session_state:
                st.session_state[
                    "sale_availability_rate"
                ] = ownership_unit_availability_rate_default
            st.experimental_set_query_params(query=dumps(st.session_state.to_dict()))
            rental_unit_availability_rate_default = (
                acs_data[(acs_data['geoid'] == st.session_state['geoid']) &
                         (acs_data['title'] == 'GROSS RENT')]
                .loc[:, "proration_available_units"]
                .drop_duplicates()
                .to_list()
                .pop()
            )
            st.slider(
                "Rental Unit Availability Rate",
                0.0,
                1.0,
                round(rental_unit_availability_rate_default, 2),
                0.01,
                key="rental_availability_rate",
            )
            if "rental_availability_rate" not in st.session_state:
                st.session_state[
                    "rental_availability_rate"
                ] = rental_unit_availability_rate_default
            st.experimental_set_query_params(query=dumps(st.session_state.to_dict()))
            st.slider(
                "Home Value to Income Ratio",
                2.5,
                4.5,
                3.5,
                0.01,
                key="home_value_to_income_ratio",
            )
            if "home_value_to_income_ratio" not in st.session_state:
                st.session_state["home_value_to_income_ratio"] = 3.5
            st.experimental_set_query_params(query=dumps(st.session_state.to_dict()))


renter_income_limit = round(st.session_state["median_income_selection"] * 0.6)
owner_income_limit = st.session_state["median_income_selection"]
max_affordable_rent = round((renter_income_limit / 12) * 0.3)
max_affordable_price = round(
    owner_income_limit * st.session_state["home_value_to_income_ratio"]
)


owner_results = (
    acs_data[(acs_data['geoid'] == st.session_state['geoid']) &
             (acs_data['title'] == 'VALUE')]
    .loc[:, ["range_min", "range_max", "estimate"]]
)

owner_results["range_max"][owner_results["range_max"] < 200000] = 199999
owner_results["range_min"][owner_results["range_max"] < 200000] = 0
owner_results = pd.pivot_table(
    owner_results, values="estimate", index=["range_max", "range_min"], aggfunc=sum
).reset_index()

renter_results = (
    acs_data[(acs_data['geoid'] == st.session_state['geoid']) &
             (acs_data['title'] == 'GROSS RENT')]
    .loc[:, ["range_min", "range_max", "estimate"]]
)

renter_results["range_max"][renter_results["range_max"] < 800] = 799
renter_results["range_min"][renter_results["range_max"] < 800] = 0
renter_results = pd.pivot_table(
    renter_results, values="estimate", index=["range_max", "range_min"], aggfunc=sum
).reset_index()

owner_results["Available Units"] = round(
    owner_results["estimate"] * st.session_state["sale_availability_rate"]
)
renter_results["Available Units"] = round(
    renter_results["estimate"] * st.session_state["rental_availability_rate"]
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


with st.container():

    with st.container():
        with st.spinner("Wait for it..."):
            time.sleep(1)

        st.metric(
            label="Selected Median income",
            value=f"${st.session_state['median_income_selection']:,}",
        )
        st.caption(
            "This median income selection was calcualted based on the your choices above"
        )

    col1a, col1b, col1c = st.columns(3, gap="large")
    with col1a:
        st.metric(label="Baseline Estimate", value=f"{total_affordable_units:,}")

    with col1b:
        st.metric(label="Annual Goal", value=f"{round(total_affordable_units*0.03):,}")

    with col1c:
        st.metric(
            label="Three Year Cycle Goal",
            value=f"{round(total_affordable_units*0.09):,}",
        )

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
            f"${st.session_state['median_income_selection']:,}" + " x 1.0",
        )

    with col4:
        st.metric(
            label="Renter Income Limit",
            value=f"${renter_income_limit:,}",
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
            help="Homeowner/Homebuyer Income Limit of "
            + f"${owner_income_limit:,}"
            + " x "
            + f"{st.session_state['rental_availability_rate']:}",
        )

    with col6:
        st.metric(
            label="Max Affordable Rent",
            value=f"${max_affordable_rent:,}",
            help="Renter Income Limit of ("
            + f"${renter_income_limit:,}"
            + "/12) x 0.3",
        )

owner_export = owner_results[
    ["Range", "Occupied Units", "Available Units", "Affordable Units"]
]

renter_export = renter_results[
    ["Range", "Occupied Units", "Available Units", "Affordable Units"]
]

with st.expander("Housing Affordability by Range"):
    tab1, tab2 = st.tabs(["For-Sale Table", "Rental Table"])
    with tab1:
        st.dataframe(owner_export)
    with tab2:
        st.dataframe(renter_export)

buffer = io.BytesIO()

with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
    # Write each dataframe to a different worksheet.
    owner_export.style.to_excel(writer, sheet_name="For-Sale Table", index=False)
    renter_export.to_excel(writer, sheet_name="Rental Table", index=False)

    # Close the Pandas Excel writer and output the Excel file to the buffer
    writer.save()

    st.download_button(
        label="Download Your Baseline Results",
        data=buffer,
        file_name="baseline_results.xlsx",
        mime="application/vnd.ms-excel",
    )
