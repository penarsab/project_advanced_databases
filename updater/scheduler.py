import schedule
import time
from updater.multi_fetcher import update_all_symbols

# Lista kryptowalut do śledzenia
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']

def job():
    print("🔄 Aktualizacja danych...")
    update_all_symbols(SYMBOLS)

def run_scheduler():
    job()  # uruchomienie przy starcie
    schedule.every().hour.do(job)

    print("🕒 Uruchomiono harmonogram co godzinę")
    while True:
        schedule.run_pending()
        time.sleep(10)

if __name__ == '__main__':
    run_scheduler()
