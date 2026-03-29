import streamlit as st
import pandas as pd
from finviz.screener import Screener

# Konfiguration
st.set_page_config(page_title="Ariel Finviz Momentum", layout="wide")

@st.cache_data(ttl=3600)
def run_finviz_scan(index_filter):
    """Holt Daten von Finviz und filtert nach Stage 2."""
    # ta_sma200_pa: Price above SMA200
    # ta_sma50_pa: Price above SMA50
    # ta_perf_pc: Price performance (Quarter) > 0
    filters = [index_filter, 'ta_sma200_pa', 'ta_sma50_pa']
    
    try:
        # Wir nutzen die 'Performance' Tabelle für RS-Daten
        stock_list = Screener(filters=filters, table='Performance', order='-perf13w')
        if not stock_list:
            return pd.DataFrame()
        return pd.DataFrame(stock_list.data)
    except Exception as e:
        st.error(f"Finviz-Fehler: {e}")
        return pd.DataFrame()

st.title("🏹 Ariel & Zanger Momentum Matrix")
st.markdown("Strategie: **Stage 2 Leader** & **Relative Strength (RS)**")

# Sidebar für Filter
index_choice = st.sidebar.radio("Index Fokus:", ('S&P 500', 'Nasdaq 100'))
index_map = {'S&P 500': 'idx_sp500', 'Nasdaq 100': 'idx_ndx'}

if st.button(f'🚀 Scan {index_choice} starten'):
    with st.spinner('Analysiere Markt-Leader...'):
        df = run_finviz_scan(index_map[index_choice])
        
        if not df.empty:
            # --- DATEN-CLEANING ---
            # Wir wandeln alle %-Spalten sicher in Zahlen um
            cols_to_convert = ['Perf Quart', 'Perf Month', 'Perf Year', 'Volatility']
            for col in cols_to_convert:
                if col in df.columns:
                    df[col] = df[col].str.replace('%', '', regex=False)
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            # Sortierung nach RS (Perf Quart)
            df = df.sort_values(by='Perf Quart', ascending=False).dropna(subset=['Perf Quart'])

            # --- DYNAMISCHE SPALTEN-AUSWAHL (Verhindert KeyError) ---
            # Wir definieren, was wir sehen WOLLEN, und prüfen, was DA ist.
            target_cols = ['Ticker', 'Price', 'Perf Quart', 'Perf Month', 'Perf Year', 'Volatility', 'Sector', 'Industry']
            available_cols = [c for c in target_cols if c in df.columns]

            st.subheader(f"Top {len(df)} Momentum Aktien ({index_choice})")

            # Darstellung der Tabelle
            st.dataframe(
                df[available_cols].style.background_gradient(
                    subset=['Perf Quart'] if 'Perf Quart' in available_cols else [], 
                    cmap='RdYlGn'
                ),
                use_container_width=True,
                height=600
            )

            # TradingView Watchlist Export
            st.subheader("📋 Watchlist Export")
            ticker_str = ",".join(df['Ticker'].tolist())
            st.text_area("Copy-Paste für TradingView:", ticker_str, height=100)
            
            # Zanger/Ariel Hinweis
            st.info("💡 **Tipp:** Suche in TradingView nach Aktien, die ein 'Tight Base' (geringe Volatilität) bilden, während der RS Score hoch bleibt.")
        else:
            st.warning("Keine Ergebnisse. Wahrscheinlich blockiert Finviz die IP oder keine Aktie erfüllt das Stage-2-Kriterium.")
