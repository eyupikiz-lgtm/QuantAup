# backtesting/simple_backtester.py
import pandas as pd
import numpy as np

class SimpleBacktester:
    def __init__(self, initial_capital=100000, commission=0.001):
        self.initial_capital = initial_capital
        self.commission = commission
    
    def run_ma_crossover_backtest(self, data, short_window=10, long_window=30, 
                                stop_loss=0.02, take_profit=0.04):
        """Moving Average Crossover backtest - KÜÇÜK HARF DÜZELTMESİ"""
        print(f"🔁 Backtest çalıştırılıyor: MA({short_window},{long_window})")
        
        # Sütun isimlerini kontrol et ve küçük harfe çevir
        data = data.copy()
        data.columns = [col.lower() for col in data.columns]  # ✅ KÜÇÜK HARF
        
        # Moving Average hesapla
        data['sma_short'] = data['close'].rolling(window=short_window).mean()
        data['sma_long'] = data['close'].rolling(window=long_window).mean()
        
        # Sinyaller
        data['signal'] = 0
        data['position'] = 0
        
        # Backtest logic
        in_position = False
        entry_price = 0
        portfolio_value = self.initial_capital
        cash = self.initial_capital
        shares = 0
        
        portfolio_values = []
        trades = []
        
        print(f"📊 Veri uzunluğu: {len(data)} kayıt")
        print(f"📅 Tarih aralığı: {data.index[0].date()} - {data.index[-1].date()}")
        
        for i in range(long_window, len(data)):
            current_price = data['close'].iloc[i]
            sma_short = data['sma_short'].iloc[i]
            sma_long = data['sma_long'].iloc[i]
            prev_sma_short = data['sma_short'].iloc[i-1]
            prev_sma_long = data['sma_long'].iloc[i-1]
            
            # AL sinyali
            if not in_position and sma_short > sma_long and prev_sma_short <= prev_sma_long:
                # AL
                shares = cash / current_price
                cash = 0
                entry_price = current_price
                in_position = True
                data['signal'].iloc[i] = 1
                data['position'].iloc[i] = shares
                trades.append({
                    'date': data.index[i],
                    'type': 'BUY',
                    'price': current_price,
                    'shares': shares
                })
                print(f"📈 {data.index[i].date()} - AL: {current_price:.2f}")
            
            # SAT sinyali veya risk yönetimi
            elif in_position:
                price_change = (current_price - entry_price) / entry_price
                
                # Take Profit
                if price_change >= take_profit:
                    data['signal'].iloc[i] = -1
                    trades.append({
                        'date': data.index[i],
                        'type': 'SELL',
                        'price': current_price,
                        'shares': shares,
                        'reason': 'TAKE_PROFIT',
                        'pnl': price_change * 100
                    })
                    print(f"💰 {data.index[i].date()} - Take Profit: {current_price:.2f} (+{price_change*100:.1f}%)")
                
                # Stop Loss
                elif price_change <= -stop_loss:
                    data['signal'].iloc[i] = -1  
                    trades.append({
                        'date': data.index[i],
                        'type': 'SELL', 
                        'price': current_price,
                        'shares': shares,
                        'reason': 'STOP_LOSS',
                        'pnl': price_change * 100
                    })
                    print(f"🛑 {data.index[i].date()} - Stop Loss: {current_price:.2f} ({price_change*100:.1f}%)")
                
                # SAT sinyali
                elif sma_short < sma_long and prev_sma_short >= prev_sma_long:
                    data['signal'].iloc[i] = -1
                    trades.append({
                        'date': data.index[i],
                        'type': 'SELL',
                        'price': current_price, 
                        'shares': shares,
                        'reason': 'MA_CROSSOVER',
                        'pnl': price_change * 100
                    })
                    print(f"📉 {data.index[i].date()} - SAT: {current_price:.2f}")
                
                # Pozisyonu kapat
                if data['signal'].iloc[i] == -1:
                    cash = shares * current_price * (1 - self.commission)
                    shares = 0
                    in_position = False
                    data['position'].iloc[i] = 0
            
            # Portfolio değeri
            if in_position:
                portfolio_value = shares * current_price
            else:
                portfolio_value = cash
            
            portfolio_values.append(portfolio_value)
        
        # Sonuçları ekle
        data = data.iloc[long_window:].copy()
        data['portfolio_value'] = portfolio_values
        data['returns'] = data['portfolio_value'].pct_change()
        
        return data, trades

    def calculate_performance_metrics(self, results, trades):
        """Performans metriklerini hesapla"""
        initial_value = self.initial_capital
        final_value = results['portfolio_value'].iloc[-1]
        total_return = (final_value - initial_value) / initial_value * 100
        
        # Buy & Hold getirisi
        buy_hold_return = (results['close'].iloc[-1] - results['close'].iloc[0]) / results['close'].iloc[0] * 100
        
        # Volatilite ve Sharpe
        returns = results['returns'].dropna()
        volatility = returns.std() * np.sqrt(252) * 100  # Yıllık volatilite
        sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252) if len(returns) > 0 else 0
        
        # Drawdown
        portfolio_values = results['portfolio_value']
        peak = portfolio_values.expanding().max()
        drawdown = (peak - portfolio_values) / peak
        max_drawdown = drawdown.max() * 100
        
        # İşlem istatistikleri
        total_trades = len(trades)
        buy_trades = len([t for t in trades if t['type'] == 'BUY'])
        sell_trades = len([t for t in trades if t['type'] == 'SELL'])
        
        # Kazanç/kayıp oranı
        profitable_trades = len([t for t in trades if t.get('pnl', 0) > 0])
        win_rate = profitable_trades / sell_trades * 100 if sell_trades > 0 else 0
        
        metrics = {
            'total_return': total_return,
            'buy_hold_return': buy_hold_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'total_trades': total_trades,
            'buy_trades': buy_trades,
            'sell_trades': sell_trades,
            'win_rate': win_rate
        }
        
        return metrics