# test_new_format.py
import pandas as pd
from database.bist_data_loader import BISTDataLoader

def test_single_file():
    """Tek bir dosyayı test et"""
    print("🧪 Tek dosya testi...")
    
    loader = BISTDataLoader()
    
    # Test dosyası
    test_file = r"C:\iDealPython\data\IMKBH_ZRGYO\2025\IMKBH_ZRGYO_G_2025.csv"
    
    if os.path.exists(test_file):
        print(f"🔍 Test dosyası: {test_file}")
        
        # Dosyayı yükle
        df = loader.load_bist_data(test_file)
        
        if df is not None and not df.empty:
            print(f"✅ Dosya başarıyla yüklendi!")
            print(f"📊 Veri boyutu: {df.shape}")
            print(f"📅 Tarih aralığı: {df.index[0]} - {df.index[-1]}")
            print(f"💰 Fiyat örnekleri:")
            print(df.head(3))
            print(f"📈 Son fiyat: {df['Close'].iloc[-1]:.2f}")
            
            return True
        else:
            print("❌ Dosya yüklenemedi!")
            return False
    else:
        print("❌ Test dosyası bulunamadı!")
        return False

def quick_database_fill():
    """Hızlı database doldurma testi"""
    print("⚡ Hızlı database doldurma...")
    
    from database.bist_data_loader import BISTDatabaseManager
    
    db = BISTDatabaseManager()
    
    # Sadece ZRGYO sembolünü yükle
    base_path = r"C:\iDealPython\data"
    zrgyo_path = os.path.join(base_path, "IMKBH_ZRGYO", "2025")
    
    if os.path.exists(zrgyo_path):
        print(f"🔍 ZRGYO dosyaları bulundu")
        
        for file in os.listdir(zrgyo_path):
            if file.endswith('.csv'):
                full_path = os.path.join(zrgyo_path, file)
                print(f"📥 İşleniyor: {file}")
                
                symbol, timeframe, year = db.loader.parse_bist_filename(file)
                
                if symbol and timeframe:
                    df = db.loader.load_bist_data(full_path)
                    
                    if df is not None and not df.empty:
                        success = db.save_to_database(df, symbol, timeframe)
                        if success:
                            print(f"✅ {symbol} ({timeframe}) - {len(df)} kayıt eklendi")
                        else:
                            print(f"❌ Kaydetme hatası")
                    else:
                        print(f"⚠️ Boş veri")
                else:
                    print(f"⚠️ Dosya adı parse edilemedi")
    
    # Sonuçları kontrol et
    symbols = db.get_available_symbols()
    print(f"\n📊 Database durumu: {len(symbols)} sembol")
    
    if symbols:
        for symbol in symbols:
            for tf in db.get_available_timeframes(symbol):
                data = db.get_symbol_data(symbol, tf)
                if data is not None:
                    print(f"   {symbol} ({tf}): {len(data)} kayıt")

if __name__ == "__main__":
    import os
    
    print("🚀 Yeni Format Testi")
    print("=" * 50)
    
    # Önce tek dosya testi
    if test_single_file():
        print("\n" + "=" * 50)
        # Sonra database testi
        quick_database_fill()