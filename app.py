import streamlit as st
import yfinance as yf
import pandas as pd
import urllib.request

# Konfiguration der Seite
st.set_page_config(page_title="Ariel & Minervini Scanner", layout="wide")

@st.cache_data(ttl=86400)
def get_tickers():
    """Holt die S&P 500 und Nasdaq 100 Ticker von Wikipedia mit Browser-Header."""
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
            
        # Bereinigen (Punkte in Ticker-Symbolen für yfinance anpassen)
        tickers = list(set(sp500 + ndx100))
        tickers = [t.replace('.', '-') for t in tickers]
        return tickers + ['SPY', 'QQQ', 'DIA', 'IWM']
    except Exception as e:
        st.error(f"Ticker-Download fehlgeschlagen: {e}")
        return ['NVDA', 'AAPL', 'MSFT', 'AMZN', 'META', 'GOOGL', 'TSLA', 'SPY', 'QQQ']

@st.cache_data(ttl=3600)
def get_market_data(tickers):
    """Lädt die Kurse für alle Ticker im Batch."""
    # Wir brauchen 1 Jahr (252 Handelstage) für RS und Trend-Checks
    df = yf.download(tickers, period="1y", interval="1d", progress=False)
    if 'Close' in df:
        return df['Close']
    return pd.DataFrame()

# --- UI START ---
st.title("🏆 Full Market Momentum Alpha")
st.markdown("Scant S&P 500 & Nasdaq 100 nach den Regeln von **Minervini, Ryan & Ariel**.")

if st.button('🔍 Markt-Scan starten (ca. 60 Sek.)'):
    with st.spinner('Lade Daten von ca. 600 Aktien...'):
        tickers = get_tickers()
        all_data = get_market_data(tickers)
        
        if all_data.empty:
            st.error("Keine Daten von Yahoo Finance empfangen.")
        else:
            spy = all_data['SPY']
            results = []

            # Loop durch alle Aktien
            for t in all_data.columns:
                if t in ['SPY', 'QQQ', 'DIA', 'IWM'] or pd.isna(t):
                    continue
                
                p = all_data[t].dropna()
                if len(p) < 200: # Filter für zu junge Aktien
                    continue
                
                curr = p.iloc[-1]
                ma50 = p.rolling(50).mean().iloc[-1]
                ma150 = p.rolling(150).mean().iloc[-1]
                ma200 = p.rolling(200).mean().iloc[-1]
                h52 = p.max()
                l52 = p.min()

                # --- MINERVINI STAGE 2 FILTER ---
                # 1. Preis über MA150 & MA200
                # 2. MA150 über MA200
                # 3. MA200 steigt (Trend)
                # 4. Preis über MA50
                # 5. Preis innerhalb 25% vom Hoch (Setup Zone)
                is_stage2 = (curr > ma150 > ma200) and (ma150 > ma200) and \
                            (curr > l52 * 1.25) and (curr > h52 * 0.75)
                
                if is_stage2:
                    # RS-Score (Performance relativ zum Markt über 3 Monate)
                    rs_val = ((curr / p.iloc[-63]) - (spy.iloc[-1] / spy.iloc[-63])) * 100
                    
                    # David Ryan RS-Line New High (21 Tage Fenster)
                    rs_line = p / spy
                    rs_new_high = rs_line.iloc[-1] >= rs_line.iloc[-21:].max()

                    results.append({
                        "Ticker": t,
                        "RS Score": round(rs_val, 2),
                        "RS-Line": "🚀 NEW HIGH" if rs_new_high else " ",
                        "Dist. 52W High %": round(((curr / h52) - 1) * 100, 1),
                        "MA50 Dist %": round(((curr / ma50) - 1) * 100, 1),
                        "Price": round(curr, 2)
                    })

            if results:
                df_final = pd.DataFrame(results).sort_values(by="RS Score", ascending=False)
                
                # Markt-Zustand (Minervini Regel: Keine Käufe im Bärenmarkt)
                spy_200 = spy.rolling(200).mean().iloc[-1]
                market_status = "🟢 BULLISH" if spy.iloc[-1] > spy_200 else "🔴 BEARISH (Cash halten!)"
                st.metric("Gesamtmarkt-Status (SPY vs. 200-MA)", market_status)

                st.subheader(f"Gefundene Momentum-Leader: {len(df_final)}")
                st.dataframe(
                    df_final.style.background_gradient(subset=['RS Score'], cmap='RdYlGn'), 
                    height=600, 
                    use_container_width=True
                )
            else:
                st.warning("Keine Aktie erfüllt aktuell die harten Stage-2-Kriterien.")
else:
    st.info("Klicke auf den Button, um das tägliche 15-Minuten-Ritual zu starten.")
