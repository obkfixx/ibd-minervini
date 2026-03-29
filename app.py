import streamlit as st
import pandas as pd
from finviz.screener import Screener

# Konfiguration
st.set_page_config(page_title="Ariel Finviz Alpha", layout="wide")

@st.cache_data(ttl=3600)
def run_finviz_scan(index_filter):
    """Nutzt die finviz-library mit Fehlerbehandlung."""
    # Filter: Preis > MA200 & Preis > MA50 (Minervini Stage 2 Basis)
    base_filters = [index_filter, 'ta_sma200_pa', 'ta_sma50_pa'] 
    
    try:
        # Abruf der Performance-Tabelle, sortiert nach 13-Wochen (Quarter)
        stock_list = Screener(filters=base_filters, table='Performance', order='-perf13w')
        
        if not stock_list or len(stock_list) == 0:
            return pd.DataFrame()
            
        df = pd.DataFrame(stock_list.data)
        return df
    except Exception as e:
        st.error(f"Finviz Abruf-Fehler: {e}")
        return pd.DataFrame()

st.title("🏹 Ariel & Ryan: Momentum Scanner")
st.markdown("Fokus: **Stage 2 Trend** & **Relative Stärke (3 Monate)**")

# Index Auswahl
index_choice = st.sidebar.radio(
    "Markt-Fokus wählen:",
    ('S&P 500', 'Nasdaq 100')
)

index_map = {
    'S&P 500': 'idx_sp500',
    'Nasdaq 100': 'idx_ndx'
}

if st.button(f'🚀 Scan {index_choice} starten'):
    with st.spinner(f'Analysiere {index_choice} Komponenten...'):
        df = run_finviz_scan(index_map[index_choice])
        
        if not df.empty:
            # --- SICHERE DATEN-UMWANDLUNG ---
            cols_to_fix = ['Perf Quart', 'Perf Month', 'Perf Year', 'Volatility']
            
            for col in cols_to_fix:
                if col in df.columns:
                    # 1. Entferne das % Zeichen
                    df[col] = df[col].str.replace('%', '', regex=False)
                    # 2. Umwandeln in Zahlen, Fehler (wie '-') werden zu NaN (Not a Number)
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Sortierung nach Relative Strength (Performance Quartal)
            df = df.sort_values(by='Perf Quart', ascending=False).dropna(subset=['Perf Quart'])
            
            st.subheader(f"Top Momentum Leader: {index_choice}")
            
            # Anzeige-Spalten
            display_cols = ['Ticker', 'Price', 'Perf Quart', 'Perf Month', 'Perf Year', 'Volatility', 'Sector']
            
            # Heatmap-Tabelle
            st.dataframe(
                df[display_cols].style.background_gradient(subset=['Perf Quart'], cmap='RdYlGn'),
                use_container_width=True,
                height=600
            )
            
            # Copy-Paste Sektion für TradingView
            ticker_list = ",".join(df['Ticker'].tolist())
            st.text_area("TradingView Watchlist:", ticker_list)
            
            st.success(f"Erfolgreich {len(df)} Aktien im Stage 2 Trend gefunden.")
        else:
            st.warning("Keine Daten gefunden. Finviz blockiert eventuell die Cloud-IP. Bitte kurz warten und erneut versuchen.")
