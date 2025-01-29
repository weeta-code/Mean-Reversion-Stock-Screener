import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import yfinance as yf
import numpy as np
from plotly.subplots import make_subplots
import time


# Data Pulling, Processing, Technical Indication Creation


def fetch_stock_data(ticker, period, interval):
    data = yf.download(ticker, period=period, interval=interval)
    return data

def process_data(data):
    if data.index.tzinfo is None:
        data.index = data.index.tz_localize('UTC')
    data.index = data.index.tz_convert('US/Eastern')
    data.reset_index(inplace=True)
    data.rename(columns={'Date': 'Datetime'}, inplace=True)
    return data

# Basic but necessary information for display/indication calculator
def series_to_float(series):
    """Given a 1-element Series, return its float value."""
    return float(series.iloc[0])

def calculate_metrics(data):
    last_close_series = data['Close'].iloc[-1]
    last_close = series_to_float(last_close_series)

    first_close_series = data['Close'].iloc[0]
    first_close = series_to_float(first_close_series)

    change = last_close - first_close
    pct_change = (change / first_close) * 100

    # For High/Low, check if they're already floats.
    high_val = data['High'].max()
    if not isinstance(high_val, (int, float, np.number)):
        high_val = float(high_val.iloc[0])  # if it's also a single-row Series

    low_val = data['Low'].min()
    if not isinstance(low_val, (int, float, np.number)):
        low_val = float(low_val.iloc[0])

    vol_series = data['Volume'].sum()
    volume_val = float(vol_series.iloc[0])
    return last_close, change, pct_change, high_val, low_val, volume_val




def calculate_rsi(data, periods=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=periods, min_periods=1).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periods, min_periods=1).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_bollinger_bands(
        prices: pd.Series, 
        window: int = 20, 
        num_std: float = 2.0
    ):
        rolling_mean = prices.rolling(window=window, min_periods=0).mean()
        rolling_std = prices.rolling(window=window, min_periods=0).std()
        
        upper_band = rolling_mean + (num_std * rolling_std)
        lower_band = rolling_mean - (num_std * rolling_std)
        
        return upper_band, rolling_mean, lower_band

# Assistant tools and what we want to screen for in stocks
def add_technical_indicators(data):
    rsi = calculate_rsi(data['Close']).fillna(0)
    data['RSI'] = rsi
    data['UpperBand'], data['MiddleBand'], data['LowerBand'] = calculate_bollinger_bands(data['Close'], 20, 2.0)
    return data


# Mostly Front-end things such as creating out Layout

st.set_page_config(layout='wide')
st.title('Mean Reversion Stock Screener')

 
# Sidebar parametric values

st.sidebar.header('Chart Parameters')
ticker = st.sidebar.text_input('Ticker', 'AAPL')
chart_type = st.sidebar.selectbox('Chart Type', ['Candlestick', 'Line'])
tp = st.sidebar.selectbox('Time Period', ['1d', '1wk', '1mo', '1y', 'max'])
indicators = st.sidebar.multiselect('Technical Indicators', ['RSI', 'Bollinger Bands'])

# Interval Mapping for time periods(tp)
interval_mapping = {
    '1d' : '5m',
    '1wk' : '30m',
    '1mo' : '1d',
    '1y' : '1wk',
    'max' : '1wk'
}

# Dashboard Updating

data = fetch_stock_data(ticker, tp, interval_mapping[tp])
data = process_data(data)
data = add_technical_indicators(data)
last_close, change, pct_change, high, low, volume = calculate_metrics(data)
data.columns = data.columns.droplevel(1)

st.metric(
        label=f"{ticker} Last Price",
        value=f"{last_close:,.2f} USD",
        delta=f"{change:,.2f} ({pct_change:,.2f}%)"
    )

col1, col2, col3 = st.columns(3)
col1.metric("High", f"{high:,.2f} USD")
col2.metric("Low", f"{low:,.2f} USD")
col3.metric("Volume", f"{volume:,}")

    # Plotting the chart
fig = make_subplots(
    rows=2, cols=1,
    shared_xaxes=True,
    row_heights=[0.7, 0.3],      
    vertical_spacing=0.2        
)
if chart_type == 'Candlestick':
        fig.add_trace(go.Candlestick(
            x=data['Datetime'],
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name='Price'
        ), 
        row=1, col=1
)   
else:
        fig.add_trace(
        go.Scatter(
        x=data['Datetime'],
        y=data['Close'],
        name='Close Price'
        ), 
        row=1, col=1
)

      
    
for indicator in indicators:
        if indicator == 'RSI':
            fig.add_trace(
                go.Scatter(
                x=data['Datetime'],
                y=data['RSI'],
                name='RSI',
                line=dict(color='purple')
            ),
            row=2, col=1
    )
        elif indicator == 'Bollinger Bands':
            print(data['Datetime'])
            fig.add_trace(go.Scatter(x=data['Datetime'], y=data['UpperBand'], name='Upper Band'), row=1, col=1)
            fig.add_trace(go.Scatter(x=data['Datetime'], y=data['MiddleBand'], name='Middle Band'), row=1, col=1)
            fig.add_trace(go.Scatter(x=data['Datetime'], y=data['LowerBand'], name='Lower Band'), row=1, col=1)

fig.update_layout(xaxis_rangeslider_visible=False, 
                      title=f'{ticker.upper()} {tp.upper()} Chart',
                      yaxis_title='Price (USD)',
                      yaxis2_title='RSI',
                      height=700)
st.plotly_chart(fig, use_container_width=True)

    # Historical data display & technical indicators
st.subheader('Historical Data')
st.dataframe(data[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']])

st.subheader('Technical indicators')
st.dataframe(data[['Datetime', 'RSI', 'UpperBand', 'MiddleBand', 'LowerBand']])


# Sidebar section for real-time pricing of selected symbols
st.sidebar.header('Real-Time Price Action')
stock_symbols = ['AAPL', 'GOOGL', 'AMZN', 'MSFT', 'NVDA', 'ARM', 'CRM']
for symbol in stock_symbols:
    real_time_data = fetch_stock_data(symbol, '1d', '5m')
    if not real_time_data.empty:
        real_time_data = process_data(real_time_data)
        last_price_series = real_time_data['Close'].iloc[-1]
        last_price = series_to_float(last_price_series)
        first_price_series = real_time_data['Close'].iloc[0]
        first_price = series_to_float(first_price_series)
        change = last_price - first_price
        pct_change_series = (change/real_time_data['Open'].iloc[0]) * 100
        pct_change = series_to_float(pct_change_series)        
        st.sidebar.metric(f"{symbol}", f"{last_price:.2f} USD", f"{change:.2f} ({pct_change:.2f}%)")


st.sidebar.subheader('About')
st.sidebar.info('This screener provides analytical information about tickers of your own choosing allowing you to form a watchlist of stocks that match your needs.')