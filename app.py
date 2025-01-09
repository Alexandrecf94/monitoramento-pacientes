import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
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

# Autorizar cliente do gspread
client = gspread.authorize(creds)

# ID da planilha e aba
spreadsheet_id = "12m2kUbhJnjjUPqyoJiu0YOxvw7x5jtfdtZuMbfEQLfo"  # Substitua pelo ID correto da sua planilha
sheet_name = "Laboratório"       # Nome da aba

# Função para carregar os dados
def get_data(sheet_name):
    sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)
    all_values = sheet.get_all_values()
    headers = all_values[0]  # Pressupõe cabeçalho na primeira linha
    data = all_values[1:]    # Dados começam na segunda linha
    return pd.DataFrame(data, columns=headers)

# Configuração do Streamlit
st.title("Monitoramento de Pacientes")
df = get_data(sheet_name)

# Exibir os dados
st.write("Dados do Laboratório:")
st.dataframe(df)

# Verificar se as colunas necessárias existem
if "DATA" in df.columns and "Hemoglobina" in df.columns:
    # Gráfico de Hemoglobina
    plt.figure(figsize=(10, 6))
    plt.plot(df["DATA"], pd.to_numeric(df["Hemoglobina"], errors="coerce"), marker="o", label="Hemoglobina (g/dL)")
    plt.xlabel("Data")
    plt.ylabel("Hemoglobina (g/dL)")
    plt.title("Hemoglobina ao longo do tempo")
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid()
    st.pyplot(plt)
else:
    st.error("Colunas 'DATA' e/ou 'Hemoglobina' não encontradas no DataFrame.")
