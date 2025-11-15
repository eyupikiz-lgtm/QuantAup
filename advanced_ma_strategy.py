# strategies/advanced_ma_strategy.py
import pandas as pd
import numpy as np
import cupy as cp
from numba import cuda

class AdvancedMAStrategy:
    def __init__(self, short_window=10, long_window=30, 
                 stop_loss=0.02, take_profit=0.04, trailing_stop=0.015):
        self.short_window = short_window
        self.long_window = long_window
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.trailing_stop = trailing_stop
        
    def generate_signals(self, data):
        """CUDA ile hızlandırılmış sinyal üretimi"""
        closes = cp.asarray(data['Close'].values, dtype=cp.float32)
        
        # CUDA'da MA hesaplama
        sma_short = self.rolling_mean_cuda(closes, self.short_window)
        sma_long = self.rolling_mean_cuda(closes, self.long_window)
        
        # Sinyal üretimi
        signals = cp.zeros_like(closes)
        positions = cp.zeros_like(closes)
        
        # CUDA kernel ile sinyal hesaplama
        self.calculate_signals_cuda[256, 256](closes, sma_short, sma_long, 
                                            signals, positions,
                                            self.stop_loss, self.take_profit)
        
        # Stop loss/take profit uygula
        signals_with_stops = self.apply_risk_management_cuda(
            closes, signals, positions, self.stop_loss, self.take_profit
        )
        
        return cp.asnumpy(signals_with_stops)
    
    @cuda.jit
    def calculate_signals_cuda(closes, sma_short, sma_long, signals, positions,
                             stop_loss, take_profit):
        i = cuda.grid(1)
        if i >= len(closes) - 1 or i < max(short_window, long_window):
            return
        
        # Moving Average crossover
        if sma_short[i] > sma_long[i] and sma_short[i-1] <= sma_long[i-1]:
            signals[i] = 1  # AL
            positions[i] = closes[i]  # Giriş fiyatı
            
        elif sma_short[i] < sma_long[i] and sma_short[i-1] >= sma_long[i-1]:
            signals[i] = -1  # SAT
            positions[i] = 0
    
    def apply_risk_management_cuda(self, closes, signals, positions, stop_loss, take_profit):
        """CUDA ile risk yönetimi"""
        managed_signals = signals.copy()
        
        # Stop loss ve take profit kontrolü
        for i in range(len(closes)):
            if positions[i] > 0:  # Açık pozisyon var
                current_price = closes[i]
                entry_price = positions[i]
                
                # Take Profit kontrolü
                if (current_price - entry_price) / entry_price >= take_profit:
                    managed_signals[i] = -1  # Kar realizasyonu
                    positions[i] = 0
                
                # Stop Loss kontrolü
                elif (entry_price - current_price) / entry_price >= stop_loss:
                    managed_signals[i] = -1  # Stop loss tetiklendi
                    positions[i] = 0
        
        return managed_signals