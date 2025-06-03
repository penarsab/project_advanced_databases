from sqlalchemy import Column, Integer, String, Float, BigInteger
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class CryptoPrice(Base):
    __tablename__ = 'crypto_prices'

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), index=True, nullable=False)
    timestamp = Column(BigInteger, index=True, nullable=False)  # ms since epoch
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)

    def __repr__(self):
        return f"<CryptoPrice(symbol='{self.symbol}', timestamp={self.timestamp}, close={self.close})>"
