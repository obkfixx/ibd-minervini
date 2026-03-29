import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Full Market Momentum Scanner", layout="wide")

@st.cache_data(ttl=86400) # Cache für 24h, um Ladezeiten zu minimieren
def get_sp500_tickers():
    # Lädt die aktuellen S&P 500 Ticker von Wikipedia
    table = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    return table[0]['Symbol'].tolist()

@st.cache_data(ttl=3600)
def get_market_data(tickers):
    # Batch-Download für Geschwindigkeit
    # Wir nehmen 1 Jahr für RS-Score und Stage 2 Check
    data = yf.download(tickers, period="1y", interval="1d", progress=False)['Close']
    return data

st.title("🏆 Professional Market Screener")
st.markdown("Scant **S&P 500** & **Nasdaq 100** nach Minervini & David Ryan Kriterien.")

if st.button('🔍 Kompletten Markt-Scan starten (ca. 30 Sek.)'):
    with st.spinner('Lade Marktdaten...'):
        tickers = list(set(get_sp500_tickers() + ['QQQ', 'SPY', 'DIA', 'IWM']))
        all_data = get_market_data(tickers)
        
        if all_data.empty:
            st.error("Datenabruf fehlgeschlagen.")
        else:
            spy = all_data['SPY']
            results = []

            # Wir loopen durch alle verfügbaren Aktien
            for t in all_data.columns:
                if t in ['SPY', 'QQQ', 'DIA', 'IWM']: continue
                
                p = all_data[t].dropna()
                if len(p) < 200: continue # Ignoriere IPOs ohne Historie
                
                curr = p.iloc[-1]
                ma50 = p.rolling(50).mean().iloc[-1]
                ma150 = p.rolling(150).mean().iloc[-1]
                ma200 = p.rolling(200).mean().iloc[-1]
                h52 = p.max()
                
                # --- DER HARTE MINERVINI FILTER ---
                # 1. Preis über MA150 und MA200
                # 2. MA150 über MA200
                # 3. MA200 steigt (Trend)
                # 4. Preis über MA50
                # 5. Preis innerhalb 25% vom Hoch
                is_stage2 = (curr > ma150 > ma200) and (ma50 > ma150) and (curr > h52 * 0.75)
                
                if is_stage2: # Nur "Stage 2" Aktien kommen in die Liste (Saves Memory)
                    # RS Score (IBD Style: 3M Performance relativ zum Markt)
                    rs_score = ((curr / p.iloc[-63]) - (spy.iloc[-1] / spy.iloc[-63])) * 100
                    
                    # David Ryan RS-Line New High
                    rs_line = p / spy
                    rs_new_high = rs_line.iloc[-1] >= rs_line.iloc[-21:].max()

                    results.append({
                        "Ticker": t,
                        "RS Score": round(rs_score, 2),
                        "RS-Line": "🚀" if rs_new_high else " ",
                        "Dist. High %": round(((curr / h52) - 1) * 100, 1),
                        "Price": round(curr, 2)
                    })

            df_final = pd.DataFrame(results).sort_values(by="RS Score", ascending=False)

            # Marktanalyse
            spy_trend = "🟢 BULLISH" if spy.iloc[-1] > spy.rolling(200).mean().iloc[-1] else "🔴 BEARISH"
            st.metric("Gesamtmarkt-Status (SPY 200-MA)", spy_status)

            st.subheader(f"Gefundene Leader: {len(df_final)}")
            st.dataframe(df_final.style.background_gradient(subset=['RS Score'], cmap='RdYlGn'), height=600)

else:
    st.info("Klicke den Button, um ca. 600 Aktien nach Momentum-Leadern zu durchsuchen.")
