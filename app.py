import streamlit as st
import pandas as pd
from finviz.screener import Screener

# Konfiguration
st.set_page_config(page_title="Ariel Leaderboard + Sektoren", layout="wide")

@st.cache_data(ttl=3600)
def get_combined_finviz_data(index_filter):
    """Kombiniert 'Overview' (Sektoren) und 'Performance' (Momentum) Daten."""
    filters = [index_filter, 'ta_sma200_pa', 'ta_sma50_pa']
    try:
        # 1. Overview für Sektoren & Industrie
        overview_list = Screener(filters=filters, table='Overview')
        df_overview = pd.DataFrame(overview_list.data)
        
        # 2. Performance für RS-Daten
        perf_list = Screener(filters=filters, table='Performance')
        df_perf = pd.DataFrame(perf_list.data)
        
        if df_overview.empty or df_perf.empty:
            return pd.DataFrame()
            
        # 3. Zusammenführen über den Ticker
        # Wir behalten vom Overview: Ticker, Sector, Industry
        # Wir behalten von Performance: Ticker, Perf Quart, Perf Month, Volatility
        df_combined = pd.merge(
            df_overview[['Ticker', 'Sector', 'Industry', 'Price']], 
            df_perf[['Ticker', 'Perf Quart', 'Perf Month', 'Volatility']], 
            on='Ticker'
        )
        return df_combined
    except Exception as e:
        st.error(f"Daten-Merge Fehler: {e}")
        return pd.DataFrame()

st.title("🏹 Ariel Leaderboard (Top 30 + Sektoren)")
st.markdown("Kombinierte Sicht: **Momentum** trifft **Branchen-Stärke**.")

index_choice = st.sidebar.radio("Markt-Fokus:", ('S&P 500', 'Nasdaq 100'))
index_map = {'S&P 500': 'idx_sp500', 'Nasdaq 100': 'idx_ndx'}

if st.button(f'🚀 Analyse {index_choice} starten'):
    with st.spinner('Kombiniere Sektoren und Performance-Daten...'):
        df = get_combined_finviz_data(index_map[index_choice])
        
        if not df.empty:
            # --- DATEN-CLEANING ---
            cols_to_fix = ['Perf Quart', 'Perf Month', 'Volatility']
            for col in cols_to_fix:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col].str.replace('%', '', regex=False), errors='coerce')

            # Sortierung nach 3-Monats-Performance (RS) und Top 30
            df = df.sort_values(by='Perf Quart', ascending=False).head(30)

            # --- SEKTOR-ANALYSE CHART ---
            st.subheader("📊 Gruppen-Stärke (Sektor-Verteilung)")
            sector_counts = df['Sector'].value_counts()
            st.bar_chart(sector_counts)
            
            # --- DIE MASTER-TABELLE ---
            st.subheader(f"Top 30 Momentum-Werte inkl. Sektoren")
            
            # Definierte Spaltenreihenfolge für Ariel-Fokus
            display_cols = ['Ticker', 'Sector', 'Industry', 'Price', 'Perf Quart', 'Perf Month', 'Volatility']
            
            try:
                st.dataframe(
                    df[display_cols].style.background_gradient(
                        subset=['Perf Quart'], cmap='RdYlGn'
                    ).format(precision=2),
                    use_container_width=True,
                    height=500
                )
            except:
                st.dataframe(df[display_cols], use_container_width=True)

            # Watchlist Export
            ticker_str = ",".join(df['Ticker'].tolist())
            st.text_area("TradingView Watchlist:", ticker_str, height=70)

            st.info("""
            **Warum Sektoren?** Institutionen kaufen oft ganze Branchen (Clustering). 
            Wenn in den Top 30 z.B. viele 'Software - Infrastructure' Titel auftauchen, 
            ist das dein Signal für den nächsten Sektor-Run.
            """)
        else:
            st.warning("Keine Daten gefunden oder Finviz-Limit erreicht. Bitte kurz warten.")
