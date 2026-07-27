import streamlit as st
import pandas as pd
from datetime import datetime
import json
import gspread
from google.oauth2.service_account import Credentials
import traceback

# Configuração da Página
st.set_page_config(page_title="Gestão de Frotas - ITON", page_icon="🚗", layout="centered")

# ==========================================
# 1. SISTEMA DE LOGIN (O MESMO DOS OUTROS)
# ==========================================
USUARIOS = {
    "lucas": {"senha": "123", "nome": "Lucas Biazoto (Admin)", "papel": "admin"},
    "kauai": {"senha": "123", "nome": "Kauai Darlei dos Santos Vieira", "papel": "lider"},
    "diego": {"senha": "123", "nome": "Diego de Faria Santos", "papel": "lider"},
    "jefferson": {"senha": "123", "nome": "Jefferson Santos Nascimento", "papel": "lider"},
    "gilberto": {"senha": "123", "nome": "Gilberto Bento de Souza Santos", "papel": "lider"}
}

def check_password():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        st.markdown("<h2 style='text-align: center;'>🚗 Frotas - ITON</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Faça o login para acessar os veículos.</p>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            usuario = st.text_input("👤 Usuário (Seu primeiro nome)", key="login_user").lower().strip()
            senha = st.text_input("🔑 Senha", type="password", key="login_pass")
            
            if st.button("Entrar no Sistema", use_container_width=True, type="primary"):
                if usuario in USUARIOS and USUARIOS[usuario]["senha"] == senha:
                    st.session_state["logged_in"] = True
                    st.session_state["usuario_atual"] = usuario
                    st.session_state["nome_usuario"] = USUARIOS[usuario]["nome"]
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
        return False
    return True

if not check_password():
    st.stop()

# ==========================================
# 2. CONEXÃO COM O GOOGLE SHEETS
# ==========================================
def conectar_google():
    try:
        credenciais_dict = json.loads(st.secrets["google_credentials"])
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(credenciais_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        # O SEU LINK MESTRE DA PLANILHA GERAL
        LINK_DA_PLANILHA = "https://docs.google.com/spreadsheets/d/1oI9pPGXngdE1jrOaQGIRhHMfLnt_Evh9tN_9lQkLaOU/edit?gid=1342849862#gid=1342849862"
        
        documento = client.open_by_url(LINK_DA_PLANILHA)
        
        # Abre as duas abas novas que você criou
        aba_diario = documento.worksheet("DIARIO_FROTA")
        aba_financeiro = documento.worksheet("FINANCEIRO_FROTA")
        
        return aba_diario, aba_financeiro
    except Exception as e:
        st.error("🚨 Erro fatal ao conectar com o Google.")
        st.code(traceback.format_exc(), language="python")
        st.stop()

aba_diario, aba_financeiro = conectar_google()

# ==========================================
# LISTAS BASE (CARROS E EQUIPE)
# ==========================================
LISTA_VEICULOS = [
    "Gol (Empresa)", 
    "Livina - 7 Lugares (Empresa)", 
    "Uno (Empresa)",
    "Veículo Alugado (Localiza/Unidas)"
]

LISTA_COLABORADORES = [
    "Danilo Alves de Oliveira", "Diego de Faria Santos", "Diego Sergio Simão", 
    "Evane Jacinto Pacheco", "Flavio Mateus", "Francisco Damazio Moraes", 
    "Hebert Deivison Silveira Pereira", "Jeferson Miranda do Cabo", 
    "Jefferson Santos Nascimento", "Jonathan Araújo Mendonça", 
    "Jorge Esbrisse Martins", "Kauai Darlei dos Santos Vieira", 
    "Marco Aurelio Jesus da Costa", "Paulo Cesar de Souza", "Rafael Damaciano", 
    "Robinson William dos Santos Machado", "Kauã Rodrigues Roza", "Niuleno Alves de Souza"
]
LISTA_COLABORADORES.sort()

# Gerenciamento de Estado para as Telas de Confirmação
if "revisao_checklist" not in st.session_state:
    st.session_state["revisao_checklist"] = None
if "revisao_financeiro" not in st.session_state:
    st.session_state["revisao_financeiro"] = None
if "sucesso" not in st.session_state:
    st.session_state["sucesso"] = False

# ==========================================
# 3. CABEÇALHO DO APLICATIVO
# ==========================================
col_titulo, col_user = st.columns([3, 1])
with col_titulo:
    st.markdown("<h2>🚗 Gestão de Frotas</h2>", unsafe_allow_html=True)
with col_user:
    st.write(f"👤 **{st.session_state['nome_usuario'].split()[0]}**")
    if st.button("Sair"):
        st.session_state["logged_in"] = False
        st.rerun()

st.divider()

# ==========================================
# TELA DE SUCESSO (Comum para os dois módulos)
# ==========================================
if st.session_state["sucesso"]:
    st.success("🎉 Registro enviado para a planilha com sucesso!")
    st.balloons()
    if st.button("⬅️ Fazer Novo Lançamento", type="primary", use_container_width=True):
        st.session_state["sucesso"] = False
        st.rerun()
    st.stop()

# ==========================================
# NAVEGAÇÃO POR ABAS
# ==========================================
aba1, aba2 = st.tabs(["📋 Checklist Diário (Vistoria)", "💸 Financeiro (Abastecimento)"])

# ------------------------------------------
# MÓDULO 1: CHECKLIST DIÁRIO
# ------------------------------------------
with aba1:
    if st.session_state["revisao_checklist"] is not None:
        # TELA DE REVISÃO DO CHECKLIST
        dados = st.session_state["revisao_checklist"]
        st.info("🔍 Confira os dados da vistoria antes de enviar:")
        
        st.write(f"**Veículo:** {dados[2]}")
        st.write(f"**Hodômetro:** {dados[3]} KM")
        st.write(f"**Luzes de Alerta:** {dados[4]}")
        st.write(f"**Pneus:** {dados[5]}")
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if st.button("✅ SALVAR VISTORIA", type="primary", use_container_width=True, key="btn_salvar_chk"):
                aba_diario.append_row(dados)
                st.session_state["revisao_checklist"] = None
                st.session_state["sucesso"] = True
                st.rerun()
        with col_c2:
            if st.button("❌ CORRIGIR", use_container_width=True, key="btn_corr_chk"):
                st.session_state["revisao_checklist"] = None
                st.rerun()
    else:
        # TELA DE PREENCHIMENTO DO CHECKLIST
        st.markdown("Preencha rapidamente antes de ligar o veículo.")
        
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            motorista_chk = st.selectbox("👷 Motorista:", ["Selecione..."] + LISTA_COLABORADORES, key="mot_chk")
            veiculo_chk = st.selectbox("🚗 Qual o veículo?", ["Selecione..."] + LISTA_VEICULOS, key="vei_chk")
        
        with col_v2:
            km_atual = st.number_input("📟 Hodômetro (KM do Painel):", min_value=0, step=1)
            
        st.markdown("**Inspeção Visual Rápida:**")
        col_i1, col_i2 = st.columns(2)
        with col_i1:
            luz_painel = st.radio("🚨 Tem alguma luz vermelha/amarela acesa no painel?", ["Não, tudo apagado", "Sim, tem luz acesa"])
        with col_i2:
            pneus = st.radio("🛞 Algum pneu parece murcho ou danificado?", ["Não, estão OK", "Sim, parece murcho/furado"])
            
        obs_chk = st.text_area("📝 Observações (Ex: Bateram no carro, ar parou, etc):", placeholder="Opcional...")
        
        if st.button("👀 Conferir Checklist", type="primary", use_container_width=True):
            if motorista_chk == "Selecione..." or veiculo_chk == "Selecione...":
                st.error("⚠️ Selecione o Motorista e o Veículo.")
            elif km_atual == 0:
                st.error("⚠️ Informe o KM atual do painel.")
            else:
                data_hora = datetime.now().strftime("%d/%m/%Y %H:%M")
                if obs_chk.strip() == "": obs_chk = "-"
                
                # Prepara a linha para a aba DIARIO_FROTA
                linha_chk = [data_hora, motorista_chk, veiculo_chk, km_atual, luz_painel, pneus, obs_chk]
                st.session_state["revisao_checklist"] = linha_chk
                st.rerun()

# ------------------------------------------
# MÓDULO 2: FINANCEIRO (ABASTECIMENTO)
# ------------------------------------------
with aba2:
    if st.session_state["revisao_financeiro"] is not None:
        # TELA DE REVISÃO DO FINANCEIRO
        dados_fin = st.session_state["revisao_financeiro"]
        st.info("🔍 Confira os dados financeiros antes de enviar:")
        
        st.write(f"**Veículo:** {dados_fin[2]}")
        st.write(f"**Tipo de Gasto:** {dados_fin[3]}")
        st.write(f"**Valor Pago:** R$ {dados_fin[4]}")
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            if st.button("✅ SALVAR GASTO", type="primary", use_container_width=True, key="btn_salvar_fin"):
                aba_financeiro.append_row(dados_fin)
                st.session_state["revisao_financeiro"] = None
                st.session_state["sucesso"] = True
                st.rerun()
        with col_f2:
            if st.button("❌ CORRIGIR", use_container_width=True, key="btn_corr_fin"):
                st.session_state["revisao_financeiro"] = None
                st.rerun()
    else:
        # TELA DE PREENCHIMENTO DO FINANCEIRO
        st.markdown("Registre os gastos com o veículo (Sempre peça Nota Fiscal).")
        
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            data_fin = st.date_input("📅 Data do Gasto:")
            motorista_fin = st.selectbox("👷 Motorista:", ["Selecione..."] + LISTA_COLABORADORES, key="mot_fin")
            veiculo_fin = st.selectbox("🚗 Veículo abastecido:", ["Selecione..."] + LISTA_VEICULOS, key="vei_fin")
            
        with col_g2:
            tipo_gasto = st.selectbox("💳 Tipo de Despesa:", [
                "Abastecimento (Gasolina/Etanol)", 
                "Abastecimento (Diesel)", 
                "Pedágio", 
                "Lavagem", 
                "Manutenção (Borracharia, Peças)"
            ])
            valor_gasto = st.number_input("💰 Valor Total (R$):", min_value=0.0, step=10.0, format="%.2f")
            
        obs_fin = st.text_area("📝 Observações (Ex: Posto Ipiranga, Pneu Furado):", placeholder="Opcional...")
        
        if st.button("👀 Conferir Gasto", type="primary", use_container_width=True):
            if motorista_fin == "Selecione..." or veiculo_fin == "Selecione...":
                st.error("⚠️ Selecione o Motorista e o Veículo.")
            elif valor_gasto <= 0:
                st.error("⚠️ O valor gasto deve ser maior que zero.")
            else:
                data_formatada = data_fin.strftime("%d/%m/%Y")
                if obs_fin.strip() == "": obs_fin = "-"
                
                # Prepara a linha para a aba FINANCEIRO_FROTA
                linha_fin = [
                    data_formatada, motorista_fin, veiculo_fin, tipo_gasto, 
                    str(valor_gasto).replace('.', ','), obs_fin
                ]
                st.session_state["revisao_financeiro"] = linha_fin
                st.rerun()
