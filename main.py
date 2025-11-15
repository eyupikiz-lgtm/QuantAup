# main.py
import sys
import pandas as pd
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                           QWidget, QPushButton, QComboBox, QTextEdit, QTabWidget,
                           QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QProgressBar,
                           QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
                           QSplitter, QFrame, QMessageBox)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont, QPalette, QColor
import pyqtgraph as pg
import warnings

# Uyarıları gizle
warnings.filterwarnings('ignore')

from database.bist_data_loader import BISTDatabaseManager
from backtesting.cuda_backtester import CUDABacktester

class BacktestThread(QThread):
    """Backtest işlemi için thread"""
    finished = pyqtSignal(object, object, object)  # results, trades, metrics
    progress = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, backtester, data, params):
        super().__init__()
        self.backtester = backtester
        self.data = data
        self.params = params
    
    def run(self):
        try:
            self.progress.emit("Backtest başlatılıyor...")
            results, trades = self.backtester.run_ma_crossover_backtest(
                self.data, **self.params
            )
            
            self.progress.emit("Performans metrikleri hesaplanıyor...")
            metrics = self.backtester.calculate_performance_metrics(results, trades)
            
            self.finished.emit(results, trades, metrics)
            
        except Exception as e:
            self.error.emit(str(e))

class OptimizationThread(QThread):
    """Optimizasyon işlemi için thread"""
    finished = pyqtSignal(object, object)  # best_params, best_metrics
    progress = pyqtSignal(int, str)
    
    def __init__(self, optimizer, data, param_ranges):
        super().__init__()
        self.optimizer = optimizer
        self.data = data
        self.param_ranges = param_ranges
    
    def run(self):
        try:
            best_params, best_metrics = self.optimizer.optimize_ma_parameters(
                self.data, self.param_ranges
            )
            self.finished.emit(best_params, best_metrics)
        except Exception as e:
            print(f"Optimizasyon thread hatası: {e}")
            self.finished.emit(None, None)

class TradingPlatform(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = BISTDatabaseManager()
        self.backtester = CUDABacktester()
        self.current_results = None
        self.current_metrics = None
        
        self.init_ui()
        self.load_initial_data()
    
    def init_ui(self):
        """Arayüzü başlat"""
        self.setWindowTitle("BIST Trading Platform - GPU Optimizasyon")
        self.setGeometry(100, 50, 1600, 900)
        
        # Ana widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Ana layout
        main_layout = QHBoxLayout(central_widget)
        
        # Sol panel - Kontroller
        left_panel = self.create_left_panel()
        left_panel.setMaximumWidth(450)
        
        # Sağ panel - Grafikler ve sonuçlar
        right_panel = self.create_right_panel()
        
        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 1200])
        
        main_layout.addWidget(splitter)
    
    def create_left_panel(self):
        """Sol kontrol paneli"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Başlık
        title = QLabel("BIST Trading Platform")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Sembol seçimi
        symbol_group = QGroupBox("Sembol Seçimi")
        symbol_layout = QVBoxLayout(symbol_group)
        
        symbol_row = QHBoxLayout()
        symbol_row.addWidget(QLabel("Sembol:"))
        self.symbol_combo = QComboBox()
        self.load_symbols_btn = QPushButton("Yükle")
        self.load_symbols_btn.clicked.connect(self.load_symbols)
        symbol_row.addWidget(self.symbol_combo)
        symbol_row.addWidget(self.load_symbols_btn)
        symbol_layout.addLayout(symbol_row)
        
        timeframe_row = QHBoxLayout()
        timeframe_row.addWidget(QLabel("Timeframe:"))
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(['1d', '1h', '5m'])
        timeframe_row.addWidget(self.timeframe_combo)
        symbol_layout.addLayout(timeframe_row)
        
        layout.addWidget(symbol_group)
        
        # Strateji parametreleri
        strategy_group = QGroupBox("MA Crossover Stratejisi")
        strategy_layout = QVBoxLayout(strategy_group)
        
        # Short MA
        short_layout = QHBoxLayout()
        short_layout.addWidget(QLabel("Short MA:"))
        self.short_ma = QSpinBox()
        self.short_ma.setRange(1, 100)
        self.short_ma.setValue(10)
        short_layout.addWidget(self.short_ma)
        strategy_layout.addLayout(short_layout)
        
        # Long MA
        long_layout = QHBoxLayout()
        long_layout.addWidget(QLabel("Long MA:"))
        self.long_ma = QSpinBox()
        self.long_ma.setRange(1, 200)
        self.long_ma.setValue(30)
        long_layout.addWidget(self.long_ma)
        strategy_layout.addLayout(long_layout)
        
        # Stop Loss
        sl_layout = QHBoxLayout()
        sl_layout.addWidget(QLabel("Stop Loss (%):"))
        self.stop_loss = QDoubleSpinBox()
        self.stop_loss.setRange(0.1, 10.0)
        self.stop_loss.setValue(2.0)
        self.stop_loss.setSingleStep(0.5)
        sl_layout.addWidget(self.stop_loss)
        strategy_layout.addLayout(sl_layout)
        
        # Take Profit
        tp_layout = QHBoxLayout()
        tp_layout.addWidget(QLabel("Take Profit (%):"))
        self.take_profit = QDoubleSpinBox()
        self.take_profit.setRange(0.1, 15.0)
        self.take_profit.setValue(4.0)
        self.take_profit.setSingleStep(0.5)
        tp_layout.addWidget(self.take_profit)
        strategy_layout.addLayout(tp_layout)
        
        layout.addWidget(strategy_group)
        
        # Optimizasyon parametreleri
        optimization_group = self.create_optimization_controls()
        layout.addWidget(optimization_group)
        
        # İşlem butonları
        buttons_group = QGroupBox("İşlemler")
        buttons_layout = QVBoxLayout(buttons_group)
        
        self.backtest_btn = QPushButton("Backtest Çalıştır")
        self.backtest_btn.clicked.connect(self.run_backtest)
        buttons_layout.addWidget(self.backtest_btn)
        
        self.optimize_btn = QPushButton("GPU Optimizasyon Başlat")
        self.optimize_btn.clicked.connect(self.run_optimization)
        buttons_layout.addWidget(self.optimize_btn)
        
        layout.addWidget(buttons_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Durum mesajı
        self.status_label = QLabel("Hazır")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        return panel
    
    def create_optimization_controls(self):
        """Optimizasyon parametre kontrolleri"""
        optimization_group = QGroupBox("Optimizasyon Ayarları")
        optimization_layout = QVBoxLayout(optimization_group)
        
        # Short MA aralığı
        short_range_layout = QHBoxLayout()
        short_range_layout.addWidget(QLabel("Short MA:"))
        self.short_min = QSpinBox()
        self.short_min.setRange(1, 50)
        self.short_min.setValue(5)
        self.short_max = QSpinBox()
        self.short_max.setRange(10, 100)
        self.short_max.setValue(20)
        self.short_step = QSpinBox()
        self.short_step.setRange(1, 10)
        self.short_step.setValue(3)
        
        short_range_layout.addWidget(QLabel("Min:"))
        short_range_layout.addWidget(self.short_min)
        short_range_layout.addWidget(QLabel("Max:"))
        short_range_layout.addWidget(self.short_max)
        short_range_layout.addWidget(QLabel("Step:"))
        short_range_layout.addWidget(self.short_step)
        optimization_layout.addLayout(short_range_layout)
        
        # Long MA aralığı
        long_range_layout = QHBoxLayout()
        long_range_layout.addWidget(QLabel("Long MA:"))
        self.long_min = QSpinBox()
        self.long_min.setRange(20, 100)
        self.long_min.setValue(25)
        self.long_max = QSpinBox()
        self.long_max.setRange(30, 200)
        self.long_max.setValue(60)
        self.long_step = QSpinBox()
        self.long_step.setRange(5, 20)
        self.long_step.setValue(10)
        
        long_range_layout.addWidget(QLabel("Min:"))
        long_range_layout.addWidget(self.long_min)
        long_range_layout.addWidget(QLabel("Max:"))
        long_range_layout.addWidget(self.long_max)
        long_range_layout.addWidget(QLabel("Step:"))
        long_range_layout.addWidget(self.long_step)
        optimization_layout.addLayout(long_range_layout)
        
        # Stop Loss aralığı
        sl_layout = QHBoxLayout()
        sl_layout.addWidget(QLabel("Stop Loss (%):"))
        self.sl_min = QDoubleSpinBox()
        self.sl_min.setRange(0.5, 5.0)
        self.sl_min.setValue(1.0)
        self.sl_max = QDoubleSpinBox()
        self.sl_max.setRange(1.0, 10.0)
        self.sl_max.setValue(3.0)
        self.sl_step = QDoubleSpinBox()
        self.sl_step.setRange(0.5, 2.0)
        self.sl_step.setValue(0.5)
        
        sl_layout.addWidget(QLabel("Min:"))
        sl_layout.addWidget(self.sl_min)
        sl_layout.addWidget(QLabel("Max:"))
        sl_layout.addWidget(self.sl_max)
        sl_layout.addWidget(QLabel("Step:"))
        sl_layout.addWidget(self.sl_step)
        optimization_layout.addLayout(sl_layout)
        
        # Take Profit aralığı
        tp_layout = QHBoxLayout()
        tp_layout.addWidget(QLabel("Take Profit (%):"))
        self.tp_min = QDoubleSpinBox()
        self.tp_min.setRange(1.0, 10.0)
        self.tp_min.setValue(2.0)
        self.tp_max = QDoubleSpinBox()
        self.tp_max.setRange(2.0, 20.0)
        self.tp_max.setValue(6.0)
        self.tp_step = QDoubleSpinBox()
        self.tp_step.setRange(0.5, 2.0)
        self.tp_step.setValue(1.0)
        
        tp_layout.addWidget(QLabel("Min:"))
        tp_layout.addWidget(self.tp_min)
        tp_layout.addWidget(QLabel("Max:"))
        tp_layout.addWidget(self.tp_max)
        tp_layout.addWidget(QLabel("Step:"))
        tp_layout.addWidget(self.tp_step)
        optimization_layout.addLayout(tp_layout)
        
        return optimization_group
    
    def create_right_panel(self):
        """Sağ panel - Grafikler ve sonuçlar"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Tab widget
        self.tabs = QTabWidget()
        
        # Equity Curve tab
        self.equity_tab = QWidget()
        equity_layout = QVBoxLayout(self.equity_tab)
        
        # PyQtGraph grafikleri
        self.equity_plot = pg.PlotWidget(title="Portföy Performansı")
        self.equity_plot.addLegend()
        self.equity_plot.setLabel('left', 'Portföy Değeri (TL)')
        self.equity_plot.setLabel('bottom', 'Tarih')
        equity_layout.addWidget(self.equity_plot)
        
        self.tabs.addTab(self.equity_tab, "Equity Curve")
        
        # Performans tab
        self.performance_tab = QWidget()
        performance_layout = QVBoxLayout(self.performance_tab)
        
        # Performans metrikleri
        metrics_group = QGroupBox("Performans Metrikleri")
        metrics_layout = QVBoxLayout(metrics_group)
        
        self.metrics_text = QTextEdit()
        self.metrics_text.setMaximumHeight(200)
        metrics_layout.addWidget(self.metrics_text)
        
        performance_layout.addWidget(metrics_group)
        
        # İşlemler tablosu
        trades_group = QGroupBox("İşlem Geçmişi")
        trades_layout = QVBoxLayout(trades_group)
        
        self.trades_table = QTableWidget()
        self.trades_table.setColumnCount(6)
        self.trades_table.setHorizontalHeaderLabels([
            'Tarih', 'İşlem', 'Fiyat', 'Adet', 'Sebep', 'Kar/Zarar (%)'
        ])
        trades_layout.addWidget(self.trades_table)
        
        performance_layout.addWidget(trades_group)
        
        self.tabs.addTab(self.performance_tab, "Performans")
        
        # Optimizasyon tab
        self.optimization_tab = QWidget()
        optimization_layout = QVBoxLayout(self.optimization_tab)
        
        # Optimizasyon sonuçları
        optimization_results_group = QGroupBox("Optimizasyon Sonuçları")
        optimization_results_layout = QVBoxLayout(optimization_results_group)
        
        self.optimization_text = QTextEdit()
        optimization_results_layout.addWidget(self.optimization_text)
        
        optimization_layout.addWidget(optimization_results_group)
        
        self.tabs.addTab(self.optimization_tab, "Optimizasyon")
        
        layout.addWidget(self.tabs)
        
        return panel
    
    def load_initial_data(self):
        """Başlangıç verilerini yükle"""
        self.load_symbols()
    
    def load_symbols(self):
        """Sembolleri yükle"""
        try:
            symbols = self.db.get_available_symbols()
            self.symbol_combo.clear()
            self.symbol_combo.addItems(symbols)
            self.status_label.setText(f"{len(symbols)} sembol yüklendi")
        except Exception as e:
            self.show_error(f"Semboller yüklenirken hata: {e}")
    
    def run_backtest(self):
        """Backtest çalıştır"""
        symbol = self.symbol_combo.currentText()
        timeframe = self.timeframe_combo.currentText()
        
        if not symbol:
            self.show_error("Lütfen sembol seçin!")
            return
        
        # Parametreleri al
        params = {
            'short_window': self.short_ma.value(),
            'long_window': self.long_ma.value(),
            'stop_loss': self.stop_loss.value() / 100,
            'take_profit': self.take_profit.value() / 100
        }
        
        # Veriyi al
        data = self.db.get_symbol_data(symbol, timeframe)
        if data is None or data.empty:
            self.show_error(f"{symbol} verisi bulunamadı!")
            return
        
        # Thread başlat
        self.backtest_thread = BacktestThread(self.backtester, data, params)
        self.backtest_thread.progress.connect(self.update_progress)
        self.backtest_thread.finished.connect(self.on_backtest_finished)
        self.backtest_thread.error.connect(self.show_error)
        
        self.backtest_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Backtest çalışıyor...")
        
        self.backtest_thread.start()
    
    def run_optimization(self):
        """Optimizasyon çalıştır"""
        symbol = self.symbol_combo.currentText()
        timeframe = self.timeframe_combo.currentText()
        
        if not symbol:
            self.show_error("Lütfen sembol seçin!")
            return
        
        # Arayüzden parametre aralıklarını al
        param_ranges = {
            'short_min': self.short_min.value(),
            'short_max': self.short_max.value(),
            'short_step': self.short_step.value(),
            'long_min': self.long_min.value(), 
            'long_max': self.long_max.value(),
            'long_step': self.long_step.value(),
            'sl_min': self.sl_min.value(),
            'sl_max': self.sl_max.value(), 
            'sl_step': self.sl_step.value(),
            'tp_min': self.tp_min.value(),
            'tp_max': self.tp_max.value(),
            'tp_step': self.tp_step.value()
        }
        
        # Kombinasyon sayısını kontrol et
        combinations = self._calculate_combinations(param_ranges)
        if combinations > 500:
            reply = QMessageBox.question(
                self, 'Çok Fazla Kombinasyon', 
                f'{combinations} kombinasyon var. Devam etmek istiyor musunuz?\n(Bu işlem birkaç dakika sürebilir)',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Veriyi al
        data = self.db.get_symbol_data(symbol, timeframe)
        if data is None or data.empty:
            self.show_error(f"{symbol} verisi bulunamadı!")
            return
        
        # Fast optimizer kullan (şimdilik basit versiyon)
        from backtesting.fast_optimizer import FastOptimizer
        optimizer = FastOptimizer(self.backtester)
        
        # Thread başlat
        self.optimization_thread = OptimizationThread(optimizer, data, param_ranges)
        self.optimization_thread.progress.connect(self.update_optimization_progress)
        self.optimization_thread.finished.connect(self.on_optimization_finished)
        
        self.optimize_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText(f"Optimizasyon başlatıldı ({combinations} kombinasyon)")
        self.tabs.setCurrentIndex(2)
        
        self.optimization_thread.start()
    
    def _calculate_combinations(self, param_ranges):
        """Kombinasyon sayısını hesapla"""
        short_count = len(range(param_ranges['short_min'], param_ranges['short_max'] + 1, param_ranges['short_step']))
        long_count = len(range(param_ranges['long_min'], param_ranges['long_max'] + 1, param_ranges['long_step']))
        sl_count = len(np.arange(param_ranges['sl_min']/100, param_ranges['sl_max']/100 + 0.001, param_ranges['sl_step']/100))
        tp_count = len(np.arange(param_ranges['tp_min']/100, param_ranges['tp_max']/100 + 0.001, param_ranges['tp_step']/100))
        
        total = short_count * long_count * sl_count * tp_count
        return total
    
    def update_progress(self, message):
        """Progress güncelle"""
        self.status_label.setText(message)
    
    def update_optimization_progress(self, percent, message):
        """Optimizasyon progress güncelle"""
        self.progress_bar.setValue(percent)
        self.status_label.setText(message)
    
    def on_backtest_finished(self, results, trades, metrics):
        """Backtest tamamlandığında"""
        self.backtest_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Backtest tamamlandı")
        
        self.current_results = results
        self.current_metrics = metrics
        
        # Grafikleri çiz
        self.plot_results(results, trades)
        
        # Metrikleri göster
        self.show_metrics(metrics)
        
        # İşlemleri göster
        self.show_trades(trades)
        
        self.tabs.setCurrentIndex(0)  # Equity curve tab'ına geç
    
    def on_optimization_finished(self, best_params, best_metrics):
        """Optimizasyon tamamlandığında"""
        self.optimize_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Optimizasyon tamamlandı")
        
        if best_params and best_metrics:
            # Optimizasyon sonuçlarını göster
            result_text = f"🎯 EN İYİ PARAMETRELER:\n"
            result_text += f"Short MA: {best_params['short_window']}\n"
            result_text += f"Long MA: {best_params['long_window']}\n"
            result_text += f"Stop Loss: {best_params['stop_loss']*100:.1f}%\n"
            result_text += f"Take Profit: {best_params['take_profit']*100:.1f}%\n\n"
            
            result_text += f"📊 PERFORMANS:\n"
            result_text += f"Toplam Getiri: {best_metrics['total_return']:.2f}%\n"
            result_text += f"Buy & Hold: {best_metrics['buy_hold_return']:.2f}%\n"
            result_text += f"Maksimum Drawdown: {best_metrics['max_drawdown']:.2f}%\n"
            result_text += f"Sharpe Oranı: {best_metrics['sharpe_ratio']:.2f}\n"
            result_text += f"Win Rate: {best_metrics['win_rate']:.1f}%"
            
            self.optimization_text.setText(result_text)
            
            # Parametreleri güncelle
            self.short_ma.setValue(best_params['short_window'])
            self.long_ma.setValue(best_params['long_window'])
            self.stop_loss.setValue(best_params['stop_loss'] * 100)
            self.take_profit.setValue(best_params['take_profit'] * 100)
            
        else:
            self.optimization_text.setText("Optimizasyon sonucu bulunamadı!")
    
    def plot_results(self, results, trades):
        """Basit ve güvenli grafik çizimi"""
        try:
            self.equity_plot.clear()
            
            # Portfolio değeri
            equity_curve = self.equity_plot.plot(
                results.index, 
                results['portfolio_value'], 
                pen=pg.mkPen('#00ff00', width=2), 
                name='Portföy Değeri'
            )
            
            # Buy & Hold karşılaştırması
            initial_value = self.backtester.initial_capital
            buy_hold_value = (results['close'] / results['close'].iloc[0]) * initial_value
            buy_hold_curve = self.equity_plot.plot(
                results.index,
                buy_hold_value,
                pen=pg.mkPen('#1f77b4', width=1, style=pg.QtCore.Qt.PenStyle.DashLine),
                name='Buy & Hold'
            )
            
            # AL/SAT sinyalleri
            buy_signals = results[results['signal'] == 1]
            sell_signals = results[results['signal'] == -1]
            
            if len(buy_signals) > 0:
                buy_scatter = pg.ScatterPlotItem(
                    buy_signals.index, 
                    buy_signals['portfolio_value'],
                    pen=pg.mkPen('#00ff00'), 
                    brush=pg.mkBrush('#00ff00'), 
                    size=12,
                    symbol='t', 
                    name='AL'
                )
                self.equity_plot.addItem(buy_scatter)
            
            if len(sell_signals) > 0:
                sell_scatter = pg.ScatterPlotItem(
                    sell_signals.index,
                    sell_signals['portfolio_value'],
                    pen=pg.mkPen('#ff0000'), 
                    brush=pg.mkBrush('#ff0000'), 
                    size=12,
                    symbol='t1', 
                    name='SAT'
                )
                self.equity_plot.addItem(sell_scatter)
            
            self.equity_plot.addLegend()
            self.equity_plot.setLabel('left', 'Portföy Değeri (TL)')
            self.equity_plot.setLabel('bottom', 'Tarih')
            
            if self.current_metrics:
                self.equity_plot.setTitle(f"Backtest Sonuçları - Getiri: {self.current_metrics.get('total_return', 0):.2f}%")
                
        except Exception as e:
            print(f"Grafik çizim hatası: {e}")
            self.show_error(f"Grafik oluşturulamadı: {e}")
    
    def show_metrics(self, metrics):
        """Performans metriklerini göster"""
        if not metrics:
            self.metrics_text.setText("Metrikler hesaplanamadı")
            return
            
        text = f"""
💰 PORTFÖY PERFORMANSI:
------------------------
Toplam Getiri: {metrics.get('total_return', 0):.2f}%
Buy & Hold Getirisi: {metrics.get('buy_hold_return', 0):.2f}%
Getiri Farkı: {metrics.get('total_return', 0) - metrics.get('buy_hold_return', 0):.2f}%

📊 RİSK METRİKLERİ:
------------------------
Maksimum Drawdown: {metrics.get('max_drawdown', 0):.2f}%
Yıllık Volatilite: {metrics.get('volatility', 0):.2f}%
Sharpe Oranı: {metrics.get('sharpe_ratio', 0):.2f}

🎯 İŞLEM İSTATİSTİKLERİ:
------------------------
Toplam İşlem: {metrics.get('total_trades', 0)}
AL İşlemleri: {metrics.get('buy_trades', 0)}
SAT İşlemleri: {metrics.get('sell_trades', 0)}
Win Rate: {metrics.get('win_rate', 0):.1f}%
        """
        self.metrics_text.setText(text)
    
    def show_trades(self, trades):
        """İşlem geçmişini göster"""
        self.trades_table.setRowCount(len(trades))
        
        for row, trade in enumerate(trades):
            self.trades_table.setItem(row, 0, QTableWidgetItem(str(trade['date'].date())))
            self.trades_table.setItem(row, 1, QTableWidgetItem(trade['type']))
            self.trades_table.setItem(row, 2, QTableWidgetItem(f"{trade['price']:.2f}"))
            self.trades_table.setItem(row, 3, QTableWidgetItem(f"{trade.get('shares', 0):.0f}"))
            self.trades_table.setItem(row, 4, QTableWidgetItem(trade.get('reason', '')))
            self.trades_table.setItem(row, 5, QTableWidgetItem(f"{trade.get('pnl', 0):.1f}%" if trade.get('pnl') else ""))
        
        self.trades_table.resizeColumnsToContents()
    
    def show_error(self, message):
        """Hata mesajı göster"""
        self.backtest_btn.setEnabled(True)
        self.optimize_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Hata oluştu")
        
        QMessageBox.critical(self, "Hata", message)

def main():
    app = QApplication(sys.argv)
    
    # Dark theme
    app.setStyle('Fusion')
    
    window = TradingPlatform()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()