# backtesting/fast_optimizer.py
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

class FastOptimizer:
    def __init__(self, backtester):
        self.backtester = backtester
    
    def optimize_ma_parameters(self, data, param_ranges, max_workers=None):
        """Hızlı optimizasyon"""
        print("🚀 Hızlı optimizasyon başlatılıyor...")
        
        # Daha az kombinasyon ile hızlı optimizasyon
        combinations = self._generate_smart_combinations(param_ranges)
        total_combinations = len(combinations)
        
        print(f"🔍 {total_combinations} kombinasyon test edilecek")
        
        best_return = -float('inf')
        best_params = None
        best_metrics = None
        
        # Threading ile paralel execution
        with ThreadPoolExecutor(max_workers=min(4, total_combinations)) as executor:
            future_to_combo = {
                executor.submit(self._evaluate_single_combination, data.copy(), combo): combo 
                for combo in combinations
            }
            
            completed = 0
            for future in as_completed(future_to_combo):
                combo = future_to_combo[future]
                try:
                    metrics = future.result()
                    completed += 1
                    
                    if metrics and metrics.get('total_return', -999) > best_return:
                        best_return = metrics['total_return']
                        best_params = combo
                        best_metrics = metrics
                    
                    if completed % 5 == 0:
                        print(f"⏳ {completed}/{total_combinations} - En iyi: {best_return:.2f}%")
                        
                except Exception as e:
                    print(f"❌ Kombinasyon hatası: {e}")
                    continue
        
        print(f"✅ Optimizasyon tamamlandı! En iyi getiri: {best_return:.2f}%")
        return best_params, best_metrics
    
    def _generate_smart_combinations(self, param_ranges):
        """Akıllı parametre kombinasyonları"""
        combinations = []
        
        # Çok daha az kombinasyon
        short_range = param_ranges.get('short_window', [5, 10, 15])
        long_range = param_ranges.get('long_window', [20, 30, 50])
        stop_loss_range = param_ranges.get('stop_loss', [0.015, 0.02])
        take_profit_range = param_ranges.get('take_profit', [0.03, 0.04])
        
        for short in short_range:
            for long in long_range:
                if short >= long - 5:  # MA'lar arasında yeterli fark olmalı
                    continue
                for sl in stop_loss_range:
                    for tp in take_profit_range:
                        if tp > sl + 0.01:  # TP > SL + margin olmalı
                            combinations.append({
                                'short_window': short,
                                'long_window': long,
                                'stop_loss': sl,
                                'take_profit': tp
                            })
        
        return combinations[:16]  # Maksimum 16 kombinasyon
    
    def _evaluate_single_combination(self, data, params):
        """Tek kombinasyon değerlendirme"""
        try:
            results, trades = self.backtester.run_ma_crossover_backtest(data, **params)
            if results is not None and not results.empty:
                metrics = self.backtester.calculate_performance_metrics(results, trades)
                return metrics
        except Exception as e:
            print(f"Kombinasyon değerlendirme hatası: {e}")
        return None