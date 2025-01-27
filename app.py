import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from typing import List
from data_acquisition import AdvancedStockDataProcessor
import numpy as np

class QuantitativeStockScreener:
    def __init__(self):
        self.data_processor = None
        self.stock_universe = []

    def initialize(self):
        self.data_processor = AdvancedStockDataProcessor()
        
        self.stock_universe = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", 
            "META", "TSLA", "NFLX", "INTC", "CSCO"
        ]

    def render_stock_screener(self):
        st.title("🚀 Advanced Quantitative Stock Screener")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            selected_stocks = st.multiselect(
                "Select Stocks", 
                self.stock_universe,
                default=self.stock_universe[:5]
            )
        
        with col2:
            volatility_threshold = st.slider(
                "Volatility Threshold (%)", 
                min_value=10.0, 
                max_value=100.0, 
                value=30.0
            )
        
        if not selected_stocks:
            st.warning("Please select at least one stock.")
            return
        
        # Screen high volatility stocks
        high_vol_stocks = self.data_processor.screen_high_volatility_stocks(
            selected_stocks, 
            volatility_threshold
        )
        
        if not high_vol_stocks:
            st.info("No stocks meet the high volatility criteria.")
            return
        
        self.render_stock_analysis(high_vol_stocks)

    def render_stock_analysis(self, stocks: List[str]):
        for ticker in stocks:
            with st.expander(f"📈 {ticker} Detailed Analysis"):
                self.render_stock_details(ticker)

    def render_stock_details(self, ticker: str):
        timeframe = ['1d']  
        historical_data = self.data_processor.fetch_historical_data(ticker, timeframes=timeframe)
        
        st.write(f"Available Timeframes for {ticker}: {list(historical_data.keys())}")
        
        preferred_order = ['1d']
        data = None
        selected_tf = None

        for tf in preferred_order:
            if tf in historical_data and not historical_data[tf].empty:
                data = historical_data[tf]
                selected_tf = tf
                break

        if data is None:
            st.warning(f"No historical data available for {ticker} in the specified timeframes.")
            return

        if 'Close' not in data.columns or data['Close'].empty:
            st.warning(f"'Close' data is unavailable for {ticker} in the '{selected_tf}' timeframe.")
            return

        try:
            # print(data['Close'].iloc[-1])
            row_series = data['Close'].iloc[-1]
            current_price = float(row_series.iloc[0])
             #print(current_price)
            if not isinstance(current_price, (float, int, np.floating, np.integer)):
                raise TypeError(f"'Close' price is not a numeric type: {type(current_price)}")
            st.metric("Current Price", f"${current_price:.2f}")
        except (IndexError, TypeError) as e:
            st.warning(f"Error accessing 'Close' price data: {e}")
            current_price = None

        try:
            current_rsi = data['RSI'].iloc[-1]
            if not isinstance(current_rsi, (float, int, np.floating, np.integer)):
                raise TypeError(f"RSI value is not numeric: {type(current_rsi)}")
            st.metric("1d RSI", f"{current_rsi:.2f}")
        except (IndexError, TypeError) as e:
            st.metric("1d RSI", "N/A")
            st.warning(f"Error accessing RSI data: {e}")

        # Handle Implied Volatility metric
        implied_vol = self.data_processor.calculate_implied_volatility(ticker)
        if not np.isnan(implied_vol):
            st.metric("Implied Volatility", f"{implied_vol:.2f}%")
        else:
            st.metric("Implied Volatility", "N/A")

        fig = self.create_interactive_chart(data, ticker, selected_tf)
        st.plotly_chart(fig, use_container_width=True)

    def create_interactive_chart(self, data: pd.DataFrame, ticker: str, timeframe: str):
        fig = go.Figure()
        
        # Candlestick chart
        fig.add_trace(go.Candlestick(
            x=data['Datetime'],
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name=ticker
        ))
        
        # Bollinger Bands
        fig.add_trace(go.Scatter(
            x=data.index, 
            y=data['BB_Upper'], 
            line=dict(color='green', width=1),
            name='Upper BB'
        ))
        fig.add_trace(go.Scatter(
            x=data.index, 
            y=data['BB_Middle'], 
            line=dict(color='blue', width=1),
            name='Middle BB'
        ))
        fig.add_trace(go.Scatter(
            x=data.index, 
            y=data['BB_Lower'], 
            line=dict(color='red', width=1),
            name='Lower BB'
        ))
        
        # RSI Subplot
        fig.add_trace(go.Scatter(
            x=data.index, 
            y=data['RSI'], 
            mode='lines',
            name='RSI',
            yaxis='y2'
        ))
        
        fig.update_layout(
            title=f'{ticker} Price and Indicators ({timeframe})',
            yaxis2=dict(
                title='RSI',
                overlaying='y',
                side='right'
            ),
            height=600
        )
        
        return fig

def main():
    st.sidebar.title("🔐 Quantitative Trading Interface")
    st.sidebar.write("No API Key needed. Data is fetched via yfinance.")
    
    # Create an instance of the QuantitativeStockScreener
    app = QuantitativeStockScreener()
    
    try:
        # Initialize (no key needed)
        app.initialize()
        st.success("Initialization successful! Use the options to explore data.")
        
        # *** This line actually shows the screener UI ***
        app.render_stock_screener()
    
    except Exception as e:
        st.error(f"Initialization failed: {str(e)}")

if __name__ == "__main__":
    main()
