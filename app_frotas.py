import streamlit as st
import pandas as pd
from datetime import datetime
import json
import gspread
from google.oauth2.service_account import Credentials
import traceback
import google.generativeai as genai
from PIL import Image
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

st.set_page_config(page_title="Gestão de Frotas - ITON", page_icon="🚗", layout="centered")

# ==========================================
# 1. LOGIN COM PERFIS
# ==========================================
USUARIOS = {
    "lucas": {"senha": "123", "nome": "Lucas Biazoto (Admin)", "papel": "admin"},
    "kauai": {"senha": "123", "nome": "Kauai Darlei dos Santos Vieira", "papel": "lider"},
    "diego": {"senha": "123", "nome": "Diego de Faria Santos", "papel": "lider"},
    "jefferson": {"senha": "123", "nome": "Jefferson Santos Nascimento", "papel": "lider"},
    "gilberto": {"senha": "123", "nome": "Gilberto Bento de Souza Santos", "papel": "lider"}
}

def check_password():
    if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
    if not st.session_state["logged_in"]:
        st.markdown("<h2 style='text-align: center;'>🚗 Frotas - ITON</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            usuario = st.text_input("👤 Usuário (Primeiro nome)", key="login_user").lower().strip()
            senha = st.text_input("🔑 Senha", type="password", key="login_pass")
            if st.button("Entrar no Sistema", use_container_width=True, type="primary"):
                if usuario in USUARIOS and USUARIOS[usuario]["senha"] == senha:
                    st.session_state["logged_in"] = True
                    st.session_state["usuario_atual"] = usuario
                    st.session_state["nome_usuario"] = USUARIOS[usuario]["nome"]
                    st.session_state["papel"] = USUARIOS[usuario]["papel"]
                    st.rerun()
                else: st.error("Usuário ou senha incorretos.")
        return False
    return True

if not check_password(): st.stop()

# ==========================================
# 2. CONEXÕES GERAIS E IA
# ==========================================
@st.cache_resource
def conectar_google():
    try:
        credenciais_dict = json.loads(st.secrets["google_credentials"])
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(credenciais_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        # Conexão com a planilha (usando o link direto)
        documento = client.open_by_url("https://docs.google.com/spreadsheets/d/1oI9pPGXngdE1jrOaQGIRhHMfLnt_Evh9tN_9lQkLaOU/edit?gid=1342849862#gid=1342849862")
        aba_diario = documento.worksheet("DIARIO_FROTA")
        aba_financeiro = documento.worksheet("FINANCEIRO_FROTA")
        
        # Conexão Drive
        drive_service = build('drive', 'v3', credentials=creds)
        
        # COLOQUE O SEU ID AQUI NOVAMENTE!
        PASTA_ID = "1qgEiEr2sbpjOAqN0ZvJH64VhvFpEZ7TZ" 
        
        return aba_diario, aba_financeiro, drive_service, PASTA_ID
    except Exception as e:
        st.error("🚨 Erro de conexão com o Google Sheets ou Drive.")
        st.stop()

def configurar_ia():
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-3.5-flash')
        return model
    except Exception as e:
        st.error("🚨 Erro de configuração da IA.")
        return None

aba_diario, aba_financeiro, drive_service, PASTA_ID = conectar_google()
modelo_ia = configurar_ia()

# ==========================================
# LISTAS BASE
# ==========================================
LISTA_VEICULOS = ["Gol (Empresa)", "Livina - 7 Lugares (Empresa)", "Uno (Empresa)", "Veículo Alugado (Localiza/Unidas)"]
LISTA_COLABORADORES = ["Danilo Alves de Oliveira", "Diego de Faria Santos", "Diego Sergio Simão", "Evane Jacinto Pacheco", "Flavio Mateus", "Francisco Damazio Moraes", "Hebert Deivison Silveira Pereira", "Jeferson Miranda do Cabo", "Jefferson Santos Nascimento", "Jonathan Araújo Mendonça", "Jorge Esbrisse Martins", "Kauai Darlei dos Santos Vieira", "Marco Aurelio Jesus da Costa", "Paulo Cesar de Souza", "Rafael Damaciano", "Robinson William dos Santos Machado", "Kauã Rodrigues Roza", "Niuleno Alves de Souza"]
LISTA_COLABORADORES.sort()

if "sucesso" not in st.session_state: st.session_state["sucesso"] = False

# ==========================================
# 3. CABEÇALHO
# ==========================================
col_titulo, col_user = st.columns([3, 1])
with col_titulo: st.markdown("<h2>🚗 Frota & Despesas</h2>", unsafe_allow_html=True)
with col_user:
    st.write(f"👤 **{st.session_state['nome_usuario'].split()[0]}**")
    if st.button("Sair", use_container_width=True):
        st.session_state["logged_in"] = False
        st.rerun()
st.divider()

if st.session_state["sucesso"]:
    st.success("🎉 Registro salvo com sucesso!")
    st.balloons()
    if st.button("⬅️ Voltar", type="primary", use_container_width=True):
        st.session_state["sucesso"] = False
        st.rerun()
    st.stop()

is_admin = st.session_state["papel"] == "admin"
abas = st.tabs(["📋 Checklist", "💸 Registrar Gasto", "💰 Painel Admin (Saldos)"] if is_admin else ["📋 Checklist", "💸 Registrar Gasto", "💰 Meu Saldo"])

# ------------------------------------------
# ABA 1: CHECKLIST DIÁRIO
# ------------------------------------------
with abas[0]:
    st.markdown("**Vistoria Rápida (Antes de sair com o carro)**")
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        mot_chk = st.selectbox("👷 Motorista:", ["Selecione..."] + LISTA_COLABORADORES, key="chk_mot")
        vei_chk = st.selectbox("🚗 Veículo:", ["Selecione..."] + LISTA_VEICULOS, key="chk_vei")
    with col_v2:
        km_atual = st.number_input("📟 Hodômetro (KM do Painel):", min_value=0, step=1)
    
    col_i1, col_i2 = st.columns(2)
    with col_i1: luz_painel = st.radio("🚨 Luz de alerta no painel?", ["Não, tudo apagado", "Sim, tem luz acesa"])
    with col_i2: pneus = st.radio("🛞 Pneu murcho/danificado?", ["Não, estão OK", "Sim, avariado"])
        
    foto_painel = st.file_uploader("📸 Foto do Painel (Obrigatório)", type=['png', 'jpg', 'jpeg'], key="foto_chk")
    obs
