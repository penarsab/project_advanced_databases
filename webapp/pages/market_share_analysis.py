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
st.title("Cryptocurrency Market Share")

# Load available cryptocurrencies
symbols_query = "SELECT DISTINCT symbol FROM crypto_prices"
symbols = pd.read_sql(symbols_query, con=engine)['symbol'].tolist()

selected_symbols = st.multiselect("Select cryptocurrencies for market share analysis", symbols, default=symbols[:3])

# Download data for selected cryptocurrencies
dfs = []
for symbol in selected_symbols:
    df = pd.read_sql(f"""
        SELECT timestamp, volume FROM crypto_prices
        WHERE symbol = '{symbol}'
        ORDER BY timestamp ASC
    """, con=engine)
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['symbol'] = symbol
    dfs.append(df)

# Merge data
df_all = pd.concat(dfs)
df_all = df_all.sort_values(by='datetime')

# Date filter
min_date = df_all['datetime'].min().date()
max_date = df_all['datetime'].max().date()

start_date = st.date_input("From", min_value=min_date, max_value=max_date, value=min_date)
end_date = st.date_input("To", min_value=min_date, max_value=max_date, value=max_date)

df_all = df_all[(df_all['datetime'].dt.date >= start_date) & (df_all['datetime'].dt.date <= end_date)]

# Volume filter (optional)
use_volume_filter = st.checkbox("Enable volume range filter", value=False)

if use_volume_filter:
    q25 = df_all['volume'].quantile(0.25)
    q75 = df_all['volume'].quantile(0.75)

    def volume_category(volume):
        if volume <= q25:
            return 'Low'
        elif volume <= q75:
            return 'Medium'
        else:
            return 'High'

    df_all['volume_category'] = df_all['volume'].apply(volume_category)

    volume_options = ['Low', 'Medium', 'High']
    selected_volume_category = st.selectbox("Select volume category", options=volume_options)
    df_all = df_all[df_all['volume_category'] == selected_volume_category]

# Aggregate total volumes per symbol
volume_summary = df_all.groupby('symbol')['volume'].sum().reset_index()

# Create pie chart
pie_chart = alt.Chart(volume_summary).mark_arc(innerRadius=50).encode(
    theta=alt.Theta(field="volume", type="quantitative"),
    color=alt.Color(field="symbol", type="nominal"),
    tooltip=['symbol', 'volume']
).properties(
    width=600,
    height=600,
    title='Market Share by Volume'
)

st.altair_chart(pie_chart, use_container_width=True)

# Display volume summary table
st.subheader("Volume Summary Table")
st.dataframe(volume_summary)

# Export data
csv_buffer = io.StringIO()
volume_summary.to_csv(csv_buffer, index=False)
csv_data = csv_buffer.getvalue()

st.download_button(
    label="Download data as CSV",
    data=csv_data,
    file_name='market_share_data.csv',
    mime='text/csv'
)

st.subheader("Filtered Data Table")
st.dataframe(df_all)