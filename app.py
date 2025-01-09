import streamlit as st
from google.oauth2.service_account import Credentials
import gspread
import pandas as pd
import matplotlib.pyplot as plt
import os
import json

# Configuração do Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]

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

    return df

# Configuração do Streamlit
st.title("Monitoramento de Pacientes")

# Carregar dados
try:
    df = get_data(sheet_name)
    if not df.empty:
        st.write("Dados do Laboratório:")
        st.dataframe(df)

        # Gráfico de Hemoglobina
        plt.figure(figsize=(10, 6))
        plt.plot(df["DATA"], df["Hemoglobina"], marker="o", label="Hemoglobina (g/dL)")
        plt.xlabel("Data")
        plt.ylabel("Hemoglobina (g/dL)")
        plt.title("Hemoglobina ao longo do tempo")
        plt.xticks(rotation=45)
        plt.legend()
        plt.grid()
        st.pyplot(plt)
    else:
        st.error("Nenhum dado válido foi carregado. Verifique a planilha.")
except Exception as e:
    st.error(f"Erro ao carregar os dados: {e}")

