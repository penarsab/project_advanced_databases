import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
import altair as alt
import io

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
st.title("Time Series Cryptocurrency Price Dashboard")

# List available cryptocurrencies
symbols_query = "SELECT DISTINCT symbol FROM crypto_prices"
symbols = pd.read_sql(symbols_query, con=engine)['symbol'].tolist()

selected_symbols = st.multiselect("Select cryptocurrencies to compare", symbols, default=[symbols[0]])

# Download data for selected symbols
dfs = []
for symbol in selected_symbols:
    df = pd.read_sql(f"""
        SELECT timestamp, close, volume FROM crypto_prices
        WHERE symbol = '{symbol}'
        ORDER BY timestamp ASC
    """, con=engine)

    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['symbol'] = symbol
    dfs.append(df[['datetime', 'close', 'volume', 'symbol']])

# Merge data
df_all = pd.concat(dfs)
df_all = df_all.sort_values(by='datetime')

# Date filter
min_date = df_all['datetime'].min().date()
max_date = df_all['datetime'].max().date()
start_date = st.date_input("From", min_value=min_date, max_value=max_date, value=min_date)
end_date = st.date_input("To", min_value=min_date, max_value=max_date, value=max_date)

df_all = df_all[(df_all['datetime'].dt.date >= start_date) & (df_all['datetime'].dt.date <= end_date)]

# Price filter
min_price = float(df_all['close'].min())
max_price = float(df_all['close'].max())

price_range = st.slider("Close price range",
                        min_value=min_price,
                        max_value=max_price,
                        value=(min_price, max_price),
                        step=0.01)

df_all = df_all[(df_all['close'] >= price_range[0]) & (df_all['close'] <= price_range[1])]

# Percentage change filter
df_all = df_all.sort_values(by='datetime')
df_all['pct_change'] = df_all.groupby('symbol')['close'].pct_change() * 100
df_all.dropna(subset=['pct_change'], inplace=True)

min_change = float(df_all['pct_change'].min())
max_change = float(df_all['pct_change'].max())

change_range = st.slider("Percentage change range",
                         min_value=round(min_change, 2),
                         max_value=round(max_change, 2),
                         value=(round(min_change, 2), round(max_change, 2)),
                         step=0.1)

df_all = df_all[(df_all['pct_change'] >= change_range[0]) & (df_all['pct_change'] <= change_range[1])]

# Volume filter (optional)
use_volume_filter = st.checkbox("Enable volume filter", value=False)

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

# Dynamic scaling for better chart visibility
y_min = df_all['close'].min() * 0.98
y_max = df_all['close'].max() * 1.02

chart = alt.Chart(df_all).mark_line().encode(
    x=alt.X('datetime:T', title='Date'),
    y=alt.Y('close:Q', title='Close Price', scale=alt.Scale(domain=[y_min, y_max])),
    color=alt.Color('symbol:N', title='Cryptocurrency')
).properties(
    width=900,
    height=500,
    title='Cryptocurrency Prices Over Time'
)

st.altair_chart(chart, use_container_width=True)

# Export data
csv_buffer = io.StringIO()
df_all.to_csv(csv_buffer, index=False)
csv_data = csv_buffer.getvalue()

st.download_button(
    label="Download data as CSV",
    data=csv_data,
    file_name='crypto_data.csv',
    mime='text/csv'
)

st.subheader("Filtered Data Table")
st.dataframe(df_all)