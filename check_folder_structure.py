# check_folder_structure.py
import os

def check_folder_structure():
    """Klasör yapısını kontrol et"""
    base_path = r"C:\iDealPython\data"
    
    print(f"🔍 Klasör yapısı kontrol ediliyor: {base_path}")
    
    if not os.path.exists(base_path):
        print("❌ Ana klasör bulunamadı!")
        return False
    
    # IMKBH_ ile başlayan klasörleri listele
    imkb_folders = []
    for item in os.listdir(base_path):
        item_path = os.path.join(base_path, item)
        if os.path.isdir(item_path) and item.startswith('IMKBH_'):
            imkb_folders.append(item)
    
    print(f"📁 IMKBH klasörleri: {len(imkb_folders)} adet")
    
    if not imkb_folders:
        print("❌ IMKBH_ ile başlayan klasör bulunamadı!")
        return False
    
    for folder in imkb_folders[:5]:  # İlk 5'i göster
        folder_path = os.path.join(base_path, folder)
        symbol = folder.replace('IMKBH_', '')
        print(f"\n📂 {folder} (Sembol: {symbol}):")
        
        # Yıl klasörlerini listele
        year_folders = []
        for year_item in os.listdir(folder_path):
            year_path = os.path.join(folder_path, year_item)
            if os.path.isdir(year_path) and year_item.isdigit():
                year_folders.append(year_item)
        
        year_folders.sort()
        print(f"   📅 Yıllar: {year_folders}")
        
        # En son yıldaki dosyaları göster (örnek)
        if year_folders:
            latest_year = year_folders[-1]
            latest_year_path = os.path.join(folder_path, latest_year)
            csv_files = [f for f in os.listdir(latest_year_path) if f.endswith('.csv')]
            print(f"   📄 {latest_year} dosyaları: {csv_files}")
            
            # Dosya formatını kontrol et
            if csv_files:
                sample_file = csv_files[0]
                print(f"   🔍 Örnek dosya: {sample_file}")
                
                # Dosya içeriğini kontrol et (ilk satır)
                try:
                    sample_path = os.path.join(latest_year_path, sample_file)
                    with open(sample_path, 'r', encoding='utf-8') as f:
                        first_line = f.readline().strip()
                        print(f"   📝 İlk satır: {first_line}")
                except Exception as e:
                    print(f"   ❌ Dosya okuma hatası: {e}")
    
    if len(imkb_folders) > 5:
        print(f"\n   ... ve {len(imkb_folders) - 5} klasör daha")
    
    return True

def check_specific_symbol(symbol="AKBNK"):
    """Belirli bir sembolün klasör yapısını kontrol et"""
    base_path = r"C:\iDealPython\data"
    symbol_folder = f"IMKBH_{symbol}"
    symbol_path = os.path.join(base_path, symbol_folder)
    
    print(f"\n🔍 {symbol} klasör yapısı kontrol ediliyor...")
    
    if not os.path.exists(symbol_path):
        print(f"❌ {symbol_folder} klasörü bulunamadı!")
        return False
    
    print(f"✅ {symbol_folder} klasörü mevcut")
    
    # Yıl klasörlerini listele
    year_folders = []
    for year_item in os.listdir(symbol_path):
        year_path = os.path.join(symbol_path, year_item)
        if os.path.isdir(year_path) and year_item.isdigit():
            year_folders.append(year_item)
    
    year_folders.sort()
    print(f"📅 {symbol} yılları: {year_folders}")
    
    # Her yıldaki dosyaları göster
    for year in year_folders[-2:]:  # Son 2 yıl
        year_path = os.path.join(symbol_path, year)
        csv_files = [f for f in os.listdir(year_path) if f.endswith('.csv')]
        print(f"   {year}: {csv_files}")
    
    return True

if __name__ == "__main__":
    print("📁 BIST Klasör Yapısı Kontrolü")
    print("=" * 50)
    
    # Genel klasör yapısını kontrol et
    if check_folder_structure():
        print("\n" + "=" * 50)
        print("✅ Klasör yapısı uygun!")
        
        # AKBNK'yı özellikle kontrol et
        check_specific_symbol("AKBNK")
    else:
        print("\n❌ Klasör yapısında sorun var!")