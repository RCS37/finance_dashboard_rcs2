import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import time
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("Dashboard Avançado de Scalp com Sinais C/V/N")

# Entrada do ativo e intervalo de atualização
ticker_input = st.text_input("Digite o símbolo do ativo (ex: AAPL, TSLA, WDO=F):", "AAPL")
update_interval = st.number_input("Intervalo de atualização (segundos):", min_value=10, value=60, step=10)

# -----------------------------
# Função para calcular indicadores
# -----------------------------
def calcular_indicadores(df):
    df = df.copy()
    df['SMA5'] = df['Close'].rolling(5).mean()
    df['SMA10'] = df['Close'].rolling(10).mean()
    df['EMA5'] = df['Close'].ewm(span=5, adjust=False).mean()
    df['EMA10'] = df['Close'].ewm(span=10, adjust=False).mean()
    df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
    macd = ta.trend.MACD(df['Close'])
    df['MACD'] = macd.macd()
    df['MACD_signal'] = macd.macd_signal()
    bb = ta.volatility.BollingerBands(df['Close'], window=20, window_dev=2)
    df['BB_High'] = bb.bollinger_hband()
    df['BB_Low'] = bb.bollinger_lband()
    df['Pivot'] = (df['High'] + df['Low'] + df['Close']) / 3
    return df

# -----------------------------
# Função para sinais C/V/N
# -----------------------------
def sinais_cvns(df):
    df = df.copy()
    sinais = []
    for i in range(len(df)):
        c = v = n = 0
        # SMA
        if df['SMA5'].iloc[i] > df['SMA10'].iloc[i]:
            c += 1
        elif df['SMA5'].iloc[i] < df['SMA10'].iloc[i]:
            v += 1
        else:
            n += 1
        # EMA
        if df['EMA5'].iloc[i] > df['EMA10'].iloc[i]:
            c += 1
        elif df['EMA5'].iloc[i] < df['EMA10'].iloc[i]:
            v += 1
        else:
            n += 1
        # RSI
        rsi = df['RSI'].iloc[i]
        if rsi < 30:
            c += 1
        elif rsi > 70:
            v += 1
        else:
            n += 1
        # MACD
        macd = df['MACD'].iloc[i]
        signal = df['MACD_signal'].iloc[i]
        if macd > signal:
            c += 1
        elif macd < signal:
            v += 1
        else:
            n += 1
        # Bollinger Bands
        close = df['Close'].iloc[i]
        if close < df['BB_Low'].iloc[i]:
            c += 1
        elif close > df['BB_High'].iloc[i]:
            v += 1
        else:
            n += 1
        # Pivot
        pivot = df['Pivot'].iloc[i]
        if close > pivot:
            c += 1
        elif close < pivot:
            v += 1
        else:
            n += 1
        # Tendência final
        if c > v and c > n:
            sinais.append("Compra")
        elif v > c and v > n:
            sinais.append("Venda")
        else:
            sinais.append("Neutro")
    df['Sinal'] = sinais
    return df

# -----------------------------
# Função para plotar gráfico Plotly
# -----------------------------
def plotar_grafico(df, periodo):
    cores = {'Compra':'green', 'Venda':'red', 'Neutro':'gray'}
    # Eixo X seguro
    x_axis = pd.Series(df.index)
    
    fig = go.Figure(data=[go.Candlestick(
        x=x_axis,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        increasing_line_color='black',
        decreasing_line_color='black'
    )])
    
    # Marcar sinais
    for i in range(len(df)):
        fig.add_shape(
            type="circle",
            x0=i-0.3, x1=i+0.3,
            y0=df['Close'].iloc[i]*0.998, y1=df['Close'].iloc[i]*1.002,
            line_color=cores[df['Sinal'].iloc[i]],
            fillcolor=cores[df['Sinal'].iloc[i]],
        )
    
    fig.update_layout(title=f"{ticker_input} - Período {periodo}", xaxis_rangeslider_visible=False)
    return fig

# -----------------------------
# Loop de atualização em tempo real
# -----------------------------
if ticker_input:
    placeholder = st.empty()
    while True:
        try:
            periodos = {'5m': ('7d', '5m'), '15m': ('60d', '15m'), '1h': ('730d', '1h'), '1d': ('max', '1d')}
            analises = {}
            for periodo, (duracao, intervalo) in periodos.items():
                df = yf.download(tickers=ticker_input, period=duracao, interval=intervalo, progress=False)
                # Garantir que colunas numéricas sejam Series 1D
                for col in ['Open','High','Low','Close','Adj Close','Volume']:
                    if col in df.columns:
                        df[col] = pd.Series(df[col])
                df = calcular_indicadores(df)
                df = sinais_cvns(df)
                analises[periodo] = df
            
            # Mostrar resultados e gráficos
            with placeholder.container():
                st.subheader(f"Dashboard de {ticker_input}")
                for periodo, df in analises.items():
                    sinais_ult = df['Sinal'].value_counts()
                    st.markdown(f"**Período {periodo}** | Último preço: {df['Close'].iloc[-1]:.2f}")
                    st.markdown(f"Indicadores → Compra: {sinais_ult.get('Compra',0)}, Venda: {sinais_ult.get('Venda',0)}, Neutro: {sinais_ult.get('Neutro',0)}")
                    st.markdown(f"Tendência final: {df['Sinal'].iloc[-1]}")
                    st.plotly_chart(plotar_grafico(df, periodo), use_container_width=True)
            
            time.sleep(update_interval)
        except Exception as e:
            st.error(f"Erro ao buscar dados do ativo {ticker_input}: {e}")
            break
else:
    st.info("Digite um símbolo de ativo para buscar os dados.")
