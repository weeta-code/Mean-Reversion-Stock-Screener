import streamlit as st
from app import QuantitativeStockScreener

# Ensure set_page_config is the first Streamlit command
st.set_page_config(
    page_title="Quantitative Stock Screener",
    page_icon="📊",
    layout="wide"
)

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
