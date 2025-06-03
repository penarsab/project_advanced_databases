import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from .models import Base
from .models import CryptoPrice


# Wczytaj dane z pliku .env
load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Utwórz silnik i sesję SQLAlchemy
engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine)

def get_session():
    return SessionLocal()

def create_all_tables():
    Base.metadata.create_all(bind=engine)

def save_prices(prices: list[dict], symbol: str):
    """
    Zapisuje dane świecowe do bazy danych, pomijając duplikaty.
    """
    session = get_session()
    try:
        existing_timestamps = {
            row[0] for row in session.query(CryptoPrice.timestamp)
                                     .filter(CryptoPrice.symbol == symbol)
                                     .all()
        }

        new_records = []
        for p in prices:
            if p['timestamp'] not in existing_timestamps:
                new_records.append(
                    CryptoPrice(
                        symbol=symbol,
                        timestamp=p['timestamp'],
                        open=p['open'],
                        high=p['high'],
                        low=p['low'],
                        close=p['close'],
                        volume=p['volume']
                    )
                )

        session.add_all(new_records)
        session.commit()
        print(f"Zapisano {len(new_records)} nowych rekordów dla {symbol}")

    except Exception as e:
        session.rollback()
        print(f"Błąd zapisu do bazy: {e}")

    finally:
        session.close()
