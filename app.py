import streamlit as st
import pandas as pd
from finviz.screener import Screener

# Konfiguration der Seite
st.set_page_config(page_title="Ariel Momentum Top 30", layout="wide")

@st.cache_data(ttl=3600)
def run_finviz_scan(index_filter):
    """Holt Daten von Finviz: Stage 2 & Momentum."""
    # Filter: Preis über MA200 & MA50 (Minervini Stage 2 Basis)
    filters = [index_filter, 'ta_sma200_pa', 'ta_sma50_pa']
    try:
        # Abruf der Performance-Tabelle, sortiert nach 13-Wochen (Quarter)
        stock_list = Screener(filters=filters, table='Performance', order='-perf13w')
        if not stock_list:
            return pd.DataFrame()
        return pd.DataFrame(stock_list.data)
    except Exception as e:
        st.error(f"Finviz-Fehler: {e}")
        return pd.DataFrame()

st.title("🏹 Ariel Top 30 Leaderboard")
st.markdown("Strategie: **Sektor-Stärke** & **Relative Stärke (3 Monate)**")

# Sidebar Auswahl
index_choice = st.sidebar.radio("Index Fokus:", ('S&P 500', 'Nasdaq 100'))
index_map = {'S&P 500': 'idx_sp500', 'Nasdaq 100': 'idx_ndx'}

if st.button(f'🚀 Top 30 {index_choice} scannen'):
    with st.spinner('Analysiere Sektoren und Leader...'):
        df_raw = run_finviz_scan(index_map[index_choice])
        
        if not df_raw.empty:
            # --- DATEN-REINIGUNG ---
            # Kopie erstellen um SettingWithCopyWarning zu vermeiden
            df = df_raw.copy()
            
            cols_to_fix = ['Perf Quart', 'Perf Month', 'Volatility']
            for col in cols_to_fix:
                if col in df.columns:
                    # Entferne % und wandle in Zahlen um
                    df[col] = pd.to_numeric(df[col].str.replace('%', '', regex=False), errors='coerce')

            # Sortierung nach Momentum & Begrenzung auf Top 30
            df = df.sort_values(by='Perf Quart', ascending=False).head(30)

            # --- SEKTOR-ANALYSE (Ariel Group Strength) ---
            st.subheader("📊 Sektor-Verteilung der Top 30")
            if 'Sector' in df.columns:
                sector_counts = df['Sector'].value_counts()
                st.bar_chart(sector_counts)
            
            # --- LEADER-TABELLE ---
            st.subheader(f"Die 30 stärksten Titel ({index_choice})")
            
            # Relevante Spalten definieren
            display_cols = ['Ticker', 'Sector', 'Industry', 'Price', 'Perf Quart', 'Perf Month', 'Volatility']
            
            # Nur vorhandene Spalten anzeigen (Safety Check)
            available_cols = [c for c in display_cols if c in df.columns]

            try:
                # Darstellung mit Farbskala (benötigt matplotlib)
                st.dataframe(
                    df[available_cols].style.background_gradient(
                        subset=['Perf Quart'], cmap='RdYlGn'
                    ),
                    use_container_width=True,
                    height=450
                )
            except Exception as e:
                # Fallback falls Styling fehlschlägt
                st.dataframe(df[available_cols], use_container_width=True, height=450)

            # --- WATCHLIST EXPORT ---
            st.subheader("📋 Watchlist Export")
            ticker_str = ",".join(df['Ticker'].tolist())
            st.text_area("TradingView Watchlist (Top 30):", ticker_str, height=70)

            st.info("""
            **Ariel-Tipp:** Wenn ein Sektor (z.B. 'Technology') dominiert, fließen dort die institutionellen Gelder. 
            Suche innerhalb dieser Gruppen nach VCP-Mustern.
            """)
        else:
            st.warning("Keine Daten gefunden. Bitte versuche es in 5-10 Minuten erneut (Finviz IP-Limit).")
else:
    st.info("Klicke auf den Button, um das tägliche Screening-Ritual für die Top 30 zu starten.")
