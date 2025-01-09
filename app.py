import streamlit as st
from google.oauth2.service_account import Credentials
import gspread
import pandas as pd
import matplotlib.pyplot as plt
import os
import json
from datetime import datetime

# Configuração do Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]

# Carregar credenciais do Secrets
credentials_json = os.getenv("GOOGLE_CREDENTIALS")
creds = Credentials.from_service_account_info(json.loads(credentials_json), scopes=SCOPES)

# Autorizar cliente do Google Sheets
client = gspread.authorize(creds)

# ID da planilha
spreadsheet_id = "12m2kUbhJnjjUPqyoJiu0YOxvw7x5jtfdtZuMbfEQLfo"

# Nome da aba na planilha
sheet_name = "Laboratório"

# Função para carregar os dados da planilha
def get_data(sheet_name):
    sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)
    all_values = sheet.get_all_values()

    # Ignorar a primeira linha e usar a segunda como cabeçalho
    headers = all_values[1]
    data = all_values[2:]

    # Criar DataFrame
    df = pd.DataFrame(data, columns=headers)

    # Remover a coluna "Status" se existir
    if "Status" in df.columns:
        df.drop(columns=["Status"], inplace=True)

    # Converter colunas numéricas automaticamente
    for col in df.columns[1:]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["DATA"] = pd.to_datetime(df["DATA"], format="%d-%b-%Y", errors="coerce")
    return df

# Função para gerar gráficos
def generate_graph(df, exame_selecionado, data_inicial, data_final, marcos_temporais):
    df_filtrado = df[(df["DATA"] >= data_inicial) & (df["DATA"] <= data_final)]

    plt.figure(figsize=(10, 6))
    plt.plot(df_filtrado["DATA"], df_filtrado[exame_selecionado], marker="o", label=f"{exame_selecionado} (valor)")
    plt.xlabel("Data")
    plt.ylabel(exame_selecionado)
    plt.title(f"{exame_selecionado} ao longo do tempo")
    plt.xticks(rotation=45)

    # Adicionar marcos temporais
    for data, evento in marcos_temporais:
        plt.axvline(data, linestyle="--", color="red", alpha=0.7, label=evento)

    plt.legend()
    plt.grid()
    return plt

# Função para salvar gráficos em cache
graph_cache = []  # Lista para armazenar gráficos

def save_graph_to_cache(graph):
    if len(graph_cache) >= 10:
        graph_cache.pop(0)  # Remover o gráfico mais antigo se atingir o limite
    graph_cache.append(graph)

# Configuração do Streamlit
st.title("Monitoramento de Pacientes")

# Aba de navegação
tabs = st.tabs(["Visualizar Dados", "Gráficos Gerados"])

# Aba: Visualizar Dados
with tabs[0]:
    try:
        df = get_data(sheet_name)

        if not df.empty:
            st.sidebar.header("Configuração do Gráfico")
            exames_disponiveis = [col for col in df.columns if col != "DATA"]
            exame_selecionado = st.sidebar.selectbox("Selecione o exame:", exames_disponiveis)

            # Selecionar intervalo de tempo
            data_inicial = st.sidebar.date_input("Data inicial:", min_value=df["DATA"].min(), max_value=df["DATA"].max(), value=df["DATA"].min())
            data_final = st.sidebar.date_input("Data final:", min_value=df["DATA"].min(), max_value=df["DATA"].max(), value=df["DATA"].max())

            # Adicionar marcos temporais
            st.sidebar.subheader("Marcos Temporais")
            marcos_temporais = []
            if "marcos" not in st.session_state:
                st.session_state["marcos"] = []

            with st.sidebar.expander("Adicionar Marcos Temporais"):
                nova_data = st.date_input("Data do Marco:", key="nova_data")
                novo_evento = st.text_input("Descrição do Evento:", key="novo_evento")
                if st.button("Adicionar Marco"):
                    if nova_data and novo_evento:
                        st.session_state["marcos"].append((pd.to_datetime(nova_data), novo_evento))

            marcos_temporais = st.session_state["marcos"]

            # Gerar gráfico
            graph = generate_graph(df, exame_selecionado, pd.to_datetime(data_inicial), pd.to_datetime(data_final), marcos_temporais)
            st.pyplot(graph)

            # Botão para salvar gráfico
            if st.button("Salvar Gráfico"):
                save_graph_to_cache(graph)
                st.success("Gráfico salvo com sucesso!")
        else:
            st.error("Nenhum dado válido foi carregado. Verifique a planilha.")
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")

# Aba: Gráficos Gerados
with tabs[1]:
    st.header("Gráficos Gerados")
    if graph_cache:
        for i, cached_graph in enumerate(graph_cache):
            st.pyplot(cached_graph)
            st.markdown(f"Gráfico {i+1}")
    else:
        st.write("Nenhum gráfico salvo ainda.")
