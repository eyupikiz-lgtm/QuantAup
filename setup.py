# setup.py
from database.bist_data_loader import BISTDatabaseManager

def main():
    print("🚀 BIST Trading Platform Setup")
    print("=" * 50)
    
    # Database manager oluştur
    db_manager = BISTDatabaseManager()
    
    # Database'i initialize et
    db_manager.initialize_database()
    
    print("✅ Setup tamamlandı!")
    
    # Test: Mevcut sembolleri ve timeframe'leri göster
    print("\n📊 Database Özeti:")
    symbols = db_manager.get_available_symbols()
    timeframes = db_manager.get_available_timeframes()
    
    print(f"Semboller: {symbols[:10]}{'...' if len(symbols) > 10 else ''}")
    print(f"Timeframes: {timeframes}")
    
    # Test: AKBNK verisini çek
    if symbols:
        test_symbol = symbols[0]
        print(f"\n🧪 Test: {test_symbol} verisi çekiliyor...")
        data = db_manager.get_symbol_data(test_symbol, '5m')
        
        if data is not None:
            print(f"📊 {test_symbol} verisi: {len(data)} kayıt")
            print(data.head(3))
        else:
            print("❌ Test başarısız!")

if __name__ == "__main__":
    main()