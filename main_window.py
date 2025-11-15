# main_window.py
import sys
import pandas as pd
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                           QWidget, QPushButton, QComboBox, QTextEdit, QTabWidget,
                           QLabel, QLineEdit)
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtChart import QChart, QChartView, QLineSeries
import pyqtgraph as pg

from database.db_manager import DatabaseManager
from backtesting.cuda_backtester import CUDABacktester
from strategies.moving_average_cross import MovingAverageCrossStrategy

class BacktestThread(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, backtester, data, strategy):
        super().__init__()
        self.backtester = backtester
        self.data = data
        self.strategy = strategy
    
    def run(self):
        try:
            signals = self.strategy.generate_signals(self.data)
            results = self.backtester.run_backtest(self.data, signals)
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.backtester = CUDABacktester()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("CUDA Trading Platform")
        self.setGeometry(100, 100, 1400, 900)
        
        # Main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        self.symbol_combo = QComboBox()
        self.symbol_combo.addItems(['AAPL', 'GOOGL', 'MSFT', 'BTC-USD'])
        
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(['1m', '5m', '1h', '1d'])
        
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems(['Moving Average Cross', 'RSI', 'MACD'])
        
        self.run_btn = QPushButton("Backtest Çalıştır")
        self.run_btn.clicked.connect(self.run_backtest)
        
        self.optimize_btn = QPushButton("Optimize Et")
        self.optimize_btn.clicked.connect(self.run_optimization)
        
        controls_layout.addWidget(QLabel("Sembol:"))
        controls_layout.addWidget(self.symbol_combo)
        controls_layout.addWidget(QLabel("Timeframe:"))
        controls_layout.addWidget(self.timeframe_combo)
        controls_layout.addWidget(QLabel("Strateji:"))
        controls_layout.addWidget(self.strategy_combo)
        controls_layout.addWidget(self.run_btn)
        controls_layout.addWidget(self.optimize_btn)
        
        # Results area
        self.results_text = QTextEdit()
        self.results_text.setPlaceholderText("Backtest sonuçları burada görünecek...")
        
        # Charts tab
        self.chart_tabs = QTabWidget()
        self.equity_chart = pg.PlotWidget(title="Equity Curve")
        self.drawdown_chart = pg.PlotWidget(title="Drawdown")
        
        self.chart_tabs.addTab(self.equity_chart, "Equity Curve")
        self.chart_tabs.addTab(self.drawdown_chart, "Drawdown")
        
        layout.addLayout(controls_layout)
        layout.addWidget(self.results_text)
        layout.addWidget(self.chart_tabs)
    
    def run_backtest(self):
        symbol = self.symbol_combo.currentText()
        timeframe = self.timeframe_combo.currentText()
        
        # Veriyi çek
        data = self.db.get_symbol_data(symbol, timeframe)
        
        if data is None:
            self.results_text.append("❌ Veri bulunamadı!")
            return
        
        # Strateji seç
        strategy = MovingAverageCrossStrategy(short_window=10, long_window=30)
        
        # Thread'de backtest çalıştır
        self.backtest_thread = BacktestThread(self.backtester, data, strategy)
        self.backtest_thread.finished.connect(self.on_backtest_finished)
        self.backtest_thread.error.connect(self.on_backtest_error)
        self.backtest_thread.start()
        
        self.results_text.append("🔁 Backtest çalıştırılıyor (CUDA)...")
    
    def on_backtest_finished(self, results):
        self.results_text.append("✅ Backtest tamamlandı!")
        
        # Sonuçları göster
        total_return = (results['Portfolio_Value'].iloc[-1] - 100000) / 1000
        self.results_text.append(f"💰 Toplam Getiri: {total_return:.2f}%")
        
        # Grafikleri çiz
        self.plot_equity_curve(results)
    
    def on_backtest_error(self, error_msg):
        self.results_text.append(f"❌ Hata: {error_msg}")
    
    def plot_equity_curve(self, results):
        """Equity curve çiz"""
        self.equity_chart.clear()
        
        # Portfolio değerini çiz
        portfolio_line = pg.PlotDataItem(
            results.index, 
            results['Portfolio_Value'],
            pen=pg.mkPen('g', width=2)
        )
        self.equity_chart.addItem(portfolio_line)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()