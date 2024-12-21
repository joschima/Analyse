import streamlit as st
import yfinance as yf
from ta.trend import MACD
import requests
import datetime

# API-Key für NewsAPI (ersetzen mit deinem Key)
API_KEY = "fb83c645d9ea492e9e5c9a5be0fb556a"

# Titel der App
st.title("📈 Aktienanalyse Tool (EUR)")

# Eingabefeld für Ticker
ticker = st.text_input("🔎 Gib ein Ticker-Symbol ein (z.B. AAPL, TSLA, IUSQ.DE):")

# Schlagwörter zur gezielten Suche
KEYWORDS = ["earnings", "forecast", "revenue", "growth", "outlook", "stock price", "report", "dividend", "acquisition", "crash"]

if ticker:
    data = yf.Ticker(ticker)
    hist = data.history(period='1y')
    stock_name = data.info.get('longName', ticker)  # Name der Aktie

    # Finanzkennzahlen anzeigen
    st.write("### 📊 Finanzkennzahlen")
    info = data.info
    explanations = {
        'marketCap': ("Marktkapitalisierung", '€'),
        'trailingPE': ("KGV (Kurs-Gewinn-Verhältnis)", ''),
        'forwardPE': ("Forward KGV", ''),
        'dividendYield': ("Dividendenrendite", '%'),
        'profitMargins': ("Gewinnmarge", ''),
        'returnOnAssets': ("ROA (Return on Assets)", ''),
        'returnOnEquity': ("ROE (Return on Equity)", '')
    }
    
    for key, (desc, unit) in explanations.items():
        value = info.get(key, 'N/A')
        if key == 'marketCap' and isinstance(value, (int, float)):
            value = f"{int(value):,}".replace(',', '.') + f" {unit}"
        elif key == 'dividendYield' and isinstance(value, float):
            value = f"{round(value * 100, 2):.2f}".replace('.', ',') + f" {unit}"
        elif isinstance(value, float):
            value = f"{value:.2f}".replace('.', ',') + f" {unit}"
        
        st.write(f"**{desc}**: {value}")

    # Kursdaten plotten
    st.write("### 📈 Aktienkursverlauf (1 Jahr)")
    st.line_chart(hist['Close'])

    # Nachrichten abrufen und anzeigen
    st.write(f"### 📰 Aktuelle Nachrichten zu {stock_name}")
    
    @st.cache_data
    def get_stock_news(stock_name):
        url = "https://newsapi.org/v2/everything"
        today = datetime.datetime.now()
        one_week_ago = today - datetime.timedelta(days=7)
        two_weeks_ago = today - datetime.timedelta(days=14)
        
        # Schlagwörter zur Suche hinzufügen
        query = f"{stock_name} ({' OR '.join(KEYWORDS)})"
        
        # 1. Nachrichten von MarketWatch, WSJ und Barron's (bis 2 Wochen)
        sources = 'marketwatch.com,wsj.com,barrons.com'
        params_priority = {
            'q': query,
            'from': two_weeks_ago.strftime('%Y-%m-%d'),
            'to': today.strftime('%Y-%m-%d'),
            'language': 'en',
            'sortBy': 'relevancy',
            'apiKey': API_KEY,
            'domains': sources
        }
        
        # 2. Alle anderen relevanten Nachrichten (bis zu 7 Tage)
        params_general = {
            'q': query,
            'from': one_week_ago.strftime('%Y-%m-%d'),
            'to': today.strftime('%Y-%m-%d'),
            'language': 'en',
            'sortBy': 'relevancy',
            'apiKey': API_KEY
        }
        
        news_items = []
        
        # Anfrage an priorisierte Quellen
        response_priority = requests.get(url, params=params_priority)
        if response_priority.status_code == 200:
            articles = response_priority.json().get('articles', [])
            for article in articles:
                headline = article['title']
                link = article['url']
                source_name = article['source']['name']
                news_items.append((headline, link, source_name))
        
        # Anfrage an allgemeine Quellen
        response_general = requests.get(url, params=params_general)
        if response_general.status_code == 200:
            articles = response_general.json().get('articles', [])
            for article in articles:
                headline = article['title']
                link = article['url']
                source_name = article['source']['name']
                news_items.append((headline, link, source_name))
        
        # Nachrichten sortieren: Priorisierte Quellen zuerst, dann andere
        news_items.sort(key=lambda x: x[2] in ["MarketWatch", "The Wall Street Journal", "Barron's"], reverse=True)
        
        if not news_items:
            st.warning("🚫 Keine relevanten Nachrichten gefunden.")
        
        return news_items[:10]  # Maximal 10 Nachrichten

    # Nachrichten abrufen und anzeigen
    news = get_stock_news(stock_name)
    
    if news:
        for headline, url, source in news:
            st.write(f"**[{headline}]({url})**  \n_Quelle: {source}_")
    else:
        st.write(f"🚫 Keine aktuellen Nachrichten zu **{stock_name}** gefunden.")

    # MACD und Kauf/Verkauf-Signale anzeigen
    st.write("### 📉 MACD Analyse")
    macd = MACD(hist['Close']).macd()
    
    st.line_chart(macd)
