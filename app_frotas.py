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
# 1. SISTEMA DE LOGIN COM PERFIS
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
        st.markdown("<p style='text-align: center;'>Faça o login para acessar o sistema.</p>", unsafe_allow_html=True)
        
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
        
        # Link da planilha MESTRE
        LINK_DA_PLANILHA = "https://docs.google.com/spreadsheets/d/1oI9pPGXngdE1jrOaQGIRhHMfLnt_Evh9tN_9lQkLaOU/edit?gid=1342849862#gid=1342849862"
        documento = client.open_by_url(LINK_DA_PLANILHA)
        
        aba_diario = documento.worksheet("DIARIO_FROTA")
        aba_financeiro = documento.worksheet("FINANCEIRO_FROTA")
        
        return aba_diario, aba_financeiro
    except Exception as e:
        st.error("🚨 Erro de conexão com a planilha.")
        st.code(traceback.format_exc(), language="python")
        st.stop()

aba_diario, aba_financeiro = conectar_google()

# ==========================================
# LISTAS BASE
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

# Gerenciamento de Estado
if "sucesso" not in st.session_state: st.session_state["sucesso"] = False

# ==========================================
# 3. CABEÇALHO DO APLICATIVO
# ==========================================
col_titulo, col_user = st.columns([3, 1])
with col_titulo:
    st.markdown("<h2>🚗 Frota & Despesas</h2>", unsafe_allow_html=True)
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

# ==========================================
# DEFINIÇÃO DAS ABAS POR PERFIL
# ==========================================
is_admin = st.session_state["papel"] == "admin"

if is_admin:
    abas = st.tabs(["📋 Checklist", "💸 Registrar Gasto", "💰 Painel Admin (Saldos)"])
else:
    abas = st.tabs(["📋 Checklist", "💸 Registrar Gasto", "💰 Meu Saldo"])

# ------------------------------------------
# ABA 1: CHECKLIST DIÁRIO (VISTORIA)
# ------------------------------------------
with abas[0]:
    st.markdown("**Vistoria Rápida (Antes de sair com o carro)**")
    
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        mot_chk = st.selectbox("👷 Motorista:", ["Selecione..."] + LISTA_COLABORADORES, key="chk_mot")
        vei_chk = st.selectbox("🚗 Veículo:", ["Selecione..."] + LISTA_VEICULOS, key="chk_vei")
    with col_v2:
        km_atual = st.number_input("📟 Hodômetro (KM do Painel):", min_value=0, step=1)
        
    st.markdown("**Inspeção:**")
    col_i1, col_i2 = st.columns(2)
    with col_i1:
        luz_painel = st.radio("🚨 Luz de alerta no painel?", ["Não, tudo apagado", "Sim, tem luz acesa"])
    with col_i2:
        pneus = st.radio("🛞 Pneu murcho/danificado?", ["Não, estão OK", "Sim, avariado"])
        
    obs_chk = st.text_area("📝 Observações (Ex: Bateram no carro):", placeholder="Opcional...")
    
    if st.button("✅ Enviar Vistoria", type="primary", use_container_width=True):
        if mot_chk == "Selecione..." or vei_chk == "Selecione...":
            st.error("Selecione motorista e veículo.")
        elif km_atual == 0:
            st.error("Informe o KM.")
        else:
            with st.spinner("Salvando..."):
                data_hora = datetime.now().strftime("%d/%m/%Y %H:%M")
                obs = obs_chk if obs_chk.strip() else "-"
                aba_diario.append_row([data_hora, mot_chk, vei_chk, km_atual, luz_painel, pneus, obs])
                st.session_state["sucesso"] = True
                st.rerun()

# ------------------------------------------
# ABA 2: REGISTRAR GASTO (MOTORISTA)
# ------------------------------------------
with abas[1]:
    st.markdown("**Lançamento de Despesas do Veículo**")
    
    # Motorista seleciona seus dados
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        data_gasto = st.date_input("📅 Data do Gasto:")
        mot_gasto = st.selectbox("👷 Quem gastou?", ["Selecione..."] + LISTA_COLABORADORES, key="gasto_mot")
    with col_g2:
        vei_gasto = st.selectbox("🚗 Veículo:", ["Selecione..."] + LISTA_VEICULOS, key="gasto_vei")
        tipo_gasto = st.selectbox("💳 Categoria:", ["Combustível", "Pedágio", "Manutenção", "Lava-rápido"])
        
    valor_gasto = st.number_input("💰 Valor Total Gasto (R$):", min_value=0.0, step=10.0, format="%.2f")
    
    # Placeholder para a futura IA
    foto_nota = st.file_uploader("📸 Anexar Foto da Nota (Para conferência futura da IA)", type=['png', 'jpg', 'jpeg'])
    if foto_nota:
        st.info("🤖 Em breve: A Inteligência Artificial lerá esta nota automaticamente!")

    obs_gasto = st.text_area("📝 Observações (Nome do posto, etc):", placeholder="Opcional...")
    
    if st.button("✅ Salvar Despesa", type="primary", use_container_width=True):
        if mot_gasto == "Selecione..." or vei_gasto == "Selecione...":
            st.error("Selecione motorista e veículo.")
        elif valor_gasto <= 0:
            st.error("O valor deve ser maior que zero.")
        else:
            with st.spinner("Salvando gasto..."):
                obs = obs_gasto if obs_gasto.strip() else "-"
                linha = [
                    data_gasto.strftime("%d/%m/%Y"), mot_gasto, vei_gasto, 
                    "Saída (Gasto)", tipo_gasto, str(valor_gasto).replace('.', ','), obs
                ]
                aba_financeiro.append_row(linha)
                st.session_state["sucesso"] = True
                st.rerun()

# ------------------------------------------
# ABA 3: SALDOS E ADIANTAMENTOS
# ------------------------------------------
with abas[2]:
    # Lógica para buscar e calcular saldos
    with st.spinner("Calculando saldos da planilha..."):
        dados_fin = aba_financeiro.get_all_records()
        df_fin = pd.DataFrame(dados_fin)
    
    # Se houver dados, converte valores para número
    if not df_fin.empty:
        # Pega a coluna pelo nome correto
        df_fin['Valor (R$)'] = df_fin['Valor (R$)'].astype(str).str.replace(',', '.').astype(float)
        
    if is_admin:
        st.markdown("### 💸 Lançar Novo Adiantamento (PIX)")
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            data_ad = st.date_input("📅 Data do PIX:")
            mot_ad = st.selectbox("👷 Para quem?", ["Selecione..."] + LISTA_COLABORADORES, key="ad_mot")
        with col_a2:
            valor_ad = st.number_input("💰 Valor Enviado (R$):", min_value=0.0, step=50.0, format="%.2f")
            
        if st.button("✅ Registrar PIX Enviado", type="primary", use_container_width=True):
            if mot_ad == "Selecione...": st.error("Selecione o motorista.")
            elif valor_ad <= 0: st.error("Valor inválido.")
            else:
                with st.spinner("Registrando envio..."):
                    linha = [
                        data_ad.strftime("%d/%m/%Y"), mot_ad, "-", 
                        "Entrada (Adiantamento)", "PIX da Empresa", str(valor_ad).replace('.', ','), "Adiantamento"
                    ]
                    aba_financeiro.append_row(linha)
                    st.session_state["sucesso"] = True
                    st.rerun()
                    
        st.divider()
        st.markdown("### 📊 Visão Geral de Saldos (Toda a Equipe)")
        if not df_fin.empty:
            resumo = []
            for motorista in df_fin['Motorista'].unique():
                df_mot = df_fin[df_fin['Motorista'] == motorista]
                entradas = df_mot[df_mot['Tipo Movimento'] == 'Entrada (Adiantamento)']['Valor (R$)'].sum()
                saidas = df_mot[df_mot['Tipo Movimento'] == 'Saída (Gasto)']['Valor (R$)'].sum()
                saldo = entradas - saidas
                if saldo != 0: # Mostra só quem tem dinheiro em mãos ou quem tirou do bolso
                    resumo.append({"Motorista": motorista, "Saldo Atual": f"R$ {saldo:.2f}"})
            
            if resumo:
                st.dataframe(pd.DataFrame(resumo), use_container_width=True)
            else:
                st.info("Nenhum saldo pendente com os motoristas.")
                
    else: # VISÃO DO LÍDER/MOTORISTA
        st.markdown("### 💰 Meu Saldo de Adiantamento")
        if df_fin.empty:
            st.info("Você ainda não tem movimentações.")
        else:
            nome_usuario = st.session_state["nome_usuario"]
            # Encontra o nome exato na lista pelo primeiro nome
            nome_completo = next((nome for nome in LISTA_COLABORADORES if nome.split()[0].lower() == st.session_state["usuario_atual"]), None)
            
            if nome_completo:
                df_meu = df_fin[df_fin['Motorista'] == nome_completo]
                minhas_entradas = df_meu[df_meu['Tipo Movimento'] == 'Entrada (Adiantamento)']['Valor (R$)'].sum()
                minhas_saidas = df_meu[df_meu['Tipo Movimento'] == 'Saída (Gasto)']['Valor (R$)'].sum()
                meu_saldo = minhas_entradas - minhas_saidas
                
                cor = "green" if meu_saldo >= 0 else "red"
                st.markdown(f"<h1 style='text-align: center; color: {cor};'>R$ {meu_saldo:.2f}</h1>", unsafe_allow_html=True)
                st.markdown("<p style='text-align: center;'>Valor que você ainda tem em mãos da empresa.</p>", unsafe_allow_html=True)
                
                st.write("**Meu Extrato:**")
                st.dataframe(df_meu[['Data', 'Tipo Movimento', 'Valor (R$)']], use_container_width=True)
