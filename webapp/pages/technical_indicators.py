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


# Zakres wolumenu
min_volume = float(df['volume'].min())
max_volume = float(df['volume'].max())
volume_range = st.slider(
    "📈 Zakres wolumenu",
    min_value=min_volume,
    max_value=max_volume,
    value=(min_volume, max_volume)
)

df = df[(df['volume'] >= volume_range[0]) & (df['volume'] <= volume_range[1])]

def candlestick_chart(data: pd.DataFrame):
    base = alt.Chart(data)
    open_close_color = alt.condition(
        'datum.open <= datum.close',
        alt.value('#06982d'),
        alt.value('#ae1325')
    )

    y_domain = [data['low'].min(), data['high'].max()]

    rule = base.mark_rule().encode(
        x='datetime:T',
        y=alt.Y('low:Q', scale=alt.Scale(domain=y_domain)),
        y2='high:Q'
    )
    bar = base.mark_bar().encode(
        x='datetime:T',
        y=alt.Y('open:Q', scale=alt.Scale(domain=y_domain)),
        y2='close:Q',
        color=open_close_color
    )
    return rule + bar

def volume_chart(data: pd.DataFrame):
    return alt.Chart(data).mark_bar(color='#aaaaaa').encode(
        x='datetime:T',
        y=alt.Y('volume:Q', title='Wolumen')
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
    candle = candlestick_chart(df).properties(height=300)
    ind = indicator_chart(df, f"RSI ({period})").properties(height=150)
    vol = volume_chart(df).properties(height=100)
    st.altair_chart(candle & ind & vol, use_container_width=True)
else:
    ind_name = f"{indicator} ({period})"
    candle = candlestick_chart(df)
    ind_line = indicator_chart(df, ind_name)
    chart = alt.layer(
        candle,
        ind_line
    ).resolve_scale(y='independent').properties(height=400)
    vol = volume_chart(df).properties(height=100)
    st.altair_chart(chart & vol, use_container_width=True)

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
