# database/db_manager.py
import psycopg2
import pandas as pd
import numpy as np
import cupy as cp  # CUDA desteği
from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

Base = declarative_base()

class MarketData(Base):
    __tablename__ = 'market_data'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), index=True)
    datetime = Column(DateTime, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    timeframe = Column(String(10))  # '1m', '5m', '1h', '1d'
    session = Column(String(10))    # 'normal', 'afterhours'

class DatabaseManager:
    def __init__(self, db_url="postgresql://user:pass@localhost/trading"):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        
    def create_tables(self):
        """Database tablolarını oluştur"""
        Base.metadata.create_all(self.engine)
        print("✅ Database tabloları oluşturuldu")
    
    def bulk_insert_from_csv(self, csv_path, symbol, timeframe):
        """CSV'den database'e veri yükle"""
        df = pd.read_csv(csv_path)
        
        # Seans kontrolü - BIST için
        df = self._add_session_info(df, timeframe)
        
        records = []
        for idx, row in df.iterrows():
            record = MarketData(
                symbol=symbol,
                datetime=row['DateTime'],
                open=row['Open'],
                high=row['High'],
                low=row['Low'],
                close=row['Close'],
                volume=row['Volume'],
                timeframe=timeframe,
                session=row.get('Session', 'normal')
            )
            records.append(record)
        
        session = self.Session()
        session.bulk_save_objects(records)
        session.commit()
        session.close()
        
        print(f"✅ {symbol} ({timeframe}) verisi database'e yüklendi: {len(records)} kayıt")
    
    def _add_session_info(self, df, timeframe):
        """BIST seans bilgilerini ekle"""
        if timeframe in ['1d', '1h']:
            # Günlük veriler için seans kontrolü
            df['Session'] = 'normal'
        else:
            # Intraday için seans saatleri
            df['Hour'] = pd.to_datetime(df['DateTime']).dt.hour
            df['Session'] = df['Hour'].apply(
                lambda x: 'normal' if 10 <= x <= 18 else 'afterhours'
            )
        return df