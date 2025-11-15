# backtesting/parallel_optimizer.py
import pandas as pd
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp
from tqdm import tqdm

class ParallelOptimizer:
    def __init__(self, backtester):
        self.backtester = backtester
    
    def optimize_ma_parameters(self, data, param_ranges, max_workers=None):
        """GERÇEK Parallel optimizasyon"""
        if max_workers is None:
            max_workers = mp.cpu_count()
        
        print(f"🚀 PARALLEL Optimizasyon ({max_workers} core)")
        
        combinations = self._generate_combinations_from_ranges(param_ranges)
        total_combinations = len(combinations)
        
        print(f"🔍 {total_combinations} kombinasyon - {max_workers} parallel işlem")
        
        # Data'yı worker'lar için hazırla
        data_dict = {
            'open': data['open'].values,
            'high': data['high'].values, 
            'low': data['low'].values,
            'close': data['close'].values,
            'volume': data['volume'].values,
            'index': data.index
        }
        
        best_return = -999999.0
        best_params = None
        best_metrics = None
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._evaluate_combination_worker, data_dict, combo): combo 
                for combo in combinations
            }
            
            with tqdm(total=total_combinations, desc="Optimizasyon") as pbar:
                for future in as_completed(futures):
                    combo = futures[future]
                    try:
                        metrics = future.result()
                        pbar.update(1)
                        
                        if metrics and metrics.get('total_return', -999999) > best_return:
                            best_return = metrics['total_return']
                            best_params = combo
                            best_metrics = metrics
                            pbar.set_postfix(best=f"{best_return:.2f}%")
                            
                    except Exception as e:
                        pbar.update(1)
                        continue
        
        print(f"✅ Optimizasyon tamamlandı! En iyi: {best_return:.2f}%")
        return best_params, best_metrics
    
    def _generate_combinations_from_ranges(self, param_ranges):
        """Aralıklardan kombinasyon üret"""
        combinations = []
        
        short_range = range(
            param_ranges['short_min'], 
            param_ranges['short_max'] + 1, 
            param_ranges['short_step']
        )
        
        long_range = range(
            param_ranges['long_min'],
            param_ranges['long_max'] + 1,
            param_ranges['long_step'] 
        )
        
        stop_loss_range = np.arange(
            param_ranges['sl_min'] / 100,
            param_ranges['sl_max'] / 100 + 0.001,
            param_ranges['sl_step'] / 100
        )
        
        take_profit_range = np.arange(
            param_ranges['tp_min'] / 100, 
            param_ranges['tp_max'] / 100 + 0.001,
            param_ranges['tp_step'] / 100
        )
        
        for short in short_range:
            for long in long_range:
                if short >= long - 5:
                    continue
                for sl in stop_loss_range:
                    for tp in take_profit_range:
                        if tp > sl + 0.01:
                            combinations.append({
                                'short_window': short,
                                'long_window': long,
                                'stop_loss': round(sl, 3),
                                'take_profit': round(tp, 3)
                            })
        
        return combinations
    
    def _evaluate_combination_worker(self, data_dict, params):
        """Worker process için backtest"""
        try:
            # Data'yı yeniden oluştur
            data = pd.DataFrame({
                'open': data_dict['open'],
                'high': data_dict['high'],
                'low': data_dict['low'], 
                'close': data_dict['close'],
                'volume': data_dict['volume']
            }, index=data_dict['index'])
            
            results, trades = self.backtester.run_ma_crossover_backtest(data, **params)
            metrics = self.backtester.calculate_performance_metrics(results, trades)
            return metrics
        except:
            return None