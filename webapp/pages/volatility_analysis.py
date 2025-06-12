import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
import altair as alt
import io
import datetime

# Load environment variables
load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

st.set_page_config(layout="wide")
st.title("Volatility Analysis Dashboard")

# List available cryptocurrencies
symbols_query = "SELECT DISTINCT symbol FROM crypto_prices"
symbols = pd.read_sql(symbols_query, con=engine)['symbol'].tolist()

selected_symbol = st.selectbox("Select cryptocurrency", symbols)

# Download data
query = f"""
    SELECT timestamp, open, high, low, close, volume FROM crypto_prices
    WHERE symbol = '{selected_symbol}'
    ORDER BY timestamp ASC
"""
df = pd.read_sql(query, con=engine)
df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')

# Date filter
min_date = df['datetime'].min().date()
max_date = df['datetime'].max().date()

start_date = st.date_input("From", min_value=min_date, max_value=max_date, value=min_date)
end_date = st.date_input("To", min_value=min_date, max_value=max_date, value=max_date)

df = df[(df['datetime'].dt.date >= start_date) & (df['datetime'].dt.date <= end_date)]

# Volatility window parameter
period = st.slider("Volatility window (number of periods)", min_value=5, max_value=50, value=20)

# Calculate volatility (rolling standard deviation)
df['volatility'] = df['close'].rolling(window=period).std()

# Volatility value filter
min_vol = float(df['volatility'].min())
max_vol = float(df['volatility'].max())

vol_range = st.slider("Volatility range (standard deviation)",
                      min_value=round(min_vol, 2),
                      max_value=round(max_vol, 2),
                      value=(round(min_vol, 2), round(max_vol, 2)),
                      step=0.01)

df = df[(df['volatility'] >= vol_range[0]) & (df['volatility'] <= vol_range[1])]

# Volume filter (optional)
use_volume_filter = st.checkbox("Enable volume filter", value=False)

if use_volume_filter:
    q25 = df['volume'].quantile(0.25)
    q75 = df['volume'].quantile(0.75)

    def volume_category(volume):
        if volume <= q25:
            return 'Low'
        elif volume <= q75:
            return 'Medium'
        else:
            return 'High'

    df['volume_category'] = df['volume'].apply(volume_category)

    volume_options = ['Low', 'Medium', 'High']
    selected_volume_category = st.selectbox("Select volume category", options=volume_options)

    df = df[df['volume_category'] == selected_volume_category]

# Dynamic scaling for better visualization
y_min = df['close'].min() * 0.98
y_max = df['close'].max() * 1.02

# Price chart
price_chart = alt.Chart(df).mark_line(color='blue').encode(
    x='datetime:T',
    y=alt.Y('close:Q', title='Close Price', scale=alt.Scale(domain=[y_min, y_max]))
).properties(height=300, width=900, title="Price Chart")

# Volatility chart
vol_min = df['volatility'].min() * 0.98
vol_max = df['volatility'].max() * 1.02

vol_chart = alt.Chart(df).mark_area(color='orange', opacity=0.5).encode(
    x='datetime:T',
    y=alt.Y('volatility:Q', title='Volatility (std dev)', scale=alt.Scale(domain=[vol_min, vol_max]))
).properties(height=200, width=900, title="Volatility Over Time")

st.altair_chart(price_chart & vol_chart, use_container_width=True)

# Export data
csv_buffer = io.StringIO()
df.to_csv(csv_buffer, index=False)
csv_data = csv_buffer.getvalue()

st.download_button(
    label="Download data as CSV",
    data=csv_data,
    file_name='volatility_data.csv',
    mime='text/csv'
)

st.subheader("Filtered Data Table")
st.dataframe(df)