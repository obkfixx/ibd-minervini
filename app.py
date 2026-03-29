import streamlit as st
import yfinance as yf
import pandas as pd
import urllib.request
import requests

# Konfiguration
st.set_page_config(page_title="Finviz-Style Momentum Scanner", layout="wide")

def get_headers():
    return {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

@st.cache_data(ttl=86400)
def get_tickers():
    """Holt S&P 500 und Nasdaq 100 Ticker von Wikipedia."""
    try:
        hdr = get_headers()
        # S&P 500
        req_sp = urllib.request.Request('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies', headers=hdr)
        with urllib.request.urlopen(req_sp) as response:
            sp500 = pd.read_html(response)[0]['Symbol'].tolist()
        
        # Nasdaq 100
        req_ndx = urllib.request.Request('https://en.wikipedia.org/wiki/Nasdaq-100#Components', headers=hdr)
        with urllib.request.urlopen(req_ndx) as response:
            ndx100 = pd.read_html(response)[0]['Ticker'].tolist()
            
        tickers = list(set(sp500 + ndx100))
        return [t.replace('.', '-') for t in tickers] + ['SPY']
    except Exception as e:
        return ['NVDA', 'AAPL', 'MSFT', 'AMZN', 'META', 'GOOGL', 'TSLA', 'SPY']

@st.cache_data(ttl=3600)
def get_market_data(tickers):
    """Lädt Daten im Batch und flacht Multi-Index ab."""
    # Wir nehmen 1.5 Jahre für stabile 200-MA Berechnungen
    df = yf.download(tickers, period="1.5y", interval="1d", progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df = df['Close']
    return df

st.title("🏹 High-Performance Momentum Scanner")
st.markdown("Kombiniert **Finviz-Daten-Tiefe** mit **Minervini-Präzision**.")

if st.button('🚀 Full Market Scan starten'):
    with st.spinner('Scanne Marktsegmente (Finviz-Style)...'):
        tickers = get_tickers()
        all_data = get_market_data(tickers)
        
        if all_data.empty:
            st.error("Datenabruf fehlgeschlagen. Yahoo Finance blockiert aktuell.")
        else:
            spy = all_data['SPY'].dropna()
            results = []

            for t in all_data.columns:
                if t == 'SPY' or pd.isna(t): continue
                
                p = all_data[t].dropna()
                if len(p) < 200: continue
                
                # Aktuelle Werte
                curr = p.iloc[-1]
                ma50 = p.rolling(50).mean().iloc[-1]
                ma150 = p.rolling(150).mean().iloc[-1]
                ma200 = p.rolling(200).mean().iloc[-1]
                h52 = p.max()
                l52 = p.min()

                # --- DER MINERVINI "TREND TEMPLATE" CHECK ---
                # 1. Preis > MA150 und Preis > MA200
                # 2. MA150 > MA200
                # 3. MA200 steigt seit mindestens 1 Monat
                # 4. MA50 > MA150 und MA50 > MA200
                # 5. Preis > MA50
                # 6. Preis mind. 30% über 52W-Tief
                # 7. Preis innerhalb 25% vom 52W-Hoch
                
                c1 = curr > ma150 and curr > ma200
                c2 = ma150 > ma200
                c3 = ma200 > p.rolling(200).mean().iloc[-22] # MA200 Trend
                c4 = ma50 > ma150 and ma50 > ma200
                c5 = curr > ma50
                c6 = curr > (l52 * 1.30)
                c7 = curr > (h52 * 0.75)

                if all([c1, c2, c3, c4, c5, c6, c7]):
                    # RS Score (Ariel/Ryan Style)
                    stock_perf = (curr / p.iloc[-63]) - 1
                    spy_perf = (spy.iloc[-1] / spy.iloc[-63]) - 1
                    rs_val = (stock_perf - spy_perf) * 100
                    
                    # David Ryan RS-Line New High
                    rs_line = p / spy.reindex(p.index).ffill()
                    rs_new_high = rs_line.iloc[-1] >= rs_line.iloc[-21:].max()

                    results.append({
                        "Ticker": t,
                        "RS Score": round(rs_val, 2),
                        "RS-Line": "🚀 NEW HIGH" if rs_new_high else " ",
                        "Dist. High %": round(((curr / h52) - 1) * 100, 1),
                        "ADR (Volatility)": round((p.pct_change().rolling(20).std() * 100).iloc[-1], 2)
                    })

            if results:
                df_res = pd.DataFrame(results).sort_values(by="RS Score", ascending=False)
                
                # Markt-Zustand
                spy_ma200 = spy.rolling(200).mean().iloc[-1]
                status = "🟢 BULLISH" if spy.iloc[-1] > spy_ma200 else "🔴 BEARISH"
                st.metric("Gesamtmarkt-Status (SPY vs 200-MA)", status)

                st.subheader(f"Leader gefunden: {len(df_res)}")
                st.dataframe(df_res.style.background_gradient(subset=['RS Score'], cmap='RdYlGn'), use_container_width=True)
            else:
                st.warning("Keine Aktie erfüllt aktuell die harten Kriterien (Stage 2). Der Markt ist wahrscheinlich in einer Korrektur.")
