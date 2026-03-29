import streamlit as st
import pandas as pd
from finviz.screener import Screener

# Konfiguration
st.set_page_config(page_title="Ariel Finviz Alpha", layout="wide")

@st.cache_data(ttl=3600)
def run_finviz_scan():
    """Nutzt die finviz-library für einen Profi-Scan."""
    # Filter-Logik (Ariel / Minervini / Ryan):
    # idx_sp500 = S&P 500
    # ta_sma200_pa = Preis über 200-Tage-Linie (Stage 2 Basis)
    # ta_sma50_pa = Preis über 50-Tage-Linie (Kurzfristiges Momentum)
    # ta_highlow52w_nh = Neues 52-Wochen-Hoch (Optional, für Zanger-Stil)
    
    filters = ['idx_sp500', 'ta_sma200_pa', 'ta_sma50_pa'] 
    
    try:
        # Wir rufen die Performance-Tabelle ab
        stock_list = Screener(filterlist=filters, table='Performance', order='-perf13w')
        
        # In Pandas DataFrame umwandeln
        df = pd.DataFrame(stock_list.data)
        return df
    except Exception as e:
        st.error(f"Fehler beim Finviz-Abruf: {e}")
        return pd.DataFrame()

st.title("🏹 Ariel & Ryan: Finviz Leader-Scanner")
st.markdown("Scant den **S&P 500** nach den stärksten Aktien (Stage 2 + Momentum).")

if st.button('🚀 Markt-Scan ausführen'):
    with st.spinner('Lese Finviz-Daten aus...'):
        df = run_finviz_scan()
        
        if not df.empty:
            # Spalten-Bereinigung für das Dashboard
            # 'Perf Quart' ist unser RS-Score Ersatz
            df['RS Score'] = df['Perf Quart'].str.replace('%', '').astype(float)
            
            # Leaderboard sortieren
            df_final = df.sort_values(by='RS Score', ascending=False)
            
            st.subheader("Top Momentum Leader (Quarterly Performance)")
            
            # Wichtige Spalten für das 15-Minuten-Ritual
            display_cols = ['Ticker', 'Price', 'RS Score', 'Perf Month', 'Perf Year', 'Volatility']
            
            # Styling: Grün für hohe RS-Werte
            st.dataframe(
                df_final[display_cols].style.background_gradient(subset=['RS Score'], cmap='RdYlGn'),
                use_container_width=True,
                height=600
            )
            
            # Export für TradingView
            ticker_list = ",".join(df_final['Ticker'].tolist())
            st.text_area("TradingView Watchlist (Copy-Paste):", ticker_list)
            
            st.success("Scan erfolgreich. Diese Aktien zeigen die stärkste relative Stärke im S&P 500.")
        else:
            st.warning("Keine Daten gefunden oder Finviz blockiert die IP. Versuche es später erneut.")
