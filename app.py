import streamlit as st
import pandas as pd
from finviz.screener import Screener

# Konfiguration
st.set_page_config(page_title="Ariel Momentum Top 30", layout="wide")

@st.cache_data(ttl=3600)
def run_finviz_scan(index_filter):
    """Holt Daten von Finviz: Stage 2 & Momentum."""
    filters = [index_filter, 'ta_sma200_pa', 'ta_sma50_pa']
    try:
        # Wir nutzen die 'Performance' Tabelle
        stock_list = Screener(filters=filters, table='Performance', order='-perf13w')
        if not stock_list:
            return pd.DataFrame()
        return pd.DataFrame(stock_list.data)
    except Exception as e:
        st.error(f"Finviz-Fehler: {e}")
        return pd.DataFrame()

st.title("🏹 Ariel Top 30 Leaderboard")
st.markdown("Fokus: **Sektor-Stärke** & **Relative Stärke (3 Monate)**")

# Sidebar
index_choice = st.sidebar.radio("Index Fokus:", ('S&P 500', 'Nasdaq 100'))
index_map = {'S&P 500': 'idx_sp500', 'Nasdaq 100': 'idx_ndx'}

if st.button(f'🚀 Top 30 {index_choice} scannen'):
    with st.spinner('Analysiere Sektoren und Leader...'):
        df = run_finviz_scan(index_map[index_choice])
        
        if not df.empty:
            # --- DATEN-REINIGUNG ---
            cols_to_fix = ['Perf Quart', 'Perf Month', 'Volatility']
            for col in cols_to_fix:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col].str.replace('%', '', regex=False), errors='coerce')

            # Sortierung & Top 30 Limit
            df = df.sort_values(by='Perf Quart', ascending=False).head(30)

            # --- SEKTOR-ANALYSE ---
            st.subheader("📊 Sektor-Verteilung der Top 30")
            if 'Sector' in df.columns:
                sector_counts = df['Sector'].value_counts()
                st.bar_chart(sector_counts)
            
            # --- LEADER-TABELLE ---
            st.subheader(f"Die 30 stärksten Titel ({index_choice})")
            
            # Relevante Spalten (Sektor & Industry inkludiert)
            display_cols = ['
