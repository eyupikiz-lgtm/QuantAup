# backtesting/portfolio_backtester.py
import pandas as pd
import numpy as np
from database.db_manager import DatabaseManager

class PortfolioBacktester:
    def __init__(self, db_manager):
        self.db = db_manager
    
    def run_portfolio_backtest(self, symbols, strategy_class, params, start_date, end_date):
        """Portfolio seviyesinde backtest"""
        print(f"📊 Portfolio Backtest: {len(symbols)} sembol")
        
        portfolio_results = {}
        
        for symbol in symbols:
            print(f"🔍 {symbol} analiz ediliyor...")
            
            # Veriyi çek
            data = self.db.get_symbol_data(symbol, start_date, end_date)
            
            if data is not None:
                # Stratejiyi uygula
                strategy = strategy_class(**params)
                signals = strategy.generate_signals(data)
                
                # Backtest çalıştır
                backtester = CUDABacktester()
                results = backtester.run_backtest(data, signals)
                
                portfolio_results[symbol] = results
        
        # Portfolio aggregate hesapla
        portfolio_equity = self.calculate_portfolio_equity(portfolio_results)
        
        return portfolio_results, portfolio_equity
    
    def calculate_portfolio_equity(self, portfolio_results):
        """Portfolio equity curve hesapla"""
        # Tüm sembollerin getirilerini birleştir
        all_returns = pd.DataFrame()
        
        for symbol, results in portfolio_results.items():
            if 'Strategy_Returns' in results:
                all_returns[symbol] = results['Strategy_Returns']
        
        # Eşit ağırlıklı portfolio
        portfolio_returns = all_returns.mean(axis=1)
        portfolio_equity = (1 + portfolio_returns).cumprod() * 100000
        
        return portfolio_equity