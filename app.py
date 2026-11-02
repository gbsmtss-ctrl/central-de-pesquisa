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

# Tenta importar o ReportLab; caso não esteja instalado no Streamlit Cloud, usa fallback com PIL
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    REPORTLAB_DISPONIVEL = True
except ImportError:
    REPORTLAB_DISPONIVEL = False

# Configuração da página
st.set_page_config(
    page_title="Central de Pesquisa - Gestão do Laboratório",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- INJEÇÃO DE CSS: APARÊNCIA APP-LIKE & PALETA CIENTÍFICA COESA ---
st.markdown(
    """
    <style>
    /* Oculta os menus nativos de dev do Streamlit (GitHub, Fork, Top Bar, Footer) */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    [data-testid="stToolbar"] {display: none;}
    
    /* Fundo Geral */
    .stApp {
        background-color: #F8FAFC;
    }
    
    /* Estilização da Barra Lateral */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E2E8F0;
    }
    
    /* Botões do Menu Lateral */
    [data-testid="stSidebar"] div.stButton > button {
        text-align: left !important;
        justify-content: flex-start !important;
        padding: 8px 12px !important;
        width: 100% !important;
        margin-bottom: 3px !important;
        border-radius: 6px !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease-in-out !important;
    }
    
    [data-testid="stSidebar"] div.stButton > button[kind="secondary"] {
        background-color: transparent !important;
        color: #475569 !important;
        border: none !important;
        box-shadow: none !important;
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
        border-top: none !important;
        border-right: none !important;
        border-bottom: none !important;
        box-shadow: none !important;
    }

    h1, h2, h3 {
        color: #0F172A !important;
        font-family: 'Segoe UI', Roboto, sans-serif;
    }
    
    .sidebar-section {
        font-size: 0.70rem;
        font-weight: 800;
        color: #94A3B8;
        text-transform: uppercase;
        margin-top: 1.2rem;
        margin-bottom: 0.4rem;
        letter-spacing: 0.08em;
    }

    /* KPI Cards na Página Inicial */
    .kpi-card {
        border-radius: 10px;
        padding: 16px 20px;
        border: 1px solid #E2E8F0;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }
    .kpi-card-blue { background-color: #F0F9FF; border-left: 4px solid #0284C7; }
    .kpi-card-green { background-color: #ECFDF5; border-left: 4px solid #059669; }
    .kpi-card-amber { background-color: #FFFBEB; border-left: 4px solid #D97706; }
    .kpi-card-purple { background-color: #F5F3FF; border-left: 4px solid #7C3AED; }
    
    .kpi-val { font-size: 1.8rem; font-weight: 800; color: #0F172A; line-height: 1; }
    .kpi-label { font-size: 0.82rem; font-weight: 600; color: #475569; margin-top: 4px; }
    .kpi-icon { font-size: 2rem; opacity: 0.85; }

    /* Badges */
    .badge-ativo {
        background-color: #DCFCE7;
        color: #15803D;
        padding: 3px 10px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 0.78rem;
        display: inline-block;
    }
    .badge-pendente {
        background-color: #FEF3C7;
        color: #B45309;
        padding: 3px 10px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 0.78rem;
        display: inline-block;
    }
    .avatar-circle {
        width: 38px;
        height: 38px;
        border-radius: 50%;
        background-color: #E2E8F0;
        color: #334155;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 0.9rem;
    }
    .css-card {
        background-color: white;
        padding: 16px;
        border-radius: 8px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
        margin-bottom: 12px;
    }
    .aviso-card {
        background-color: #FFFFFF;
        border-radius: 8px;
        padding: 14px 16px;
        margin-bottom: 10px;
        border-left: 4px solid #0E7490;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }
    .event-card {
        background-color: #FFFFFF;
        border-radius: 8px;
        padding: 12px 14px;
        margin-bottom: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
        border: 1px solid #E2E8F0;
    }
    .pop-preview-card {
        background-color: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-left: 4px solid #0E7490;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 15px;
    }
    .tree-orientador {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #0E7490;
        padding: 12px 16px;
        border-radius: 8px;
        margin-top: 15px;
        font-weight: bold;
        font-size: 0.95rem;
        color: #0F172A;
    }
    .tree-orientado {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        padding: 10px 14px;
        border-radius: 6px;
        margin-left: 24px;
        margin-top: 6px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .table-header {
        font-size: 0.72rem;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        padding-bottom: 6px;
        border-bottom: 1px solid #E2E8F0;
        margin-bottom: 10px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- PERSISTÊNCIA DE DADOS EM ARQUIVOS LOCAL/JSON ---
ARQUIVO_INTEGRANTES = "integrantes.json"
ARQUIVO_AGENDA = "agenda.json"
ARQUIVO_USUARIOS = "usuarios.json"
ARQUIVO_ARQUIVOS = "arquivos.json"
ARQUIVO_PASTAS = "pastas.json"
ARQUIVO_POPS = "pops.json"
ARQUIVO_AVISOS = "avisos.json"
ARQUIVO_GRUPOS = "grupos_pesquisa.json"

CATEGORIAS_PADRAO = [
    "Iniciação Científica",
    "Mestrado",
    "Doutorado",
    "Pós-Doutorado",
    "Orientador",
    "Técnico / Pesquisador",
]

CORES_GOOGLE_AGENDA = {
    "🔵 Azul (Reunião / Geral)": "#0284C7",
    "🟢 Verde (Ensaio / Experimento)": "#059669",
    "🔴 Vermelho (Urgente / Importante)": "#DC2626",
    "🟣 Roxo (Apresentação / Defesa)": "#7C3AED",
    "🟠 Laranja (Manutenção / Limpeza)": "#EA580C",
    "🟡 Dourado (Prazo / Entrega)": "#D97706",
    "🩵 Ciano (Treinamento)": "#0891B2",
}

REAGENTES_CADASTRADOS = [
    "Extrato Enzimático de Lipase",
    "Solução Tampão Fosfato 0.1M (pH 7.0)",
    "Álcool Etílico 70%",
    "Reagente de Bradford",
    "Meio de Cultura BDA",
    "Solução de NaOH 1M",
    "Ácido Clorídrico 0.5M",
]

POPS_PADRAO = [
    "Operação e Higienização do Espectrofotômetro",
    "Preparo de Solução Tampão Fosfato",
    "Calibração e Uso do pHmetro",
    "Esterilização em Autoclave",
    "Higienização de Capela de Fluxo Laminar",
]

DESTINOS_ETIQUETAS = {
    "Tubo Eppendorf (0.5 mL / 1.5 mL / 2.0 mL)": 15,
    "Tubo Falcon (15 mL)": 22,
    "Tubo Falcon (50 mL)": 30,
    "Frasco / Béquer / Erlenmeyer": 45,
    "Bancada / Equipamento / Prateleira": 65,
}

INTEGRANTES_INICIAIS = [
    {
        "Nome": "Eliane Pereira Cipolatti",
        "Categoria": "Orientador",
        "Vínculo": "UFRRJ - Engenharia de Alimentos",
        "Telefone": "(21) 99999-9999",
        "Email": "elianecipolatti@ufrrj.br",
        "DiasHorarios": "Seg e Qua - 08:00 às 17:00",
        "Lattes": "http://lattes.cnpq.br/",
        "Situação": "Ativo",
        "Orientador": "-",
        "Coorientador": "-",
        "OrientadorStatus": "Aprovado"
    },
    {
        "Nome": "Gabriela Mendes Farias Matos",
        "Categoria": "Mestrado",
        "Vínculo": "UFRRJ - Química Industrial",
        "Telefone": "(21) 99677-8065",
        "Email": "gbsmtsm@ufrrj.br",
        "DiasHorarios": "Ter e Qui - 09:00 às 18:00",
        "Lattes": "-",
        "Situação": "Ativo",
        "Orientador": "Eliane Pereira Cipolatti",
        "Coorientador": "-",
        "OrientadorStatus": "Aprovado"
    },
]

AVISOS_INICIAIS = [
    {
        "id": 1,
        "titulo": "📢 Manutenção da Autoclave e Capela",
        "conteudo": "A manutenção preventiva ocorrerá nesta sexta-feira pela manhã. Agende seus ensaios com antecedência.",
        "categoria": "Manutenção",
        "cor": "#EA580C",
        "autor": "Gabriela Mendes Farias Matos",
        "data": datetime.now().strftime("%d/%m/%Y"),
    }
]

AGENDA_INICIAL = [
    {
        "id": 1,
        "titulo": "Reunião de Alinhamento Semanal",
        "data": datetime.now().strftime("%Y-%m-%d"),
        "hora_inicio": "09:00",
        "hora_fim": "10:30",
        "tipo": "Reunião",
        "cor": "#0284C7",
        "descricao": "Discussão dos resultados de fermentação da semana.",
        "autor": "Gabriela Mendes Farias Matos"
    }
]

PASTAS_INICIAIS = [
    {"nome": "Geral", "descricao": "Arquivos gerais do laboratório", "criador": "admin", "status": "Aprovado"},
    {"nome": "POPs e Protocolos", "descricao": "Procedimentos Operacionais Padrão", "criador": "admin", "status": "Aprovado"},
]

POPS_INICIAIS = [
    {
        "codigo": "POP-OHE-v1",
        "titulo": "Operação e Higienização do Espectrofotômetro",
        "versao": 1,
        "objetivo": "Padronizar a operação e limpeza do equipamento para garantir medições precisas.",
        "materiais": "Cubetas de quartzo, álcool 70%, lenço de papel macio, tampões.",
        "passos": "1. Ligar o equipamento 15 minutos antes da leitura.\n2. Ajustar o comprimento de onda desejado.\n3. Realizar o branco com a solução controle.\n4. Ler as amostras em triplicata.\n5. Higienizar as cubetas após o uso.",
        "seguranca": "Uso obrigatório de jaleco, luvas de nitrilo e óculos de proteção.",
        "referencias": "AHA, J. (2020). Spectrophotometry Standards and Practices. Journal of Lab Bio, 12(3), 45-50.",
        "autor": "Eliane Pereira Cipolatti",
        "status": "Aprovado",
    }
]

GRUPOS_INICIAIS = [
    {
        "id": 1,
        "nome": "Biocatalise & Tecnologia Enzimática",
        "descricao": "Pesquisa focada no uso de lipases imobilizadas para produção de biocombustíveis e bioprodtos.",
        "lider": "Eliane Pereira Cipolatti",
        "senha": "123",
        "membros": ["Eliane Pereira Cipolatti", "Gabriela Mendes Farias Matos"],
        "status": "Aprovado",
        "solicitante": "Eliane Pereira Cipolatti",
        "membros_pendentes": [],
        "agenda": [
            {
                "id": 101,
                "titulo": "Discussão de Artigo - Imobilização de Enzimas",
                "data": datetime.now().strftime("%Y-%m-%d"),
                "hora_inicio": "14:00",
                "hora_fim": "15:30",
                "descricao": "Leitura e crítica do artigo sobre suporte de sílica mesoporosa.",
                "autor": "Gabriela Mendes Farias Matos"
            }
        ],
        "mural": "📌 **Anotações do Grupo:** Apresentação da qualificação agendada para o próximo mês. Revisar dados do lote 3 de lipases."
    }
]

def carregar_dados(arquivo, padrao):
    if os.path.exists(arquivo):
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                dados = json.load(f)
                if dados:
                    return dados
        except Exception:
            return padrao
    return padrao

def salvar_dados(arquivo, dados):
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

def gerar_codigo_pop(titulo, versao=1):
    palavras = [w for w in titulo.split() if len(w) > 2 and w.lower() not in ["de", "da", "do", "dos", "das", "em", "para", "com", "e"]]
    if palavras:
        sigla = "".join([p[0].upper() for p in palavras])[:6]
    else:
        sigla = "DOC"
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
        t_header.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F1F5F9')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t_header)
        story.append(Spacer(1, 15))

        sections = [
            ("1. OBJETIVO", pop_dict.get("objetivo", "")),
            ("2. MATERIAIS E EQUIPAMENTOS", pop_dict.get("materiais", "")),
            ("3. PROCEDIMENTO / PASSO A PASSO", pop_dict.get("passos", "")),
            ("4. SEGURANÇA E EPIs", pop_dict.get("seguranca", "")),
            ("5. REFERÊNCIAS BIBLIOGRÁFICAS", pop_dict.get("referencias", "-")),
        ]

        sec_title_style = ParagraphStyle(
            'SecTitle',
            parent=styles['Heading2'],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor('#0E7490'),
            bold=True
        )

        body_style = ParagraphStyle(
            'BodyTextCustom',
            parent=styles['Normal'],
            fontSize=9.5,
            leading=13.5,
            textColor=colors.HexColor('#334155')
        )

        for title, content in sections:
            story.append(Paragraph(title, sec_title_style))
            story.append(Spacer(1, 4))
            content_p = str(content).replace('\n', '<br/>')
            story.append(Paragraph(content_p, body_style))
            story.append(Spacer(1, 10))

        doc.build(story)
        return buffer.getvalue()
    else:
        page = Image.new("RGB", (612, 792), "white")
        draw = ImageDraw.Draw(page)
        draw.rectangle([30, 30, 582, 100], fill="#F1F5F9", outline="#CBD5E1")
        draw.text((40, 40), f"PROCEDIMENTO OPERACIONAL PADRÃO - {pop_dict['codigo']}", fill="black")
        draw.text((40, 60), f"Título: {pop_dict['titulo']} (Versão {pop_dict['versao']})", fill="black")
        draw.text((40, 80), f"Autor: {pop_dict.get('autor','N/A')}", fill="black")

        y = 120
        secoes = [
            ("1. OBJETIVO", pop_dict.get("objetivo", "")),
            ("2. MATERIAIS", pop_dict.get("materiais", "")),
            ("3. PASSO A PASSO", pop_dict.get("passos", "")),
            ("4. SEGURANÇA", pop_dict.get("seguranca", "")),
            ("5. REFERÊNCIAS", pop_dict.get("referencias", "")),
        ]

        for tit, txt in secoes:
            draw.text((40, y), tit, fill="#0E7490")
            y += 20
            for line in str(txt).split("\n"):
                draw.text((50, y), line[:80], fill="#334155")
                y += 15
            y += 10

        buf = BytesIO()
        page.save(buf, format="PDF")
        return buf.getvalue()

def gerar_pdf_etiquetas(qr_img_pil, quantidade, mm_size, id_amostra=""):
    dpi = 150
    px_per_mm = dpi / 25.4
    page_w = int(210 * px_per_mm)
    page_h = int(297 * px_per_mm)

    label_px = int(mm_size * px_per_mm)
    margin_px = int(10 * px_per_mm)
    spacing_px = int(4 * px_per_mm)

    pages = []
    current_page = Image.new("RGB", (page_w, page_h), "white")
    draw = ImageDraw.Draw(current_page)

    x = margin_px
    y = margin_px

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
            x = margin_px
            y = margin_px

        draw.rectangle([x, y, x + label_px, y + label_px], outline="lightgray", width=1)

        qr_x = x + (label_px - qr_size_px) // 2
        qr_y = y + (2 if has_text else (label_px - qr_size_px) // 2)
        current_page.paste(qr_resized, (qr_x, qr_y))

        if has_text:
            text_y = y + qr_size_px + 2
            draw.text((x + 4, text_y), f"ID: {id_amostra[:12]}", fill="black")

        x += label_px + spacing_px

    pages.append(current_page)

    pdf_buffer = BytesIO()
    if len(pages) == 1:
        pages[0].save(pdf_buffer, format="PDF", resolution=float(dpi))
    else:
        pages[0].save(
            pdf_buffer,
            format="PDF",
            resolution=float(dpi),
            save_all=True,
            append_images=pages[1:],
        )

    return pdf_buffer.getvalue()

usuario_admin_padrao = [{
    "nome": "Gabriela Mendes Farias Matos",
    "usuario": "admin",
    "senha": "123",
    "categoria": "Mestrado",
    "vinculo": "UFRRJ - Química Industrial",
    "telefone": "(21) 99677-8065",
    "email": "gbsmtsm@ufrrj.br",
    "status": "Aprovado",
    "is_admin": True,
    "orientador": "Eliane Pereira Cipolatti",
    "coorientador": "-",
    "orientador_status": "Aprovado"
}]

# --- INICIALIZAÇÃO DA SESSÃO ---
if "usuarios" not in st.session_state:
    st.session_state.usuarios = carregar_dados(ARQUIVO_USUARIOS, usuario_admin_padrao)
if "integrantes" not in st.session_state:
    st.session_state.integrantes = carregar_dados(ARQUIVO_INTEGRANTES, INTEGRANTES_INICIAIS)
if "agenda" not in st.session_state:
    st.session_state.agenda = carregar_dados(ARQUIVO_AGENDA, AGENDA_INICIAL)
if "avisos_db" not in st.session_state:
    st.session_state.avisos_db = carregar_dados(ARQUIVO_AVISOS, AVISOS_INICIAIS)
if "arquivos_db" not in st.session_state:
    st.session_state.arquivos_db = carregar_dados(ARQUIVO_ARQUIVOS, [])
if "pastas_db" not in st.session_state:
    st.session_state.pastas_db = carregar_dados(ARQUIVO_PASTAS, PASTAS_INICIAIS)
if "pops_db" not in st.session_state:
    st.session_state.pops_db = carregar_dados(ARQUIVO_POPS, POPS_INICIAIS)
if "grupos_db" not in st.session_state:
    st.session_state.grupos_db = carregar_dados(ARQUIVO_GRUPOS, GRUPOS_INICIAIS)
if "grupos_autenticados" not in st.session_state:
    st.session_state.grupos_autenticados = []
if "pasta_aberta_drive" not in st.session_state:
    st.session_state.pasta_aberta_drive = None
if "seq_amostra" not in st.session_state:
    st.session_state.seq_amostra = 1
if "menu_selecionado" not in st.session_state:
    st.session_state.menu_selecionado = "🏠 Página Inicial & Avisos"

usr_param = st.query_params.get("usr")
if usr_param:
    usr_encontrado = next(
        (
            u for u in st.session_state.usuarios
            if str(u.get("usuario")).lower() == str(usr_param).lower()
            and u.get("status") == "Aprovado"
        ),
        None,
    )
    if usr_encontrado:
        st.session_state.usuario_logado = usr_encontrado
    else:
        st.query_params.clear()
        st.session_state.usuario_logado = None
else:
    if "usuario_logado" not in st.session_state:
        st.session_state.usuario_logado = None

# --- VALIDAÇÃO GLOBAL DE ACESSO ---
if st.session_state.usuario_logado:
    usr_ativo = next(
        (
            u for u in st.session_state.usuarios
            if str(u.get("usuario", "")).strip().lower() == str(st.session_state.usuario_logado.get("usuario", "")).strip().lower()
            and u.get("status") == "Aprovado"
        ),
        None,
    )
    if not usr_ativo:
        st.session_state.usuario_logado = None
        st.query_params.clear()
        st.rerun()

# --- TELA DE LOGIN E CADASTRO ---
if st.session_state.usuario_logado is None:
    st.title("🧪 Central de Pesquisa - Controle de Acesso ⚗️")

    aba_login, aba_cadastro, aba_recuperar = st.tabs([
        "Entrar no Sistema", 
        "Solicitar Acesso", 
        "🔑 Recuperar Senha"
    ])

    lista_orientadores_opts = ["Sem Orientador / Não se aplica"] + [
        p["Nome"] for p in st.session_state.integrantes if p.get("Categoria") == "Orientador"
    ]

    with aba_login:
        st.subheader("Login")
        with st.form("form_login"):
            user_input = st.text_input("Usuário, E-mail ou Nome Completo")
            senha_input = st.text_input("Senha", type="password")
            btn_login = st.form_submit_button("Entrar", type="primary")

            if btn_login:
                usr_clean = user_input.strip().lower()
                usuario_encontrado = None

                for u in st.session_state.usuarios:
                    u_usr = str(u.get("usuario", "")).strip().lower()
                    u_email = str(u.get("email", "")).strip().lower()
                    u_nome = str(u.get("nome", "")).strip().lower()

                    if usr_clean in [u_usr, u_email, u_nome]:
                        usuario_encontrado = u
                        break

                if usuario_encontrado:
                    if usuario_encontrado["senha"] == senha_input:
                        if usuario_encontrado["status"] == "Aprovado":
                            st.session_state.usuario_logado = usuario_encontrado
                            st.query_params["usr"] = usuario_encontrado["usuario"]
                            st.success(f"Bem-vindo(a), {usuario_encontrado['nome']}!")
                            st.rerun()
                        elif usuario_encontrado["status"] == "Pendente":
                            st.warning("⚠️ O seu cadastro está PENDENTE de aprovação.")
                        else:
                            st.error("❌ Sua solicitação de acesso foi recusada.")
                    else:
                        st.error("Senha incorreta.")
                else:
                    st.error("Usuário não encontrado.")

    with aba_cadastro:
        st.subheader("Pedir Permissão de Acesso")
        with st.form("form_solicitar_acesso"):
            novo_nome = st.text_input("Nome Completo *")
            nova_categoria = st.selectbox("Categoria *", CATEGORIAS_PADRAO)
            novo_orientador = st.selectbox("Orientador Responsável (se houver)", lista_orientadores_opts)
            novo_vinculo = st.text_input("Vínculo / Curso *", "UFRRJ - Engenharia Química")
            novo_telefone = st.text_input("Telefone para Contato *")
            novo_email = st.text_input("E-mail para Contato *")
            novo_usuario = st.text_input("Usuário Desejado *")
            nova_senha = st.text_input("Criar Senha *", type="password")
            btn_solicitar = st.form_submit_button("Enviar Solicitação")

            if btn_solicitar:
                if not (novo_nome and novo_usuario and nova_senha and novo_vinculo and novo_telefone and novo_email):
                    st.error("Por favor, preencha todos os campos obrigatórios (*).")
                else:
                    usr_clean = novo_usuario.strip().lower()

                    ja_aprovado = any(
                        str(u.get("usuario", "")).strip().lower() == usr_clean and u.get("status") == "Aprovado"
                        for u in st.session_state.usuarios
                    )

                    if ja_aprovado:
                        st.error("Este nome de usuário pertence a uma conta ativa no sistema.")
                    else:
                        orient_val = "-" if novo_orientador.startswith("Sem Orientador") else novo_orientador

                        st.session_state.usuarios.append({
                            "nome": novo_nome.strip(),
                            "usuario": novo_usuario.strip(),
                            "senha": nova_senha,
                            "categoria": nova_categoria,
                            "vinculo": novo_vinculo.strip(),
                            "telefone": novo_telefone.strip(),
                            "email": novo_email.strip(),
                            "status": "Pendente",
                            "is_admin": False,
                            "orientador": orient_val,
                            "coorientador": "-",
                            "orientador_status": "Pendente" if orient_val != "-" else "Aprovado"
                        })
                        salvar_dados(ARQUIVO_USUARIOS, st.session_state.usuarios)

                        st.session_state.integrantes.append({
                            "Nome": novo_nome.strip(),
                            "Categoria": nova_categoria,
                            "Vínculo": novo_vinculo.strip(),
                            "Telefone": novo_telefone.strip(),
                            "Email": novo_email.strip(),
                            "DiasHorarios": "Não informado",
                            "Lattes": "-",
                            "Situação": "Pendente",
                            "Orientador": orient_val,
                            "Coorientador": "-",
                            "OrientadorStatus": "Pendente" if orient_val != "-" else "Aprovado"
                        })
                        salvar_dados(ARQUIVO_INTEGRANTES, st.session_state.integrantes)

                        st.success("Solicitação enviada com sucesso! Aguarde a aprovação do Administrador.")

    with aba_recuperar:
        st.subheader("🔑 Recuperação e Redefinição de Senha")
        st.caption("Informe seu usuário ou e-mail cadastrado para redefinir a sua senha.")
        with st.form("form_recuperar_senha"):
            rec_identificador = st.text_input("Usuário ou E-mail Cadastrado *")
            nova_senha_rec = st.text_input("Nova Senha *", type="password")
            conf_senha_rec = st.text_input("Confirmar Nova Senha *", type="password")
            btn_recuperar = st.form_submit_button("Redefinir Senha", type="primary")

            if btn_recuperar:
                if not rec_identificador.strip() or not nova_senha_rec:
                    st.error("Preencha todos os campos obrigatórios (*).")
                elif nova_senha_rec != conf_senha_rec:
                    st.error("A confirmação da nova senha não coincide.")
                else:
                    ident_clean = rec_identificador.strip().lower()
                    usr_alvo = next(
                        (
                            u for u in st.session_state.usuarios
                            if str(u.get("usuario", "")).strip().lower() == ident_clean
                            or str(u.get("email", "")).strip().lower() == ident_clean
                        ),
                        None,
                    )

                    if usr_alvo:
                        usr_alvo["senha"] = nova_senha_rec
                        salvar_dados(ARQUIVO_USUARIOS, st.session_state.usuarios)
                        st.success("✅ Senha redefinida com sucesso!")
                    else:
                        st.error("Nenhum usuário foi encontrado com este Usuário/E-mail.")

# --- ÁREA LOGADA ---
else:
    usuario_atual = st.session_state.usuario_logado
    is_admin = usuario_atual.get("is_admin", False)

    # Cálculo Dinâmico de Notificações
    num_pend_usr = len([u for u in st.session_state.usuarios if u.get("status") == "Pendente"])
    num_pend_perfis = len([u for u in st.session_state.usuarios if u.get("pendente_atualizacao")])
    num_pend_arqs = len([a for a in st.session_state.arquivos_db if a.get("status") == "Pendente"])
    num_pend_pops = len([p for p in st.session_state.pops_db if p.get("status") == "Pendente"])
    num_pend_pastas = len([p for p in st.session_state.pastas_db if p.get("status") == "Pendente"])
    num_pend_orient = len([p for p in st.session_state.integrantes if p.get("OrientadorStatus") == "Pendente"])
    
    num_pend_grupos = len([g for g in st.session_state.grupos_db if g.get("status") == "Pendente"])
    num_pend_membros_grp = sum([len(g.get("membros_pendentes", [])) for g in st.session_state.grupos_db])

    total_notif_admin = num_pend_usr + num_pend_perfis + num_pend_arqs + num_pend_pops + num_pend_pastas + num_pend_orient + num_pend_grupos + num_pend_membros_grp

    usr_atual_reg = next((u for u in st.session_state.usuarios if str(u.get("usuario")).lower() == str(usuario_atual["usuario"]).lower()), usuario_atual)
    notif_meu_perfil = 1 if usr_atual_reg.get("pendente_atualizacao") else 0

    hoje_str = datetime.now().strftime("%Y-%m-%d")
    notif_agenda_hoje = len([e for e in st.session_state.agenda if e.get("data") == hoje_str])
    notif_avisos = len(st.session_state.avisos_db)

    # --- CABEÇALHO E MENU DA SIDEBAR ---
    st.sidebar.markdown(
        """
        <div style="display: flex; align-items: center; gap: 10px; padding: 5px 0 15px 0;">
            <div style="background-color: #0E7490; color: white; border-radius: 8px; padding: 8px; font-size: 1.1rem; font-weight: bold;">
                🧪
            </div>
            <div>
                <h3 style="margin:0; font-size: 1.05rem; color: #0F172A !important;">Central de Pesquisa</h3>
                <span style="font-size: 0.75rem; color: #64748B;">Laboratório de Bioquímica</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    def render_menu_item(chave, rotulo, notif_count=0):
        is_selected = (st.session_state.get("menu_selecionado") == chave)
        badge = f" 🔴 ({notif_count})" if notif_count > 0 else ""
        display_label = f"{rotulo}{badge}"

        if st.sidebar.button(
            display_label,
            key=f"nav_btn_{chave}",
            use_container_width=True,
            type="primary" if is_selected else "secondary"
        ):
            st.session_state.menu_selecionado = chave
            st.rerun()

    # Seções Agrupadas com Divisores Suaves
    st.sidebar.markdown('<div class="sidebar-section">PAINEL PRINCIPAL</div>', unsafe_allow_html=True)
    render_menu_item("🏠 Página Inicial & Avisos", "🏠 Página Inicial & Avisos", notif_avisos)
    render_menu_item("📅 Agenda & Calendário", "📅 Agenda & Calendário", notif_agenda_hoje)

    st.sidebar.markdown('<div class="sidebar-section">GESTÃO DO LABORATÓRIO</div>', unsafe_allow_html=True)
    render_menu_item("👥 Equipe", "👥 Equipe")
    render_menu_item("🎓 Orientados", "🎓 Orientados", num_pend_orient if is_admin else 0)
    render_menu_item("🔬 Grupo de Pesquisa", "🔬 Grupo de Pesquisa", (num_pend_grupos + num_pend_membros_grp) if is_admin else 0)
    render_menu_item("🕒 Presença no Laboratório", "🕒 Presença no Laboratório")

    st.sidebar.markdown('<div class="sidebar-section">CONHECIMENTO</div>', unsafe_allow_html=True)
    render_menu_item("📁 Repositório de Arquivos", "📁 Repositório de Arquivos")
    render_menu_item("🏷️ Gerar QR Code de Amostras", "🏷️ Gerar QR Code de Amostras")
    render_menu_item("📝 Criador de POP", "📝 Criador de POP")

    st.sidebar.markdown('<div class="sidebar-section">CONFIGURAÇÕES</div>', unsafe_allow_html=True)
    if is_admin:
        render_menu_item("🛡️ Administração", "🛡️ Administração", total_notif_admin)
    render_menu_item("👤 Meu perfil", "👤 Meu perfil", notif_meu_perfil)

    menu_selecionado = st.session_state.menu_selecionado

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        f"""
        <div style="padding: 2px 0;">
            <div style="font-weight: bold; color: #0F172A; font-size: 0.88rem;">{usuario_atual['nome']}</div>
            <div style="font-size: 0.78rem; color: #64748B;">{'Administrador' if is_admin else 'Pesquisador'}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.sidebar.button("🚪 Sair da conta"):
        st.query_params.clear()
        st.session_state.usuario_logado = None
        st.rerun()

    # --- 0. PÁGINA INICIAL & AVISOS (COM GRID DE KPI CARDS E CONTAINERS COM BORDA) ---
    if menu_selecionado == "🏠 Página Inicial & Avisos":
        st.title("🏠 Painel Geral de Pesquisa")
        st.caption(f"Bem-vindo(a) de volta, **{usuario_atual['nome']}**! Acompanhe abaixo o resumo das atividades.")

        st.markdown("<br>", unsafe_allow_html=True)

        # GRID DE CARTOES DE METRICAS (KPI CARDS SIDE-BY-SIDE 4 COLUNAS OU 2x2 EM CELULARES)
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)

        with kpi1:
            st.markdown(
                f"""
                <div class="kpi-card kpi-card-blue">
                    <div>
                        <div class="kpi-val">{len(st.session_state.integrantes)}</div>
                        <div class="kpi-label">Integrantes</div>
                    </div>
                    <div class="kpi-icon">👥</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with kpi2:
            eventos_futuros = [e for e in st.session_state.agenda if e.get("data", "") >= hoje_str]
            st.markdown(
                f"""
                <div class="kpi-card kpi-card-green">
                    <div>
                        <div class="kpi-val">{len(eventos_futuros)}</div>
                        <div class="kpi-label">Próximos Eventos</div>
                    </div>
                    <div class="kpi-icon">📅</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with kpi3:
            st.markdown(
                f"""
                <div class="kpi-card kpi-card-amber">
                    <div>
                        <div class="kpi-val">{len(st.session_state.avisos_db)}</div>
                        <div class="kpi-label">Avisos Ativos</div>
                    </div>
                    <div class="kpi-icon">📢</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with kpi4:
            pops_aprov = len([p for p in st.session_state.pops_db if p.get("status") == "Aprovado"])
            st.markdown(
                f"""
                <div class="kpi-card kpi-card-purple">
                    <div>
                        <div class="kpi-val">{pops_aprov}</div>
                        <div class="kpi-label">POPs Vigentes</div>
                    </div>
                    <div class="kpi-icon">📝</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("<br>", unsafe_allow_html=True)

        col_left, col_right = st.columns([1.3, 1])

        with col_left:
            # CONTAINER COM BORDA PARA O MURAL DE AVISOS
            with st.container(border=True):
                st.subheader("📢 Mural de Avisos do Laboratório")

                if is_admin:
                    with st.expander("➕ Publicar Novo Aviso (Apenas Administrador)"):
                        with st.form("form_novo_aviso"):
                            tit_aviso = st.text_input("Título do Aviso *")
                            cat_aviso = st.selectbox("Categoria", ["Informativo", "Manutenção", "Urgente", "Segurança", "Eventos"])
                            cor_aviso = st.selectbox("Cor de Destaque", list(CORES_GOOGLE_AGENDA.keys()))
                            txt_aviso = st.text_area("Conteúdo do Aviso *", height=100)
                            btn_postar = st.form_submit_button("📌 Publicar Aviso", type="primary")

                            if btn_postar:
                                if tit_aviso.strip() and txt_aviso.strip():
                                    novo_id = max([a.get("id", 0) for a in st.session_state.avisos_db], default=0) + 1
                                    st.session_state.avisos_db.insert(0, {
                                        "id": novo_id,
                                        "titulo": tit_aviso.strip(),
                                        "conteudo": txt_aviso.strip(),
                                        "categoria": cat_aviso,
                                        "cor": CORES_GOOGLE_AGENDA[cor_aviso],
                                        "autor": usuario_atual["nome"],
                                        "data": datetime.now().strftime("%d/%m/%Y"),
                                    })
                                    salvar_dados(ARQUIVO_AVISOS, st.session_state.avisos_db)
                                    st.success("Aviso publicado com sucesso!")
                                    st.rerun()
                                else:
                                    st.error("Preencha o título e o conteúdo do aviso.")

                if st.session_state.avisos_db:
                    for idx, av in enumerate(st.session_state.avisos_db):
                        c_hex = av.get("cor", "#0E7490")
                        st.markdown(
                            f"""
                            <div class="aviso-card" style="border-left-color: {c_hex};">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <h4 style="margin: 0; color: #0F172A; font-size: 0.95rem;">{av['titulo']}</h4>
                                    <span style="font-size: 0.72rem; background-color: #F1F5F9; padding: 2px 8px; border-radius: 10px; color: #475569; font-weight: 600;">
                                        {av.get('categoria', 'Geral')}
                                    </span>
                                </div>
                                <p style="margin: 6px 0; color: #334155; font-size: 0.88rem;">{av['conteudo']}</p>
                                <div style="font-size: 0.75rem; color: #94A3B8; text-align: right;">
                                    Postado por <b>{av.get('autor','Admin')}</b> em {av.get('data','-')}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        if is_admin:
                            c_d1, c_d2 = st.columns([5, 1])
                            with c_d2:
                                if st.button("🗑️ Excluir", key=f"del_aviso_{av.get('id', idx)}"):
                                    st.session_state.avisos_db = [item for item in st.session_state.avisos_db if item.get("id") != av.get("id")]
                                    salvar_dados(ARQUIVO_AVISOS, st.session_state.avisos_db)
                                    st.warning("Aviso excluído.")
                                    st.rerun()
                else:
                    st.info("Nenhum aviso publicado no mural.")

        with col_right:
            # CONTAINER COM BORDA PARA COMPROMISSOS E REUNIÕES
            with st.container(border=True):
                st.subheader("📅 Próximas Reuniões & Compromissos")
                st.caption("Atividades agendadas no Calendário Oficial")

                eventos_ordenados = sorted(
                    st.session_state.agenda,
                    key=lambda x: (x.get("data", ""), x.get("hora_inicio", ""))
                )
                eventos_validos = [e for e in eventos_ordenados if e.get("data", "") >= hoje_str]

                if eventos_validos:
                    for ev in eventos_validos[:5]:
                        cor_ev = ev.get("cor", "#0284C7")
                        try:
                            dt_obj = datetime.strptime(ev["data"], "%Y-%m-%d")
                            dt_formatada = dt_obj.strftime("%d/%m/%Y (%a)")
                        except Exception:
                            dt_formatada = ev.get("data", "-")

                        st.markdown(
                            f"""
                            <div class="event-card" style="border-left: 4px solid {cor_ev};">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <strong style="color: #0F172A; font-size: 0.9rem;">{ev['titulo']}</strong>
                                    <span style="font-size: 0.72rem; font-weight: bold; color: {cor_ev};">{ev.get('tipo', 'Reunião')}</span>
                                </div>
                                <div style="font-size: 0.8rem; color: #475569; margin-top: 4px;">
                                    🕒 <b>{dt_formatada}</b> das {ev.get('hora_inicio','--')} às {ev.get('hora_fim','--')}
                                </div>
                                <div style="font-size: 0.78rem; color: #64748B; margin-top: 4px;">
                                    {ev.get('descricao', '')}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                else:
                    st.info("Não há compromissos futuros agendados.")

    # --- 0.1 AGENDA & CALENDÁRIO ---
    elif menu_selecionado == "📅 Agenda & Calendário":
        st.title("📅 Agenda & Calendário de Atividades")
        st.caption("Organização de reuniões, uso de equipamentos e compromissos do grupo estilo Google Agenda.")

        aba_ver_agenda, aba_add_agenda = st.tabs([
            "📆 Visualizar Agenda",
            "➕ Agendar Compromisso / Reunião"
        ])

        with aba_ver_agenda:
            col_m1, col_m2 = st.columns(2)
            ano_atual = datetime.now().year
            mes_atual = datetime.now().month

            with col_m1:
                mes_sel = st.selectbox("Selecione o Mês", list(range(1, 13)), index=mes_atual - 1, format_func=lambda m: calendar.month_name[m].capitalize())
            with col_m2:
                ano_sel = st.number_input("Ano", min_value=2024, max_value=2030, value=ano_atual)

            st.markdown(f"### 🗓️ Calendário de {calendar.month_name[mes_sel].capitalize()} de {ano_sel}")
            
            cal = calendar.monthcalendar(ano_sel, mes_sel)
            dias_semana = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

            cols_hdr = st.columns(7)
            for i, d in enumerate(dias_semana):
                cols_hdr[i].markdown(f"<div style='text-align:center; font-weight:bold; color:#64748B;'>{d}</div>", unsafe_allow_html=True)

            eventos_mes = {}
            for ev in st.session_state.agenda:
                try:
                    ev_dt = datetime.strptime(ev["data"], "%Y-%m-%d")
                    if ev_dt.year == ano_sel and ev_dt.month == mes_sel:
                        d_num = ev_dt.day
                        if d_num not in eventos_mes:
                            eventos_mes[d_num] = []
                        eventos_mes[d_num].append(ev)
                except Exception:
                    pass

            for semana in cal:
                cols_dias = st.columns(7)
                for i, dia in enumerate(semana):
                    if dia == 0:
                        cols_dias[i].markdown("<div style='height:60px; background:#F1F5F9; border-radius:6px; margin:2px;'></div>", unsafe_allow_html=True)
                    else:
                        evs_dia = eventos_mes.get(dia, [])
                        bolinhas = "".join([f"<span style='color:{e.get('cor','#0284C7')}; font-size:1.2rem; line-height:1;'>●</span>" for e in evs_dia])
                        
                        bg_style = "background:#ECFEFF; border:1px solid #67E8F9;" if dia == datetime.now().day and mes_sel == mes_atual and ano_sel == ano_atual else "background:white; border:1px solid #E2E8F0;"
                        
                        cols_dias[i].markdown(
                            f"""
                            <div style='height:60px; {bg_style} border-radius:6px; padding:4px; margin:2px;'>
                                <div style='font-weight:bold; font-size:0.8rem; color:#334155;'>{dia}</div>
                                <div style='margin-top:2px;'>{bolinhas}</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

            st.markdown("---")
            st.subheader("📋 Lista Detalhada de Compromissos do Mês")

            eventos_do_mes_lista = []
            for ev in st.session_state.agenda:
                try:
                    ev_dt = datetime.strptime(ev["data"], "%Y-%m-%d")
                    if ev_dt.year == ano_sel and ev_dt.month == mes_sel:
                        eventos_do_mes_lista.append(ev)
                except Exception:
                    pass

            eventos_do_mes_lista = sorted(eventos_do_mes_lista, key=lambda x: (x.get("data", ""), x.get("hora_inicio", "")))

            if eventos_do_mes_lista:
                for idx, ev in enumerate(eventos_do_mes_lista):
                    cor_ev = ev.get("cor", "#0284C7")
                    dt_f = datetime.strptime(ev["data"], "%Y-%m-%d").strftime("%d/%m/%Y")
                    
                    c_ev1, c_ev2 = st.columns([4, 1])
                    with c_ev1:
                        st.markdown(
                            f"""
                            <div class="event-card" style="border-left: 5px solid {cor_ev};">
                                <h4 style="margin: 0; color: #0F172A;">{ev['titulo']}</h4>
                                <div style="color: #475569; font-size: 0.85rem; margin-top: 4px;">
                                    📅 <b>{dt_f}</b> | 🕒 <b>{ev.get('hora_inicio')} às {ev.get('hora_fim')}</b> | 🏷️ <b>{ev.get('tipo')}</b>
                                </div>
                                <div style="color: #64748B; font-size: 0.85rem; margin-top: 4px;">
                                    {ev.get('descricao')}
                                </div>
                                <div style="color: #94A3B8; font-size: 0.75rem; margin-top: 4px;">
                                    Organizado por: <b>{ev.get('autor', 'Desconhecido')}</b>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    with c_ev2:
                        if is_admin or ev.get("autor") == usuario_atual["nome"]:
                            if st.button("🗑️ Cancelar", key=f"del_agenda_{ev.get('id', idx)}"):
                                st.session_state.agenda = [e for e in st.session_state.agenda if e.get("id") != ev.get("id")]
                                salvar_dados(ARQUIVO_AGENDA, st.session_state.agenda)
                                st.warning("Compromisso removido da agenda.")
                                st.rerun()
            else:
                st.info(f"Nenhum compromisso agendado para {calendar.month_name[mes_sel].capitalize()} de {ano_sel}.")

        with aba_add_agenda:
            st.subheader("➕ Agendar Novo Compromisso / Reunião")
            with st.form("form_novo_evento"):
                tit_event = st.text_input("Título do Evento / Reunião *")
                
                c_d1, c_d2, c_d3 = st.columns(3)
                with c_d1:
                    data_event = st.date_input("Data *", datetime.now().date())
                with c_d2:
                    h_inicio = st.time_input("Horário de Início *", time(9, 0))
                with c_d3:
                    h_fim = st.time_input("Horário de Término *", time(10, 0))

                c_c1, c_c2 = st.columns(2)
                with c_c1:
                    tipo_event = st.selectbox("Categoria do Evento", ["Reunião", "Ensaio de Bancada", "Uso de Equipamento", "Apresentação / Defesa", "Manutenção", "Outro"])
                with c_c2:
                    cor_label = st.selectbox("Cor na Agenda (Estilo Google)", list(CORES_GOOGLE_AGENDA.keys()))

                desc_event = st.text_area("Descrição / Link da Videochamada / Pauta", height=80)

                btn_add_agenda = st.form_submit_button("📅 Salvar na Agenda", type="primary")

                if btn_add_agenda:
                    if tit_event.strip():
                        novo_id_e = max([e.get("id", 0) for e in st.session_state.agenda], default=0) + 1
                        st.session_state.agenda.append({
                            "id": novo_id_e,
                            "titulo": tit_event.strip(),
                            "data": data_event.strftime("%Y-%m-%d"),
                            "hora_inicio": h_inicio.strftime("%H:%M"),
                            "hora_fim": h_fim.strftime("%H:%M"),
                            "tipo": tipo_event,
                            "cor": CORES_GOOGLE_AGENDA[cor_label],
                            "descricao": desc_event.strip(),
                            "autor": usuario_atual["nome"]
                        })
                        salvar_dados(ARQUIVO_AGENDA, st.session_state.agenda)
                        st.success("✅ Compromisso agendado com sucesso!")
                        st.rerun()
                    else:
                        st.error("Informe o título do evento.")

    # --- 1. EQUIPE ---
    elif menu_selecionado == "👥 Equipe":
        st.title("👥 Todos os Integrantes do Laboratório")

        c_busca, c_vazia = st.columns([2, 1])
        with c_busca:
            termo_busca = st.text_input("Pesquisar por nome, e-mail ou vínculo", placeholder="Pesquisar por nome, e-mail ou vínculo", label_visibility="collapsed")

        cat_filtro = st.selectbox("Filtrar Categoria", ["Todos"] + CATEGORIAS_PADRAO, key="filtro_cat")

        if is_admin:
            with st.expander("➕ Cadastrar / Editar Integrante Manualmente"):
                lista_orientadores = ["-"] + [p["Nome"] for p in st.session_state.integrantes if p.get("Categoria") == "Orientador"]
                
                with st.form("form_cad_int"):
                    f_nome = st.text_input("Nome Completo *")
                    f_cat = st.selectbox("Categoria", CATEGORIAS_PADRAO)
                    f_orient = st.selectbox("Orientador Responsável", lista_orientadores)
                    f_coorient = st.selectbox("Coorientador Responsável", lista_orientadores)
                    f_vinc = st.text_input("Vínculo / Curso", "UFRRJ - Engenharia Química")
                    f_tel = st.text_input("Telefone")
                    f_email = st.text_input("E-mail *")
                    f_horarios = st.text_input("Dias e Horários", "Não informado")
                    f_lattes = st.text_input("Link do Lattes", "http://lattes.cnpq.br/")
                    f_situacao = st.selectbox("Situação", ["Ativo", "Pendente", "Inativo"])
                    btn_salv = st.form_submit_button("Salvar Integrante", type="primary")

                    if btn_salv and f_nome:
                        existente = next(
                            (p for p in st.session_state.integrantes if p["Nome"].strip().lower() == f_nome.strip().lower()),
                            None,
                        )
                        if existente:
                            existente["Categoria"] = f_cat
                            existente["Vínculo"] = f_vinc
                            existente["Telefone"] = f_tel
                            existente["Email"] = f_email
                            existente["DiasHorarios"] = f_horarios
                            existente["Lattes"] = f_lattes
                            existente["Situação"] = f_situacao
                            existente["Orientador"] = f_orient
                            existente["Coorientador"] = f_coorient
                            existente["OrientadorStatus"] = "Aprovado"
                        else:
                            st.session_state.integrantes.append({
                                "Nome": f_nome.strip(),
                                "Categoria": f_cat,
                                "Vínculo": f_vinc.strip(),
                                "Telefone": f_tel.strip(),
                                "Email": f_email.strip(),
                                "DiasHorarios": f_horarios.strip(),
                                "Lattes": f_lattes.strip(),
                                "Situação": f_situacao,
                                "Orientador": f_orient,
                                "Coorientador": f_coorient,
                                "OrientadorStatus": "Aprovado"
                            })
                        salvar_dados(ARQUIVO_INTEGRANTES, st.session_state.integrantes)
                        st.success(f"Integrante {f_nome} salvo!")
                        st.rerun()

        integrantes_filtrados = st.session_state.integrantes

        if cat_filtro != "Todos":
            integrantes_filtrados = [p for p in integrantes_filtrados if p.get("Categoria") == cat_filtro]

        if termo_busca.strip():
            tb = termo_busca.lower().strip()
            integrantes_filtrados = [
                p for p in integrantes_filtrados
                if tb in str(p.get("Nome", "")).lower()
                or tb in str(p.get("Vínculo", p.get("Vinculo", ""))).lower()
                or tb in str(p.get("Email", "")).lower()
            ]

        st.markdown("<br>", unsafe_allow_html=True)

        col_hdr = st.columns([2.5, 1.2, 1.8, 1.8, 1.0, 0.8, 1.2])
        col_hdr[0].markdown("<div class='table-header'>INTEGRANTE</div>", unsafe_allow_html=True)
        col_hdr[1].markdown("<div class='table-header'>CATEGORIA</div>", unsafe_allow_html=True)
        col_hdr[2].markdown("<div class='table-header'>VÍNCULO / CURSO</div>", unsafe_allow_html=True)
        col_hdr[3].markdown("<div class='table-header'>DIAS E HORÁRIOS</div>", unsafe_allow_html=True)
        col_hdr[4].markdown("<div class='table-header'>LATTES</div>", unsafe_allow_html=True)
        col_hdr[5].markdown("<div class='table-header'>SITUAÇÃO</div>", unsafe_allow_html=True)
        col_hdr[6].markdown("<div class='table-header'></div>", unsafe_allow_html=True)

        if integrantes_filtrados:
            for idx, p in enumerate(integrantes_filtrados):
                c1, c2, c3, c4, c5, c6, c7 = st.columns([2.5, 1.2, 1.8, 1.8, 1.0, 0.8, 1.2])

                nome_str = p.get("Nome", "-")
                email_str = p.get("Email", "-")
                cat_str = p.get("Categoria", "-")
                vinc_str = p.get("Vínculo", p.get("Vinculo", "-"))
                hor_str = p.get("DiasHorarios", "Não informado")
                lattes_str = p.get("Lattes", "-")
                sit_str = p.get("Situação", "Ativo")

                iniciais = "".join([n[0] for n in nome_str.split()[:2]]).upper() if nome_str != "-" else "LT"

                with c1:
                    st.markdown(
                        f"""
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <div class="avatar-circle">{iniciais}</div>
                            <div>
                                <div style="font-weight: 700; color: #0F172A; font-size: 0.88rem;">{nome_str}</div>
                                <div style="color: #64748B; font-size: 0.78rem; text-decoration: underline;">{email_str}</div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                with c2:
                    st.write(cat_str)

                with c3:
                    st.write(vinc_str)

                with c4:
                    st.write(hor_str)

                with c5:
                    if str(lattes_str).startswith("http"):
                        st.markdown(f"<a href='{lattes_str}' target='_blank' style='color:#0E7490; font-weight:600; text-decoration:none;'>Abrir Lattes ↗</a>", unsafe_allow_html=True)
                    else:
                        st.write("-")

                with c6:
                    if sit_str == "Ativo":
                        st.markdown("<span class='badge-ativo'>Ativo</span>", unsafe_allow_html=True)
                    else:
                        st.markdown("<span class='badge-pendente'>Pendente</span>", unsafe_allow_html=True)

                with c7:
                    with st.popover("Ficha"):
                        st.markdown(f"### 👤 {nome_str}")
                        st.write(f"**Categoria:** {cat_str}")
                        st.write(f"**Orientador:** {p.get('Orientador', '-')}")
                        st.write(f"**Coorientador:** {p.get('Coorientador', '-')}")
                        st.write(f"**Vínculo:** {vinc_str}")
                        st.write(f"**Telefone:** {p.get('Telefone', '-')}")
                        st.write(f"**E-mail:** {email_str}")
                        if is_admin:
                            st.markdown("---")
                            if st.button("🗑️ Excluir Integrante", key=f"del_int_{idx}"):
                                nome_del = nome_str.strip().lower()
                                email_del = email_str.strip().lower()

                                st.session_state.integrantes = [
                                    item for item in st.session_state.integrantes
                                    if str(item.get("Nome", "")).strip().lower() != nome_del
                                    and str(item.get("Email", "")).strip().lower() != email_del
                                ]
                                salvar_dados(ARQUIVO_INTEGRANTES, st.session_state.integrantes)

                                st.session_state.usuarios = [
                                    u for u in st.session_state.usuarios
                                    if str(u.get("nome", "")).strip().lower() != nome_del
                                    and str(u.get("email", "")).strip().lower() != email_del
                                ]
                                salvar_dados(ARQUIVO_USUARIOS, st.session_state.usuarios)

                                st.warning(f"Integrante '{nome_str}' excluído com sucesso!")
                                st.rerun()

                st.markdown("<hr style='margin: 6px 0; border: none; border-top: 1px solid #F1F5F9;'/>", unsafe_allow_html=True)
        else:
            st.info("Nenhum integrante encontrado.")

    # --- 2. ORIENTADOS ---
    elif menu_selecionado == "🎓 Orientados":
        st.title("🎓 Orientados e Alunos por Sequência de Orientador")
        st.caption("Acompanhamento hierárquico encadeado: **Orientador ➔ Alunos Orientados (e Coorientadores)** (Definido exclusivamente pelo Administrador).")

        orientadores = [p for p in st.session_state.integrantes if p.get("Categoria") == "Orientador"]
        alunos = [
            p for p in st.session_state.integrantes
            if p.get("Categoria") in ["Iniciação Científica", "Mestrado", "Doutorado", "Pós-Doutorado"]
        ]

        for orient in orientadores:
            nome_orient = orient["Nome"]
            st.markdown(
                f"""
                <div class="tree-orientador">
                    👨‍🏫 Orientador(a): <b>{nome_orient}</b> 
                    <span style="font-size:0.8rem; font-weight:normal; color:#64748B;">({orient.get('Vínculo', '-')})</span>
                </div>
                """,
                unsafe_allow_html=True
            )

            alunos_do_orientador = [
                a for a in alunos
                if a.get("Orientador") == nome_orient
