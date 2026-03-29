import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Momentum Alpha Screener", layout="wide")

@st.cache_data(ttl=86400)
def get_tickers():
    # Holt S&P 500 von Wikipedia
    sp500 = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]['Symbol'].tolist()
    # Holt Nasdaq 100 von Wikipedia
    ndx100 = pd.read_html('https://en.wikipedia.org/wiki/Nasdaq-100#Components')[0]['Ticker'].tolist()
    # Kombinieren und Duplikate entfernen
    return list(set(sp500 + ndx100 + ['SPY', 'QQQ', 'DIA', 'IWM']))

@st.cache_data(ttl=3600)
def get_data(tickers):
    # Batch-Download der Schlusskurse (1 Jahr für Momentum/Trend)
    df = yf.download(tickers, period="1y", interval="1d", progress=False)['Close']
    return df

st.title("🏆 Full Market Momentum Scanner")
st.markdown("Scant S&P 500 & Nasdaq 100 nach **Minervini**, **Ryan** & **Ariel** Kriterien.")

if st.button('🔍 Markt-Scan starten (ca. 45-60 Sek.)'):
    with st.spinner('Lade Daten von ca. 600 Aktien...'):
        tickers = get_tickers()
        all_data = get_data(tickers)
        
        if all_data.empty:
            st.error("Keine Daten empfangen. Bitte erneut versuchen.")
        else:
            spy = all_data['SPY']
            results = []

            # Loop durch alle Spalten (Aktien)
            for t in all_data.columns:
                if t in ['SPY', 'QQQ', 'DIA', 'IWM'] or pd.isna(t): continue
                
                p = all_data[t].dropna()
                if len(p) < 200: continue
                
                curr = p.iloc[-1]
                # Gleitende Durchschnitte für Minervini Trend Template
                ma50 = p.rolling(50).mean().iloc[-1]
                ma150 = p.rolling(150).mean().iloc[-1]
                ma200 = p.rolling(200).mean().iloc[-1]
                h52 = p.max()
                l52 = p.min()

                # --- HARTE FILTER (Minervini Stage 2) ---
                # 1. Preis über MA150 & MA200
                # 2. MA150 über MA200
                # 3. MA200 steigt (Trend-Bestätigung)
                # 4. Preis mind. 25% über 52W-Tief
                # 5. Preis innerhalb 25% vom 52W-Hoch (Setup-Zone)
                is_stage2 = (curr > ma150 > ma200) and (ma150 > ma200) and \
                            (curr > l52 * 1.25) and (curr > h52 * 0.75)
                
                if is_stage2:
                    # RS-Score (Performance relativ zum SPY über 3 Monate)
                    rs_val = ((curr / p.iloc[-63]) - (spy.iloc[-1] / spy.iloc[-63])) * 100
                    
                    # David Ryan RS-Line Check (Neues 21-Tage-Hoch in der relativen Stärke)
                    rs_line = p / spy
                    rs_new_high = rs_line.iloc[-1] >= rs_line.iloc[-21:].max()

                    results.append({
                        "Ticker": t,
                        "RS Score": round(rs_val, 2),
                        "RS-Line": "🚀 NEW HIGH" if rs_new_high else " ",
                        "Dist. High %": round(((curr / h52) - 1) * 100, 1),
                        "MA50 Dist %": round(((curr / ma50) - 1) * 100, 1)
                    })

            if results:
                df_final = pd.DataFrame(results).sort_values(by="RS Score", ascending=False)
                
                # Markt-Zustand (Mark-Minervini-Regel: Nur kaufen, wenn der Markt mitspielt)
                spy_200 = spy.rolling(200).mean().iloc[-1]
                market_status = "🟢 RISK-ON" if spy.iloc[-1] > spy_200 else "🔴 RISK-OFF (Vorsicht!)"
                st.metric("Gesamtmarkt (SPY vs. 200-MA)", market_status)

                st.subheader(f"Gefundene Momentum-Leader: {len(df_final)}")
                st.dataframe(df_final.style.background_gradient(subset=['RS Score'], cmap='RdYlGn'), height=600)
            else:
                st.warning("Keine Aktie erfüllt aktuell die harten Stage-2-Kriterien.")
else:
    st.info("Klicke auf den Button, um das tägliche Screening-Ritual zu starten.")
