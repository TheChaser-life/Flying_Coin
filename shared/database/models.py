import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class AssetClass(str, enum.Enum):
    STOCK = "STOCK"
    CRYPTO = "CRYPTO"
    FOREX = "FOREX"
    COMMODITY = "COMMODITY"

class DataProvider(str, enum.Enum):
    YAHOO = "YAHOO"
    BINANCE = "BINANCE"
    KRAKEN = "KRAKEN"
    COINBASE = "COINBASE"

class ModelName(str, enum.Enum):
    LSTM = "LSTM"
    XGBOOST = "XGBOOST"
    ARIMA = "ARIMA"
    FINBERT = "FINBERT"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    portfolios = relationship("Portfolio", back_populates="user", cascade="all, delete-orphan")

class Symbol(Base):
    __tablename__ = "symbols"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    asset_class = Column(SQLEnum(AssetClass), nullable=False)
    exchange = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    market_data = relationship("MarketData", back_populates="symbol", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="symbol", cascade="all, delete-orphan")
    sentiments = relationship("Sentiment", back_populates="symbol", cascade="all, delete-orphan")

class MarketData(Base):
    __tablename__ = "market_data"
    __table_args__ = (
        UniqueConstraint('symbol_id', 'timestamp', 'source', name='uix_market_data_symbol_time_source'),
    )

    id = Column(Integer, primary_key=True, index=True)
    symbol_id = Column(Integer, ForeignKey("symbols.id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    source = Column(SQLEnum(DataProvider), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    symbol = relationship("Symbol", back_populates="market_data")

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    symbol_id = Column(Integer, ForeignKey("symbols.id"), nullable=False, index=True)
    model_name = Column(SQLEnum(ModelName), nullable=False, index=True)
    target_date = Column(DateTime, nullable=False, index=True)
    predicted_value = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=True) # Between 0 and 1
    actual_value = Column(Float, nullable=True) # To be updated later for backtesting/evaluation
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    symbol = relationship("Symbol", back_populates="predictions")

class Sentiment(Base):
    __tablename__ = "sentiments"

    id = Column(Integer, primary_key=True, index=True)
    symbol_id = Column(Integer, ForeignKey("symbols.id"), nullable=False, index=True)
    source = Column(String(255), nullable=False) # e.g., Twitter, Reuters, Bloomberg
    timestamp = Column(DateTime, nullable=False, index=True)
    sentiment_score = Column(Float, nullable=False) # e.g., -1.0 to 1.0
    sentiment_label = Column(String(50), nullable=True) # POSITIVE, NEGATIVE, NEUTRAL
    text_snippet = Column(String(1000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    symbol = relationship("Symbol", back_populates="sentiments")

class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="portfolios")
