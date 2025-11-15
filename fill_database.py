# fill_database.py
import os
import time
from tqdm import tqdm
from database.bist_data_loader import BISTDatabaseManager

def fill_database_with_progress():
    """Progress bar ile database doldurma"""
    print("🚀 Database doldurma işlemi başlatılıyor...")
    print("⏰ Bu işlem birkaç dakika sürebilir...")
    
    db = BISTDatabaseManager()
    
    # Database'i doldur
    print("\n📥 Veriler database'e yükleniyor...")
    start_time = time.time()
    
    loaded_files, error_files = db.initialize_database()
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n✅ Database doldurma tamamlandı!")
    print(f"⏱️  Toplam süre: {duration:.2f} saniye ({duration/60:.2f} dakika)")
    print(f"📊 Başarılı dosya: {loaded_files}")
    print(f"📊 Hatalı dosya: {error_files}")
    
    # Son kontrol
    print("\n🔍 Son kontrol...")
    symbols = db.get_available_symbols()
    timeframes = db.get_available_timeframes()
    
    if symbols:
        print(f"✅ Başarılı! {len(symbols)} sembol yüklendi")
        print(f"📊 Timeframe'ler: {timeframes}")
        
        # İlk 5 sembolün özeti
        print(f"\n📈 İlk 5 Sembol Özeti:")
        for symbol in symbols[:5]:
            print(f"   {symbol}:")
            for tf in timeframes:
                data = db.get_symbol_data(symbol, tf)
                if data is not None:
                    print(f"     {tf}: {len(data):,} kayıt")
    else:
        print("❌ Database hala boş görünüyor!")

def quick_fill_test():
    """Hızlı test - sadece birkaç dosya yükle"""
    print("⚡ Hızlı Test - Sadece birkaç dosya yüklenecek...")
    
    db = BISTDatabaseManager()
    
    # Sadece birkaç dosya yükle
    base_path = r"C:\iDealPython\data"
    test_files = []
    
    # AKBNK'nın 2025 yılı dosyalarını bul
    akbnk_path = os.path.join(base_path, "IMKBH_AKBNK", "2025")
    if os.path.exists(akbnk_path):
        for file in os.listdir(akbnk_path):
            if file.endswith('.csv'):
                full_path = os.path.join(akbnk_path, file)
                test_files.append(('AKBNK', '2025', file, full_path))
                print(f"📄 Bulundu: {file}")
    
    if not test_files:
        print("❌ Test dosyaları bulunamadı! Klasör yapısını kontrol edin.")
        return
    
    print(f"\n🔍 {len(test_files)} test dosyası yüklenecek...")
    
    for symbol, year, filename, full_path in test_files:
        print(f"📥 İşleniyor: {filename}")
        
        symbol_from_file, timeframe, year_from_file = db.loader.parse_bist_filename(filename)
        
        if symbol_from_file and timeframe:
            df = db.loader.load_bist_data(full_path)
            
            if df is not None and not df.empty:
                success = db.save_to_database(df, symbol_from_file, timeframe)
                if success:
                    print(f"✅ {symbol_from_file} ({timeframe}) - {len(df)} kayıt eklendi")
                else:
                    print(f"❌ Kaydetme hatası: {filename}")
            else:
                print(f"⚠️ Boş veri: {filename}")
        else:
            print(f"⚠️ Dosya adı parse edilemedi: {filename}")
    
    # Sonuçları göster
    symbols = db.get_available_symbols()
    print(f"\n📊 Database durumu: {len(symbols)} sembol")
    for symbol in symbols:
        for tf in db.get_available_timeframes(symbol):
            data = db.get_symbol_data(symbol, tf)
            if data is not None:
                print(f"   {symbol} ({tf}): {len(data)} kayıt")

def parallel_fill_database():
    """Parallel database doldurma (daha hızlı)"""
    print("🚀 Parallel Database Doldurma")
    print("⏰ Bu işlem daha hızlı olacak...")
    
    db = BISTDatabaseManager()
    
    # Tüm dosyaları bul
    all_files = db.scan_directory_structure()
    
    total_files = len(all_files)
    print(f"📊 Toplam {total_files} dosya işlenecek...")
    
    # Batch processing - her seferinde 10 dosya
    batch_size = 10
    loaded_files = 0
    
    for i in range(0, total_files, batch_size):
        batch = all_files[i:i + batch_size]
        print(f"\n🔄 Batch {i//batch_size + 1}/{(total_files + batch_size - 1)//batch_size}")
        
        for symbol, year, filename, full_path in batch:
            print(f"   📥 {filename}")
            
            symbol_from_file, timeframe, year_from_file = db.loader.parse_bist_filename(filename)
            
            if symbol_from_file and timeframe:
                df = db.loader.load_bist_data(full_path)
                
                if df is not None and not df.empty:
                    success = db.save_to_database(df, symbol_from_file, timeframe)
                    if success:
                        loaded_files += 1
        
        print(f"   ✅ Bu batch tamamlandı - Toplam: {loaded_files}/{total_files}")
    
    print(f"\n🎯 Parallel doldurma tamamlandı!")
    print(f"📊 Toplam yüklenen: {loaded_files}/{total_files}")

if __name__ == "__main__":
    print("🗄️ BIST Database Doldurma")
    print("=" * 50)
    
    # Kullanıcı seçimi
    print("1: Tüm database'i doldur (uzun sürebilir)")
    print("2: Hızlı test (sadece birkaç dosya)")
    print("3: Parallel doldurma (daha hızlı)")
    
    choice = input("\nSeçiminiz (1, 2 veya 3): ").strip()
    
    if choice == "1":
        fill_database_with_progress()
    elif choice == "2":
        quick_fill_test()
    elif choice == "3":
        parallel_fill_database()
    else:
        print("❌ Geçersiz seçim!")