import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
import altair as alt
import io

# Wczytaj dane logowania
load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

st.set_page_config(layout="wide")
st.title("📊 Technical Indicators Dashboard")

# Lista symboli
symbols_query = "SELECT DISTINCT symbol FROM crypto_prices"
symbols = pd.read_sql(symbols_query, con=engine)['symbol'].tolist()

selected_symbol = st.selectbox("Wybierz kryptowalutę", symbols)

# Pobierz dane
query = f"""
    SELECT timestamp, open, high, low, close, volume FROM crypto_prices
    WHERE symbol = '{selected_symbol}'
    ORDER BY timestamp ASC
"""

df = pd.read_sql(query, con=engine)
df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')

# Filtr daty
min_date = df['datetime'].min().date()
max_date = df['datetime'].max().date()
start_date = st.date_input("📅 Od", min_value=min_date, max_value=max_date, value=min_date)
end_date = st.date_input("📅 Do", min_value=min_date, max_value=max_date, value=max_date)

df = df[(df['datetime'].dt.date >= start_date) & (df['datetime'].dt.date <= end_date)]

# Parametry wskaźnika
indicator = st.selectbox("Wybierz wskaźnik", ["SMA", "EMA", "RSI"])
period = st.slider("Okres wskaźnika", min_value=5, max_value=100, value=20)

# Oblicz wskaźnik
if indicator == "SMA":
    df['indicator'] = df['close'].rolling(window=period).mean()
elif indicator == "EMA":
    df['indicator'] = df['close'].ewm(span=period, adjust=False).mean()
else:  # RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    df['indicator'] = 100 - (100 / (1 + rs))

point_limit = st.slider("🔢 Liczba ostatnich punktów", min_value=10, max_value=1000, value=200, step=10)
df = df.tail(point_limit)

def price_chart(data: pd.DataFrame):
    return alt.Chart(data).mark_line(color="#1f77b4").encode(
        x='datetime:T',
        y=alt.Y('close:Q', title='Cena (close)')
    )

def indicator_chart(data: pd.DataFrame, name: str):
    color = "#ff7f0e"
    y = alt.Y('indicator:Q', title=name)
    if name.startswith('RSI'):
        y = alt.Y('indicator:Q', title=name, scale=alt.Scale(domain=[0, 100]))
    return alt.Chart(data).mark_line(color=color).encode(
        x='datetime:T',
        y=y
    )

if indicator == "RSI":
    price = price_chart(df).properties(height=300)
    ind = indicator_chart(df, f"RSI ({period})").properties(height=150)
    st.altair_chart(price & ind, use_container_width=True)
else:
    ind_name = f"{indicator} ({period})"
    chart = alt.layer(
        price_chart(df),
        indicator_chart(df, ind_name)
    ).resolve_scale(y='independent').properties(height=500)
    st.altair_chart(chart, use_container_width=True)

# Eksport danych
csv_buffer = io.StringIO()
df.to_csv(csv_buffer, index=False)
csv_data = csv_buffer.getvalue()

st.download_button(
    label="Pobierz dane jako CSV",
    data=csv_data,
    file_name='indicator_data.csv',
    mime='text/csv'
)
