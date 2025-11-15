# ui/optimization_panel.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                           QLabel, QLineEdit, QPushButton, QProgressBar,
                           QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import QThread, pyqtSignal
import pandas as pd

class OptimizationThread(QThread):
    finished = pyqtSignal(dict, object, float)
    progress = pyqtSignal(int)
    
    def __init__(self, optimizer, data, param_grid):
        super().__init__()
        self.optimizer = optimizer
        self.data = data
        self.param_grid = param_grid
    
    def run(self):
        best_params, best_results, best_score = self.optimizer.optimize_ma_strategy(
            self.data, self.param_grid
        )
        self.finished.emit(best_params, best_results, best_score)

class OptimizationPanel(QWidget):
    def __init__(self, db_manager, backtester):
        super().__init__()
        self.db = db_manager
        self.backtester = backtester
        self.optimizer = CUDAStrategyOptimizer(backtester)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Parametre aralıkları
        param_group = QGroupBox("Optimizasyon Parametreleri")
        param_layout = QVBoxLayout()
        
        # Short MA aralığı
        short_layout = QHBoxLayout()
        short_layout.addWidget(QLabel("Short MA:"))
        self.short_min = QLineEdit("5")
        self.short_max = QLineEdit("50")
        self.short_step = QLineEdit("5")
        short_layout.addWidget(QLabel("Min:"))
        short_layout.addWidget(self.short_min)
        short_layout.addWidget(QLabel("Max:"))
        short_layout.addWidget(self.short_max)
        short_layout.addWidget(QLabel("Step:"))
        short_layout.addWidget(self.short_step)
        param_layout.addLayout(short_layout)
        
        # Long MA aralığı
        long_layout = QHBoxLayout()
        long_layout.addWidget(QLabel("Long MA:"))
        self.long_min = QLineEdit("20")
        self.long_max = QLineEdit("200")
        self.long_step = QLineEdit("10")
        long_layout.addWidget(QLabel("Min:"))
        long_layout.addWidget(self.long_min)
        long_layout.addWidget(QLabel("Max:"))
        long_layout.addWidget(self.long_max)
        long_layout.addWidget(QLabel("Step:"))
        long_layout.addWidget(self.long_step)
        param_layout.addLayout(long_layout)
        
        # Stop Loss/Take Profit
        risk_layout = QHBoxLayout()
        risk_layout.addWidget(QLabel("Stop Loss (%):"))
        self.stop_loss_values = QLineEdit("1.0,1.5,2.0,2.5,3.0")
        risk_layout.addWidget(self.stop_loss_values)
        risk_layout.addWidget(QLabel("Take Profit (%):"))
        self.take_profit_values = QLineEdit("2.0,3.0,4.0,5.0,6.0")
        risk_layout.addWidget(self.take_profit_values)
        param_layout.addLayout(risk_layout)
        
        param_group.setLayout(param_layout)
        layout.addWidget(param_group)
        
        # Kontroller
        control_layout = QHBoxLayout()
        self.optimize_btn = QPushButton("Optimizasyon Başlat")
        self.optimize_btn.clicked.connect(self.start_optimization)
        self.progress_bar = QProgressBar()
        
        control_layout.addWidget(self.optimize_btn)
        control_layout.addWidget(self.progress_bar)
        layout.addLayout(control_layout)
        
        # Sonuçlar tablosu
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            'Short MA', 'Long MA', 'Stop Loss', 'Take Profit', 
            'Lineerlik Skor', 'Toplam Getiri'
        ])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.results_table)
        
        self.setLayout(layout)
    
    def start_optimization(self):
        """Optimizasyonu başlat"""
        # Parametre grid oluştur
        param_grid = {
            'short_window': range(
                int(self.short_min.text()), 
                int(self.short_max.text()) + 1, 
                int(self.short_step.text())
            ),
            'long_window': range(
                int(self.long_min.text()), 
                int(self.long_max.text()) + 1, 
                int(self.long_step.text())
            ),
            'stop_loss': [x/100 for x in map(float, self.stop_loss_values.text().split(','))],
            'take_profit': [x/100 for x in map(float, self.take_profit_values.text().split(','))]
        }
        
        # Veriyi yükle (örnek olarak AKBNK)
        data = self.db.get_symbol_data('AKBNK', '5m')
        
        if data is None:
            print("❌ Veri bulunamadı!")
            return
        
        # Optimizasyon thread'ini başlat
        self.optimization_thread = OptimizationThread(self.optimizer, data, param_grid)
        self.optimization_thread.finished.connect(self.on_optimization_finished)
        self.optimization_thread.start()
        
        self.optimize_btn.setEnabled(False)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
    
    def on_optimization_finished(self, best_params, best_results, best_score):
        """Optimizasyon tamamlandığında"""
        self.optimize_btn.setEnabled(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        
        # Sonuçları tabloya ekle
        row_position = self.results_table.rowCount()
        self.results_table.insertRow(row_position)
        
        self.results_table.setItem(row_position, 0, QTableWidgetItem(str(best_params['short_window'])))
        self.results_table.setItem(row_position, 1, QTableWidgetItem(str(best_params['long_window'])))
        self.results_table.setItem(row_position, 2, QTableWidgetItem(f"{best_params['stop_loss']*100:.1f}%"))
        self.results_table.setItem(row_position, 3, QTableWidgetItem(f"{best_params['take_profit']*100:.1f}%"))
        self.results_table.setItem(row_position, 4, QTableWidgetItem(f"{best_score:.4f}"))
        
        total_return = (best_results['Portfolio_Value'].iloc[-1] - 100000) / 1000
        self.results_table.setItem(row_position, 5, QTableWidgetItem(f"{total_return:.2f}%"))
        
        print(f"✅ Optimizasyon tamamlandı! En iyi parametreler: {best_params}")