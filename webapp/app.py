import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

# Wczytaj dane logowania z .env
load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# Połączenie z bazą
DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

# Streamlit app
st.set_page_config(layout="wide")
st.title("📈 Cryptocurrency Price Tracker")

# Lista dostępnych kryptowalut
symbols_query = "SELECT DISTINCT symbol FROM crypto_prices"
symbols = pd.read_sql(symbols_query, con=engine)['symbol'].tolist()

selected_symbols = st.multiselect("Wybierz kryptowaluty do porównania", symbols, default=[symbols[0]])

import altair as alt

# Pobierz dane dla wszystkich wybranych symboli
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

# Połącz wszystkie dane w jeden DataFrame
df_all = pd.concat(dfs)
df_all = df_all.sort_values(by='datetime')

# Filtrowanie po czasie
min_date = df_all['datetime'].min().date()
max_date = df_all['datetime'].max().date()
start_date = st.date_input("📅 Od", min_value=min_date, max_value=max_date, value=min_date)
end_date = st.date_input("📅 Do", min_value=min_date, max_value=max_date, value=max_date)

df_all = df_all[(df_all['datetime'].dt.date >= start_date) &
                (df_all['datetime'].dt.date <= end_date)]

# Zakres ceny close
min_price = float(df_all['close'].min())
max_price = float(df_all['close'].max())

price_range = st.slider("🎚️ Zakres ceny (close)",
                        min_value=min_price,
                        max_value=max_price,
                        value=(min_price, max_price),
                        step=0.01)

df_all = df_all[(df_all['close'] >= price_range[0]) & (df_all['close'] <= price_range[1])]


# Zmiana procentowa
df_all = df_all.sort_values(by='datetime')  # dla pewności
df_all['pct_change'] = df_all.groupby('symbol')['close'].pct_change() * 100
df_all.dropna(subset=['pct_change'], inplace=True)

min_change = float(df_all['pct_change'].min())
max_change = float(df_all['pct_change'].max())

change_range = st.slider("📊 Zakres zmiany procentowej",
                         min_value=round(min_change, 2),
                         max_value=round(max_change, 2),
                         value=(round(min_change, 2), round(max_change, 2)),
                         step=0.1)

df_all = df_all[(df_all['pct_change'] >= change_range[0]) &
                (df_all['pct_change'] <= change_range[1])]



# Zakres wolumenu
min_volume = float(df_all['volume'].min())
max_volume = float(df_all['volume'].max())
volume_range = st.slider(
    "📈 Zakres wolumenu",
    min_value=min_volume,
    max_value=max_volume,
    value=(min_volume, max_volume)
)

df_all = df_all[(df_all['volume'] >= volume_range[0]) & (df_all['volume'] <= volume_range[1])]


# 📈 Altair multi-line chart
y_min = float(df_all['close'].min())
y_max = float(df_all['close'].max())

chart = alt.Chart(df_all).mark_line().encode(
    x=alt.X('datetime:T', title='Data'),
    y=alt.Y('close:Q', title='Cena (close)', scale=alt.Scale(domain=[y_min, y_max])),
    color=alt.Color('symbol:N', title='Kryptowaluta')
).properties(
    width=900,
    height=500,
    title='Porównanie cen kryptowalut'
)


st.altair_chart(chart, use_container_width=True)


import io

# Przygotuj dane do eksportu
csv_buffer = io.StringIO()
df_all.to_csv(csv_buffer, index=False)
csv_data = csv_buffer.getvalue()

# Przycisk pobierania
st.download_button(
    label="📥 Pobierz dane jako CSV",
    data=csv_data,
    file_name='crypto_data.csv',
    mime='text/csv'
)
