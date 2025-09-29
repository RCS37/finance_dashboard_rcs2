import streamlit as st
import pandas as pd

# -------------------------------
# Título do App
# -------------------------------
st.title("Finance Dashboard RCS2")

# -------------------------------
# Carregar dados
# -------------------------------
uploaded_file = st.file_uploader("Escolha um arquivo CSV", type="csv")
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.write("Dados carregados com sucesso:")
    st.dataframe(df.head())
else:
    st.warning("Por favor, faça upload de um arquivo CSV.")
    st.stop()

# -------------------------------
# Conversão segura para numérico
# -------------------------------
st.subheader("Conversão de colunas para numérico")
for col in df.columns:
    try:
        # Tenta converter a coluna para numérico
        df[col] = pd.to_numeric(df[col].squeeze(), errors='coerce')
        st.success(f"Coluna '{col}' convertida com sucesso.")
    except Exception as e:
        st.warning(f"Não foi possível converter a coluna '{col}': {e}")

# -------------------------------
# Mostrar dados após conversão
# -------------------------------
st.subheader("Dados após conversão")
st.dataframe(df.head())

# -------------------------------
# Estatísticas descritivas (opcional)
# -------------------------------
if st.checkbox("Mostrar estatísticas descritivas"):
    st.subheader("Estatísticas descritivas")
    st.write(df.describe())

# -------------------------------
# Exemplo de gráfico simples
# -------------------------------
if st.checkbox("Mostrar gráfico de uma coluna numérica"):
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
    if numeric_cols:
        selected_col = st.selectbox("Selecione a coluna para gráfico", numeric_cols)
        st.line_chart(df[selected_col])
    else:
        st.info("Não há colunas numéricas para plotar.")

