import streamlit as st
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
import seaborn as sns
import matplotlib.pyplot as plt
import io
import datetime
from functools import reduce

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
st.title("Cryptocurrency Correlations")

# Load available symbols
symbols_query = "SELECT DISTINCT symbol FROM crypto_prices"
symbols = pd.read_sql(symbols_query, con=engine)['symbol'].tolist()

# Select cryptocurrencies for correlation analysis
selected_symbols = st.multiselect("Select cryptocurrencies for correlation analysis", symbols, default=symbols[:3])

# Download data for selected symbols
dfs = []
for symbol in selected_symbols:
    df = pd.read_sql(f"""
        SELECT timestamp, close FROM crypto_prices
        WHERE symbol = '{symbol}'
        ORDER BY timestamp ASC
    """, con=engine)
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df[['datetime', 'close']].rename(columns={'close': symbol})
    dfs.append(df)

# Merge data by datetime
if dfs:
    df_merged = reduce(lambda left, right: pd.merge(left, right, on='datetime', how='inner'), dfs)
else:
    st.warning("Please select at least one cryptocurrency.")
    st.stop()

# Date filter
min_date = df_merged['datetime'].min().date()
max_date = df_merged['datetime'].max().date()

start_date = st.date_input("From", min_value=min_date, max_value=max_date, value=min_date)
end_date = st.date_input("To", min_value=min_date, max_value=max_date, value=max_date)

df_merged = df_merged[(df_merged['datetime'].dt.date >= start_date) & (df_merged['datetime'].dt.date <= end_date)]

# Correlation type selection
corr_type = st.selectbox("Select correlation type", ["pearson", "spearman"])

# Calculate correlations
df_corr = df_merged.drop(columns=['datetime']).corr(method=corr_type)

# Display heatmap
st.subheader("Correlation Matrix")

fig, ax = plt.subplots(figsize=(4, 3))
heatmap = sns.heatmap(df_corr, annot=True, fmt=".2f", annot_kws={"size": 8}, cmap='coolwarm', center=0, ax=ax)

# Reduce ticklabel font size
ax.set_xticklabels(ax.get_xticklabels(), fontsize=8)
ax.set_yticklabels(ax.get_yticklabels(), fontsize=8)

# Reduce colorbar font size
colorbar = heatmap.collections[0].colorbar
colorbar.ax.tick_params(labelsize=8)

st.pyplot(fig, use_container_width=False)

# Scatter plot for selected 2 cryptocurrencies
if len(selected_symbols) >= 2:
    st.subheader("Scatter plot for selected cryptocurrencies")
    crypto_x = st.selectbox("Select cryptocurrency for X axis", selected_symbols, index=0)
    crypto_y = st.selectbox("Select cryptocurrency for Y axis", selected_symbols, index=1)

    fig2, ax2 = plt.subplots(figsize=(4, 3))
    ax2.scatter(df_merged[crypto_x], df_merged[crypto_y], alpha=0.6, s=20)

    ax2.set_xlabel(crypto_x, fontsize=10)
    ax2.set_ylabel(crypto_y, fontsize=10)
    ax2.set_title(f'Scatter plot: {crypto_x} vs {crypto_y}', fontsize=10)

    ax2.tick_params(axis='both', labelsize=8)

    st.pyplot(fig2, use_container_width=False)
else:
    st.info("Please select at least two cryptocurrencies to display scatter plot.")

# Export data
csv_buffer = io.StringIO()
df_merged.to_csv(csv_buffer, index=False)
csv_data = csv_buffer.getvalue()

st.download_button(
    label="Download data as CSV",
    data=csv_data,
    file_name='correlation_data.csv',
    mime='text/csv'
)

st.subheader("Merged Filtered Data Table")
st.dataframe(df_merged)