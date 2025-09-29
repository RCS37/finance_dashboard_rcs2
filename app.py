import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import plotly.graph_objects as go

st.set_page_config(page_title="Painel Financeiro Seguro", layout="wide")

# ==========================
# Funções
# ==========================
def calcular_pivos(df):
    ultima = df.iloc[-1]
    high, low, close = ultima["High"], ultima["Low"], ultima["Close"]
    pp = (high + low + close)/3
    return {
        "Clássico": {
            "S1": 2*pp - high, "S2": pp - (high - low), "S3": low - 2*(high-pp),
            "R1": 2*pp - low, "R2": pp + (high - low), "R3": high + 2*(pp-low)
        },
        "Fibonacci": {
            "S1": pp - 0.382*(high-low), "S2": pp - 0.618*(high-low), "S3": pp - (high-low),
            "R1": pp + 0.382*(high-low), "R2": pp + 0.618*(high-low), "R3": pp + (high-low)
        }
    }

def gerar_indicadores(df):
    ultima = df.iloc[-1]
    sinais = []

    # RSI
    if "rsi" in df.columns and pd.notna(ultima["rsi"]):
        rsi = ultima["rsi"]
        sinais.append(("RSI(14)", rsi, "Compra" if rsi<30 else "Venda" if rsi>70 else "Neutro"))
    else:
        sinais.append(("RSI(14)", None, "N/A"))

    # MACD
    if "macd" in df.columns and pd.notna(ultima["macd"]) and "macd_signal" in df.columns and pd.notna(ultima["macd_signal"]):
        macd, macd_sig = ultima["macd"], ultima["macd_signal"]
        sinais.append(("MACD(12,26)", macd, "Compra" if macd>macd_sig else "Venda"))
    else:
        sinais.append(("MACD(12,26)", None, "N/A"))

    # ADX
    if "adx" in df.columns and pd.notna(ultima["adx"]):
        adx = ultima["adx"]
        sinais.append(("ADX(14)", adx, "Compra" if adx>25 else "Neutro"))
    else:
        sinais.append(("ADX(14)", None, "N/A"))

    # Médias móveis
    for ma in [5,20,50,200]:
        if f"ma{ma}" in df.columns and pd.notna(ultima[f"ma{ma}"]):
            val = ultima[f"ma{ma}"]
            sinais.append((f"MA{ma}", val, "Compra" if ultima["Close"]>val else "Venda"))
        else:
            sinais.append((f"MA{ma}", None, "N/A"))

    return pd.DataFrame(sinais, columns=["Indicador", "Valor", "Sinal"])

def detectar_padroes(df):
    padroes = []
    ultima = df.iloc[-1]
    corpo = abs(ultima["Close"] - ultima["Open"])
    total = ultima["High"] - ultima["Low"]
    if total == 0:
        return pd.DataFrame([["Nenhum","—"]], columns=["Padrão","Status"])
    if corpo <= 0.1*total:
        padroes.append(("Doji", "Detectado"))
    if ultima["Close"] > ultima["Open"] and corpo/total<0.3:
        padroes.append(("Martelo", "Detectado"))
    if ultima["Open"] > ultima["Close"] and corpo/total<0.3:
        padroes.append(("Enforcado", "Detectado"))
    return pd.DataFrame(padroes) if padroes else pd.DataFrame([["Nenhum","—"]], columns=["Padrão","Status"])

def plotar_candles(df, pivos):
    fig = go.Figure(data=[go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"]
    )])
    # Médias móveis
    for ma, cor in zip([5,20,50,200], ["blue","orange","green","red"]):
        if f"ma{ma}" in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df[f"ma{ma}"], mode="lines", name=f"MA{ma}", line=dict(color=cor, width=1)))
    # Pivôs Clássico
    for nivel, valor in pivos["Clássico"].items():
        fig.add_hline(y=valor, line_dash="dot", annotation_text=nivel, annotation_position="right")
    fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_dark", height=600)
    return fig

# ==========================
# Interface
# ==========================
st.title("📊 Painel Financeiro Seguro")

tickers = st.multiselect("Escolha ativos", ["AAPL", "TSLA", "AMD", "MSFT", "NVDA"], default=["AAPL"])
intervalo = st.selectbox("Intervalo de candles", ["5m","15m","30m","1h","1d"], index=0)

for t in tickers:
    st.subheader(f"Ativo: {t}")

    # Baixa dados
    df = yf.download(t, interval=intervalo, period="7d")  # pelo menos 7 dias para intraday
    if df.empty:
        st.warning(f"Não há dados suficientes para {t} no intervalo {intervalo}")
        continue

    df = df.reset_index()
    for col in ["Close", "Open", "High", "Low"]:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df = df.dropna(subset=["Close", "Open", "High", "Low"])
    if df.empty:
        st.warning(f"Após limpeza, não há dados válidos para {t}")
        continue

    # Indicadores - cálculo seguro
    if len(df["Close"]) >= 14:
        df["rsi"] = ta.momentum.RSIIndicator(df["Close"]).rsi()
        df["adx"] = ta.trend.ADXIndicator(df["High"], df["Low"], df["Close"]).adx()
    else:
        df["rsi"] = df["adx"] = pd.Series([None]*len(df))
    if len(df["Close"]) >= 26:
        macd = ta.trend.MACD(df["Close"])
        df["macd"] = macd.macd()
        df["macd_signal"] = macd.macd_signal()
    else:
        df["macd"] = df["macd_signal"] = pd.Series([None]*len(df))

    # Médias móveis seguras
    for ma in [5,20,50,200]:
        if len(df["Close"]) >= ma:
            df[f"ma{ma}"] = ta.trend.SMAIndicator(df["Close"], window=ma).sma_indicator()
        else:
            df[f"ma{ma}"] = pd.Series([None]*len(df))

    # Sinais
    st.dataframe(gerar_indicadores(df))

    # Pivôs
    pivos = calcular_pivos(df)
    st.json(pivos)

    # Gráfico candles + MAs + pivôs
    fig = plotar_candles(df, pivos)
    st.plotly_chart(fig, use_container_width=True)

    # Padrões de Candlestick
    st.markdown("### 🔎 Padrões de Candlestick")
    st.dataframe(detectar_padroes(df))
