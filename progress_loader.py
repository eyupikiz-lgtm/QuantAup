# database/progress_loader.py
import time
from tqdm import tqdm

class ProgressBISTDatabaseManager(BISTDatabaseManager):
    def initialize_database_with_progress(self):
        """Progress bar ile database initialization"""
        print("🚀 Database initialization başlatılıyor...")
        
        self.create_database()
        all_files = self.scan_directory_structure()
        
        total_files = len(all_files)
        loaded_files = 0
        errors = 0
        
        print(f"📊 Toplam {total_files} dosya işlenecek...")
        
        # Progress bar
        with tqdm(total=total_files, desc="📥 Dosyalar yükleniyor") as pbar:
            for symbol, year, filename, full_path in all_files:
                try:
                    symbol_from_file, timeframe, year_from_file = self.loader.parse_bist_filename(filename)
                    
                    if symbol_from_file and timeframe:
                        df = self.loader.load_bist_data(full_path)
                        
                        if df is not None and not df.empty:
                            success = self.save_to_database(df, symbol_from_file, timeframe)
                            if success:
                                loaded_files += 1
                    
                    pbar.update(1)
                    pbar.set_postfix({
                        'Yüklenen': loaded_files, 
                        'Hatalar': errors,
                        'Şu anki': symbol
                    })
                    
                except Exception as e:
                    errors += 1
                    pbar.set_postfix({'Hatalar': errors})
                    continue
        
        print(f"✅ Database initialization tamamlandı!")
        print(f"📊 Sonuç: {loaded_files}/{total_files} dosya başarıyla yüklendi")
        print(f"⚠️ Hatalı dosya: {errors}")