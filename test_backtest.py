# test_backtest.py
import pandas as pd
import numpy as np
from database.bist_data_loader import BISTDatabaseManager
from backtesting.simple_backtester import SimpleBacktester

def test_backtest_detailed():
    """Detaylı backtest testi"""
    print("🧪 Detaylı Backtest Testi")
    print("=" * 50)
    
    # Database'den veri çek
    db = BISTDatabaseManager()
    
    # Farklı sembol ve timeframe'lerde test
    test_cases = [
        {'symbol': 'AKBNK', 'timeframe': '1d', 'name': 'AKBNK Günlük'},
        {'symbol': 'ZRGYO', 'timeframe': '1d', 'name': 'ZRGYO Günlük'},
        {'symbol': 'AKBNK', 'timeframe': '1h', 'name': 'AKBNK Saatlik'},
        {'symbol': 'AKBNK', 'timeframe': '5m', 'name': 'AKBNK 5 Dakika'}
    ]
    
    for test_case in test_cases:
        symbol = test_case['symbol']
        timeframe = test_case['timeframe']
        name = test_case['name']
        
        print(f"\n🔍 {name} Testi:")
        print("-" * 30)
        
        data = db.get_symbol_data(symbol, timeframe)
        
        if data is not None and not data.empty:
            print(f"✅ {symbol} ({timeframe}): {len(data):,} kayıt")
            
            # Backtest çalıştır
            backtester = SimpleBacktester(initial_capital=100000)
            results, trades = backtester.run_ma_crossover_backtest(
                data, 
                short_window=10, 
                long_window=30,
                stop_loss=0.02,
                take_profit=0.04
            )
            
            # Performans metrikleri
            metrics = backtester.calculate_performance_metrics(results, trades)
            
            # Sonuçları göster
            print(f"📊 {name} SONUÇLARI:")
            print(f"   💰 Strateji Getirisi: {metrics['total_return']:.2f}%")
            print(f"   📈 Buy & Hold Getirisi: {metrics['buy_hold_return']:.2f}%")
            print(f"   📉 Maksimum Drawdown: {metrics['max_drawdown']:.2f}%")
            print(f"   📊 Sharpe Oranı: {metrics['sharpe_ratio']:.2f}")
            print(f"   📈 İşlem Sayısı: {metrics['total_trades']}")
            print(f"   🎯 Win Rate: {metrics['win_rate']:.1f}%")
            print(f"   ⚡ Getiri Farkı: {metrics['total_return'] - metrics['buy_hold_return']:.2f}%")
            
            # Son 5 işlemi göster
            if trades:
                print(f"\n   📋 Son 5 İşlem:")
                for trade in trades[-5:]:
                    print(f"      {trade['date'].date()} - {trade['type']} - {trade['price']:.2f} - {trade.get('reason', '')}")
            
        else:
            print(f"❌ {symbol} ({timeframe}) verisi bulunamadı")

def compare_strategies():
    """Farklı strateji parametrelerini karşılaştır"""
    print("\n🎯 Strateji Karşılaştırması")
    print("=" * 50)
    
    db = BISTDatabaseManager()
    data = db.get_symbol_data('AKBNK', '1d')
    
    if data is not None:
        strategies = [
            {'name': 'Hızlı MA', 'short': 5, 'long': 20, 'stop': 0.015, 'tp': 0.03},
            {'name': 'Orta MA', 'short': 10, 'long': 30, 'stop': 0.02, 'tp': 0.04},
            {'name': 'Yavaş MA', 'short': 20, 'long': 50, 'stop': 0.025, 'tp': 0.05}
        ]
        
        backtester = SimpleBacktester(initial_capital=100000)
        
        print("🔍 Strateji Karşılaştırması:")
        print("-" * 50)
        
        for strategy in strategies:
            print(f"\n📊 {strategy['name']} Stratejisi:")
            results, trades = backtester.run_ma_crossover_backtest(
                data,
                short_window=strategy['short'],
                long_window=strategy['long'],
                stop_loss=strategy['stop'],
                take_profit=strategy['tp']
            )
            
            metrics = backtester.calculate_performance_metrics(results, trades)
            
            print(f"   MA({strategy['short']},{strategy['long']}) | SL:{strategy['stop']*100}% | TP:{strategy['tp']*100}%")
            print(f"   📈 Getiri: {metrics['total_return']:.2f}%")
            print(f"   📉 Drawdown: {metrics['max_drawdown']:.2f}%")
            print(f"   📊 Sharpe: {metrics['sharpe_ratio']:.2f}")
            print(f"   🎯 Win Rate: {metrics['win_rate']:.1f}%")

if __name__ == "__main__":
    # Detaylı backtest testi
    test_backtest_detailed()
    
    # Strateji karşılaştırması
    compare_strategies()