from database.db_manager import create_all_tables, save_prices
from data_fetching.fetch_prices import fetch_candles

def initialize():
    print("🛠️ Tworzenie tabel w bazie danych...")
    create_all_tables()

    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    for symbol in symbols:
        print(f"⬇️  Pobieranie danych dla: {symbol}")
        data = fetch_candles(symbol, interval='1h', limit=1000)
        if data:
            print(f"💾 Zapis danych do bazy dla: {symbol}")
            save_prices(data, symbol)
        else:
            print(f"❌ Brak danych dla: {symbol}")

    print("✅ Inicjalizacja zakończona.")

if __name__ == '__main__':
    initialize()
