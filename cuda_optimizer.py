# optimization/cuda_optimizer.py
import cupy as cp
import numpy as np
import pandas as pd
from itertools import product
from tqdm import tqdm

class CUDAStrategyOptimizer:
    def __init__(self, backtester):
        self.backtester = backtester
    
    def optimize_ma_strategy(self, data, param_grid):
        """Moving Average stratejisi için CUDA optimizasyonu"""
        print("🎯 CUDA Optimizasyon başlatılıyor...")
        
        # Parametre kombinasyonları
        short_windows = param_grid.get('short_window', range(5, 51, 5))
        long_windows = param_grid.get('long_window', range(20, 201, 10))
        stop_losses = param_grid.get('stop_loss', [0.01, 0.015, 0.02, 0.025, 0.03])
        take_profits = param_grid.get('take_profit', [0.02, 0.03, 0.04, 0.05, 0.06])
        
        best_score = -np.inf
        best_params = None
        best_results = None
        
        # CUDA ile paralel optimizasyon
        total_combinations = len(short_windows) * len(long_windows) * len(stop_losses) * len(take_profits)
        
        print(f"🔍 {total_combinations} kombinasyon test edilecek...")
        
        with tqdm(total=total_combinations) as pbar:
            for short_win in short_windows:
                for long_win in long_windows:
                    if short_win >= long_win:
                        continue
                    
                    for stop_loss in stop_losses:
                        for take_profit in take_profits:
                            if take_profit <= stop_loss:
                                continue
                            
                            # Strateji oluştur
                            strategy = AdvancedMAStrategy(
                                short_window=short_win,
                                long_window=long_win,
                                stop_loss=stop_loss,
                                take_profit=take_profit
                            )
                            
                            # Backtest çalıştır
                            signals = strategy.generate_signals(data)
                            results = self.backtester.run_backtest(data, signals)
                            
                            # Lineerlik skoru hesapla
                            score = self.calculate_linearity_score(results)
                            
                            if score > best_score:
                                best_score = score
                                best_params = {
                                    'short_window': short_win,
                                    'long_window': long_win,
                                    'stop_loss': stop_loss,
                                    'take_profit': take_profit
                                }
                                best_results = results
                            
                            pbar.update(1)
        
        print(f"✅ Optimizasyon tamamlandı! En iyi skor: {best_score:.4f}")
        return best_params, best_results, best_score
    
    def calculate_linearity_score(self, results):
        """Getiri eğrisinin lineerlik skorunu hesapla"""
        portfolio_values = results['Portfolio_Value'].values
        time_index = np.arange(len(portfolio_values))
        
        # Lineer regresyon
        slope, intercept = np.polyfit(time_index, portfolio_values, 1)
        linear_fit = slope * time_index + intercept
        
        # R-squared (lineerlik ölçütü)
        ss_res = np.sum((portfolio_values - linear_fit) ** 2)
        ss_tot = np.sum((portfolio_values - np.mean(portfolio_values)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        # Drawdown cezası
        max_drawdown = self.calculate_max_drawdown(portfolio_values)
        drawdown_penalty = max(0, max_drawdown - 0.1) * 10  # %10'dan fazla drawdown cezası
        
        # Sharpe oranı bonusu
        returns = results['Strategy_Returns'].dropna()
        sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252) if len(returns) > 0 else 0
        sharpe_bonus = max(0, sharpe) * 0.1
        
        final_score = r_squared - drawdown_penalty + sharpe_bonus
        return final_score
    
    def calculate_max_drawdown(self, portfolio_values):
        """Maksimum drawdown hesapla"""
        peak = np.maximum.accumulate(portfolio_values)
        drawdown = (peak - portfolio_values) / peak
        return np.max(drawdown)