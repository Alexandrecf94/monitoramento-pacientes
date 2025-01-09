import streamlit as st
from google.oauth2.service_account import Credentials
import gspread
import pandas as pd
import matplotlib.pyplot as plt
import os
import json

# Configuração do Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

# Carregar credenciais do Secrets
credentials_json = os.getenv("GOOGLE_CREDENTIALS")
creds = Credentials.from_service_account_info(json.loads(credentials_json), scopes=SCOPES)

# Autorizar cliente do Google Sheets
client = gspread.authorize(creds)

# ID da sua planilha no Google Sheets
spreadsheet_id = "12m2kUbhJnjjUPqyoJiu0YOxvw7x5jtfdtZuMbfEQLfo"  # Substitua pelo ID correto

# Nome da aba que você quer acessar
sheet_name = "Laboratório"

# Função para carregar os dados da aba
@st.cache_data(ttl=600)  # Cache com validade de 10 minutos
def get_data(sheet_name):
    sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)
    all_values = sheet.get_all_values()

    # Ignorar a primeira linha (sem dados úteis) e usar a segunda linha como cabeçalho
    headers = all_values[1]  # A segunda linha contém os títulos
    data = all_values[2:]    # Dados começam na terceira linha

    # Criar DataFrame
    df = pd.DataFrame(data, columns=headers)

    # Converter colunas numéricas para tipo correto
    for col in ["Hemoglobina", "Hematócrito", "Leucócitos", "Plaquetas", "Glicemia", "Ureia"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Converter a coluna de datas
    df["DATA"] = pd.to_datetime(df["DATA"], format="%d-%b-%Y", errors="coerce")

    return df

# Função para gerar gráficos
def plot_graph(df, exame_selecionado, data_inicial, data_final, marcos):
    # Filtrar os dados pelo intervalo de tempo
    df_filtrado = df[(df["DATA"] >= pd.to_datetime(data_inicial)) & (df["DATA"] <= pd.to_datetime(data_final))]

    # Criar o gráfico
    plt.figure(figsize=(10, 6))
    plt.plot(df_filtrado["DATA"], df_filtrado[exame_selecionado], marker="o", label=f"{exame_selecionado} (valor)")
    plt.xlabel("Data")
    plt.ylabel(exame_selecionado)
    plt.title(f"{exame_selecionado} ao longo do tempo")
    plt.xticks(rotation=45)

    # Adicionar marcos temporais
    for linha in marcos:
        plt.axvline(pd.to_datetime(linha["data"]), linestyle="--", color="red", alpha=0.7, label=linha["evento"])

    plt.legend()
    plt.grid()
    return plt

# Configuração do Streamlit
st.title("Monitoramento de Pacientes")

# Carregar dados
try:
    df = get_data(sheet_name)

    if not df.empty:
        # Controle para selecionar exame
        st.sidebar.header("Configuração do Gráfico")
        exame_selecionado = st.sidebar.selectbox(
            "Selecione o exame:", 
            df.columns[1:]  # Exibe todas as colunas (exceto "DATA")
        )

        # Controle para selecionar intervalo de tempo
        data_inicial = st.sidebar.date_input("Data inicial:", value=df["DATA"].min(), min_value=df["DATA"].min(), max_value=df["DATA"].max())
        data_final = st.sidebar.date_input("Data final:", value=df["DATA"].max(), min_value=df["DATA"].min(), max_value=df["DATA"].max())

        # Controle para marcos temporais
        st.sidebar.subheader("Marcos Temporais")
        marcos_temporais = []
        with st.sidebar.expander("Adicionar Marcos Temporais"):
            if st.button("Adicionar"):
                nova_data = st.date_input("Data do Marco:")
                novo_evento = st.text_input("Descrição do Evento:")
                if nova_data and novo_evento:
                    marcos_temporais.append({"data": nova_data, "evento": novo_evento})

        # Gerar gráfico
        plt = plot_graph(df, exame_selecionado, data_inicial, data_final, marcos_temporais)
        st.pyplot(plt)

    else:
        st.error("Nenhum dado válido foi carregado. Verifique a planilha.")
except Exception as e:
    st.error(f"Erro ao carregar os dados: {e}")



