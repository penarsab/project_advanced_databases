import requests
import time

def fetch_candles(symbol: str, interval: str = '1h', limit: int = 1000):
    """
    Pobiera dane świecowe (candlestick) z Binance API.
    """
    url = 'https://api.binance.com/api/v3/klines'
    params = {
        'symbol': symbol.upper(),
        'interval': interval,
        'limit': limit
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        raw_data = response.json()

        candles = []
        for candle in raw_data:
            candles.append({
                'timestamp': int(candle[0]),          # open time (ms since epoch)
                'open': float(candle[1]),
                'high': float(candle[2]),
                'low': float(candle[3]),
                'close': float(candle[4]),
                'volume': float(candle[5])
            })

        return candles

    except Exception as e:
        print(f"Błąd pobierania danych z Binance dla {symbol}: {e}")
        return []
