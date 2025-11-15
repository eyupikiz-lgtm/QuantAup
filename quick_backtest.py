# quick_backtest.py
from database.bist_data_loader import BISTDatabaseManager
from backtesting.simple_backtester import SimpleBacktester

def quick_test():
    """Hızlı backtest testi"""
    print("⚡ Hızlı Backtest Testi")
    print("=" * 50)
    
    db = BISTDatabaseManager()
    
    # AKBNK günlük verisi ile test
    data = db.get_symbol_data('AKBNK', '1d')
    
    if data is not None:
        print(f"✅ AKBNK Günlük verisi: {len(data)} kayıt")
        
        backtester = SimpleBacktester(initial_capital=100000)
        results, trades = backtester.run_ma_crossover_backtest(
            data, 
            short_window=10, 
            long_window=30,
            stop_loss=0.02,
            take_profit=0.04
        )
        
        metrics = backtester.calculate_performance_metrics(results, trades)
        
        print(f"\n🎉 BACKTEST SONUÇLARI:")
        print(f"💰 Başlangıç: 100,000 TL")
        print(f"💰 Son Portföy: {results['portfolio_value'].iloc[-1]:,.0f} TL")
        print(f"📈 Toplam Getiri: {metrics['total_return']:.2f}%")
        print(f"📈 Buy & Hold: {metrics['buy_hold_return']:.2f}%")
        print(f"📉 Max Drawdown: {metrics['max_drawdown']:.2f}%")
        print(f"📊 İşlem Sayısı: {metrics['total_trades']}")
        print(f"🎯 Win Rate: {metrics['win_rate']:.1f}%")
        
        return True
    else:
        print("❌ Veri bulunamadı!")
        return False

if __name__ == "__main__":
    quick_test()