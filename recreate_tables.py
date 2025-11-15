# recreate_tables.py
from database.bist_data_loader import BISTDatabaseManager, Base

def recreate_tables():
    """Table'ları yeniden oluştur"""
    print("🗑️ Table'lar yeniden oluşturuluyor...")
    
    db = BISTDatabaseManager()
    
    try:
        # Önce table'ı sil
        Base.metadata.drop_all(db.engine)
        print("✅ Eski table silindi")
        
        # Yeni table oluştur
        Base.metadata.create_all(db.engine)
        print("✅ Yeni table oluşturuldu")
        
    except Exception as e:
        print(f"❌ Table yeniden oluşturma hatası: {e}")

if __name__ == "__main__":
    recreate_tables()