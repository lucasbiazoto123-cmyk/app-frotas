import streamlit as st
import pandas as pd
from datetime import datetime
import json
import gspread
from google.oauth2.service_account import Credentials
import google.generativeai as genai
from PIL import Image
import io
import requests
import base64

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
# 2. CONEXÕES (SHEETS E IA)
# ==========================================
@st.cache_resource
def conectar_google():
    try:
        credenciais_dict = json.loads(st.secrets["google_credentials"])
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(credenciais_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        # Conexão com as planilhas
        documento = client.open_by_url("https://docs.google.com/spreadsheets/d/1oI9pPGXngdE1jrOaQGIRhHMfLnt_Evh9tN_9lQkLaOU/edit?gid=1342849862#gid=1342849862")
        aba_diario = documento.worksheet("DIARIO_FROTA")
        aba_financeiro = documento.worksheet("FINANCEIRO_FROTA")
        
        return aba_diario, aba_financeiro
    except Exception as e:
        st.error("🚨 Erro de conexão com o Google Sheets.")
        st.stop()

def configurar_ia():
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        # Retornamos para o modelo LITE para ter mais requisições gratuitas (15 por minuto)
        model = genai.GenerativeModel('gemini-3.5-flash-lite')
        return model
    except Exception as e:
        st.error("🚨 Erro de conexão com a Inteligência Artificial.")
        return None

aba_diario, aba_financeiro = conectar_google()
modelo_ia = configurar_ia()

# ==========================================
# LISTAS BASE
# ==========================================
LISTA_VEICULOS = ["Gol (Empresa)", "Livina - 7 Lugares (Empresa)", "Uno (Empresa)", "Veículo Alugado (Localiza/Unidas)"]
LISTA_COLABORADORES = ["Danilo Alves de Oliveira", "Diego de Faria Santos", "Diego Sergio Simão", "Evane Jacinto Pacheco", "Flavio Mateus", "Francisco Damazio Moraes", "Hebert Deivison Silveira Pereira", "Jeferson Miranda do Cabo", "Jefferson Santos Nascimento", "Jonathan Araújo Mendonça", "Jorge Esbrisse Martins", "Kauai Darlei dos Santos Vieira", "Marco Aurelio Jesus da Costa", "Paulo Cesar de Souza", "Rafael Damaciano", "Robinson William dos Santos Machado", "Kauã Rodrigues Roza", "Niuleno Alves de Souza"]
LISTA_COLABORADORES.sort()

if "sucesso" not in st.session_state: st.session_state["sucesso"] = False

# ==========================================
# 3. CABEÇALHO E NAVEGAÇÃO
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
    obs_chk = st.text_area("📝 Observações:", placeholder="Opcional...")
    
    if st.button("✅ Enviar Vistoria", type="primary", use_container_width=True):
        if mot_chk == "Selecione..." or vei_chk == "Selecione..." or km_atual == 0 or not foto_painel:
            st.error("⚠️ Preencha TODOS os campos e anexe a foto do painel para enviar.")
        else:
            with st.spinner("Salvando vistoria..."):
                data_hora = datetime.now().strftime("%d/%m/%Y %H:%M")
                obs = obs_chk if obs_chk.strip() else "-"
                aba_diario.append_row([data_hora, mot_chk, vei_chk, km_atual, luz_painel, pneus, obs])
                st.session_state["sucesso"] = True
                st.rerun()

# ------------------------------------------
# ABA 2: REGISTRAR GASTO (IA + IMGBB)
# ------------------------------------------
with abas[1]:
    st.markdown("**Lançamento de Despesas do Veículo**")
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        data_gasto = st.date_input("📅 Data do Gasto:")
        mot_gasto = st.selectbox("👷 Quem gastou?", ["Selecione..."] + LISTA_COLABORADORES, key="gasto_mot")
    with col_g2:
        vei_gasto = st.selectbox("🚗 Veículo:", ["Selecione..."] + LISTA_VEICULOS, key="gasto_vei")
        tipo_gasto = st.selectbox("💳 Categoria:", ["Combustível", "Pedágio", "Manutenção", "Lava-rápido"])
        
    valor_gasto = st.number_input("💰 Valor Total Gasto (R$):", min_value=0.0, step=10.0, format="%.2f")
    foto_nota = st.file_uploader("📸 Foto da Nota Fiscal (Obrigatório)", type=['png', 'jpg', 'jpeg'], key="foto_nota")
    obs_gasto = st.text_area("📝 Observações (Nome do posto, etc):", placeholder="Opcional...")
    
    if st.button("✅ Salvar Despesa", type="primary", use_container_width=True):
        if mot_gasto == "Selecione..." or vei_gasto == "Selecione...":
            st.error("⚠️ Você esqueceu de selecionar o Motorista ou Veículo.")
        elif valor_gasto <= 0:
            st.error("⚠️ O valor do gasto não pode ser zero.")
        elif not foto_nota:
            st.error("⚠️ A foto da nota fiscal é OBRIGATÓRIA.")
        else:
            with st.spinner("🤖 A IA está auditando a nota fiscal, aguarde..."):
                try:
                    # 1. ABRIR E COMPRIMIR A FOTO (REDUZ PESO PARA NÃO TRAVAR A IA)
                    imagem_aberta = Image.open(foto_nota)
                    if imagem_aberta.mode != 'RGB':
                        imagem_aberta = imagem_aberta.convert('RGB')
                    imagem_aberta.thumbnail((800, 800))
                    
                    # 2. IA ANALISA A FOTO
                    comando_ia = f"Leia esta nota fiscal. O valor total legível nela é exatamente R$ {valor_gasto:.2f}? Responda apenas 'APROVADO' se bater, ou 'RECUSADO - [motivo]' se não bater ou não estiver legível."
                    resposta_ia = modelo_ia.generate_content([comando_ia, imagem_aberta])
                    texto_resposta = resposta_ia.text.strip().upper()
                    
                    if texto_resposta.startswith("APROVADO"):
                        st.success("✅ IA Aprovou o valor! Enviando comprovante para a nuvem...")
                        
                        # 3. ENVIAR FOTO PARA O IMGBB (Nuvem de imagens)
                        img_byte_arr = io.BytesIO()
                        imagem_aberta.save(img_byte_arr, format='JPEG', quality=80)
                        encoded_image = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
                        
                        url_imgbb = "https://api.imgbb.com/1/upload"
                        payload = {
                            "key": st.secrets["IMGBB_API_KEY"],
                            "image": encoded_image
                        }
                        resposta_imgbb = requests.post(url_imgbb, data=payload)
                        link_nota = resposta_imgbb.json()["data"]["url"]
                        
                        # 4. SALVAR NA PLANILHA GOOGLE
                        obs_final = obs_gasto if obs_gasto.strip() else "-"
                        
                        linha = [
                            data_gasto.strftime("%d/%m/%Y"), 
                            mot_gasto, 
                            vei_gasto, 
                            "Saída (Gasto)", 
                            tipo_gasto, 
                            float(valor_gasto), 
                            obs_final,
                            link_nota  # Link cai na coluna H
                        ]
                        aba_financeiro.append_row(linha)
                        st.session_state["sucesso"] = True
                        st.rerun()
                    else:
                        st.error("🚨 A Inteligência Artificial RECUSOU este lançamento.")
                        st.warning(f"**Motivo:** {texto_resposta}")
                except Exception as e:
                    st.error("Erro na comunicação com a IA ou envio da imagem.")
                    st.code(str(e))

# ------------------------------------------
# ABA 3: SALDOS (COM BLINDAGEM ANTI-ESPAÇO)
# ------------------------------------------
def blindagem_moeda(valor):
    if isinstance(valor, (int, float)): return float(valor)
    v = str(valor).upper().replace('R$', '').strip()
    if not v: return 0.0
    if '.' in v and ',' in v: v = v.replace('.', '').replace(',', '.')
    elif ',' in v: v = v.replace(',', '.')
    try: return float(v)
    except: return 0.0

with abas[2]:
    with st.spinner("Calculando saldos em tempo real..."):
        try:
            dados_fin = aba_financeiro.get_all_records()
            df_fin = pd.DataFrame(dados_fin)
            if not df_fin.empty:
                df_fin.columns = df_fin.columns.str.strip()
                if 'Valor (R$)' in df_fin.columns: 
                    df_fin['Valor (R$)'] = df_fin['Valor (R$)'].apply(blindagem_moeda)
        except Exception as e:
            df_fin = pd.DataFrame()
    
    if is_admin:
        st.markdown("### 💸 Lançar Novo Adiantamento (PIX)")
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            data_ad = st.date_input("📅 Data do PIX:")
            mot_ad = st.selectbox("👷 Para quem?", ["Selecione..."] + LISTA_COLABORADORES, key="ad_mot")
        with col_a2:
            valor_ad = st.number_input("💰 Valor Enviado (R$):", min_value=0.0, step=50.0, format="%.2f")
            
        if st.button("✅ Registrar PIX Enviado", type="primary", use_container_width=True):
            if mot_ad == "Selecione..." or valor_ad <= 0: 
                st.error("Preencha o motorista e o valor corretamente.")
            else:
                # Agora são 8 colunas para bater com a planilha (a última vazia para o link da foto)
                linha = [data_ad.strftime("%d/%m/%Y"), mot_ad, "-", "Entrada (Adiantamento)", "PIX da Empresa", float(valor_ad), "Adiantamento", "-"]
                aba_financeiro.append_row(linha)
                st.session_state["sucesso"] = True
                st.rerun()
                    
        st.divider()
        st.markdown("### 📊 Visão Geral de Saldos")
        if not df_fin.empty and 'Motorista' in df_fin.columns:
            resumo = []
            for motorista in df_fin['Motorista'].unique():
                if str(motorista).strip() == "": continue
                df_mot = df_fin[df_fin['Motorista'] == motorista]
                entradas = df_mot[df_mot['Tipo Movimento'].str.strip() == 'Entrada (Adiantamento)']['Valor (R$)'].sum() if 'Tipo Movimento' in df_fin.columns else 0
                saidas = df_mot[df_mot['Tipo Movimento'].str.strip() == 'Saída (Gasto)']['Valor (R$)'].sum() if 'Tipo Movimento' in df_fin.columns else 0
                saldo = entradas - saidas
                if saldo != 0: resumo.append({"Motorista": motorista, "Saldo Atual": f"R$ {saldo:.2f}".replace('.', ',')})
            if resumo: st.dataframe(pd.DataFrame(resumo), use_container_width=True)
            else: st.info("Nenhum saldo pendente encontrado.")
        else: st.info("Aguardando os primeiros lançamentos...")
                
    else: 
        st.markdown("### 💰 Meu Saldo de Adiantamento")
        if df_fin.empty or 'Motorista' not in df_fin.columns:
            st.info("Você ainda não tem movimentações registradas.")
        else:
            nome_completo = next((nome for nome in LISTA_COLABORADORES if nome.split()[0].lower() == st.session_state["usuario_atual"]), None)
            if nome_completo:
                df_meu = df_fin[df_fin['Motorista'] == nome_completo]
                minhas_entradas = df_meu[df_meu['Tipo Movimento'].str.strip() == 'Entrada (Adiantamento)']['Valor (R$)'].sum() if 'Tipo Movimento' in df_fin.columns else 0
                minhas_saidas = df_meu[df_meu['Tipo Movimento'].str.strip() == 'Saída (Gasto)']['Valor (R$)'].sum() if 'Tipo Movimento' in df_fin.columns else 0
                meu_saldo = minhas_entradas - minhas_saidas
                cor = "green" if meu_saldo >= 0 else "red"
                
                st.markdown(f"<h1 style='text-align: center; color: {cor};'>R$ {meu_saldo:.2f}</h1>".replace('.', ','), unsafe_allow_html=True)
                st.markdown("<p style='text-align: center;'>Valor que você ainda tem em mãos da empresa.</p>", unsafe_allow_html=True)
                
                st.write("**Meu Extrato:**")
                if not df_meu.empty:
                     colunas_para_mostrar = [col for col in ['Data', 'Tipo Movimento', 'Valor (R$)'] if col in df_meu.columns]
                     df_extrato = df_meu[colunas_para_mostrar].copy()
                     df_extrato['Valor (R$)'] = df_extrato['Valor (R$)'].apply(lambda x: f"R$ {float(x):.2f}".replace('.', ','))
                     st.dataframe(df_extrato, use_container_width=True, hide_index=True)
