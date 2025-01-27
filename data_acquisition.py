import pandas as pd
import numpy as np
import yfinance as yf
from typing import List, Dict

class AdvancedStockDataProcessor:
    def __init__(self):
        """
        Advanced stock data processor using yfinance 
        """
        pass

    def calculate_implied_volatility(self, ticker: str) -> float:
        try:
            stock = yf.Ticker(ticker)
            options = stock.option_chain()
            
            # Compute weighted average implied volatility across calls + puts
            call_ivs = options.calls['impliedVolatility']
            put_ivs = options.puts['impliedVolatility']
            
            weighted_iv = np.nanmean(np.concatenate([call_ivs, put_ivs]))
            return weighted_iv * 100  
        except Exception:
            return np.nan

    def fetch_historical_data(
        self, 
        ticker: str, 
        timeframes: List[str] = ['15m', '1h', '1d'],
    ) -> Dict[str, pd.DataFrame]:
        
        timeframe_period_mapping = {
            '15m': '1d',    
            '1h': '5d',     
            '1d': '1mo',    
        }
        
        historical_data = {}
        
        for tf in timeframes:
            period = timeframe_period_mapping.get(tf, '1d')
            data = yf.download(ticker, period=period, interval=tf)
            
            
            if data.empty:
                print(f"Warning: No data fetched for {ticker} with interval {tf} and period {period}.")
                continue 
            
            # Our indicators / strategy
            data['RSI'] = self._calculate_rsi(data['Close'])
            (data['BB_Upper'], 
             data['BB_Middle'], 
             data['BB_Lower']) = self._calculate_bollinger_bands(data['Close'])
            
            historical_data[tf] = data
        
        return historical_data

    def _calculate_rsi(self, prices: pd.Series, periods: int = 14) -> pd.Series:
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
        
        relative_strength = gain / loss
        rsi = 100.0 - (100.0 / (1.0 + relative_strength))
        
        return rsi

    def _calculate_bollinger_bands(
        self, 
        prices: pd.Series, 
        window: int = 20, 
        num_std: float = 2.0
    ):
        rolling_mean = prices.rolling(window=window).mean()
        rolling_std = prices.rolling(window=window).std()
        
        upper_band = rolling_mean + (num_std * rolling_std)
        lower_band = rolling_mean - (num_std * rolling_std)
        
        return upper_band, rolling_mean, lower_band

    def screen_high_volatility_stocks(
        self, 
        universe: List[str], 
        volatility_threshold: float = 30.0
    ) -> List[str]:
        high_vol_stocks = [
            ticker for ticker in universe 
            if self.calculate_implied_volatility(ticker) > volatility_threshold
        ]
        
        return high_vol_stocks
