import streamlit as st
import yfinance as yf
import pandas as pd
import urllib.request

# Konfiguration
st.set_page_config(page_title="Momentum Alpha Screener", layout="wide")

@st.cache_data(ttl=86400)
def get_tickers():
    """Holt S&P 500 und Nasdaq 100 Ticker von Wikipedia."""
    hdr = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        # S&P 500
        req_sp = urllib.request.Request('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies', headers=hdr)
        with urllib.request.urlopen(req_sp) as response:
            sp500 = pd.read_html(response)[0]['Symbol'].tolist()
        
        # Nasdaq 100
        req_ndx = urllib.request.Request('https://en.wikipedia.org/wiki/Nasdaq-100#Components', headers=hdr)
        with urllib.request.urlopen(req_ndx) as response:
            ndx100 = pd.read_html(response)[0]['Ticker'].tolist()
            
        tickers = list(set(sp500 + ndx100))
        tickers = [t.replace('.', '-') for t in tickers] # yfinance Format
        return tickers + ['SPY', 'QQQ']
    except Exception as e:
        st.error(f"Ticker-Download fehlgeschlagen: {e}")
        return ['NVDA', 'AAPL', 'MSFT', 'AMZN', 'META', 'GOOGL', 'TSLA', 'SPY', 'QQQ']

@st.cache_data(ttl=3600)
def get_market_data(tickers):
    """Lädt Daten und bereinigt den Multi-Index von yfinance."""
    df = yf.download(tickers, period="1y", interval="1d", progress=False)
    
    # Fix für yfinance Multi-Index: Wir wollen nur 'Close'
    if isinstance(df.columns, pd.MultiIndex):
        df = df['Close']
    else:
        # Falls nur ein Ticker oder altes Format
        if 'Close' in df.columns:
            df = df['Close']
            
    return df

st.title("🏆 Full Market Momentum Alpha")
st.markdown("Kriterien: **Minervini Stage 2** | **David Ryan RS-Line** | **Ariel Group Strength**")

if st.button('🔍 Markt-Scan starten'):
    with st.spinner('Scanne ca. 600 Aktien...'):
        tickers = get_tickers()
        all_data = get_market_data(tickers)
        
        if all_data.empty:
            st.error("Keine Daten empfangen. Yahoo Finance ist eventuell kurzzeitig überlastet.")
        else:
            # Sicherheitscheck: SPY muss vorhanden sein
            if 'SPY' not in all_data.columns:
                st.error("Benchmark SPY konnte nicht geladen werden.")
            else:
                spy = all_data['SPY'].dropna()
                results = []

                for t in all_data.columns:
                    if t in ['SPY', 'QQQ'] or pd.isna(t):
                        continue
                    
                    p = all_data[t].dropna()
                    if len(p) < 150: # Mindestanzahl an Datenpunkten
                        continue
                    
                    curr = p.iloc[-1]
                    # Indikatoren berechnen
                    ma50 = p.rolling(50).mean().iloc[-1]
                    ma150 = p.rolling(150).mean().iloc[-1]
                    ma200 = p.rolling(200).mean().iloc[-1]
                    h52 = p.max()
                    l52 = p.min()

                    # --- MINERVINI & RYAN FILTER ---
                    # 1. Preis über MA150 & MA200
                    # 2. MA150 über MA200
                    # 3. Preis über MA50 (Momentum)
                    # 4. Nicht tiefer als 30% vom 52W-Hoch (Relative Stärke)
                    cond_1 = curr > ma150 and curr > ma200
                    cond_2 = ma150 > ma200
                    cond_3 = curr > ma50
                    cond_4 = curr > (h52 * 0.70) 
                    
                    if cond_1 and cond_2 and cond_3 and cond_4:
                        # RS Score (vs SPY über letzten 3 Monate)
                        spy_perf = (spy.iloc[-1] / spy.iloc[-63]) - 1
                        stock_perf = (curr / p.iloc[-63]) - 1
                        rs_val = (stock_perf - spy_perf) * 100
                        
                        # RS-Line New High (Ryan Signal)
                        rs_line = p / spy.reindex(p.index).ffill()
                        rs_new_high = rs_line.iloc[-1] >= rs_line.iloc[-21:].max()

                        results.append({
                            "Ticker": t,
                            "RS Score": round(rs_val, 2),
                            "RS-Line": "🚀 NEW HIGH" if rs_new_high else " ",
                            "Dist. 52W High %": round(((curr / h52) - 1) * 100, 1),
                            "Price": round(curr, 2)
                        })

                if results:
                    df_res = pd.DataFrame(results).sort_values(by="RS Score", ascending=False)
                    
                    # Markt-Ampel
                    spy_ma200 = spy.rolling(200).mean().iloc[-1]
                    status = "🟢 BULLISH" if spy.iloc[-1] > spy_ma200 else "🔴 BEARISH"
                    st.metric("Gesamtmarkt (SPY vs 200-MA)", status)

                    st.subheader(f"Gefundene Leader: {len(df_res)}")
                    st.dataframe(df_res.style.background_gradient(subset=['RS Score'], cmap='RdYlGn'), height=600, use_container_width=True)
                else:
                    st.warning("Keine Aktie erfüllt aktuell die harten Kriterien. Versuche es in 5 Minuten erneut (Yahoo Limit).")
else:
    st.info("Klicke auf den Button für dein 15-Minuten-Ritual.")
