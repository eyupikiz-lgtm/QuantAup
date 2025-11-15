# backtesting/cuda_optimized_backtester.py
import cupy as cp
import numpy as np
from numba import cuda
import pandas as pd

class OptimizedCUDABacktester:
    def __init__(self, initial_capital=100000, commission=0.001):
        self.initial_capital = initial_capital
        self.commission = commission
    
    @cuda.jit
    def ma_crossover_signals_cuda(prices, short_ma, long_ma, signals, stop_loss, take_profit):
        """CUDA kernel: MA crossover + stop loss/take profit"""
        i = cuda.grid(1)
        
        if i >= len(prices) or i < long_ma:
            return
        
        # MA crossover sinyali
        if short_ma[i] > long_ma[i] and short_ma[i-1] <= long_ma[i-1]:
            signals[i] = 1  # AL sinyali
        elif short_ma[i] < long_ma[i] and short_ma[i-1] >= long_ma[i-1]:
            signals[i] = -1  # SAT sinyali
        else:
            signals[i] = 0
        
        # Stop loss ve take profit (basit implementasyon)
        if i > 0 and signals[i-1] == 1:  # Açık long pozisyon
            price_change = (prices[i] - prices[i-1]) / prices[i-1]
            if price_change <= -stop_loss or price_change >= take_profit:
                signals[i] = -1  # Pozisyonu kapat
    
    def calculate_moving_averages_cuda(self, prices, short_window, long_window):
        """CUDA'da moving average hesapla"""
        prices_gpu = cp.asarray(prices, dtype=cp.float32)
        
        # Rolling window için padding
        short_ma = cp.convolve(prices_gpu, cp.ones(short_window)/short_window, mode='valid')
        long_ma = cp.convolve(prices_gpu, cp.ones(long_window)/long_window, mode='valid')
        
        # Padding ekle
        short_ma = cp.concatenate([cp.full(short_window-1, cp.nan), short_ma])
        long_ma = cp.concatenate([cp.full(long_window-1, cp.nan), long_ma])
        
        return short_ma, long_ma
    
    def run_optimized_backtest(self, data, short_window=10, long_window=30, 
                             stop_loss=0.02, take_profit=0.04):
        """Optimize edilmiş CUDA backtest"""
        print("🚀 CUDA Optimized Backtest başlatılıyor...")
        
        prices = data['Close'].values
        prices_gpu = cp.asarray(prices, dtype=cp.float32)
        
        # Moving averages hesapla
        short_ma, long_ma = self.calculate_moving_averages_cuda(prices, short_window, long_window)
        
        # Sinyaller için GPU array
        signals_gpu = cp.zeros_like(prices_gpu)
        
        # CUDA kernel konfigürasyonu
        threadsperblock = 256
        blockspergrid = (len(prices_gpu) + (threadsperblock - 1)) // threadsperblock
        
        # Kernel çalıştır
        self.ma_crossover_signals_cuda[blockspergrid, threadsperblock](
            prices_gpu, short_ma, long_ma, signals_gpu, stop_loss, take_profit
        )
        
        # Sonuçları CPU'ya getir
        signals = cp.asnumpy(signals_gpu)
        
        # Backtest results
        results = self.calculate_performance(data, signals)
        
        return results
    
    def calculate_performance(self, data, signals):
        """Performans metriklerini hesapla"""
        results = data.copy()
        results['Signal'] = signals
        results['Returns'] = results['Close'].pct_change()
        results['Strategy_Returns'] = results['Signal'].shift(1) * results['Returns']
        
        # Equity curve
        results['Cumulative_Strategy'] = (1 + results['Strategy_Returns']).cumprod()
        results['Portfolio_Value'] = self.initial_capital * results['Cumulative_Strategy']
        
        return results