# test_cuda_backtest.py
import pandas as pd
from database.bist_data_loader import BISTDatabaseManager
from backtesting.cuda_optimized_backtester import OptimizedCUDABacktester

def test_cuda_backtest():
    print("🚀 CUDA Backtest Testi...")
    
    # Database'den veri çek
    db = BISTDatabaseManager()
    
    # AKBNK ile test (veya başka bir sembol)
    symbol = "AKBNK"
    print(f"🔍 {symbol} verisi çekiliyor...")
    
    data = db.get_symbol_data(symbol, '5m')
    
    if data is None or data.empty:
        print("❌ Veri bulunamadı! Başka sembol deneyelim...")
        symbols = db.get_available_symbols()
        if symbols:
            symbol = symbols[0]
            print(f"🔍 {symbol} deneyelim...")
            data = db.get_symbol_data(symbol, '5m')
    
    if data is not None and not data.empty:
        print(f"✅ {symbol} verisi hazır: {len(data)} kayıt")
        
        # CUDA Backtester
        backtester = OptimizedCUDABacktester(initial_capital=100000)
        
        # Basit MA crossover backtest
        print("🔁 CUDA Backtest çalıştırılıyor...")
        results = backtester.run_optimized_backtest(
            data, 
            short_window=10, 
            long_window=30,
            stop_loss=0.02,
            take_profit=0.04
        )
        
        # Sonuçları göster
        final_value = results['Portfolio_Value'].iloc[-1]
        total_return = (final_value - 100000) / 1000
        max_drawdown = (results['Portfolio_Value'].max() - results['Portfolio_Value'].min()) / results['Portfolio_Value'].max() * 100
        
        print(f"💰 Başlangıç: 100,000 TL")
        print(f"💰 Son Portföy: {final_value:,.2f} TL")
        print(f"📈 Toplam Getiri: {total_return:.2f}%")
        print(f"📉 Maksimum Drawdown: {max_drawdown:.2f}%")
        print(f"📊 İşlem Sayısı: {len(results[results['Signal'] != 0])}")
        
        return results
    else:
        print("❌ Test için uygun veri bulunamadı!")
        return None

if __name__ == "__main__":
    results = test_cuda_backtest()