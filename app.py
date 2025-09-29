import streamlit as st
import yfinance as yf
import pandas as pd
import time

# -------------------------------
# Título do App
# -------------------------------
st.title("Finance Dashboard em Tempo Real")

# -------------------------------
# Seleção de ativo
# -------------------------------
ticker_input = st.text_input("Digite o símbolo do ativo (ex: AAPL, TSLA, WDO=F):", "AAPL")

# -------------------------------
# Intervalo de atualização
# -------------------------------
update_interval = st.number_input("Intervalo de atualização (segundos):", min_value=10, value=60, step=10)

# -------------------------------
# Loop de atualização
# -------------------------------
if ticker_input:
    placeholder = st.empty()  # espaço para atualizar tabela e gráfico
    while True:
        try:
            # Buscar dados do Yahoo Finance
            ticker = yf.Ticker(ticker_input)
            df = ticker.history(period="5d", interval="1h")  # últimos 5 dias, 1h por vela
            df.reset_index(inplace=True)

            # Conversão segura para numérico
            for col in df.select_dtypes(include=['float64', 'int64']).columns:
                try:
                    df[col] = pd.to_numeric(df[col].squeeze(), errors='coerce')
                except Exception as e:
                    st.warning(f"Não foi possível converter a coluna '{col}': {e}")

            # Atualizar tabela
            with placeholder.container():
                st.subheader(f"Últimos dados do ativo {ticker_input}")
                st.dataframe(df)

                # Estatísticas descritivas
                if st.checkbox("Mostrar estatísticas descritivas", key="stats"):
                    st.subheader("Estatísticas descritivas")
                    st.write(df.describe())

                # Gráfico de fechamento
                if st.checkbox("Mostrar gráfico de fechamento", key="chart"):
                    st.subheader("Gráfico de preço de fechamento")
                    st.line_chart(df['Close'])

            # Espera o intervalo antes de atualizar
            time.sleep(update_interval)

        except Exception as e:
            st.error(f"Erro ao buscar dados do ativo {ticker_input}: {e}")
            break

else:
    st.info("Digite um símbolo de ativo para buscar os dados.")
