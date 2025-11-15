# test_pyqt_interface.py
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QTextEdit
from database.bist_data_loader import BISTDatabaseManager
from ui.advanced_optimization_panel import AdvancedOptimizationPanel

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = BISTDatabaseManager()
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("BIST Trading Platform - Test Arayüzü")
        self.setGeometry(100, 100, 1200, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Test butonları
        self.test_db_btn = QPushButton("Database Testi")
        self.test_db_btn.clicked.connect(self.test_database)
        
        self.test_cuda_btn = QPushButton("CUDA Backtest Testi")
        self.test_cuda_btn.clicked.connect(self.test_cuda)
        
        self.optimization_panel = AdvancedOptimizationPanel(self.db)
        
        # Sonuçlar için text alanı
        self.results_text = QTextEdit()
        self.results_text.setPlaceholderText("Test sonuçları burada görünecek...")
        
        layout.addWidget(self.test_db_btn)
        layout.addWidget(self.test_cuda_btn)
        layout.addWidget(self.optimization_panel)
        layout.addWidget(self.results_text)
    
    def test_database(self):
        """Database testi"""
        self.results_text.append("🔗 Database testi başlatılıyor...")
        
        try:
            symbols = self.db.get_available_symbols()
            timeframes = self.db.get_available_timeframes()
            
            self.results_text.append(f"✅ Mevcut semboller: {len(symbols)}")
            self.results_text.append(f"✅ Mevcut timeframe'ler: {timeframes}")
            
            if symbols:
                # İlk sembolün verisini test et
                test_symbol = symbols[0]
                data = self.db.get_symbol_data(test_symbol, '5m')
                
                if data is not None:
                    self.results_text.append(f"✅ {test_symbol} 5m verisi: {len(data)} kayıt")
                    self.results_text.append(f"📅 Veri aralığı: {data.index[0]} - {data.index[-1]}")
                else:
                    self.results_text.append("❌ Veri çekilemedi!")
                    
        except Exception as e:
            self.results_text.append(f"❌ Hata: {e}")
    
    def test_cuda(self):
        """CUDA backtest testi"""
        self.results_text.append("🚀 CUDA Backtest testi başlatılıyor...")
        
        # Bu kısımda gerçek CUDA testi yapılacak
        self.results_text.append("✅ CUDA testi hazır - Optimizasyon panelini kullanın")

def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()