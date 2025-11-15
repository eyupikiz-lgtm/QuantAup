# quick_fix_test.py
import os
import pandas as pd
from database.bist_data_loader import BISTDatabaseManager

def test_fixed_database():
    """Düzeltilmiş database testi"""
    print("🔧 Düzeltilmiş Database Testi")
    print("=" * 50)
    
    db = BISTDatabaseManager()
    
    # Sadece ZRGYO Günlük verisini test et
    base_path = r"C:\iDealPython\data"
    test_file = os.path.join(base_path, "IMKBH_ZRGYO", "2025", "IMKBH_ZRGYO_G_2025.csv")
    
    if os.path.exists(test_file):
        print(f"📥 Test dosyası: {test_file}")
        
        # Dosyayı yükle
        df = db.loader.load_bist_data(test_file)
        
        if df is not None and not df.empty:
            print(f"✅ Veri yüklendi: {len(df)} kayıt")
            
            # Database'e kaydet
            success = db.save_to_database(df, "ZRGYO", "1d")
            
            if success:
                print("🎉 BAŞARILI! Veri database'e eklendi")
                
                # Kontrol et
                symbols = db.get_available_symbols()
                print(f"📊 Database'deki semboller: {symbols}")
                
                if symbols:
                    data = db.get_symbol_data("ZRGYO", "1d")
                    if data is not None:
                        print(f"✅ ZRGYO verisi çekildi: {len(data)} kayıt")
                        print(f"📅 Son kayıt: {data.index[-1]} - {data['close'].iloc[-1]:.2f}")
                    else:
                        print("❌ ZRGYO verisi çekilemedi")
                else:
                    print("❌ Database hala boş")
            else:
                print("❌ Database kaydetme başarısız")
        else:
            print("❌ Veri yüklenemedi")
    else:
        print("❌ Test dosyası bulunamadı")

def check_table_structure():
    """Table yapısını kontrol et"""
    print("\n🔍 Table Yapısı Kontrolü")
    print("=" * 50)
    
    db = BISTDatabaseManager()
    
    try:
        # Table schema'sını kontrol et
        query = """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'market_data'
        ORDER BY ordinal_position;
        """
        
        schema = pd.read_sql(query, db.engine)
        print("📋 Market Data Table Schema:")
        print(schema)
        
        # Mevcut kayıt sayısı
        count_query = "SELECT COUNT(*) as record_count FROM market_data"
        count_result = pd.read_sql(count_query, db.engine)
        print(f"\n📊 Toplam kayıt: {count_result['record_count'].iloc[0]}")
        
    except Exception as e:
        print(f"❌ Schema kontrol hatası: {e}")

if __name__ == "__main__":
    # Önce table yapısını kontrol et
    check_table_structure()
    
    print("\n" + "=" * 50)
    
    # Sonra düzeltilmiş testi çalıştır
    test_fixed_database()