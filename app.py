import streamlit as st
from google.oauth2.service_account import Credentials
import gspread
import pandas as pd
import matplotlib.pyplot as plt
import os
import json
from datetime import datetime
from io import BytesIO

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
def generate_graph(df, exame_selecionado, data_inicial, data_final, marcos_temporais, faixas_temporais):
    df_filtrado = df[(df["DATA"] >= data_inicial) & (df["DATA"] <= data_final)]

    plt.figure(figsize=(12, 8))  # Maior tamanho para parecer mais "científico"
    plt.plot(df_filtrado["DATA"], df_filtrado[exame_selecionado], marker="o", label=f"{exame_selecionado} (valor)")
    plt.xlabel("Data")
    plt.ylabel(exame_selecionado)
    plt.title(f"{exame_selecionado} ao longo do tempo", fontsize=16)
    plt.xticks(rotation=45, ha="right")  # Rotação e alinhamento do texto no eixo X
    plt.grid(alpha=0.5)

    # Adicionar marcos temporais
    for data, evento in marcos_temporais:
        plt.axvline(data, linestyle="--", color="red", alpha=0.7, label=evento)

    # Adicionar faixas temporais
    for inicio, fim, descricao in faixas_temporais:
        plt.axvspan(inicio, fim, color="yellow", alpha=0.3, label=descricao)

    plt.legend()
    plt.tight_layout()  # Ajustar margens automaticamente para evitar cortes

    # Salvar gráfico em memória como imagem
    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")  # Garantir que o gráfico completo seja salvo
    buf.seek(0)
    plt.close()
    return buf

# Configuração do Streamlit
st.title("Monitoramento de Pacientes")

# Aba de navegação
tabs = st.tabs(["Visualizar Dados"])

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
            if "marcos" not in st.session_state:
                st.session_state["marcos"] = []

            with st.sidebar.expander("Adicionar ou Remover Marcos Temporais"):
                nova_data = st.date_input("Data do Marco:", key="nova_data")
                novo_evento = st.text_input("Descrição do Evento:", key="novo_evento")
                if st.button("Adicionar Marco"):
                    if nova_data and novo_evento:
                        st.session_state["marcos"].append((pd.to_datetime(nova_data), novo_evento))
                if st.session_state["marcos"]:
                    st.write("Marcos Adicionados:")
                    for i, (data, evento) in enumerate(st.session_state["marcos"]):
                        st.write(f"{i + 1}: {data.date()} - {evento}")
                        if st.button(f"Remover {evento}", key=f"remove_{i}"):
                            st.session_state["marcos"].pop(i)

            marcos_temporais = st.session_state["marcos"]

            # Adicionar faixas de datas
            st.sidebar.subheader("Faixas de Datas")
            if "faixas" not in st.session_state:
                st.session_state["faixas"] = []

            with st.sidebar.expander("Adicionar ou Remover Faixas de Datas"):
                faixa_inicio = st.date_input("Início da Faixa:", key="faixa_inicio")
                faixa_fim = st.date_input("Fim da Faixa:", key="faixa_fim")
                descricao_faixa = st.text_input("Descrição da Faixa:", key="descricao_faixa")
                if st.button("Adicionar Faixa"):
                    if faixa_inicio and faixa_fim and descricao_faixa:
                        st.session_state["faixas"].append((pd.to_datetime(faixa_inicio), pd.to_datetime(faixa_fim), descricao_faixa))
                if st.session_state["faixas"]:
                    st.write("Faixas Adicionadas:")
                    for i, (inicio, fim, descricao) in enumerate(st.session_state["faixas"]):
                        st.write(f"{i + 1}: {inicio.date()} - {fim.date()} ({descricao})")
                        if st.button(f"Remover Faixa: {descricao}", key=f"remove_faixa_{i}"):
                            st.session_state["faixas"].pop(i)

            faixas_temporais = st.session_state["faixas"]

            # Gerar gráfico
            graph = generate_graph(df, exame_selecionado, pd.to_datetime(data_inicial), pd.to_datetime(data_final), marcos_temporais, faixas_temporais)
            st.pyplot(plt.imread(graph), clear_figure=True)

            # Botão para baixar gráfico
            st.download_button(
                label="Baixar Gráfico",
                data=graph,
                file_name=f"{exame_selecionado}_grafico.png",
                mime="image/png"
            )
        else:
            st.error("Nenhum dado válido foi carregado. Verifique a planilha.")
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
