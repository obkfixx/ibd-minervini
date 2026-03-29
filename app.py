import streamlit as st
import pandas as pd
from finviz.screener import Screener

# Konfiguration
st.set_page_config(page_title="Ariel Finviz Alpha", layout="wide")

@st.cache_data(ttl=3600)
def run_finviz_scan(index_filter):
    """Nutzt die finviz-library mit den korrekten Argumenten."""
    # Kriterien: Preis > MA200, Preis > MA50 (Stage 2 Momentum)
    # 'ta_sma200_pa' -> Price above SMA200
    # 'ta_sma50_pa'  -> Price above SMA50
    base_filters = [index_filter, 'ta_sma200_pa', 'ta_sma50_pa'] 
    
    try:
        # Korrektes Argument: 'filters' statt 'filterlist'
        # Wir laden die 'Performance' Tabelle und sortieren nach 13-Wochen (Quarter)
        stock_list = Screener(filters=base_filters, table='Performance', order='-perf13w')
        
        # Umwandlung in DataFrame
        df = pd.DataFrame(stock_list.data)
        return df
    except Exception as e:
        st.error(f"Technischer Fehler beim Abruf: {e}")
        return pd.DataFrame()

st.title("🏹 Ariel & Ryan: Leader-Scanner (Finviz)")
st.markdown("Fokus: **Stage 2 Trend** & **Relative Stärke (3 Monate)**")

# Index Auswahl für das 15-Minuten-Ritual
index_choice = st.sidebar.radio(
    "Wähle den Markt-Fokus:",
    ('S&P 500', 'Nasdaq 100')
)

# Mapping für Finviz Filter
index_map = {
    'S&P 500': 'idx_sp500',
    'Nasdaq 100': 'idx_ndx'
}

if st.button(f'🚀 Scan {index_choice} starten'):
    with st.spinner(f'Analysiere {index_choice}...'):
        df = run_finviz_scan(index_map[index_choice])
        
        if not df.empty:
            # Daten bereinigen (Prozentzeichen entfernen)
            for col in ['Perf Quart', 'Perf Month', 'Perf Year', 'Volatility']:
                if col in df.columns:
                    df[col] = df[col].str.replace('%', '').astype(float)
            
            # Sortierung nach RS (Perf Quart)
            df = df.sort_values(by='Perf Quart', ascending=False)
            
            st.subheader(f"Momentum Leader in {index_choice}")
            
            # Wichtige Spalten für Ariel/Minervini/Ryan
            display_cols = ['Ticker', 'Price', 'Perf Quart', 'Perf Month', 'Perf Year', 'Volatility', 'Sector']
            
            # Anzeige der Tabelle
            st.dataframe(
                df[display_cols].style.background_gradient(subset=['Perf Quart'], cmap='RdYlGn'),
                use_container_width=True,
                height=600
            )
            
            # Export für TradingView/Finviz Watchlists
            ticker_list = ",".join(df['Ticker'].tolist())
            st.text_area("Watchlist für TradingView (Copy-Paste):", ticker_list)
            
            st.success(f"Gefunden: {len(df)} Aktien im Stage 2 Uptrend.")
        else:
            st.warning("Keine Daten gefunden. Finviz blockiert eventuell die Cloud-IP von Streamlit. Versuche es in 5-10 Minuten erneut.")
