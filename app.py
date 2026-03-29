import streamlit as st
import pandas as pd
from finviz.screener import Screener

# Konfiguration
st.set_page_config(page_title="Ariel Finviz Momentum", layout="wide")

@st.cache_data(ttl=3600)
def run_finviz_scan(index_filter):
    """Holt Daten von Finviz und filtert nach Stage 2."""
    # Filter: Preis über MA200 & MA50
    filters = [index_filter, 'ta_sma200_pa', 'ta_sma50_pa']
    
    try:
        # Abruf der Performance-Tabelle
        stock_list = Screener(filters=filters, table='Performance', order='-perf13w')
        if not stock_list:
            return pd.DataFrame()
        return pd.DataFrame(stock_list.data)
    except Exception as e:
        st.error(f"Finviz-Fehler: {e}")
        return pd.DataFrame()

st.title("🏹 Ariel & Zanger Momentum Matrix")
st.markdown("Strategie: **Stage 2 Leader** & **Relative Strength (RS)**")

# Sidebar
index_choice = st.sidebar.radio("Index Fokus:", ('S&P 500', 'Nasdaq 100'))
index_map = {'S&P 500': 'idx_sp500', 'Nasdaq 100': 'idx_ndx'}

if st.button(f'🚀 Scan {index_choice} starten'):
    with st.spinner('Analysiere Markt-Leader...'):
        df = run_finviz_scan(index_map[index_choice])
        
        if not df.empty:
            # --- DATEN-CLEANING ---
            cols_to_convert = ['Perf Quart', 'Perf Month', 'Perf Year', 'Volatility']
            for col in cols_to_convert:
                if col in df.columns:
                    df[col] = df[col].str.replace('%', '', regex=False)
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            # Sortierung nach RS
            df = df.sort_values(by='Perf Quart', ascending=False).dropna(subset=['Perf Quart'])

            # Dynamische Spalten
            target_cols = ['Ticker', 'Price', 'Perf Quart', 'Perf Month', 'Perf Year', 'Volatility', 'Sector', 'Industry']
            available_cols = [c for c in target_cols if c in df.columns]

            st.subheader(f"Top {len(df)} Momentum Aktien ({index_choice})")

            # --- SICHERE DARSTELLUNG ---
            try:
                # Versuche Heatmap (benötigt matplotlib)
                st.dataframe(
                    df[available_cols].style.background_gradient(
                        subset=['Perf Quart'] if 'Perf Quart' in available_cols else [], 
                        cmap='RdYlGn'
                    ),
                    use_container_width=True,
                    height=600
                )
            except ImportError:
                # Fallback falls matplotlib fehlt
                st.warning("Hinweis: Matplotlib fehlt in requirements.txt – Tabelle wird ohne Farben angezeigt.")
                st.dataframe(df[available_cols], use_container_width=True, height=600)

            # Export
            st.subheader("📋 Watchlist Export")
            ticker_str = ",".join(df['Ticker'].tolist())
            st.text_area("Copy-Paste für TradingView:", ticker_str, height=100)
            
            st.info("💡 **Ariel-Check:** Achte auf Aktien mit hohem 'Perf Quart' bei gleichzeitig sinkender 'Volatility'.")
        else:
            st.warning("Keine Ergebnisse oder IP-Blockade. Versuche es in 5 Minuten erneut.")
