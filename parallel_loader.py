# database/parallel_loader.py
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

class ParallelBISTDatabaseManager(BISTDatabaseManager):
    def initialize_database_parallel(self, max_workers=4):
        """Parallel database yükleme"""
        print(f"🚀 Parallel database initialization ({max_workers} thread)")
        
        self.create_database()
        all_files = self.scan_directory_structure()
        
        total_files = len(all_files)
        loaded_files = 0
        lock = threading.Lock()
        
        def process_file(file_info):
            symbol, year, filename, full_path = file_info
            try:
                symbol_from_file, timeframe, year_from_file = self.loader.parse_bist_filename(filename)
                
                if symbol_from_file and timeframe:
                    df = self.loader.load_bist_data(full_path)
                    
                    if df is not None and not df.empty:
                        success = self.save_to_database(df, symbol_from_file, timeframe)
                        if success:
                            with lock:
                                nonlocal loaded_files
                                loaded_files += 1
                            return True
            except Exception as e:
                pass
            return False
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(process_file, file_info) for file_info in all_files]
            
            with tqdm(total=total_files, desc="📥 Parallel yükleme") as pbar:
                for future in as_completed(futures):
                    future.result()
                    pbar.update(1)
                    pbar.set_postfix({'Yüklenen': loaded_files})
        
        print(f"✅ Parallel yükleme tamamlandı: {loaded_files}/{total_files}")