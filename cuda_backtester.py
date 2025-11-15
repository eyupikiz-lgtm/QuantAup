# backtesting/cuda_backtester.py
import pandas as pd
import numpy as np
try:
    import cupy as cp
    CUDA_AVAILABLE = True
    print("✅ CUDA aktif!")
except ImportError:
    CUDA_AVAILABLE = False
    print("❌ CUDA kullanılamıyor - CPU modu")
    import numpy as cp

class CUDABacktester:
    def __init__(self, initial_capital=100000, commission=0.001):
        self.initial_capital = initial_capital
        self.commission = commission
    
    def run_ma_crossover_backtest(self, data, short_window=10, long_window=30, 
                                stop_loss=0.02, take_profit=0.04):
        """Optimize edilmiş MA Crossover backtest"""
        print(f"🚀 Backtest başlatılıyor: MA({short_window},{long_window})")
        
        # Veriyi hazırla
        data = data.copy()
        data.columns = [col.lower() for col in data.columns]
        
        return self._run_optimized_cpu_backtest(data, short_window, long_window, stop_loss, take_profit)
    
    def _run_optimized_cpu_backtest(self, data, short_window, long_window, stop_loss, take_profit):
        """Optimize edilmiş CPU backtest - DÜZELTİLMİŞ"""
        if len(data) < long_window:
            return data, []
        
        data = data.copy()
        
        # Sütunları float olarak oluştur
        data['sma_short'] = data['close'].rolling(window=short_window, min_periods=1).mean()
        data['sma_long'] = data['close'].rolling(window=long_window, min_periods=1).mean()
        data['signal'] = 0.0  # ✅ Float olarak başlat
        data['position'] = 0.0  # ✅ Float olarak başlat
        
        # Backtest variables
        in_position = False
        entry_price = 0.0
        cash = float(self.initial_capital)
        shares = 0.0
        
        portfolio_values = []
        trades = []
        
        for i in range(len(data)):
            if i < long_window - 1:
                portfolio_values.append(cash)
                continue
                
            current_price = float(data['close'].iloc[i])
            sma_short = float(data['sma_short'].iloc[i])
            sma_long = float(data['sma_long'].iloc[i])
            
            if i > long_window - 1:
                prev_sma_short = float(data['sma_short'].iloc[i-1])
                prev_sma_long = float(data['sma_long'].iloc[i-1])
            else:
                prev_sma_short = sma_short
                prev_sma_long = sma_long
            
            # AL sinyali - MA crossover
            if (not in_position and 
                sma_short > sma_long and 
                prev_sma_short <= prev_sma_long):
                
                # AL işlemi
                shares = cash / current_price
                cash = 0.0
                entry_price = current_price
                in_position = True
                
                # ✅ Dtype uyumlu atama
                data.loc[data.index[i], 'signal'] = 1.0
                data.loc[data.index[i], 'position'] = float(shares)
                
                trades.append({
                    'date': data.index[i],
                    'type': 'BUY',
                    'price': current_price,
                    'shares': shares,
                    'reason': 'MA_CROSSOVER'
                })
            
            # SAT sinyali veya risk yönetimi
            elif in_position:
                price_change = (current_price - entry_price) / entry_price
                should_sell = False
                reason = ''
                
                # Take Profit
                if price_change >= take_profit:
                    should_sell = True
                    reason = 'TAKE_PROFIT'
                # Stop Loss
                elif price_change <= -stop_loss:
                    should_sell = True
                    reason = 'STOP_LOSS'
                # SAT sinyali - MA crossover
                elif (sma_short < sma_long and 
                      prev_sma_short >= prev_sma_long):
                    should_sell = True
                    reason = 'MA_CROSSOVER'
                
                if should_sell:
                    # SAT işlemi
                    cash = shares * current_price * (1 - self.commission)
                    pnl_percent = price_change * 100
                    shares = 0.0
                    in_position = False
                    
                    # ✅ Dtype uyumlu atama
                    data.loc[data.index[i], 'signal'] = -1.0
                    data.loc[data.index[i], 'position'] = 0.0
                    
                    trades.append({
                        'date': data.index[i],
                        'type': 'SELL',
                        'price': current_price,
                        'shares': shares,
                        'reason': reason,
                        'pnl': pnl_percent
                    })
            
            # Portfolio değeri
            if in_position:
                portfolio_value = shares * current_price
            else:
                portfolio_value = cash
            
            portfolio_values.append(float(portfolio_value))
        
        # Portfolio değerlerini ekle - dtype uyumlu
        if len(portfolio_values) == len(data):
            data['portfolio_value'] = portfolio_values
        else:
            # Uzunluk farkı varsa padding yap
            padding = [float(cash)] * (len(data) - len(portfolio_values))
            data['portfolio_value'] = padding + portfolio_values
        
        # Returns sütununu float olarak oluştur
        data['returns'] = data['portfolio_value'].pct_change().fillna(0.0).astype(float)
        
        return data, trades
    
    def calculate_performance_metrics(self, results, trades):
        """Performans metrikleri"""
        if results.empty or 'portfolio_value' not in results.columns:
            return {
                'total_return': 0.0,
                'buy_hold_return': 0.0,
                'volatility': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'total_trades': 0,
                'buy_trades': 0,
                'sell_trades': 0,
                'win_rate': 0.0
            }
            
        try:
            initial_value = float(self.initial_capital)
            final_value = float(results['portfolio_value'].iloc[-1])
            total_return = (final_value - initial_value) / initial_value * 100.0
            
            # Buy & Hold
            buy_hold_return = (float(results['close'].iloc[-1]) - float(results['close'].iloc[0])) / float(results['close'].iloc[0]) * 100.0
            
            # Risk metrikleri
            returns = results['returns'].replace([np.inf, -np.inf], 0.0).fillna(0.0).astype(float)
            if len(returns) > 1 and returns.std() > 0:
                volatility = float(returns.std() * np.sqrt(252) * 100)
                sharpe = float(np.mean(returns) / np.std(returns) * np.sqrt(252))
            else:
                volatility = 0.0
                sharpe = 0.0
            
            # Drawdown
            portfolio_values = results['portfolio_value'].astype(float)
            peak = portfolio_values.expanding().max()
            drawdown = (peak - portfolio_values) / peak
            max_drawdown = float(drawdown.max() * 100.0)
            
            # İşlem istatistikleri
            buy_trades = [t for t in trades if t['type'] == 'BUY']
            sell_trades = [t for t in trades if t['type'] == 'SELL']
            profitable_trades = len([t for t in sell_trades if t.get('pnl', 0) > 0])
            win_rate = float(profitable_trades / len(sell_trades) * 100.0) if sell_trades else 0.0
            
            return {
                'total_return': float(total_return),
                'buy_hold_return': float(buy_hold_return),
                'volatility': float(volatility),
                'sharpe_ratio': float(sharpe),
                'max_drawdown': float(max_drawdown),
                'total_trades': int(len(trades)),
                'buy_trades': int(len(buy_trades)),
                'sell_trades': int(len(sell_trades)),
                'win_rate': float(win_rate)
            }
            
        except Exception as e:
            print(f"Metrik hesaplama hatası: {e}")
            return {
                'total_return': 0.0,
                'buy_hold_return': 0.0,
                'volatility': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'total_trades': 0,
                'buy_trades': 0,
                'sell_trades': 0,
                'win_rate': 0.0
            }