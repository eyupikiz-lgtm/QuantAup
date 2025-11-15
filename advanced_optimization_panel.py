# ui/advanced_optimization_panel.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                           QLabel, QLineEdit, QPushButton, QProgressBar,
                           QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
                           QCheckBox, QSpinBox, QDoubleSpinBox)
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtChart import QChart, QChartView, QLineSeries, QValueAxis
import pyqtgraph as pg
import pandas as pd

class AdvancedOptimizationPanel(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.backtester = OptimizedCUDABacktester()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Sembol ve Timeframe seçimi
        symbol_layout = QHBoxLayout()
        symbol_layout.addWidget(QLabel("Sembol:"))
        self.symbol_combo = QComboBox()
        symbol_layout.addWidget(self.symbol_combo)
        
        symbol_layout.addWidget(QLabel("Timeframe:"))
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(['5m', '1h', '1d'])
        symbol_layout.addWidget(self.timeframe_combo)
        
        # Sembolleri yükle butonu
        self.load_symbols_btn = QPushButton("Sembolleri Yükle")
        self.load_symbols_btn.clicked.connect(self.load_symbols)
        symbol_layout.addWidget(self.load_symbols_btn)
        
        layout.addLayout(symbol_layout)
        
        # Optimizasyon parametreleri
        self.create_optimization_controls(layout)
        
        # Progress ve sonuçlar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        self.results_table = QTableWidget()
        layout.addWidget(self.results_table)
        
        self.setLayout(layout)
    
    def create_optimization_controls(self, layout):
        param_group = QGroupBox("MA Crossover Optimizasyon Parametreleri")
        param_layout = QVBoxLayout()
        
        # Short MA
        short_layout = QHBoxLayout()
        short_layout.addWidget(QLabel("Short MA:"))
        self.short_min = QSpinBox()
        self.short_min.setRange(1, 100)
        self.short_min.setValue(5)
        short_layout.addWidget(QLabel("Min:"))
        short_layout.addWidget(self.short_min)
        
        self.short_max = QSpinBox()
        self.short_max.setRange(1, 100)
        self.short_max.setValue(50)
        short_layout.addWidget(QLabel("Max:"))
        short_layout.addWidget(self.short_max)
        
        self.short_step = QSpinBox()
        self.short_step.setRange(1, 10)
        self.short_step.setValue(5)
        short_layout.addWidget(QLabel("Step:"))
        short_layout.addWidget(self.short_step)
        param_layout.addLayout(short_layout)
        
        # Long MA
        long_layout = QHBoxLayout()
        long_layout.addWidget(QLabel("Long MA:"))
        self.long_min = QSpinBox()
        self.long_min.setRange(10, 200)
        self.long_min.setValue(20)
        long_layout.addWidget(QLabel("Min:"))
        long_layout.addWidget(self.long_min)
        
        self.long_max = QSpinBox()
        self.long_max.setRange(10, 200)
        self.long_max.setValue(100)
        long_layout.addWidget(QLabel("Max:"))
        long_layout.addWidget(self.long_max)
        
        self.long_step = QSpinBox()
        self.long_step.setRange(5, 20)
        self.long_step.setValue(10)
        long_layout.addWidget(QLabel("Step:"))
        long_layout.addWidget(self.long_step)
        param_layout.addLayout(long_layout)
        
        # Risk Management
        risk_layout = QHBoxLayout()
        risk_layout.addWidget(QLabel("Stop Loss (%):"))
        self.stop_loss = QDoubleSpinBox()
        self.stop_loss.setRange(0.1, 10.0)
        self.stop_loss.setValue(2.0)
        self.stop_loss.setSingleStep(0.5)
        risk_layout.addWidget(self.stop_loss)
        
        risk_layout.addWidget(QLabel("Take Profit (%):"))
        self.take_profit = QDoubleSpinBox()
        self.take_profit.setRange(0.1, 15.0)
        self.take_profit.setValue(4.0)
        self.take_profit.setSingleStep(0.5)
        risk_layout.addWidget(self.take_profit)
        param_layout.addLayout(risk_layout)
        
        # Optimizasyon butonu
        self.optimize_btn = QPushButton("CUDA Optimizasyon Başlat")
        self.optimize_btn.clicked.connect(self.start_optimization)
        param_layout.addWidget(self.optimize_btn)
        
        param_group.setLayout(param_layout)
        layout.addWidget(param_group)
    
    def load_symbols(self):
        """Database'den sembolleri yükle"""
        symbols = self.db.get_available_symbols()
        self.symbol_combo.clear()
        self.symbol_combo.addItems(symbols)
        print(f"✅ {len(symbols)} sembol yüklendi")
    
    def start_optimization(self):
        """Optimizasyonu başlat"""
        symbol = self.symbol_combo.currentText()
        timeframe = self.timeframe_combo.currentText()
        
        if not symbol:
            print("❌ Lütfen sembol seçin!")
            return
        
        print(f"🎯 Optimizasyon başlatılıyor: {symbol} ({timeframe})")
        
        # Bu kısmı dolduralım database hazır olunca
        print("⏳ Database hazır olunca optimizasyon başlayacak...")