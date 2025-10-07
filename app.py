import streamlit as st
import pandas as pd
import joblib
from datetime import datetime
import requests

st.set_page_config(page_title="Car Price Prediction", page_icon="🚗", layout="wide")

def format_indian_currency(number):
    s = str(int(round(number)))
    if len(s) <= 3:
        return f"₹ {s}"
    last_three = s[-3:]
    other_digits = s[:-3]
    formatted_other_digits = ','.join([other_digits[max(0, i - 2):i] for i in range(len(other_digits), 0, -2)][::-1])
    return f"₹ {formatted_other_digits},{last_three}"


# Function to find the best car image
def get_car_image_url(brand, model, year):

    try:
        query = f"{year} {brand} {model}"

        endpoint = f"https://imsea.herokuapp.com/api/1?q={query.replace(' ', '%20')}"
        response = requests.get(endpoint, timeout=5)
        response.raise_for_status()  # Raise an exception for bad status codes
        results = response.json()

        if results and results.get("results"):
            return results["results"][0]

    except (requests.exceptions.RequestException, IndexError, KeyError) as e:

        print(f"Could not fetch real image for {query}: {e}")


    image_text = model.replace(" ", "%20")
    return f"https://placehold.co/600x400/2c3e50/ecf0f1?text={image_text}&font=roboto"


# Load Data & Models
@st.cache_data
def load_data_and_models():
    dealer_df = pd.read_csv('dealer_market_data.csv')
    private_df = pd.read_csv('private_market_data.csv')
    dealer_brand_map = dealer_df.groupby('company')['name'].unique().apply(list).to_dict()
    private_brand_map = private_df.groupby('company')['name'].unique().apply(list).to_dict()
    dealer_model = joblib.load('cardekho_dealer_model.joblib')
    private_model = joblib.load('private_seller_model.joblib')
    return dealer_df, private_df, dealer_brand_map, private_brand_map, dealer_model, private_model


try:
    dealer_df, private_df, dealer_map, private_map, dealer_model, private_model = load_data_and_models()
    DATA_LOADED = True
except FileNotFoundError:
    st.error("Error: Data or model files missing. Ensure they are in the same directory.")
    DATA_LOADED = False

# --- App Title ---
st.markdown("<h1 style='text-align: center; color: #1E88E5;'>Car Price Prediction Platform</h1>", unsafe_allow_html=True)
st.markdown("---")
st.write("")
st.markdown("Select market type and fill car details to get an estimated price.")

if DATA_LOADED:
    prediction_type = st.radio(
        "Select the market to predict for:",
        ("Dealer Market Value", "Private Seller Price"),
        horizontal=True
    )
    st.sidebar.header("Enter Car Details")

    if prediction_type == "Dealer Market Value":
        brand_map, source_df, model = dealer_map, dealer_df, dealer_model
    else:
        brand_map, source_df, model = private_map, private_df, private_model

    all_brands = sorted(list(brand_map.keys()))
    selected_brand = st.sidebar.selectbox("Brand", all_brands)
    available_models = sorted(brand_map.get(selected_brand, []))
    selected_model = st.sidebar.selectbox("Model", available_models)
    year = st.sidebar.slider("Model Year", 2000, datetime.now().year, 2018)
    kms_driven = st.sidebar.slider("Kilometers Driven", 0, 300000, 50000, 1000)
    fuel_type = st.sidebar.selectbox("Fuel Type", sorted(source_df['fuel_type'].unique()))
    transmission = st.sidebar.selectbox("Transmission", sorted(source_df['transmission'].unique()))

    if prediction_type == "Dealer Market Value":
        seller_type = st.sidebar.selectbox("Seller Type", ["Dealer", "Trustmark Dealer"])

    if st.sidebar.button("Predict Price"):

        input_data = {
            'year': year, 'kms_driven': kms_driven, 'mileage_kmpl': source_df['mileage_kmpl'].median(),
            'engine_cc': source_df['engine_cc'].median(), 'max_power_bhp': source_df['max_power_bhp'].median(),
            'seats': 5, f'company_{selected_brand}': 1, f'name_{selected_model}': 1,
            f'fuel_type_{fuel_type}': 1, f'transmission_{transmission}': 1,
        }
        if prediction_type == "Dealer Market Value":
            input_data['seller_type_' + seller_type] = 1

        input_df = pd.DataFrame([input_data])
        model_columns = model.get_booster().feature_names
        final_input_df = input_df.reindex(columns=model_columns, fill_value=0)
        prediction = model.predict(final_input_df)[0]
        formatted_price = format_indian_currency(prediction)

        st.markdown("---")

        st.markdown(f"<h3 style='text-align: center;'>Estimated {prediction_type}</h3>", unsafe_allow_html=True)

        st.markdown(f"<h1 style='text-align: center; color: #2ecc71;'>{formatted_price}</h1>", unsafe_allow_html=True)

        st.markdown(
            "<p style='text-align: center; color: #888;'>This is an estimate based on market data for similar vehicles. Actual prices may vary based on vehicle condition and negotiations.</p>",
            unsafe_allow_html=True)
        st.markdown("---")

        col1, col2 = st.columns([1, 1])

        with col1:
            # This will load your local 'sample.jpg' file.
            st.image("data/sample.jpg", use_container_width=True, caption=f"{year} {selected_brand} {selected_model}")


            # image_url = get_car_image_url(selected_brand, selected_model, year)
            #
            # st.markdown(
            #     f"""
            #     <div style="height: 300px; display: flex; align-items: center; justify-content: center;">
            #         <img src="{image_url}" style="width:100%; height:100%; object-fit: cover; border-radius: 10px;">
            #     </div>
            #     """,
            #     unsafe_allow_html=True
            # )

        with col2:
            st.subheader("Vehicle Specifications")
            spec_col1, spec_col2 = st.columns(2)
            with spec_col1:
                st.markdown(f"<p style='font-size: 1.2em;'>🏢 <strong>Brand:</strong> {selected_brand}</p>",
                            unsafe_allow_html=True)
                st.markdown(f"<p style='font-size: 1.2em;'>🗓️ <strong>Year:</strong> {year}</p>",
                            unsafe_allow_html=True)
                st.markdown(f"<p style='font-size: 1.2em;'>⛽ <strong>Fuel Type:</strong> {fuel_type}</p>",
                            unsafe_allow_html=True)
            with spec_col2:
                st.markdown(f"<p style='font-size: 1.2em;'>🏷️ <strong>Model:</strong> {selected_model}</p>",
                            unsafe_allow_html=True)
                st.markdown(f"<p style='font-size: 1.2em;'>🛣️ <strong>KMs Driven:</strong> {kms_driven:,}</p>",
                            unsafe_allow_html=True)
                st.markdown(f"<p style='font-size: 1.2em;'>⚙️ <strong>Transmission:</strong> {transmission}</p>",
                            unsafe_allow_html=True)

            if prediction_type == "Dealer Market Value":
                st.markdown("---")
                st.markdown(f"<p style='font-size: 1.2em;'>👨‍💼 <strong>Seller Type:</strong> {seller_type}</p>",
                            unsafe_allow_html=True)

        st.markdown("---")

