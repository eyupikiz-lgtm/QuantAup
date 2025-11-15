# check_database.py
from database.bist_data_loader import BISTDatabaseManager

def check_database_status():
    """Database durumunu kontrol et"""
    print("📊 Database Durum Kontrolü")
    print("=" * 50)
    
    db = BISTDatabaseManager()
    
    # Özet istatistikler
    summary = db.get_data_summary()
    
    if summary:
        print(f"✅ Database dolu!")
        
        # Tüm sembolleri listele
        symbols = db.get_available_symbols()
        print(f"\n📈 Toplam Sembol: {len(symbols)}")
        
        # İlk 10 sembolü göster
        print("🔍 İlk 10 Sembol:")
        for i, symbol in enumerate(symbols[:10]):
            print(f"   {i+1:2d}. {symbol}")
        
        if len(symbols) > 10:
            print(f"   ... ve {len(symbols) - 10} sembol daha")
        
        # Timeframe dağılımı
        timeframes = db.get_available_timeframes()
        print(f"\n⏰ Timeframe'ler: {timeframes}")
        
        # Örnek sembol detayları
        if symbols:
            sample_symbol = symbols[0]
            print(f"\n🧪 Örnek Sembol Detayı: {sample_symbol}")
            
            for tf in timeframes:
                data = db.get_symbol_data(sample_symbol, tf)
                if data is not None:
                    print(f"   {tf}: {len(data):,} kayıt | {data.index[0].date()} - {data.index[-1].date()}")
    
    else:
        print("❌ Database boş veya erişilemiyor!")

if __name__ == "__main__":
    check_database_status()