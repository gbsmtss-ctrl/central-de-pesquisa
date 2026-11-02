import base64
import calendar
from datetime import datetime, date, time
from io import BytesIO
import json
import os
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import qrcode
import streamlit as st

# Tenta importar ReportLab (fallback para PIL caso ausente)
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    REPORTLAB_DISPONIVEL = True
except ImportError:
    REPORTLAB_DISPONIVEL = False

st.set_page_config(
    page_title="Central de Pesquisa - Gestão do Laboratório",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- INJEÇÃO DE CSS: ESTILO APP-LIKE E PALETA DE CORES ---
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    [data-testid="stToolbar"] {display: none;}
    
    .stApp { background-color: #F8FAFC; }
    [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E2E8F0; }
    
    [data-testid="stSidebar"] div.stButton > button {
        text-align: left !important;
        justify-content: flex-start !important;
        padding: 8px 12px !important;
        width: 100% !important;
        margin-bottom: 3px !important;
        border-radius: 6px !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
    }
    
    [data-testid="stSidebar"] div.stButton > button[kind="secondary"] {
        background-color: transparent !important;
        color: #475569 !important;
        border: none !important;
    }
    [data-testid="stSidebar"] div.stButton > button[kind="secondary"]:hover {
        background-color: #F1F5F9 !important;
        color: #0E7490 !important;
    }
    
    [data-testid="stSidebar"] div.stButton > button[kind="primary"] {
        background-color: #ECFEFF !important;
        color: #0E7490 !important;
        font-weight: 700 !important;
        border-left: 4px solid #0E7490 !important;
        border-top: none !important; border-right: none !important; border-bottom: none !important;
    }

    h1, h2, h3 { color: #0F172A !important; font-family: 'Segoe UI', Roboto, sans-serif; }
    
    .sidebar-section {
        font-size: 0.70rem; font-weight: 800; color: #94A3B8;
        text-transform: uppercase; margin-top: 1.2rem; margin-bottom: 0.4rem; letter-spacing: 0.08em;
    }

    .kpi-card {
        border-radius: 10px; padding: 16px 20px; border: 1px solid #E2E8F0;
        display: flex; align-items: center; justify-content: space-between; box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }
    .kpi-card-blue { background-color: #F0F9FF; border-left: 4px solid #0284C7; }
    .kpi-card-green { background-color: #ECFDF5; border-left: 4px solid #059669; }
    .kpi-card-amber { background-color: #FFFBEB; border-left: 4px solid #D97706; }
    .kpi-card-purple { background-color: #F5F3FF; border-left: 4px solid #7C3AED; }
    
    .kpi-val { font-size: 1.8rem; font-weight: 800; color: #0F172A; line-height: 1; }
    .kpi-label { font-size: 0.82rem; font-weight: 600; color: #475569; margin-top: 4px; }
    .kpi-icon { font-size: 2rem; opacity: 0.85; }

    .badge-ativo { background-color: #DCFCE7; color: #15803D; padding: 3px 10px; border-radius: 12px; font-weight: 700; font-size: 0.78rem; display: inline-block; }
    .badge-pendente { background-color: #FEF3C7; color: #B45309; padding: 3px 10px; border-radius: 12px; font-weight: 700; font-size: 0.78rem; display: inline-block; }
    .avatar-circle { width: 38px; height: 38px; border-radius: 50%; background-color: #E2E8F0; color: #334155; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; }
    .css-card { background-color: white; padding: 16px; border-radius: 8px; border: 1px solid #E2E8F0; box-shadow: 0 1px 3px rgba(0,0,0,0.02); margin-bottom: 12px; }
    .aviso-card { background-color: #FFFFFF; border-radius: 8px; padding: 14px 16px; margin-bottom: 10px; border-left: 4px solid #0E7490; box-shadow: 0 1px 3px rgba(0,0,0,0.02); }
    .event-card { background-color: #FFFFFF; border-radius: 8px; padding: 12px 14px; margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.02); border: 1px solid #E2E8F0; }
    .pop-preview-card { background-color: #FFFFFF; border: 1px solid #CBD5E1; border-left: 4px solid #0E7490; border-radius: 8px; padding: 16px; margin-bottom: 15px; }
    .tree-orientador { background-color: #F8FAFC; border: 1px solid #E2E8F0; border-left: 4px solid #0E7490; padding: 12px 16px; border-radius: 8px; margin-top: 15px; font-weight: bold; font-size: 0.95rem; color: #0F172A; }
    .tree-orientado { background-color: #FFFFFF; border: 1px solid #E2E8F0; padding: 10px 14px; border-radius: 6px; margin-left: 24px; margin-top: 6px; display: flex; align-items: center; justify-content: space-between; }
    .table-header { font-size: 0.72rem; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em; padding-bottom: 6px; border-bottom: 1px solid #E2E8F0; margin-bottom: 10px; }
    </style>
""",
    unsafe_allow_html=True,
)

# --- ARQUIVOS JSON DE PERSISTÊNCIA ---
ARQUIVO_INTEGRANTES = "integrantes.json"
ARQUIVO_AGENDA = "agenda.json"
ARQUIVO_USUARIOS = "usuarios.json"
ARQUIVO_ARQUIVOS = "arquivos.json"
ARQUIVO_PASTAS = "pastas.json"
ARQUIVO_POPS = "pops.json"
ARQUIVO_AVISOS = "avisos.json"
ARQUIVO_GRUPOS = "grupos_pesquisa.json"

CATEGORIAS_PADRAO = ["Iniciação Científica", "Mestrado", "Doutorado", "Pós-Doutorado", "Orientador", "Técnico / Pesquisador"]
CORES_GOOGLE_AGENDA = {
    "🔵 Azul (Reunião / Geral)": "#0284C7", "🟢 Verde (Ensaio / Experimento)": "#059669",
    "🔴 Vermelho (Urgente / Importante)": "#DC2626", "🟣 Roxo (Apresentação / Defesa)": "#7C3AED",
    "🟠 Laranja (Manutenção / Limpeza)": "#EA580C", "🟡 Dourado (Prazo / Entrega)": "#D97706", "🩵 Ciano (Treinamento)": "#0891B2",
}
REAGENTES_CADASTRADOS = ["Extrato Enzimático de Lipase", "Solução Tampão Fosfato 0.1M (pH 7.0)", "Álcool Etílico 70%", "Reagente de Bradford", "Meio de Cultura BDA", "Solução de NaOH 1M", "Ácido Clorídrico 0.5M"]
POPS_PADRAO = ["Operação e Higienização do Espectrofotômetro", "Preparo de Solução Tampão Fosfato", "Calibração e Uso do pHmetro", "Esterilização em Autoclave", "Higienização de Capela de Fluxo Laminar"]
DESTINOS_ETIQUETAS = {"Tubo Eppendorf (0.5 mL / 1.5 mL / 2.0 mL)": 15, "Tubo Falcon (15 mL)": 22, "Tubo Falcon (50 mL)": 30, "Frasco / Béquer / Erlenmeyer": 45, "Bancada / Equipamento / Prateleira": 65}

INTEGRANTES_INICIAIS = [
    {"Nome": "Eliane Pereira Cipolatti", "Categoria": "Orientador", "Vínculo": "UFRRJ - Engenharia de Alimentos", "Telefone": "(21) 99999-9999", "Email": "elianecipolatti@ufrrj.br", "DiasHorarios": "Seg e Qua - 08:00 às 17:00", "Lattes": "http://lattes.cnpq.br/", "Situação": "Ativo", "Orientador": "-", "Coorientador": "-", "OrientadorStatus": "Aprovado"},
    {"Nome": "Gabriela Mendes Farias Matos", "Categoria": "Mestrado", "Vínculo": "UFRRJ - Química Industrial", "Telefone": "(21) 99677-8065", "Email": "gbsmtsm@ufrrj.br", "DiasHorarios": "Ter e Qui - 09:00 às 18:00", "Lattes": "-", "Situação": "Ativo", "Orientador": "Eliane Pereira Cipolatti", "Coorientador": "-", "OrientadorStatus": "Aprovado"},
]
AVISOS_INICIAIS = [{"id": 1, "titulo": "📢 Manutenção da Autoclave e Capela", "conteudo": "A manutenção preventiva ocorrerá nesta sexta-feira pela manhã. Agende seus ensaios com antecedência.", "categoria": "Manutenção", "cor": "#EA580C", "autor": "Gabriela Mendes Farias Matos", "data": datetime.now().strftime("%d/%m/%Y")}]
AGENDA_INICIAL = [{"id": 1, "titulo": "Reunião de Alinhamento Semanal", "data": datetime.now().strftime("%Y-%m-%d"), "hora_inicio": "09:00", "hora_fim": "10:30", "tipo": "Reunião", "cor": "#0284C7", "descricao": "Discussão dos resultados de fermentação da semana.", "autor": "Gabriela Mendes Farias Matos"}]
PASTAS_INICIAIS = [{"nome": "Geral", "descricao": "Arquivos gerais do laboratório", "criador": "admin", "status": "Aprovado"}, {"nome": "POPs e Protocolos", "descricao": "Procedimentos Operacionais Padrão", "criador": "admin", "status": "Aprovado"}]
POPS_INICIAIS = [{"codigo": "POP-OHE-v1", "titulo": "Operação e Higienização do Espectrofotômetro", "versao": 1, "objetivo": "Padronizar a operação e limpeza do equipamento para garantir medições precisas.", "materiais": "Cubetas de quartzo, álcool 70%, lenço de papel macio, tampões.", "passos": "1. Ligar o equipamento 15 minutos antes da leitura.\n2. Ajustar o comprimento de onda desejado.\n3. Realizar o branco com a solução controle.\n4. Ler as amostras em triplicata.\n5. Higienizar as cubetas após o uso.", "seguranca": "Uso obrigatório de jaleco, luvas de nitrilo e óculos de proteção.", "referencias": "AHA, J. (2020). Spectrophotometry Standards and Practices. Journal of Lab Bio, 12(3), 45-50.", "autor": "Eliane Pereira Cipolatti", "status": "Aprovado"}]
GRUPOS_INICIAIS = [{"id": 1, "nome": "Biocatalise & Tecnologia Enzimática", "descricao": "Pesquisa focada no uso de lipases imobilizadas para produção de biocombustíveis e bioprodtos.", "lider": "Eliane Pereira Cipolatti", "senha": "123", "membros": ["Eliane Pereira Cipolatti", "Gabriela Mendes Farias Matos"], "status": "Aprovado", "solicitante": "Eliane Pereira Cipolatti", "membros_pendentes": [], "agenda": [{"id": 101, "titulo": "Discussão de Artigo - Imobilização de Enzimas", "data": datetime.now().strftime("%Y-%m-%d"), "hora_inicio": "14:00", "hora_fim": "15:30", "descricao": "Leitura e crítica do artigo sobre suporte de sílica mesoporosa.", "autor": "Gabriela Mendes Farias Matos"}], "mural": "📌 **Anotações do Grupo:** Apresentação da qualificação agendada para o próximo mês."}]
usuario_admin_padrao = [{"nome": "Gabriela Mendes Farias Matos", "usuario": "admin", "senha": "123", "categoria": "Mestrado", "vinculo": "UFRRJ - Química Industrial", "telefone": "(21) 99677-8065", "email": "gbsmtsm@ufrrj.br", "status": "Aprovado", "is_admin": True, "orientador": "Eliane Pereira Cipolatti", "coorientador": "-", "orientador_status": "Aprovado"}]

def carregar_dados(arquivo, padrao):
    if os.path.exists(arquivo):
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                dados = json.load(f)
                if dados: return dados
        except Exception: return padrao
    return padrao

def salvar_dados(arquivo, dados):
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

def gerar_codigo_pop(titulo, versao=1):
    palavras = [w for w in titulo.split() if len(w) > 2 and w.lower() not in ["de", "da", "do", "dos", "das", "em", "para", "com", "e"]]
    sigla = "".join([p[0].upper() for p in palavras])[:6] if palavras else "DOC"
    return f"POP-{sigla}-v{versao}"

def gerar_pdf_pop(pop_dict):
    if REPORTLAB_DISPONIVEL:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()
        story = []
        header_data = [
            [Paragraph(f"<b>PROCEDIMENTO OPERACIONAL PADRÃO (POP)</b>", styles['Normal']), Paragraph(f"<b>CÓDIGO:</b> {pop_dict['codigo']}", styles['Normal'])],
            [Paragraph(f"<b>Título:</b> {pop_dict['titulo']}", styles['Normal']), Paragraph(f"<b>Versão:</b> {pop_dict['versao']}", styles['Normal'])],
            [Paragraph(f"<b>Elaborado por:</b> {pop_dict.get('autor', 'N/A')}", styles['Normal']), Paragraph(f"<b>Status:</b> {pop_dict.get('status', 'Aprovado')}", styles['Normal'])]
        ]
        t_header = Table(header_data, colWidths=[350, 180])
        t_header.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F1F5F9')), ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')), ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('PADDING', (0,0), (-1,-1), 6)]))
        story.append(t_header)
        story.append(Spacer(1, 15))
        sections = [("1. OBJETIVO", pop_dict.get("objetivo", "")), ("2. MATERIAIS E EQUIPAMENTOS", pop_dict.get("materiais", "")), ("3. PROCEDIMENTO / PASSO A PASSO", pop_dict.get("passos", "")), ("4. SEGURANÇA E EPIs", pop_dict.get("seguranca", "")), ("5. REFERÊNCIAS BIBLIOGRÁFICAS", pop_dict.get("referencias", "-"))]
        sec_title_style = ParagraphStyle('SecTitle', parent=styles['Heading2'], fontSize=11, leading=14, textColor=colors.HexColor('#0E7490'), bold=True)
        body_style = ParagraphStyle('BodyTextCustom', parent=styles['Normal'], fontSize=9.5, leading=13.5, textColor=colors.HexColor('#334155'))
        for title, content in sections:
            story.append(Paragraph(title, sec_title_style))
            story.append(Spacer(1, 4))
            story.append(Paragraph(str(content).replace('\n', '<br/>'), body_style))
            story.append(Spacer(1, 10))
        doc.build(story)
        return buffer.getvalue()
    else:
        page = Image.new("RGB", (612, 792), "white")
        draw = ImageDraw.Draw(page)
        draw.text((40, 40), f"POP - {pop_dict['codigo']} - {pop_dict['titulo']}", fill="black")
        buf = BytesIO()
        page.save(buf, format="PDF")
        return buf.getvalue()

def gerar_pdf_etiquetas(qr_img_pil, quantidade, mm_size, id_amostra=""):
    dpi = 150
    px_per_mm = dpi / 25.4
    page_w, page_h = int(210 * px_per_mm), int(297 * px_per_mm)
    label_px, margin_px, spacing_px = int(mm_size * px_per_mm), int(10 * px_per_mm), int(4 * px_per_mm)
    pages, current_page = [], Image.new("RGB", (page_w, page_h), "white")
    draw = ImageDraw.Draw(current_page)
    x, y = margin_px, margin_px
    has_text = bool(id_amostra) and label_px >= int(25 * px_per_mm)
    qr_size_px = label_px - int(6 * px_per_mm) if has_text else label_px
    qr_resized = qr_img_pil.resize((qr_size_px, qr_size_px))

    for idx in range(quantidade):
        if x + label_px > page_w - margin_px:
            x = margin_px
            y += label_px + spacing_px
        if y + label_px > page_h - margin_px:
            pages.append(current_page)
            current_page = Image.new("RGB", (page_w, page_h), "white")
            draw = ImageDraw.Draw(current_page)
            x, y = margin_px, margin_px
        draw.rectangle([x, y, x + label_px, y + label_px], outline="lightgray", width=1)
        qr_x = x + (label_px - qr_size_px) // 2
        qr_y = y + (2 if has_text else (label_px - qr_size_px) // 2)
        current_page.paste(qr_resized, (qr_x, qr_y))
        if has_text: draw.text((x + 4, y + qr_size_px + 2), f"ID: {id_amostra[:12]}", fill="black")
        x += label_px + spacing_px
    pages.append(current_page)
    pdf_buffer = BytesIO()
    if len(pages) == 1: pages[0].save(pdf_buffer, format="PDF", resolution=float(dpi))
    else: pages[0].save(pdf_buffer, format="PDF", resolution=float(dpi), save_all=True, append_images=pages[1:])
    return pdf_buffer.getvalue()

# --- SESSÃO GLOBAL ---
if "usuarios" not in st.session_state: st.session_state.usuarios = carregar_dados(ARQUIVO_USUARIOS, usuario_admin_padrao)
if "integrantes" not in st.session_state: st.session_state.integrantes = carregar_dados(ARQUIVO_INTEGRANTES, INTEGRANTES_INICIAIS)
if "agenda" not in st.session_state: st.session_state.agenda = carregar_dados(ARQUIVO_AGENDA, AGENDA_INICIAL)
if "avisos_db" not in st.session_state: st.session_state.avisos_db = carregar_dados(ARQUIVO_AVISOS, AVISOS_INICIAIS)
if "arquivos_db" not in st.session_state: st.session_state.arquivos_db = carregar_dados(ARQUIVO_ARQUIVOS, [])
if "pastas_db" not in st.session_state: st.session_state.pastas_db = carregar_dados(ARQUIVO_PASTAS, PASTAS_INICIAIS)
if "pops_db" not in st.session_state: st.session_state.pops_db = carregar_dados(ARQUIVO_POPS, POPS_INICIAIS)
if "grupos_db" not in st.session_state: st.session_state.grupos_db = carregar_dados(ARQUIVO_GRUPOS, GRUPOS_INICIAIS)
if "grupos_autenticados" not in st.session_state: st.session_state.grupos_autenticados = []
if "pasta_aberta_drive" not in st.session_state: st.session_state.pasta_aberta_drive = None
if "seq_amostra" not in st.session_state: st.session_state.seq_amostra = 1
if "menu_selecionado" not in st.session_state: st.session_state.menu_selecionado = "🏠 Página Inicial & Avisos"

usr_param = st.query_params.get("usr")
if usr_param:
    usr_encontrado = next((u for u in st.session_state.usuarios if str(u.get("usuario")).lower() == str(usr_param).lower() and u.get("status") == "Aprovado"), None)
    st.session_state.usuario_logado = usr_encontrado if usr_encontrado else None
else:
    if "usuario_logado" not in st.session_state: st.session_state.usuario_logado = None

# --- AUTH / LOGIN ---
if st.session_state.usuario_logado is None:
    st.title("🧪 Central de Pesquisa - Controle de Acesso ⚗️")
    aba_login, aba_cadastro, aba_recuperar = st.tabs(["Entrar no Sistema", "Solicitar Acesso", "🔑 Recuperar Senha"])

    with aba_login:
        st.subheader("Login")
        with st.form("form_login"):
            user_input = st.text_input("Usuário, E-mail ou Nome")
            senha_input = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar", type="primary"):
                usr_clean = user_input.strip().lower()
                u_enc = next((u for u in st.session_state.usuarios if usr_clean in [str(u.get("usuario","")).lower(), str(u.get("email","")).lower(), str(u.get("nome","")).lower()]), None)
                if u_enc and u_enc["senha"] == senha_input:
                    if u_enc["status"] == "Aprovado":
                        st.session_state.usuario_logado = u_enc
                        st.query_params["usr"] = u_enc["usuario"]
                        st.rerun()
                    else: st.warning("Cadastro pendente ou suspenso.")
                else: st.error("Usuário ou senha incorretos.")

    with aba_cadastro:
        with st.form("form_solicitar"):
            novo_nome = st.text_input("Nome Completo *")
            nova_cat = st.selectbox("Categoria *", CATEGORIAS_PADRAO)
            novo_vinc = st.text_input("Vínculo *", "UFRRJ - Engenharia Química")
            novo_tel = st.text_input("Telefone *")
            novo_email = st.text_input("E-mail *")
            novo_user = st.text_input("Usuário Desejado *")
            nova_senha = st.text_input("Criar Senha *", type="password")
            if st.form_submit_button("Enviar Solicitação"):
                if novo_nome and novo_user and nova_senha:
                    st.session_state.usuarios.append({"nome": novo_nome, "usuario": novo_user, "senha": nova_senha, "categoria": nova_cat, "vinculo": novo_vinc, "telefone": novo_tel, "email": novo_email, "status": "Pendente", "is_admin": False, "orientador": "-", "coorientador": "-", "orientador_status": "Pendente"})
                    salvar_dados(ARQUIVO_USUARIOS, st.session_state.usuarios)
                    st.success("Solicitação enviada para aprovação!")

    with aba_recuperar:
        with st.form("form_recuperar"):
            r_id = st.text_input("Usuário ou E-mail *")
            r_s1 = st.text_input("Nova Senha *", type="password")
            r_s2 = st.text_input("Confirmar Nova Senha *", type="password")
            if st.form_submit_button("Redefinir Senha"):
                if r_s1 == r_s2 and r_id:
                    u_alvo = next((u for u in st.session_state.usuarios if r_id.lower() in [str(u.get("usuario")).lower(), str(u.get("email")).lower()]), None)
                    if u_alvo:
                        u_alvo["senha"] = r_s1
                        salvar_dados(ARQUIVO_USUARIOS, st.session_state.usuarios)
                        st.success("Senha redefinida com sucesso!")

else:
    usuario_atual = st.session_state.usuario_logado
    is_admin = usuario_atual.get("is_admin", False)
    hoje_str = datetime.now().strftime("%Y-%m-%d")

    # --- SIDEBAR MENU ---
    st.sidebar.markdown('<div style="font-weight:bold; font-size:1.1rem; color:#0E7490;">🧪 Central de Pesquisa</div>', unsafe_allow_html=True)
    
    def nav_btn(chave, rotulo):
        if st.sidebar.button(rotulo, key=f"nav_{chave}", use_container_width=True, type="primary" if st.session_state.menu_selecionado == chave else "secondary"):
            st.session_state.menu_selecionado = chave
            st.rerun()

    st.sidebar.markdown('<div class="sidebar-section">PAINEL PRINCIPAL</div>', unsafe_allow_html=True)
    nav_btn("🏠 Página Inicial & Avisos", "🏠 Página Inicial & Avisos")
    nav_btn("📅 Agenda & Calendário", "📅 Agenda & Calendário")

    st.sidebar.markdown('<div class="sidebar-section">GESTÃO DO LABORATÓRIO</div>', unsafe_allow_html=True)
    nav_btn("👥 Equipe", "👥 Equipe")
    nav_btn("🎓 Orientados", "🎓 Orientados")
    nav_btn("🔬 Grupo de Pesquisa", "🔬 Grupo de Pesquisa")
    nav_btn("🕒 Presença no Laboratório", "🕒 Presença no Laboratório")

    st.sidebar.markdown('<div class="sidebar-section">CONHECIMENTO</div>', unsafe_allow_html=True)
    nav_btn("📁 Repositório de Arquivos", "📁 Repositório de Arquivos")
    nav_btn("🏷️ Gerar QR Code de Amostras", "🏷️ Gerar QR Code de Amostras")
    nav_btn("📝 Criador de POP", "📝 Criador de POP")

    st.sidebar.markdown('<div class="sidebar-section">CONFIGURAÇÕES</div>', unsafe_allow_html=True)
    if is_admin: nav_btn("🛡️ Administração", "🛡️ Administração")
    nav_btn("👤 Meu perfil", "👤 Meu perfil")

    st.sidebar.markdown("---")
    st.sidebar.caption(f"Logado como: **{usuario_atual['nome']}**")
    if st.sidebar.button("🚪 Sair"):
        st.query_params.clear()
        st.session_state.usuario_logado = None
        st.rerun()

    menu = st.session_state.menu_selecionado

    # --- 0. HOME PAGE (GRID METRICS & CONTAINERS WITH BORDER) ---
    if menu == "🏠 Página Inicial & Avisos":
        st.title("🏠 Painel Geral de Pesquisa")
        st.caption(f"Bem-vindo(a), **{usuario_atual['nome']}**!")

        k1, k2, k3, k4 = st.columns(4)
        k1.markdown(f'<div class="kpi-card kpi-card-blue"><div><div class="kpi-val">{len(st.session_state.integrantes)}</div><div class="kpi-label">Integrantes</div></div><div class="kpi-icon">👥</div></div>', unsafe_allow_html=True)
        k2.markdown(f'<div class="kpi-card kpi-card-green"><div><div class="kpi-val">{len([e for e in st.session_state.agenda if e.get("data","") >= hoje_str])}</div><div class="kpi-label">Próximos Eventos</div></div><div class="kpi-icon">📅</div></div>', unsafe_allow_html=True)
        k3.markdown(f'<div class="kpi-card kpi-card-amber"><div><div class="kpi-val">{len(st.session_state.avisos_db)}</div><div class="kpi-label">Avisos Ativos</div></div><div class="kpi-icon">📢</div></div>', unsafe_allow_html=True)
        k4.markdown(f'<div class="kpi-card kpi-card-purple"><div><div class="kpi-val">{len([p for p in st.session_state.pops_db if p.get("status")=="Aprovado"])}</div><div class="kpi-label">POPs Vigentes</div></div><div class="kpi-icon">📝</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        cL, cR = st.columns([1.3, 1])

        with cL:
            with st.container(border=True):
                st.subheader("📢 Mural de Avisos")
                if is_admin:
                    with st.expander("➕ Publicar Novo Aviso"):
                        with st.form("form_aviso"):
                            t_av = st.text_input("Título *")
                            c_av = st.text_area("Conteúdo *")
                            cor_av = st.selectbox("Cor", list(CORES_GOOGLE_AGENDA.keys()))
                            if st.form_submit_button("Publicar") and t_av and c_av:
                                st.session_state.avisos_db.insert(0, {"id": len(st.session_state.avisos_db)+1, "titulo": t_av, "conteudo": c_av, "cor": CORES_GOOGLE_AGENDA[cor_av], "autor": usuario_atual["nome"], "data": datetime.now().strftime("%d/%m/%Y")})
                                salvar_dados(ARQUIVO_AVISOS, st.session_state.avisos_db)
                                st.rerun()

                for av in st.session_state.avisos_db:
                    st.markdown(f'<div class="aviso-card" style="border-left-color: {av.get("cor", "#0E7490")};"><h4>{av["titulo"]}</h4><p>{av["conteudo"]}</p><small>Por {av.get("autor","-")} em {av.get("data","-")}</small></div>', unsafe_allow_html=True)

        with cR:
            with st.container(border=True):
                st.subheader("📅 Próximas Reuniões")
                evs = [e for e in st.session_state.agenda if e.get("data","") >= hoje_str]
                for ev in evs[:5]:
                    st.markdown(f'<div class="event-card" style="border-left: 4px solid {ev.get("cor", "#0284C7")};"><strong>{ev["titulo"]}</strong><div>🕒 {ev.get("data")} das {ev.get("hora_inicio")} às {ev.get("hora_fim")}</div></div>', unsafe_allow_html=True)

    # --- 0.1 AGENDA ---
    elif menu == "📅 Agenda & Calendário":
        st.title("📅 Agenda & Calendário de Atividades")
        t1, t2 = st.tabs(["📆 Visualizar Agenda", "➕ Novo Compromisso"])
        with t1:
            st.subheader("Compromissos Agendados")
            for ev in st.session_state.agenda:
                st.markdown(f'<div class="event-card"><b>{ev["titulo"]}</b> - {ev.get("data")} ({ev.get("hora_inicio")} - {ev.get("hora_fim")})<br/>{ev.get("descricao")}</div>', unsafe_allow_html=True)
        with t2:
            with st.form("form_ev"):
                t_e = st.text_input("Título *")
                d_e = st.date_input("Data *")
                hi_e = st.time_input("Início", time(9,0))
                hf_e = st.time_input("Fim", time(10,0))
                cor_e = st.selectbox("Cor", list(CORES_GOOGLE_AGENDA.keys()))
                desc_e = st.text_area("Descrição")
                if st.form_submit_button("Agendar") and t_e:
                    st.session_state.agenda.append({"id": len(st.session_state.agenda)+1, "titulo": t_e, "data": d_e.strftime("%Y-%m-%d"), "hora_inicio": hi_e.strftime("%H:%M"), "hora_fim": hf_e.strftime("%H:%M"), "cor": CORES_GOOGLE_AGENDA[cor_e], "descricao": desc_e, "autor": usuario_atual["nome"]})
                    salvar_dados(ARQUIVO_AGENDA, st.session_state.agenda)
                    st.success("Agendado!")
                    st.rerun()

    # --- 1. EQUIPE ---
    elif menu == "👥 Equipe":
        st.title("👥 Integrantes do Laboratório")
        for p in st.session_state.integrantes:
            st.markdown(f'<div class="css-card"><b>{p["Nome"]}</b> ({p.get("Categoria")}) - {p.get("Email")}<br/><small>Vínculo: {p.get("Vínculo")} | Orientador: {p.get("Orientador","-")}</small></div>', unsafe_allow_html=True)

    # --- 2. ORIENTADOS ---
    elif menu == "🎓 Orientados":
        st.title("🎓 Hierarquia de Orientação")
        orientadores = [p for p in st.session_state.integrantes if p.get("Categoria") == "Orientador"]
        for o in orientadores:
            st.markdown(f'<div class="tree-orientador">👨‍🏫 Orientador(a): {o["Nome"]}</div>', unsafe_allow_html=True)
            alunos = [a for a in st.session_state.integrantes if a.get("Orientador") == o["Nome"]]
            for al in alunos:
                st.markdown(f'<div class="tree-orientado">└─ 🎓 <b>{al["Nome"]}</b> ({al.get("Categoria")})</div>', unsafe_allow_html=True)

    # --- 2.1 GRUPOS DE PESQUISA (COM SENHA INDIVIDUAL) ---
    elif menu == "🔬 Grupo de Pesquisa":
        st.title("🔬 Área de Grupos de Pesquisa")
        meus_g = [g for g in st.session_state.grupos_db if g.get("status") == "Aprovado" and (usuario_atual["nome"] in g.get("membros", []) or is_admin)]
        if meus_g:
            g_sel = st.selectbox("Selecione o Grupo", [g["nome"] for g in meus_g])
            g_obj = next((g for g in meus_g if g["nome"] == g_sel), meus_g[0])
            
            if (g_obj["id"] not in st.session_state.grupos_autenticados) and not is_admin:
                with st.container(border=True):
                    st.warning(f"🔒 Insira a senha do grupo **{g_obj['nome']}**")
                    with st.form(f"form_pass_{g_obj['id']}"):
                        s_in = st.text_input("Senha", type="password")
                        if st.form_submit_button("Acessar"):
                            if s_in == g_obj.get("senha"):
                                st.session_state.grupos_autenticados.append(g_obj["id"])
                                st.rerun()
                            else: st.error("Senha incorreta.")
            else:
                st.success(f"🔓 Acesso Liberado: **{g_obj['nome']}**")
                st.markdown(f'<div class="css-card">{g_obj.get("descricao")}<br/><br/><b>Líder:</b> {g_obj.get("lider")}<br/><b>Mural:</b> {g_obj.get("mural")}</div>', unsafe_allow_html=True)
        else:
            st.info("Você não participa de nenhum grupo aprovado ainda.")

    # --- 3. PRESENÇA ---
    elif menu == "🕒 Presença no Laboratório":
        st.title("🕒 Presença no Laboratório")
        df_p = pd.DataFrame(st.session_state.integrantes)
        if not df_p.empty and "DiasHorarios" in df_p.columns:
            st.dataframe(df_p[["Nome", "Categoria", "DiasHorarios"]], use_container_width=True)

    # --- 4. REPOSITÓRIO ---
    elif menu == "📁 Repositório de Arquivos":
        st.title("📁 Repositório de Arquivos")
        st.subheader("Pastas Cadastradas")
        for pst in st.session_state.pastas_db:
            st.markdown(f'<div class="css-card">📁 <b>{pst["nome"]}</b> - {pst.get("descricao")}</div>', unsafe_allow_html=True)

    # --- 5. QR CODE ---
    elif menu == "🏷️ Gerar QR Code de Amostras":
        st.title("🏷️ Gerador de QR Code & Etiquetas")
        c1, c2 = st.columns([1, 1])
        with c1:
            id_ams = st.text_input("Código da Amostra", value=f"AMS-{datetime.now().strftime('%Y%m%d')}-001")
            nome_ams = st.selectbox("Reagente / Amostra", REAGENTES_CADASTRADOS)
            qtd = st.number_input("Quantidade de Etiquetas", min_value=1, max_value=50, value=6)
            btn_qr = st.button("Gerar Etiquetas", type="primary")
        with c2:
            if btn_qr or id_ams:
                img_qr = qrcode.make(f"ID: {id_ams}\nAmostra: {nome_ams}")
                buf = BytesIO()
                img_qr.save(buf, format="PNG")
                st.image(buf.getvalue(), width=180)
                pdf_labels = gerar_pdf_etiquetas(img_qr, qtd, 22, id_amostra=id_ams)
                st.download_button("📄 Baixar PDF de Etiquetas", pdf_labels, f"Etiquetas_{id_ams}.pdf", "application/pdf")

    # --- 6. CRIADOR DE POP ---
    elif menu == "📝 Criador de POP":
        st.title("📝 Procedimentos Operacionais Padrão (POPs)")
        tb1, tb2 = st.tabs(["📚 POPs Cadastrados", "➕ Criar POP com Live Preview"])
        with tb1:
            for pop in st.session_state.pops_db:
                st.markdown(f'<div class="pop-preview-card"><h3>📝 {pop["titulo"]} ({pop["codigo"]})</h3><p><b>Objetivo:</b> {pop.get("objetivo")}</p><p><b>Passos:</b> {pop.get("passos")}</p><p><b>Referências:</b> {pop.get("referencias","-")}</p></div>', unsafe_allow_html=True)
                st.download_button(f"📄 Baixar PDF - {pop['codigo']}", gerar_pdf_pop(pop), f"{pop['codigo']}.pdf", "application/pdf", key=f"dl_{pop['codigo']}")
        with tb2:
            cForm, cPrev = st.columns([1, 1])
            with cForm:
                p_tit = st.text_input("Título do POP *", "Higienização de Equipamentos")
                p_cod = gerar_codigo_pop(p_tit)
                p_obj = st.text_area("1. Objetivo *", "Padronizar rotinas.")
                p_mat = st.text_area("2. Materiais *", "Álcool 70%, papel macio.")
                p_pas = st.text_area("3. Passo a Passo *", "1. Ligar o equipamento.\n2. Limpar superfícies.")
                p_seg = st.text_area("4. Segurança *", "Uso de luvas e jaleco.")
                p_ref = st.text_area("5. Referências Bibliográficas *", "Norma ISO 9001 / Manual do Equipamento.")
                if st.button("💾 Salvar POP", type="primary"):
                    st.session_state.pops_db.append({"codigo": p_cod, "titulo": p_tit, "versao": 1, "objetivo": p_obj, "materiais": p_mat, "passos": p_pas, "seguranca": p_seg, "referencias": p_ref, "autor": usuario_atual["nome"], "status": "Aprovado"})
                    salvar_dados(ARQUIVO_POPS, st.session_state.pops_db)
                    st.success("POP cadastrado!")
                    st.rerun()
            with cPrev:
                st.markdown("### 👁️ Live Preview")
                st.markdown(f'<div class="pop-preview-card"><h3>📝 {p_tit}</h3><small>{p_cod}</small><hr/><p><b>Objetivo:</b> {p_obj}</p><p><b>Materiais:</b> {p_mat}</p><p><b>Passos:</b><br/>{p_pas.replace(chr(10),"<br/>")}</p><p><b>Segurança:</b> {p_seg}</p><p><b>Referências:</b> {p_ref}</p></div>', unsafe_allow_html=True)

    # --- 7. ADMINISTRAÇÃO ---
    elif menu == "🛡️ Administração" and is_admin:
        st.title("🛡️ Central de Administração")
        st.subheader("Atribuição de Orientador & Coorientador")
        with st.form("form_admin_or"):
            alunos_cad = [p for p in st.session_state.integrantes if p.get("Categoria") in CATEGORIAS_PADRAO[:4]]
            orient_cad = ["-"] + [p["Nome"] for p in st.session_state.integrantes if p.get("Categoria") == "Orientador"]
            if alunos_cad:
                al_sel_n = st.selectbox("Aluno", [a["Nome"] for a in alunos_cad])
                o_sel = st.selectbox("Orientador Principal", orient_cad)
                co_sel = st.selectbox("Coorientador", orient_cad)
                if st.form_submit_button("Confirmar Orientação", type="primary"):
                    al_obj = next(a for a in alunos_cad if a["Nome"] == al_sel_n)
                    al_obj["Orientador"] = o_sel
                    al_obj["Coorientador"] = co_sel
                    al_obj["OrientadorStatus"] = "Aprovado"
                    salvar_dados(ARQUIVO_INTEGRANTES, st.session_state.integrantes)
                    st.success("Vínculo de orientação atualizado!")
                    st.rerun()

    # --- 8. MEU PERFIL ---
    elif menu == "👤 Meu perfil":
        st.title("👤 Meu Perfil")
        st.write(f"**Nome:** {usuario_atual['nome']}")
        st.write(f"**E-mail:** {usuario_atual.get('email')}")
        st.write(f"**Vínculo:** {usuario_atual.get('vinculo')}")
