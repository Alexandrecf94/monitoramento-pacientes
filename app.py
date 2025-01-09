import streamlit as st

# Função para autenticação básica
def autenticar():
    # Inicializar o estado de autenticação se ainda não existir
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False  # Usuário começa como não autenticado

    # Verificar se o usuário está autenticado
    if not st.session_state["autenticado"]:
        # Exibir tela de login
        st.title("Login")
        login = st.text_input("Usuário", key="login")
        senha = st.text_input("Senha", type="password", key="senha")
        if st.button("Entrar"):
            # Validar as credenciais fixas
            if login == "admin" and senha == "1234":
                st.session_state["autenticado"] = True
                st.experimental_rerun()  # Recarregar para limpar a tela de login
            else:
                st.error("Usuário ou senha incorretos.")
        st.stop()  # Para o aplicativo até que a autenticação seja bem-sucedida

# Garantir que a função de autenticação seja chamada antes de tudo
autenticar()

# Código principal do aplicativo
st.title("Bem-vindo ao Monitoramento de Pacientes")
st.write("Você está autenticado!")



from google.oauth2.service_account import Credentials
import gspread
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
import os
import json
from io import BytesIO
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

# Função para carregar os dados de uma aba específica
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
def generate_graph(df, exame_selecionado, data_inicial, data_final, marcos_temporais, faixas_temporais, exibir_valores):
    df_filtrado = df[(df["DATA"] >= data_inicial) & (df["DATA"] <= data_final)]

    plt.figure(figsize=(12, 8))  # Tamanho maior para exibição completa
    plt.plot(df_filtrado["DATA"], df_filtrado[exame_selecionado], marker="o", label=f"{exame_selecionado} (valor)")
    plt.xlabel("Data")
    plt.ylabel(exame_selecionado)
    plt.title(f"{exame_selecionado} ao longo do tempo", fontsize=16)
    plt.xticks(rotation=45, ha="right")
    plt.grid(alpha=0.5)

    # Adicionar valores sobre os pontos
    if exibir_valores:    
        for x, y in zip(df_filtrado["DATA"], df_filtrado[exame_selecionado]):
            plt.text(x, y + 0.1, f"{y:.2f}", fontsize=9, ha="center", va="bottom", color="blue")

    # Adicionar marcos temporais
    for data, evento in marcos_temporais:
        plt.axvline(data, linestyle="--", color="red", alpha=0.7, label=evento)

    # Adicionar faixas temporais
    for inicio, fim, descricao in faixas_temporais:
        plt.axvspan(inicio, fim, color="yellow", alpha=0.3, label=descricao)

    plt.legend()
    plt.tight_layout()  # Ajuste automático das margens

    # Salvar gráfico em memória como imagem
    buf = BytesIO()
    plt.savefig(buf, format="png")  # Removido bbox_inches para evitar corte
    buf.seek(0)
    plt.close()
    return buf

# Configuração do Streamlit
st.title("Monitoramento de Pacientes")

# Menu lateral para escolher seção
secoes = ["Laboratório", "Clínica", "Conduta", "Discussão Clínica Simulada"]
secao_selecionada = st.sidebar.selectbox("Selecione a Seção:", secoes)

# Seção: Laboratório
if secao_selecionada == "Laboratório":
    st.header("Seção: Laboratório")
    tabs = st.tabs(["Gráficos", "Relatórios Automáticos", "Ajustar Gráficos com IA"])

    # Aba: Gráficos
    with tabs[0]:
        try:
            df = get_data("Laboratório")

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

                # Exibir valores nos pontos
                exibir_valores = st.sidebar.checkbox("Exibir valores nos pontos", value=False)

                # Gerar gráfico
                graph_buf = generate_graph(df, exame_selecionado, pd.to_datetime(data_inicial), pd.to_datetime(data_final), marcos_temporais, faixas_temporais, exibir_valores)
                st.image(graph_buf, caption=f"{exame_selecionado} ao longo do tempo")

                # Botão para baixar gráfico
                st.download_button("Baixar Gráfico", data=graph_buf, file_name=f"{exame_selecionado}_grafico.png", mime="image/png")
            else:
                st.error("Nenhum dado válido foi carregado. Verifique a planilha.")
        except Exception as e:
            st.error(f"Erro ao carregar os dados: {e}")

    # Aba: Relatórios Automáticos
    with tabs[1]:
        st.header("Relatórios Automáticos")
        st.write("Em desenvolvimento...")

    # Aba: Ajustar Gráficos com IA
    with tabs[2]:
        st.header("Ajustar Gráficos com IA")
        st.write("Digite comandos para ajustar os gráficos automaticamente usando IA.")

        comando = st.text_input("Digite o comando:", placeholder="Exemplo: Adicione uma linha de tendência ao gráfico.")
        if st.button("Executar Comando"):
            # Simulação de processamento de comando
            st.success(f"Comando recebido: {comando}")
            st.info("Integração com IA em desenvolvimento...")

# Seção: Clínica
elif secao_selecionada == "Clínica":
    st.header("Seção: Clínica")
    try:
        df_clinica = get_data("Evolução Clínica")

        tabs_clinica = st.tabs(["Resumo da História Clínica", "Linha Temporal"])

        # Aba: Resumo da História Clínica
        with tabs_clinica[0]:
            st.subheader("Resumo da História Clínica")
            st.write("**Dados Importantes:**")
            st.write(df_clinica)

            if st.button("Gerar Resumo da História Clínica"):
                resumo = "\n".join([f"{linha['DATA']}: {linha['DESCRICAO']}" for _, linha in df_clinica.iterrows()])
                st.text_area("Resumo Gerado:", value=resumo, height=200)

        # Aba: Linha Temporal
        with tabs_clinica[1]:
            st.subheader("Linha Temporal")

            if not df_clinica.empty:
                plt.figure(figsize=(12, 8))

                for i, row in df_clinica.iterrows():
                    plt.scatter(pd.to_datetime(row["DATA"]), i, label=row["DESCRICAO"])
                    plt.text(pd.to_datetime(row["DATA"]), i, row["DESCRICAO"], fontsize=9, ha="center", va="bottom")

                plt.xlabel("Data")
                plt.ylabel("Eventos")
                plt.title("Linha Temporal da História Clínica", fontsize=16)
                plt.grid(alpha=0.5)
                st.pyplot(plt)

    except Exception as e:
        st.error(f"Erro ao carregar os dados da clínica: {e}")

# Seção: Conduta
elif secao_selecionada == "Conduta":
    st.header("Seção: Conduta")
    try:
        df_conduta = get_data("Conduta")

        tabs_conduta = st.tabs(["Condutas Registradas", "Insights de Conduta"])

        # Aba: Condutas Registradas
        with tabs_conduta[0]:
            st.subheader("Condutas Registradas")
            st.write(df_conduta)

        # Aba: Insights de Conduta
        with tabs_conduta[1]:
            st.subheader("Insights de Conduta")
            st.write("Em desenvolvimento...")
            if st.button("Gerar Insights"):
                st.info("Integração com IA em desenvolvimento...")

    except Exception as e:
        st.error(f"Erro ao carregar os dados da conduta: {e}")

# Seção: Discussão Clínica Simulada
elif secao_selecionada == "Discussão Clínica Simulada":
    st.header("Discussão Clínica Simulada")
    st.write("Digite sua pergunta para obter uma análise clínica baseada nos dados do paciente.")

    pergunta = st.text_input("Pergunta:", placeholder="Exemplo: Quais exames adicionais devo solicitar?")
    if st.button("Consultar Especialista"):
        # Simulação de resposta da IA
        st.success("Baseado nos dados, sugere-se hemograma completo e perfil renal.")
        st.info("Integração com IA em desenvolvimento...")

