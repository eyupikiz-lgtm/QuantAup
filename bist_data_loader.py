# database/bist_data_loader.py
import pandas as pd
import numpy as np
import os
from datetime import datetime, time
import psycopg2
from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import re

Base = declarative_base()

class MarketData(Base):
    __tablename__ = 'market_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), index=True)
    datetime = Column(DateTime, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    timeframe = Column(String(10))

class BISTDataLoader:
    def __init__(self, data_path=r"C:\iDealPython\data"):
        self.data_path = data_path
        print(f"📁 Data path: {self.data_path}")
        
        # Timeframe mapping
        self.timeframe_map = {
            'G': '1d',    # Günlük
            '60': '1h',   # 60 dakika
            '5': '5m'     # 5 dakika
        }
    
    def parse_bist_filename(self, filename):
        """BIST dosya isminden sembol ve timeframe çıkar"""
        # IMKBH_AKBNK_G_2025.csv -> (AKBNK, G, 2025)
        match = re.match(r'IMKBH_([A-Z]+)_([G5]|\d+)_(\d{4})\.csv', filename)
        if match:
            symbol = match.group(1)  # AKBNK
            timeframe_key = match.group(2)  # G, 60, 5
            year = match.group(3)  # 2025
            
            # Timeframe mapping
            timeframe = self.timeframe_map.get(timeframe_key, timeframe_key + 'm')
            return symbol, timeframe, year
        return None, None, None
    
    def load_bist_data(self, filepath):
        """BIST formatındaki CSV'yi yükle - GÜNCEL FORMAT"""
        try:
            print(f"📥 Loading: {filepath}")
            
            # YENİ FORMAT: Tarih;Saat;Açılış;En Yüksek;En Düşük;Kapanış;Hacim
            # Ayırıcı: ; (noktalı virgül)
            df = pd.read_csv(filepath, delimiter=';', header=None, 
                           names=['Date', 'Time', 'Open', 'High', 'Low', 'Close', 'Volume'])
            
            print(f"📊 Raw data shape: {df.shape}")
            
            # Türkçe format düzeltmeleri - virgülü noktaya çevir
            for col in ['Open', 'High', 'Low', 'Close']:
                df[col] = df[col].astype(str).str.replace(',', '.').astype(float)
            
            df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce').fillna(0).astype(int)
            
            # DateTime oluştur - YENİ FORMAT
            # Tarih: 2025-01-02 (ISO format)
            # Saat: 00:00 (günlük verilerde)
            if df['Time'].isna().all() or (df['Time'] == '00:00').all():
                # Günlük veri - ISO format
                df['DateTime'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')
                # BIST kapanış saati ekle
                df['DateTime'] = df['DateTime'] + pd.Timedelta(hours=17, minutes=30)
            else:
                # Intraday veri
                df['DateTime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], 
                                              format='%Y-%m-%d %H:%M')
            
            df.set_index('DateTime', inplace=True)
            
            # Gereksiz sütunları kaldır
            df.drop(['Date', 'Time'], axis=1, inplace=True)
            
            # Veri kalitesi kontrolü
            print(f"✅ Processed data shape: {df.shape}")
            print(f"📅 Date range: {df.index[0]} to {df.index[-1]}")
            
            return df
            
        except Exception as e:
            print(f"❌ Dosya okuma hatası {filepath}: {e}")
            return None

class BISTDatabaseManager:
    def __init__(self, db_url="postgresql://postgres:admin123@localhost:5432/bist_trading"):
        self.db_url = db_url
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        self.loader = BISTDataLoader()  # ✅ LOADER EKLENDİ
        print("✅ Database Manager initialized")
        
    def create_database(self):
        """Database ve tabloları oluştur"""
        try:
            # Önce postgres database'e bağlan
            conn = psycopg2.connect(
                host="localhost",
                database="postgres",
                user="postgres",
                password="admin123",
                port=5432
            )
            conn.autocommit = True
            cursor = conn.cursor()
            
            # Database oluştur (yoksa)
            cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'bist_trading'")
            exists = cursor.fetchone()
            
            if not exists:
                cursor.execute('CREATE DATABASE bist_trading')
                print("✅ bist_trading database oluşturuldu")
            
            cursor.close()
            conn.close()
            
            # Tabloları oluştur
            self.create_tables()
            
        except Exception as e:
            print(f"❌ Database oluşturma hatası: {e}")
    
    def create_tables(self):
        """Gerekli tabloları oluştur"""
        try:
            Base.metadata.create_all(self.engine)
            print("✅ Tablolar oluşturuldu")
        except Exception as e:
            print(f"❌ Tablo oluşturma hatası: {e}")
    
    def save_to_database(self, df, symbol, timeframe):
        """DataFrame'i database'e kaydet - DÜZELTİLMİŞ"""
        try:
            # Sütunları ekle
            df['symbol'] = symbol
            df['timeframe'] = timeframe
            
            # Index'i sütun yap ve sütun isimlerini küçük harf yap
            df_reset = df.reset_index()
            df_reset.columns = [col.lower() for col in df_reset.columns]  # ✅ KÜÇÜK HARF
            
            print(f"💾 Kaydediliyor: {symbol} ({timeframe}) - {len(df_reset)} kayıt")
            
            # Database'e kaydet
            df_reset.to_sql('market_data', self.engine, if_exists='append', index=False)
            
            print(f"✅ {symbol} ({timeframe}) - {len(df_reset)} kayıt başarıyla eklendi")
            return True
            
        except Exception as e:
            print(f"❌ Database kaydetme hatası {symbol}: {e}")
            return False
    
    def get_available_symbols(self):
        """Database'deki tüm sembolleri listele"""
        try:
            query = "SELECT DISTINCT symbol FROM market_data ORDER BY symbol"
            df = pd.read_sql(query, self.engine)
            symbols = df['symbol'].tolist()
            print(f"📊 Mevcut semboller: {len(symbols)} adet")
            return symbols
        except Exception as e:
            print(f"❌ Sembol listeleme hatası: {e}")
            return []

    def get_available_timeframes(self, symbol=None):
        """Sembolün mevcut timeframe'lerini listele"""
        try:
            if symbol:
                query = f"SELECT DISTINCT timeframe FROM market_data WHERE symbol = '{symbol}' ORDER BY timeframe"
            else:
                query = "SELECT DISTINCT timeframe FROM market_data ORDER BY timeframe"
            
            df = pd.read_sql(query, self.engine)
            timeframes = df['timeframe'].tolist()
            print(f"📊 Mevcut timeframe'ler: {timeframes}")
            return timeframes
        except Exception as e:
            print(f"❌ Timeframe listeleme hatası: {e}")
            return []

    def get_data_summary(self):
        """Database özet istatistikleri"""
        try:
            # Toplam kayıt sayısı
            total_query = "SELECT COUNT(*) as total_records FROM market_data"
            total_df = pd.read_sql(total_query, self.engine)
            total_records = total_df['total_records'].iloc[0]
            
            # Sembol sayısı
            symbol_query = "SELECT COUNT(DISTINCT symbol) as symbol_count FROM market_data"
            symbol_df = pd.read_sql(symbol_query, self.engine)
            symbol_count = symbol_df['symbol_count'].iloc[0]
            
            # Timeframe dağılımı
            timeframe_query = """
            SELECT timeframe, COUNT(*) as record_count 
            FROM market_data 
            GROUP BY timeframe 
            ORDER BY timeframe
            """
            timeframe_df = pd.read_sql(timeframe_query, self.engine)
            
            print("📊 DATABASE ÖZETİ:")
            print(f"   Toplam Kayıt: {total_records:,}")
            print(f"   Sembol Sayısı: {symbol_count}")
            print("   Timeframe Dağılımı:")
            for _, row in timeframe_df.iterrows():
                print(f"     {row['timeframe']}: {row['record_count']:,} kayıt")
            
            return {
                'total_records': total_records,
                'symbol_count': symbol_count,
                'timeframe_distribution': timeframe_df
            }
            
        except Exception as e:
            print(f"❌ Özet istatistik hatası: {e}")
            return None
    
    def get_symbol_data(self, symbol, timeframe='5m', start_date=None, end_date=None):
        """Database'den sembol verisi çek"""
        try:
            query = f"SELECT * FROM market_data WHERE symbol = '{symbol}' AND timeframe = '{timeframe}'"
            
            if start_date:
                query += f" AND datetime >= '{start_date}'"
            if end_date:
                query += f" AND datetime <= '{end_date}'"
                
            query += " ORDER BY datetime"
            
            df = pd.read_sql(query, self.engine, parse_dates=['datetime'])
            df.set_index('datetime', inplace=True)
            
            print(f"✅ {symbol} ({timeframe}) verisi çekildi: {len(df)} kayıt")
            return df
            
        except Exception as e:
            print(f"❌ Veri çekme hatası {symbol}: {e}")
            return None

    
    def initialize_database(self):
        """Tüm BIST verilerini database'e yükle"""
        print("🚀 Database initialization başlatılıyor...")
        
        # Database oluştur
        self.create_database()
        
        # Tüm dosyaları bul
        all_files = self.scan_directory_structure()
        
        total_files = len(all_files)
        loaded_files = 0
        error_files = 0
        
        print(f"📊 Toplam {total_files} dosya işlenecek...")
        
        for symbol, year, filename, full_path in all_files:
            print(f"\n📥 Processing: {symbol} - {filename}")
            
            symbol_from_file, timeframe, year_from_file = self.loader.parse_bist_filename(filename)
            
            if symbol_from_file and timeframe:
                df = self.loader.load_bist_data(full_path)
                
                if df is not None and not df.empty:
                    success = self.save_to_database(df, symbol_from_file, timeframe)
                    if success:
                        loaded_files += 1
                        print(f"✅ {symbol_from_file} ({timeframe}) - {len(df)} kayıt eklendi")
                    else:
                        error_files += 1
                        print(f"❌ Kaydetme hatası: {filename}")
                else:
                    error_files += 1
                    print(f"⚠️ Boş veri: {filename}")
            else:
                error_files += 1
                print(f"⚠️ Dosya adı parse edilemedi: {filename}")
        
        print(f"\n🎯 Database initialization tamamlandı!")
        print(f"📊 Toplam: {total_files} dosya")
        print(f"✅ Başarılı: {loaded_files} dosya")
        print(f"❌ Hatalı: {error_files} dosya")
        
        return loaded_files, error_files

    def scan_directory_structure(self):
        """Klasör yapısını tarayarak tüm dosyaları bul"""
        base_path = self.loader.data_path
        print(f"🔍 Scanning directory structure: {base_path}")
        
        all_files = []
        
        # Tüm IMKBH_ klasörlerini bul
        for item in os.listdir(base_path):
            item_path = os.path.join(base_path, item)
            if os.path.isdir(item_path) and item.startswith('IMKBH_'):
                symbol = item.replace('IMKBH_', '')
                print(f"📁 Found symbol: {symbol}")
                
                # Yıl klasörlerini tarayın
                for year_dir in os.listdir(item_path):
                    year_path = os.path.join(item_path, year_dir)
                    if os.path.isdir(year_path) and year_dir.isdigit():
                        # CSV dosyalarını bul
                        for file in os.listdir(year_path):
                            if file.endswith('.csv') and file.startswith(f'IMKBH_{symbol}_'):
                                full_path = os.path.join(year_path, file)
                                all_files.append((symbol, year_dir, file, full_path))
        
        print(f"📊 Toplam {len(all_files)} dosya bulundu")
        return all_files