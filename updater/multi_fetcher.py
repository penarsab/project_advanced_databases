from data_fetching.fetch_prices import fetch_candles
from database.db_manager import save_prices

def update_all_symbols(symbols: list[str], interval: str = '1h', limit: int = 1000):
    for symbol in symbols:
        print(f"Pobieranie danych dla: {symbol}")
        candles = fetch_candles(symbol, interval=interval, limit=limit)
        if candles:
            save_prices(candles, symbol)
        else:
            print(f"❌ Brak danych dla: {symbol}")
