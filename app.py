import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# -------------------------------
# Auto refresh a cada 60 segundos
# -------------------------------
st_autorefresh(interval=60*1000, limit=None, key="data_refresh")

# -------------------------------
# Título do App
# -------------------------------
st.title("Finance Dashboard em Tempo Real")

# -------------------------------
# Seleção de ativo
# -------------------------------
ticker_input = st.text_input("Digite o símbolo do ativo (ex: AAPL, TSLA, WDO=F):", "AAPL")

if ticker_input:
    try:
        # -------------------------------
        # Buscar dados do Yahoo Finance
        # -------------------------------
        ticker = yf.Ticker(ticker_input)
        df = ticker.history(period="5d", interval="1h")  # últimos 5 dias, intervalo de 1h
        df.reset_index(inplace=True)

        st.subheader(f"Últimos dados do ativo {ticker_input}")
        st.dataframe(df)

        # -------------------------------
        # Conversão segura para numérico
        # -------------------------------
        for col in df.select_dtypes(include=['float64', 'int64']).columns:
            try:
                df[col] = pd.to_numeric(df[col].squeeze(), errors='coerce')
            except Exception as e:
                st.warning(f"Não foi possível converter a coluna '{col}': {e}")

        # -------------------------------
        # Estatísticas descritivas
        # -------------------------------
        if st.checkbox("Mostrar estatísticas descritivas"):
            st.subheader("Estatísticas descritivas")
            st.write(df.describe())

        # -------------------------------
        # Gráfico de fechamento
        # -------------------------------
        if st.checkbox("Mostrar gráfico de fechamento"):
            st.subheader("Gráfico de preço de fechamento")
            st.line_chart(df['Close'])

    except Exception as e:
        st.error(f"Erro ao buscar dados do ativo {ticker_input}: {e}")

else:
    st.info("Digite um símbolo de ativo para buscar os dados.")
