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

# --- TEMAS DE CORES DISPONÍVEIS ---
TEMAS_CORES = {
    "🩵 Ciano Oceano (Padrão)": {"primary": "#0E7490", "bg_light": "#ECFEFF", "border": "#06B6D4"},
    "🔵 Azul Safira": {"primary": "#1D4ED8", "bg_light": "#EFF6FF", "border": "#3B82F6"},
    "🟢 Verde Esmeralda": {"primary": "#047857", "bg_light": "#ECFDF5", "border": "#10B981"},
    "🟣 Roxo Orquídea": {"primary": "#6D28D9", "bg_light": "#F5F3FF", "border": "#8B5CF6"},
    "🟠 Laranja Pôr do Sol": {"primary": "#C2410C", "bg_light": "#FFF7ED", "border": "#F97316"},
    "🩷 Rosa Magenta": {"primary": "#BE185D", "bg_light": "#FDF2F8", "border": "#EC4899"},
    "🌑 Grafite Elegante": {"primary": "#334155", "bg_light": "#F1F5F9", "border": "#64748B"},
}

if "tema_cor" not in st.session_state:
    st.session_state.tema_cor = "🩵 Ciano Oceano (Padrão)"

tema_ativo = TEMAS_CORES.get(st.session_state.tema_cor, TEMAS_CORES["🩵 Ciano Oceano (Padrão)"])
cor_primaria = tema_ativo["primary"]
cor_bg_light = tema_ativo["bg_light"]
cor_border = tema_ativo["border"]

# --- INJEÇÃO DE CSS DINÂMICO ---
st.markdown(
    f"""
    <style>
    #MainMenu {{visibility: hidden;}}
    header {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    [data-testid="stHeader"] {{display: none;}}
    [data-testid="stToolbar"] {{display: none;}}
    
    .stApp {{ background-color: #F8FAFC; }}
    [data-testid="stSidebar"] {{ background-color: #FFFFFF; border-right: 1px solid #E2E8F0; }}
    
    [data-testid="stSidebar"] div.stButton > button {{
        text-align: left !important; justify-content: flex-start !important; padding: 8px 12px !important;
        width: 100% !important; margin-bottom: 3px !important; border-radius: 6px !important; font-size: 0.88rem !important;
    }}
    
    [data-testid="stSidebar"] div.stButton > button[kind="secondary"]:hover {{
        background-color: {cor_bg_light} !important; color: {cor_primaria} !important;
    }}
    
    [data-testid="stSidebar"] div.stButton > button[kind="primary"] {{
        background-color: {cor_bg_light} !important; color: {cor_primaria} !important; font-weight: 700 !important;
        border-left: 4px solid {cor_primaria} !important; border-top: none !important; border-right: none !important; border-bottom: none !important;
    }}

    h1, h2, h3 {{ color: #0F172A !important; font-family: 'Segoe UI', Roboto, sans-serif; }}
    .sidebar-section {{ font-size: 0.70rem; font-weight: 800; color: #94A3B8; text-transform: uppercase; margin-top: 1.2rem; margin-bottom: 0.4rem; letter-spacing: 0.08em; }}
    .aviso-card {{ background-color: #FFFFFF; border-radius: 8px; padding: 14px 16px; margin-bottom: 10px; border-left: 4px solid {cor_primaria}; box-shadow: 0 1px 3px rgba(0,0,0,0.02); }}
    .pop-preview-card {{ background-color: #FFFFFF; border: 1px solid #CBD5E1; border-left: 4px solid {cor_primaria}; border-radius: 8px; padding: 16px; margin-bottom: 15px; }}
    .tree-orientador {{ background-color: #F8FAFC; border: 1px solid #E2E8F0; border-left: 4px solid {cor_primaria}; padding: 12px 16px; border-radius: 8px; margin-top: 15px; font-weight: bold; font-size: 0.95rem; color: #0F172A; }}
    </style>
""",
    unsafe_allow_html=True,
)
    
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
                if a.get("Orientador") == nome_orient and a.get("OrientadorStatus") == "Aprovado"
            ]

            if alunos_do_orientador:
                for al in alunos_do_orientador:
                    coorient_txt = f" | <b>Coorientador:</b> {al.get('Coorientador')}" if al.get('Coorientador') and al.get('Coorientador') != "-" else ""
                    st.markdown(
                        f"""
                        <div class="tree-orientado">
                            <div>
                                <span style="color:#0E7490; font-weight:bold;">└─ 🎓 {al['Nome']}</span> 
                                <span style="font-size:0.82rem; color:#475569;">({al.get('Categoria')})</span>
                                <div style="font-size:0.78rem; color:#64748B; margin-left: 20px;">
                                    E-mail: {al.get('Email')} | Vínculo: {al.get('Vínculo')}{coorient_txt}
                                </div>
                            </div>
                            <div>
                                <span class="badge-ativo">Vínculo Confirmado</span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            else:
                st.markdown("<div style='margin-left:24px; font-size:0.85rem; color:#94A3B8; padding: 6px 0;'><i>Nenhum orientado vinculado a este orientador até o momento.</i></div>", unsafe_allow_html=True)

        st.markdown("<br>### ❓ Alunos Sem Orientador Confirmado", unsafe_allow_html=True)
        sem_orientador = [
            a for a in alunos
            if not a.get("Orientador") or a.get("Orientador") == "-" or a.get("OrientadorStatus") == "Pendente"
        ]

        if sem_orientador:
            for al in sem_orientador:
                st_txt = "Aguardando Atribuição do Admin" if al.get("OrientadorStatus") == "Pendente" else "Sem Orientador"
                st.markdown(
                    f"""
                    <div class="tree-orientado" style="margin-left:0; border-left:4px solid #F59E0B;">
                        <div>
                            <b>🎓 {al['Nome']}</b> ({al.get('Categoria')})
                            <div style="font-size:0.8rem; color:#64748B;">Orientador Solicitado: <b>{al.get('Orientador', 'Nenhum')}</b></div>
                        </div>
                        <div>
                            <span class="badge-pendente">{st_txt}</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("Todos os alunos cadastrados estão oficialmente vinculados aos seus orientadores!")

    # --- 2.1 GRUPOS DE PESQUISA (COM SENHA DE ACESSO INDIVIDUAL) ---
    elif menu_selecionado == "🔬 Grupo de Pesquisa":
        st.title("🔬 Área de Grupos de Pesquisa")
        st.caption("Acesso restrito por senha individual por grupo. Cada pesquisador só acessa e edita as informações do seu grupo.")

        meus_grupos = [
            g for g in st.session_state.grupos_db
            if g.get("status") == "Aprovado" and (usuario_atual["nome"] in g.get("membros", []) or is_admin)
        ]

        aba_grp_view, aba_grp_solicitar = st.tabs([
            "📊 Meus Grupos de Pesquisa",
            "➕ Solicitar Criação / Entrada em Grupo"
        ])

        with aba_grp_view:
            if meus_grupos:
                nomes_meus_grupos = [g["nome"] for g in meus_grupos]
                grp_sel_nome = st.selectbox("Selecione o Grupo de Pesquisa", nomes_meus_grupos)
                grupo_ativo = next((g for g in meus_grupos if g["nome"] == grp_sel_nome), meus_grupos[0])

                grp_id = grupo_ativo["id"]
                autenticado = (grp_id in st.session_state.grupos_autenticados) or is_admin

                if not autenticado:
                    with st.container(border=True):
                        st.warning(f"🔒 O Grupo **{grupo_ativo['nome']}** é protegido por senha. Insira a senha do grupo para ter acesso.")
                        with st.form(f"form_auth_grp_{grp_id}"):
                            senha_grp_input = st.text_input("Senha do Grupo", type="password")
                            btn_entrar_grp = st.form_submit_button("🔓 Acessar Área do Grupo", type="primary")

                            if btn_entrar_grp:
                                if senha_grp_input == grupo_ativo.get("senha", ""):
                                    st.session_state.grupos_autenticados.append(grp_id)
                                    st.success("Senha correta! Acesso liberado.")
                                    st.rerun()
                                else:
                                    st.error("Senha incorreta.")
                else:
                    st.markdown(
                        f"""
                        <div class="css-card" style="border-left: 4px solid #0E7490;">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <h2 style="margin:0; color:#0F172A; font-size: 1.3rem;">🔬 {grupo_ativo['nome']}</h2>
                                <span class="badge-ativo">🔓 Área Autenticada</span>
                            </div>
                            <p style="color:#475569; margin: 6px 0; font-size:0.88rem;">{grupo_ativo.get('descricao', '')}</p>
                            <div style="font-size:0.82rem; color:#64748B;">
                                👨‍🔬 <b>Líder do Grupo:</b> {grupo_ativo.get('lider', 'N/A')} | 👥 <b>Membros:</b> {len(grupo_ativo.get('membros', []))}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    if is_admin or usuario_atual["nome"] == grupo_ativo.get("lider"):
                        with st.expander("⚙️ Painel de Edição das Informações do Grupo (Admin / Líder)"):
                            with st.form(f"form_edit_grp_{grp_id}"):
                                ed_nome_g = st.text_input("Nome do Grupo", value=grupo_ativo["nome"])
                                ed_desc_g = st.text_area("Descrição do Grupo", value=grupo_ativo.get("descricao", ""))
                                ed_lider_g = st.text_input("Líder do Grupo", value=grupo_ativo.get("lider", ""))
                                ed_senha_g = st.text_input("Senha de Acesso do Grupo", value=grupo_ativo.get("senha", "123"))
                                btn_salv_grp_edit = st.form_submit_button("💾 Salvar Alterações do Grupo", type="primary")

                                if btn_salv_grp_edit:
                                    grupo_ativo["nome"] = ed_nome_g.strip()
                                    grupo_ativo["descricao"] = ed_desc_g.strip()
                                    grupo_ativo["lider"] = ed_lider_g.strip()
                                    grupo_ativo["senha"] = ed_senha_g.strip()
                                    salvar_dados(ARQUIVO_GRUPOS, st.session_state.grupos_db)
                                    st.success("Informações do grupo atualizadas com sucesso!")
                                    st.rerun()

                    st.markdown("<br>", unsafe_allow_html=True)
                    sub_tab1, sub_tab2, sub_tab3 = st.tabs([
                        "📅 Calendário Exclusivo do Grupo",
                        "📝 Mural & Projetos Internos",
                        "👥 Membros do Grupo"
                    ])

                    with sub_tab1:
                        st.subheader("📅 Calendário Individual de Atividades do Grupo")
                        st.caption("Agendamentos e compromissos visíveis somente aos participantes deste grupo.")

                        c_ag1, c_ag2 = st.columns([1.5, 1])

                        with c_ag1:
                            st.markdown("##### 📋 Compromissos Agendados")
                            agenda_grp = grupo_ativo.get("agenda", [])
                            if agenda_grp:
                                for idx_a, ev in enumerate(agenda_grp):
                                    st.markdown(
                                        f"""
                                        <div class="event-card" style="border-left: 4px solid #059669;">
                                            <div style="font-weight:bold; color:#0F172A;">{ev['titulo']}</div>
                                            <div style="font-size:0.82rem; color:#475569;">
                                                📅 <b>{ev['data']}</b> das 🕒 <b>{ev.get('hora_inicio')} às {ev.get('hora_fim')}</b>
                                            </div>
                                            <div style="font-size:0.8rem; color:#64748B; margin-top:4px;">{ev.get('descricao', '')}</div>
                                            <div style="font-size:0.75rem; color:#94A3B8; margin-top:2px;">Criado por: {ev.get('autor','-')}</div>
                                        </div>
                                        """,
                                        unsafe_allow_html=True
                                    )
                                    if is_admin or ev.get("autor") == usuario_atual["nome"]:
                                        if st.button("🗑️ Remover Evento", key=f"del_ev_grp_{idx_a}"):
                                            grupo_ativo["agenda"].pop(idx_a)
                                            salvar_dados(ARQUIVO_GRUPOS, st.session_state.grupos_db)
                                            st.warning("Evento removido da agenda do grupo.")
                                            st.rerun()
                            else:
                                st.info("Nenhum evento agendado na agenda deste grupo.")

                        with c_ag2:
                            st.markdown("##### ➕ Novo Evento do Grupo")
                            with st.form(f"form_evento_grp_{grupo_ativo['id']}"):
                                tit_ev_g = st.text_input("Título do Evento *")
                                dt_ev_g = st.date_input("Data *", datetime.now().date())
                                c_h1, c_h2 = st.columns(2)
                                with c_h1:
                                    hi_g = st.time_input("Início", time(14, 0))
                                with c_h2:
                                    hf_g = st.time_input("Fim", time(15, 0))
                                desc_ev_g = st.text_area("Descrição / Pauta")
                                btn_salv_ev_g = st.form_submit_button("📅 Salvar no Grupo", type="primary")

                                if btn_salv_ev_g and tit_ev_g.strip():
                                    if "agenda" not in grupo_ativo:
                                        grupo_ativo["agenda"] = []
                                    grupo_ativo["agenda"].append({
                                        "id": len(grupo_ativo["agenda"]) + 1,
                                        "titulo": tit_ev_g.strip(),
                                        "data": dt_ev_g.strftime("%Y-%m-%d"),
                                        "hora_inicio": hi_g.strftime("%H:%M"),
                                        "hora_fim": hf_g.strftime("%H:%M"),
                                        "descricao": desc_ev_g.strip(),
                                        "autor": usuario_atual["nome"]
                                    })
                                    salvar_dados(ARQUIVO_GRUPOS, st.session_state.grupos_db)
                                    st.success("Evento adicionado ao calendário do grupo!")
                                    st.rerun()

                    with sub_tab2:
                        st.subheader("📝 Mural & Projetos Internos do Grupo")
                        st.caption("Anotações gerais, atas de reuniões e avisos internos.")

                        mural_atual = grupo_ativo.get("mural", "Nenhuma anotação postada ainda.")
                        st.markdown(f"<div class='css-card'>{mural_atual}</div>", unsafe_allow_html=True)

                        with st.expander("✏️ Editar Mural e Anotações do Grupo"):
                            novo_mural = st.text_area("Escreva as anotações do grupo (Suporta texto e Markdown)", value=mural_atual, height=150)
                            if st.button("💾 Atualizar Mural"):
                                grupo_ativo["mural"] = novo_mural
                                salvar_dados(ARQUIVO_GRUPOS, st.session_state.grupos_db)
                                st.success("Mural do grupo atualizado!")
                                st.rerun()

                    with sub_tab3:
                        st.subheader("👥 Integrantes do Grupo")
                        for mbr in grupo_ativo.get("membros", []):
                            st.markdown(f"- 👨‍🔬 **{mbr}** {'*(Líder)*' if mbr == grupo_ativo.get('lider') else ''}")

            else:
                st.warning("⚠️ Você ainda não está vinculado a nenhum Grupo de Pesquisa aprovado.")
                st.info("Utilize a aba '➕ Solicitar Criação / Entrada em Grupo' para requisitar a criação de um novo grupo ou entrar em um grupo existente.")

        with aba_grp_solicitar:
            c_sol1, c_sol2 = st.columns(2)

            with c_sol1:
                with st.container(border=True):
                    st.subheader("➕ Solicitar Criação de Novo Grupo")
                    with st.form("form_novo_grupo_pesq"):
                        nome_novo_grp = st.text_input("Nome do Grupo de Pesquisa *")
                        desc_novo_grp = st.text_area("Descrição / Objetivos do Grupo *", height=100)
                        senha_novo_grp = st.text_input("Definir Senha de Acesso ao Grupo *", type="password", value="123")
                        btn_sol_grp = st.form_submit_button("🚀 Enviar Solicitação para o Admin", type="primary")

                        if btn_sol_grp:
                            if nome_novo_grp.strip() and desc_novo_grp.strip() and senha_novo_grp.strip():
                                novo_id_g = max([g.get("id", 0) for g in st.session_state.grupos_db], default=0) + 1
                                st.session_state.grupos_db.append({
                                    "id": novo_id_g,
                                    "nome": nome_novo_grp.strip(),
                                    "descricao": desc_novo_grp.strip(),
                                    "lider": usuario_atual["nome"],
                                    "senha": senha_novo_grp.strip(),
                                    "membros": [usuario_atual["nome"]],
                                    "status": "Pendente",
                                    "solicitante": usuario_atual["nome"],
                                    "membros_pendentes": [],
                                    "agenda": [],
                                    "mural": "Mural inicial do grupo."
                                })
                                salvar_dados(ARQUIVO_GRUPOS, st.session_state.grupos_db)
                                st.success("✅ Solicitação de novo grupo enviada para aprovação do Administrador!")
                                st.rerun()
                            else:
                                st.error("Preencha o nome, a descrição e a senha do grupo.")

            with c_sol2:
                with st.container(border=True):
                    st.subheader("🙋‍♂️ Solicitar Entrada em Grupo Existente")
                    grupos_aprovados_outros = [
                        g for g in st.session_state.grupos_db
                        if g.get("status") == "Aprovado" and usuario_atual["nome"] not in g.get("membros", [])
                    ]

                    if grupos_aprovados_outros:
                        dict_g_outros = {g["nome"]: g for g in grupos_aprovados_outros}
                        grp_entrar_nome = st.selectbox("Selecione o Grupo para Ingressar", list(dict_g_outros.keys()))

                        if st.button("📩 Solicitar Vínculo ao Grupo"):
                            grp_alvo = dict_g_outros[grp_entrar_nome]
                            if "membros_pendentes" not in grp_alvo:
                                grp_alvo["membros_pendentes"] = []

                            if usuario_atual["nome"] not in grp_alvo["membros_pendentes"]:
                                grp_alvo["membros_pendentes"].append(usuario_atual["nome"])
                                salvar_dados(ARQUIVO_GRUPOS, st.session_state.grupos_db)
                                st.success(f"Solicitação de entrada no grupo '{grp_entrar_nome}' enviada ao Admin!")
                            else:
                                st.info("Você já possui uma solicitação de entrada pendente para este grupo.")
                    else:
                        st.info("Não há outros grupos de pesquisa disponíveis para solicitação no momento.")

    # --- 3. PRESENÇA NO LABORATÓRIO ---
    elif menu_selecionado == "🕒 Presença no Laboratório":
        st.title("🕒 Presença no Laboratório")
        st.caption("Escala e horários de presença dos pesquisadores na bancada.")

        if st.session_state.integrantes:
            df_presenca = pd.DataFrame(st.session_state.integrantes)
            cols_p = ["Nome", "Categoria", "DiasHorarios"]
            for col in cols_p:
                if col not in df_presenca.columns:
                    df_presenca[col] = "-"
            st.dataframe(df_presenca[cols_p], use_container_width=True)
        else:
            st.info("Nenhum registro de presença disponível.")

    # --- 4. REPOSITÓRIO DE ARQUIVOS ---
    elif menu_selecionado == "📁 Repositório de Arquivos":
        st.title("📁 Central de Arquivos & Documentos")

        aba_docs, aba_upload, aba_nova_pasta = st.tabs([
            "📂 Drive de Arquivos",
            "📥 Enviar Arquivo",
            "📁 Criar / Solicitar Pasta",
        ])

        pastas_aprovadas = [p for p in st.session_state.pastas_db if p.get("status") == "Aprovado"]

        with aba_docs:
            if st.session_state.pasta_aberta_drive is None:
                st.subheader("📂 Suas Pastas do Laboratório")
                st.caption("Clique em uma pasta para visualizar os arquivos contidos nela.")

                cols_pastas = st.columns(3)
                for idx, pst in enumerate(pastas_aprovadas):
                    nome_p = pst["nome"]
                    desc_p = pst.get("descricao", "Sem descrição")

                    qtd_files = sum(
                        1 for a in st.session_state.arquivos_db
                        if str(a.get("pasta", "")).strip().lower() == str(nome_p).strip().lower()
                        and a.get("status") == "Aprovado"
                    )

                    with cols_pastas[idx % 3]:
                        st.markdown(
                            f"""
                            <div class="css-card">
                                <h3 style="margin:0; font-size: 1.1rem; color:#0F172A;">📁 {nome_p}</h3>
                                <p style="margin: 5px 0; color: #64748B; font-size: 0.85rem;">{desc_p}</p>
                                <span style="background-color: #E2E8F0; padding: 2px 8px; border-radius: 12px; font-size: 0.78rem; font-weight: bold; color: #334155;">
                                    📄 {qtd_files} arquivo(s)
                                </span>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        c_b1, c_b2 = st.columns([2, 1])
                        with c_b1:
                            if st.button(f"📂 Abrir", key=f"btn_open_folder_{idx}"):
                                st.session_state.pasta_aberta_drive = nome_p
                                st.rerun()
                        with c_b2:
                            if is_admin and nome_p != "Geral":
                                if st.button("🗑️", key=f"btn_del_folder_{idx}", help="Excluir Pasta"):
                                    st.session_state.pastas_db = [p for p in st.session_state.pastas_db if p["nome"] != nome_p]
                                    salvar_dados(ARQUIVO_PASTAS, st.session_state.pastas_db)
                                    st.success(f"Pasta '{nome_p}' removida.")
                                    st.rerun()

            else:
                nome_pasta_atual = st.session_state.pasta_aberta_drive

                c_top1, c_top2 = st.columns([3, 1])
                with c_top1:
                    st.subheader(f"📂 Pasta: {nome_pasta_atual}")
                with c_top2:
                    if st.button("⬅️ Voltar para Pastas", type="secondary"):
                        st.session_state.pasta_aberta_drive = None
                        st.rerun()

                st.markdown("---")

                arqs_da_pasta = [
                    a for a in st.session_state.arquivos_db
                    if str(a.get("pasta", "")).strip().lower() == str(nome_pasta_atual).strip().lower()
                    and a.get("status") == "Aprovado"
                ]

                if arqs_da_pasta:
                    for doc in arqs_da_pasta:
                        with st.container():
                            st.markdown(
                                f"""
                                <div class="css-card">
                                    <h4 style="margin:0; color:#0E7490;">📄 {doc['titulo']}</h4>
                                    <p style="margin:4px 0; color:#555; font-size:0.85rem;"><b>Enviado por:</b> {doc.get('autor', 'Desconhecido')} em {doc.get('data', '-')}</p>
                                    <p style="margin:4px 0; color:#666; font-size:0.85rem;"><i>{doc.get('descricao', '')}</i></p>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                            col_d1, col_d2 = st.columns([3, 1])
                            with col_d1:
                                b64_str = (
                                    doc.get("conteudo_b64")
                                    or doc.get("conteudo")
                                    or doc.get("arquivo_b64")
                                    or doc.get("b64")
                                )

                                if b64_str:
                                    try:
                                        bytes_f = base64.b64decode(b64_str)
                                        nome_orig = doc.get("nome_original") or f"{doc.get('titulo')}.pdf"
                                        mime_orig = doc.get("mime_type") or "application/octet-stream"

                                        st.download_button(
                                            label=f"⬇️ Baixar {nome_orig}",
                                            data=bytes_f,
                                            file_name=nome_orig,
                                            mime=mime_orig,
                                            key=f"dl_{doc['id']}",
                                        )
                                    except Exception as e:
                                        st.error(f"Erro ao processar o arquivo: {e}")
                                else:
                                    st.warning("⚠️ Conteúdo do arquivo indisponível para download.")

                            with col_d2:
                                if is_admin or doc.get("autor") == usuario_atual["nome"]:
                                    if st.button("🗑️ Excluir", key=f"del_doc_{doc['id']}"):
                                        st.session_state.arquivos_db = [a for a in st.session_state.arquivos_db if a["id"] != doc["id"]]
                                        salvar_dados(ARQUIVO_ARQUIVOS, st.session_state.arquivos_db)
                                        st.warning(f"Arquivo '{doc['titulo']}' excluído.")
                                        st.rerun()

                            st.markdown("---")
                else:
                    st.info(f"Nenhum arquivo encontrado na pasta '{nome_pasta_atual}'.")

        with aba_upload:
            st.subheader("Enviar Documento")
            lista_nomes_pastas = [p["nome"] for p in pastas_aprovadas]

            tit_doc = st.text_input("Título do Documento *")
            pasta_doc = st.selectbox("Selecione a Pasta *", lista_nomes_pastas)
            desc_doc = st.text_area("Descrição / Detalhes *", height=80)
            arq_up = st.file_uploader("Selecione o Ficheiro *")

            if st.button("📤 Confirmar Envio", type="primary"):
                if not (tit_doc.strip() and desc_doc.strip() and arq_up):
                    st.error("Preencha todos os campos obrigatórios (*).")
                else:
                    b64_str = base64.b64encode(arq_up.getvalue()).decode("utf-8")
                    novo_id = max([a.get("id", 0) for a in st.session_state.arquivos_db], default=0) + 1
                    status_doc = "Aprovado" if is_admin else "Pendente"

                    st.session_state.arquivos_db.append({
                        "id": novo_id,
                        "titulo": tit_doc.strip(),
                        "pasta": pasta_doc,
                        "descricao": desc_doc.strip(),
                        "nome_original": arq_up.name,
                        "mime_type": arq_up.type,
                        "conteudo_b64": b64_str,
                        "autor": usuario_atual["nome"],
                        "data": datetime.now().strftime("%d/%m/%Y"),
                        "status": status_doc,
                    })
                    salvar_dados(ARQUIVO_ARQUIVOS, st.session_state.arquivos_db)
                    st.success("✅ Documento salvo com sucesso!")
                    st.rerun()

        with aba_nova_pasta:
            st.subheader("Criar Nova Pasta")
            nome_pasta = st.text_input("Nome da Nova Pasta *")
            desc_pasta = st.text_input("Descrição / Finalidade *")
            if st.button("Criar Pasta", type="primary"):
                if nome_pasta and desc_pasta:
                    status_p = "Aprovado" if is_admin else "Pendente"
                    st.session_state.pastas_db.append({
                        "nome": nome_pasta.strip(),
                        "descricao": desc_pasta.strip(),
                        "criador": usuario_atual["nome"],
                        "status": status_p,
                    })
                    salvar_dados(ARQUIVO_PASTAS, st.session_state.pastas_db)
                    st.success("Pasta criada com sucesso!")
                    st.rerun()

    # --- 5. GERAR QR CODE ---
    elif menu_selecionado == "🏷️ Gerar QR Code de Amostras":
        st.title("🧪 Gerador de QR Code de Amostras & Etiquetas")

        col_f, col_q = st.columns([1.2, 1])

        with col_f:
            id_gerado_auto = f"AMS-{datetime.now().strftime('%Y%m%d')}-{st.session_state.seq_amostra:03d}"
            
            c_id1, c_id2 = st.columns([3, 1])
            with c_id1:
                id_amostra = st.text_input("Código / ID da Amostra (Gerado Automaticamente)", value=id_gerado_auto)
            with c_id2:
                st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                if st.button("🔄 Novo ID"):
                    st.session_state.seq_amostra += 1
                    st.rerun()

            opcoes_amostras = REAGENTES_CADASTRADOS + ["✍️ Outro (Digitar manualmente)"]
            sel_amostra = st.selectbox("Nome da Amostra / Reagente", opcoes_amostras)

            if sel_amostra == "✍️ Outro (Digitar manualmente)":
                nome_amostra = st.text_input("Digite o Nome da Amostra / Reagente *", "")
            else:
                nome_amostra = sel_amostra

            data_obtencao = st.date_input("Data de Obtenção", datetime.now().date())

            lista_pesquisadores = []
            mapa_pesquisadores = {}
            for p in st.session_state.integrantes:
                nome_p = p.get("Nome", "").strip()
                if nome_p:
                    tel_p = p.get("Telefone", "-")
                    email_p = p.get("Email", "-")
                    label = f"{nome_p} ({email_p} | {tel_p})"
                    lista_pesquisadores.append(label)
                    mapa_pesquisadores[label] = {
                        "nome": nome_p,
                        "telefone": tel_p,
                        "email": email_p,
                    }

            opcoes_resp = lista_pesquisadores + ["✍️ Outro (Digitar manualmente)"]

            index_padrao = 0
            for idx_opt, opt_lbl in enumerate(lista_pesquisadores):
                if usuario_atual.get("nome", "").lower() in opt_lbl.lower():
                    index_padrao = idx_opt
                    break

            sel_resp = st.selectbox("Pesquisador Responsável", opcoes_resp, index=index_padrao if lista_pesquisadores else 0)

            if sel_resp == "✍️ Outro (Digitar manualmente)":
                responsavel_nome = st.text_input("Nome do Pesquisador Responsável", "")
                responsavel_tel = st.text_input("Telefone do Responsável", "")
                responsavel_email = st.text_input("E-mail do Responsável", "")
            else:
                info_p = mapa_pesquisadores.get(sel_resp, {})
                responsavel_nome = info_p.get("nome", sel_resp)
                responsavel_tel = info_p.get("telefone", "-")
                responsavel_email = info_p.get("email", "-")

            localizacao = st.text_input("Local de Armazenamento", "Freezer -20°C / Posição B4")
            dest_selecionado = st.selectbox("Tamanho da Etiqueta", list(DESTINOS_ETIQUETAS.keys()))
            tamanho_mm = DESTINOS_ETIQUETAS[dest_selecionado]
            qtd_etiquetas = st.number_input("Quantidade de Etiquetas", min_value=1, max_value=100, value=6)
            descricao = st.text_area("Descrição / Protocolo", value="Amostra obtida via fermentação estado sólido. Tampão fosfato 0.1M pH 7.0.")
            gerar = st.button("Gerar Etiqueta QR Code", type="primary")

        with col_q:
            if gerar or id_amostra:
                conteudo_qr = (
                    f"📋 FICHA DA AMOSTRA\n"
                    f"------------------------\n"
                    f"• Código / ID: {id_amostra}\n"
                    f"• Amostra / Reagente: {nome_amostra}\n"
                    f"• Data de Obtenção: {data_obtencao.strftime('%d/%m/%Y')}\n"
                    f"• Responsável: {responsavel_nome}\n"
                    f"• Telefone do Responsável: {responsavel_tel}\n"
                    f"• E-mail do Responsável: {responsavel_email}\n"
                    f"• Local de Armazenamento: {localizacao}\n"
                    f"------------------------\n"
                    f"• Descrição / Protocolo:\n{descricao}"
                )

                img = qrcode.make(conteudo_qr)
                buffer = BytesIO()
                img.save(buffer, format="PNG")
                img_bytes = buffer.getvalue()

                st.image(img_bytes, caption=f"Pré-visualização: {id_amostra}", width=220)

                st.download_button("🖼️ Baixar QR Code (PNG)", img_bytes, f"QR_{id_amostra}.png", "image/png")
                pdf_etiquetas = gerar_pdf_etiquetas(img, qtd_etiquetas, tamanho_mm, id_amostra=id_amostra)
                st.download_button(f"📄 Baixar PDF ({qtd_etiquetas}x Etiquetas)", pdf_etiquetas, f"Etiquetas_{id_amostra}.pdf", "application/pdf")

    # --- 6. CRIADOR DE POP COM PRÉ-VISUALIZAÇÃO EM TEMPO REAL E REFERÊNCIAS ---
    elif menu_selecionado == "📝 Criador de POP":
        st.title("📝 Procedimentos Operacionais Padrão (POPs)")

        aba_pops_view, aba_pop_form = st.tabs([
            "📚 POPs Cadastrados e Prévias",
            "➕ Criar / Atualizar POP (com Pré-visualização Dinâmica)",
        ])

        with aba_pops_view:
            st.subheader("📚 Acervo de POPs do Laboratório")
            pops_aprovados = [p for p in st.session_state.pops_db if p.get("status") == "Aprovado"]

            if pops_aprovados:
                for idx, pop in enumerate(pops_aprovados):
                    with st.container():
                        st.markdown(
                            f"""
                            <div class="pop-preview-card">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <h3 style="margin: 0; color: #0F172A; font-size: 1.1rem;">📝 {pop['titulo']}</h3>
                                    <span style="background-color: #ECFEFF; color: #0E7490; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 0.82rem;">
                                        {pop['codigo']} | v{pop['versao']}
                                    </span>
                                </div>
                                <hr style="margin: 10px 0; border: none; border-top: 1px solid #E2E8F0;" />
                                <p style="margin: 4px 0; font-size: 0.88rem;"><b>1. Objetivo:</b> {pop.get('objetivo', '-')}</p>
                                <p style="margin: 4px 0; font-size: 0.88rem;"><b>2. Materiais & Equipamentos:</b> {pop.get('materiais', '-')}</p>
                                <p style="margin: 4px 0; font-size: 0.88rem;"><b>3. Passo a Passo:</b> {str(pop.get('passos', '-')).replace(chr(10), ' | ')}</p>
                                <p style="margin: 4px 0; font-size: 0.88rem;"><b>4. Segurança / EPIs:</b> {pop.get('seguranca', '-')}</p>
                                <p style="margin: 4px 0; font-size: 0.88rem;"><b>5. Referências Usadas:</b> {pop.get('referencias', '-')}</p>
                                <p style="margin: 6px 0 0 0; color: #64748B; font-size: 0.8rem;"><i>Elaborado por: {pop.get('autor', 'Desconhecido')}</i></p>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        c_pop1, c_pop2, c_pop3 = st.columns([1.5, 2, 1])

                        with c_pop1:
                            pdf_bytes = gerar_pdf_pop(pop)
                            st.download_button(
                                label="📄 Baixar PDF do POP",
                                data=pdf_bytes,
                                file_name=f"{pop['codigo']}.pdf",
                                mime="application/pdf",
                                key=f"dl_pop_{idx}",
                            )

                        with c_pop2:
                            if st.button("📂 Publicar no Repositório", key=f"trans_pop_{idx}"):
                                b64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
                                novo_id = max([a.get("id", 0) for a in st.session_state.arquivos_db], default=0) + 1
                                st.session_state.arquivos_db.append({
                                    "id": novo_id,
                                    "titulo": f"{pop['codigo']} - {pop['titulo']}",
                                    "pasta": "POPs e Protocolos",
                                    "descricao": f"Procedimento Operacional Padrão (Versão {pop['versao']}). Objetivo: {pop.get('objetivo')}",
                                    "nome_original": f"{pop['codigo']}.pdf",
                                    "mime_type": "application/pdf",
                                    "conteudo_b64": b64_pdf,
                                    "autor": pop.get("autor", usuario_atual["nome"]),
                                    "data": datetime.now().strftime("%d/%m/%Y"),
                                    "status": "Aprovado",
                                })
                                salvar_dados(ARQUIVO_ARQUIVOS, st.session_state.arquivos_db)
                                st.success("✅ POP publicado na pasta de POPs!")

                        with c_pop3:
                            if is_admin or pop.get("autor") == usuario_atual["nome"]:
                                if st.button("🗑️ Excluir", key=f"del_pop_{idx}"):
                                    st.session_state.pops_db = [item for item in st.session_state.pops_db if item.get("codigo") != pop.get("codigo")]
                                    salvar_dados(ARQUIVO_POPS, st.session_state.pops_db)
                                    st.warning(f"POP '{pop['codigo']}' excluído.")
                                    st.rerun()

                        st.markdown("<br>", unsafe_allow_html=True)
            else:
                st.info("Nenhum POP aprovado cadastrado até o momento.")

        with aba_pop_form:
            st.subheader("➕ Formulário de Criação / Atualização de POP")
            st.caption("Preencha os campos à esquerda e acompanhe a **Pré-visualização em Tempo Real** no painel da direita.")

            col_form, col_prev = st.columns([1.1, 1])

            with col_form:
                modo_criacao = st.radio("Ação", ["Criar Novo POP", "Atualizar POP Existente"], horizontal=True)

                tit_selecionado = ""
                versao_calculada = 1

                if modo_criacao == "Atualizar POP Existente":
                    pops_existentes = [p["titulo"] for p in st.session_state.pops_db]
                    if pops_existentes:
                        pop_sel_tit = st.selectbox("Selecione o POP", pops_existentes)
                        pop_existente = next((p for p in st.session_state.pops_db if p["titulo"] == pop_sel_tit), None)
                        if pop_existente:
                            tit_selecionado = pop_existente["titulo"]
                            versao_calculada = pop_existente.get("versao", 1) + 1
                    else:
                        st.warning("Nenhum POP cadastrado para atualizar.")
                else:
                    opcoes_titulos_pop = POPS_PADRAO + ["✍️ Outro (Digitar manualmente)"]
                    sel_pop_pre = st.selectbox("Título Padrão ou Manual", opcoes_titulos_pop)
                    if sel_pop_pre == "✍️ Outro (Digitar manualmente)":
                        tit_selecionado = st.text_input("Digite o Título do POP *", "Preparo de Amostras para HPLC")
                    else:
                        tit_selecionado = sel_pop_pre

                cod_auto = gerar_codigo_pop(tit_selecionado if tit_selecionado else "POP", versao_calculada)

                p_objetivo = st.text_area("1. Objetivo *", value="Padronizar o procedimento no laboratório.", height=70)
                p_materiais = st.text_area("2. Materiais & Equipamentos *", value="Equipamentos de proteção individual, reagentes e vidrarias.", height=70)
                p_passos = st.text_area("3. Procedimento / Passo a Passo *", value="1. Ligar o equipamento.\n2. Calibrar conforme instrução.\n3. Executar o ensaio.", height=110)
                p_seguranca = st.text_area("4. Segurança & EPIs *", value="Jaleco, luvas de nitrilo e óculos de proteção.", height=70)
                p_referencias = st.text_area("5. Referências Usadas / Normas *", value="Artigo/Norma de referência utilizada para elaboração do protocolo.", height=70)

                if st.button("💾 Salvar Documento POP", type="primary", use_container_width=True):
                    if not (tit_selecionado and p_objetivo and p_passos):
                        st.error("Preencha todos os campos obrigatórios (*).")
                    else:
                        status_pop = "Aprovado" if is_admin else "Pendente"

                        novo_pop_data = {
                            "codigo": cod_auto,
                            "titulo": tit_selecionado.strip(),
                            "versao": versao_calculada,
                            "objetivo": p_objetivo.strip(),
                            "materiais": p_materiais.strip(),
                            "passos": p_passos.strip(),
                            "seguranca": p_seguranca.strip(),
                            "referencias": p_referencias.strip(),
                            "autor": usuario_atual["nome"],
                            "status": status_pop,
                        }

                        st.session_state.pops_db.append(novo_pop_data)
                        salvar_dados(ARQUIVO_POPS, st.session_state.pops_db)
                        st.success(f"✅ POP '{cod_auto}' salvo com sucesso!")
                        st.rerun()

            # PAINEL DE PRÉ-VISUALIZAÇÃO EM TEMPO REAL (LIVE PREVIEW)
            with col_prev:
                st.markdown("### 👁️ Pré-visualização em Tempo Real")
                st.markdown(
                    f"""
                    <div class="pop-preview-card" style="border-left: 5px solid #0E7490; background: #FFFFFF;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <h3 style="margin: 0; color: #0F172A; font-size: 1.05rem;">📝 {tit_selecionado if tit_selecionado else 'Título do POP'}</h3>
                            <span style="background-color: #ECFEFF; color: #0E7490; padding: 4px 8px; border-radius: 6px; font-weight: bold; font-size: 0.8rem;">
                                {cod_auto} | v{versao_calculada}
                            </span>
                        </div>
                        <hr style="margin: 10px 0; border: none; border-top: 1px solid #E2E8F0;" />
                        <p style="margin: 6px 0; font-size:0.85rem;"><b>1. Objetivo:</b><br/>{p_objetivo}</p>
                        <p style="margin: 6px 0; font-size:0.85rem;"><b>2. Materiais & Equipamentos:</b><br/>{p_materiais}</p>
                        <p style="margin: 6px 0; font-size:0.85rem;"><b>3. Passo a Passo:</b><br/>{p_passos.replace(chr(10), '<br/>')}</p>
                        <p style="margin: 6px 0; font-size:0.85rem;"><b>4. Segurança & EPIs:</b><br/>{p_seguranca}</p>
                        <p style="margin: 6px 0; font-size:0.85rem;"><b>5. Referências Usadas:</b><br/>{p_referencias}</p>
                        <div style="margin-top: 12px; font-size: 0.75rem; color: #94A3B8; text-align: right;">
                            Elaborado por: <b>{usuario_atual['nome']}</b>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    # --- 7. ADMINISTRAÇÃO ---
    elif menu_selecionado == "🛡️ Administração" and is_admin:
        st.title("🛡️ Central de Aprovações e Atribuições do Administrador")

        tab_usr, tab_orient, tab_grupos, tab_perfis, tab_arq, tab_pops = st.tabs([
            "👤 Acessos de Usuários",
            "🎓 Orientação (Orientador & Coorientador)",
            "🔬 Grupos de Pesquisa",
            "✏️ Alterações de Perfil",
            "📄 Arquivos Inseridos",
            "📝 POPs",
        ])

        with tab_usr:
            st.subheader("Solicitações de Acesso Pendentes")
            pend_acessos = [u for u in st.session_state.usuarios if u.get("status") == "Pendente"]

            if pend_acessos:
                for idx, u in enumerate(pend_acessos):
                    c_inf, c_b1, c_b2 = st.columns([3, 1, 1])
                    with c_inf:
                        st.write(f"👤 **{u['nome']}** (Usuário: `{u['usuario']}`)")
                        st.caption(f"Categoria: {u.get('categoria','-')} | Orientador: {u.get('orientador','-')} | E-mail: {u.get('email','-')}")
                    with c_b1:
                        if st.button("✅ Aprovar", key=f"ap_usr_{idx}", type="primary"):
                            u["status"] = "Aprovado"
                            salvar_dados(ARQUIVO_USUARIOS, st.session_state.usuarios)

                            for p in st.session_state.integrantes:
                                if p.get("Nome", "").strip().lower() == u["nome"].strip().lower():
                                    p["Situação"] = "Ativo"
                                    if p.get("OrientadorStatus") == "Pendente":
                                        p["OrientadorStatus"] = "Aprovado"
                            salvar_dados(ARQUIVO_INTEGRANTES, st.session_state.integrantes)

                            st.success(f"Acesso aprovado para {u['nome']}!")
                            st.rerun()
                    with c_b2:
                        if st.button("❌ Recusar", key=f"rec_usr_{idx}"):
                            u["status"] = "Recusado"
                            salvar_dados(ARQUIVO_USUARIOS, st.session_state.usuarios)
                            st.warning("Solicitação recusada.")
                            st.rerun()
                    st.markdown("---")
            else:
                st.info("Nenhuma solicitação de novo acesso pendente.")

        with tab_orient:
            st.subheader("🎓 Gestão e Atribuição de Orientador & Coorientador")
            st.caption("Apenas o Administrador pode definir ou alterar quem é o Orientador e o Coorientador de cada aluno registrado.")

            lista_professores = ["-"] + [p["Nome"] for p in st.session_state.integrantes if p.get("Categoria") == "Orientador"]
            lista_alunos_cad = [p for p in st.session_state.integrantes if p.get("Categoria") in ["Iniciação Científica", "Mestrado", "Doutorado", "Pós-Doutorado"]]

            if lista_alunos_cad:
                with st.form("form_admin_orientacao"):
                    dict_alunos = {f"{a['Nome']} ({a['Categoria']})": a for a in lista_alunos_cad}
                    aluno_sel_lbl = st.selectbox("Selecione o Aluno / Pesquisador *", list(dict_alunos.keys()))
                    aluno_objeto = dict_alunos[aluno_sel_lbl]

                    idx_or_def = lista_professores.index(aluno_objeto.get("Orientador")) if aluno_objeto.get("Orientador") in lista_professores else 0
                    idx_co_def = lista_professores.index(aluno_objeto.get("Coorientador")) if aluno_objeto.get("Coorientador") in lista_professores else 0

                    c_o1, c_o2 = st.columns(2)
                    with c_o1:
                        orient_escolhido = st.selectbox("Orientador Principal *", lista_professores, index=idx_or_def)
                    with c_o2:
                        coorient_escolhido = st.selectbox("Coorientador (Opcional)", lista_professores, index=idx_co_def)

                    btn_salvar_vinculo = st.form_submit_button("💾 Confirmar Atribuição do Admin", type="primary")

                    if btn_salvar_vinculo:
                        aluno_objeto["Orientador"] = orient_escolhido
                        aluno_objeto["Coorientador"] = coorient_escolhido
                        aluno_objeto["OrientadorStatus"] = "Aprovado"
                        salvar_dados(ARQUIVO_INTEGRANTES, st.session_state.integrantes)

                        for u in st.session_state.usuarios:
                            if u.get("nome", "").strip().lower() == aluno_objeto["Nome"].strip().lower():
                                u["orientador"] = orient_escolhido
                                u["coorientador"] = coorient_escolhido
                                u["orientador_status"] = "Aprovado"
                        salvar_dados(ARQUIVO_USUARIOS, st.session_state.usuarios)

                        st.success(f"Vínculos atualizados para {aluno_objeto['Nome']}!")
                        st.rerun()

            st.markdown("---")
            st.subheader("Solicitações Pendentes de Orientação")
            pend_orient_list = [p for p in st.session_state.integrantes if p.get("OrientadorStatus") == "Pendente"]

            if pend_orient_list:
                for idx, al in enumerate(pend_orient_list):
                    c_inf, c_b1, c_b2 = st.columns([3, 1, 1])
                    with c_inf:
                        st.write(f"🎓 **Aluno(a):** {al['Nome']} ({al.get('Categoria')})")
                        st.write(f"👨‍🏫 **Orientador Solicitado:** `{al.get('Orientador')}`")
                    with c_b1:
                        if st.button("✅ Aprovar Vínculo", key=f"ap_or_{idx}", type="primary"):
                            al["OrientadorStatus"] = "Aprovado"
                            salvar_dados(ARQUIVO_INTEGRANTES, st.session_state.integrantes)

                            for u in st.session_state.usuarios:
                                if u.get("nome", "").strip().lower() == al["Nome"].strip().lower():
                                    u["orientador_status"] = "Aprovado"
                            salvar_dados(ARQUIVO_USUARIOS, st.session_state.usuarios)

                            st.success("Vínculo de orientação aprovado!")
                            st.rerun()
                    with c_b2:
                        if st.button("❌ Recusar Vínculo", key=f"rec_or_{idx}"):
                            al["Orientador"] = "-"
                            al["OrientadorStatus"] = "Recusado"
                            salvar_dados(ARQUIVO_INTEGRANTES, st.session_state.integrantes)
                            st.warning("Vínculo recusado.")
                            st.rerun()
                    st.markdown("---")
            else:
                st.info("Nenhuma solicitação de orientação pendente.")

        with tab_grupos:
            st.subheader("Aprovação de Grupos de Pesquisa e Membros")

            st.markdown("##### ➕ Novas Solicitações de Criação de Grupo")
            grps_pendentes = [g for g in st.session_state.grupos_db if g.get("status") == "Pendente"]

            if grps_pendentes:
                for idx, g in enumerate(grps_pendentes):
                    c_inf, c_b1, c_b2 = st.columns([3, 1, 1])
                    with c_inf:
                        st.write(f"🔬 **Grupo:** {g['nome']}")
                        st.caption(f"Solicitante / Líder: {g.get('lider')} | Senha Definida: `{g.get('senha')}` | Descrição: {g.get('descricao')}")
                    with c_b1:
                        if st.button("✅ Aprovar Grupo", key=f"ap_grp_{idx}", type="primary"):
                            g["status"] = "Aprovado"
                            salvar_dados(ARQUIVO_GRUPOS, st.session_state.grupos_db)
                            st.success(f"Grupo '{g['nome']}' aprovado com sucesso!")
                            st.rerun()
                    with c_b2:
                        if st.button("❌ Recusar Grupo", key=f"rec_grp_{idx}"):
                            st.session_state.grupos_db = [item for item in st.session_state.grupos_db if item["id"] != g["id"]]
                            salvar_dados(ARQUIVO_GRUPOS, st.session_state.grupos_db)
                            st.warning("Solicitação de grupo recusada.")
                            st.rerun()
                    st.markdown("---")
            else:
                st.info("Nenhuma solicitação de criação de grupo pendente.")

            st.markdown("##### 🙋‍♂️ Solicitações de Membros para Entrar em Grupos")
            tem_membro_pend = False
            for g in st.session_state.grupos_db:
                if g.get("status") == "Aprovado" and g.get("membros_pendentes"):
                    tem_membro_pend = True
                    st.write(f"🔬 **Grupo:** {g['nome']}")
                    for idx_m, mb_nome in enumerate(g["membros_pendentes"]):
                        c_inf, c_b1, c_b2 = st.columns([3, 1, 1])
                        with c_inf:
                            st.write(f"👨‍🔬 **Pesquisador:** {mb_nome}")
                        with c_b1:
                            if st.button("✅ Aceitar Membro", key=f"ap_mb_{g['id']}_{idx_m}", type="primary"):
                                g["membros"].append(mb_nome)
                                g["membros_pendentes"].remove(mb_nome)
                                salvar_dados(ARQUIVO_GRUPOS, st.session_state.grupos_db)
                                st.success(f"Membro {mb_nome} adicionado ao grupo {g['nome']}!")
                                st.rerun()
                        with c_b2:
                            if st.button("❌ Recusar Membro", key=f"rec_mb_{g['id']}_{idx_m}"):
                                g["membros_pendentes"].remove(mb_nome)
                                salvar_dados(ARQUIVO_GRUPOS, st.session_state.grupos_db)
                                st.warning("Solicitação de entrada recusada.")
                                st.rerun()
                        st.markdown("---")
            if not tem_membro_pend:
                st.info("Nenhuma solicitação de entrada de membros pendente.")

        with tab_perfis:
            st.subheader("Solicitações de Atualização de Perfil")
            pend_perfis = [u for u in st.session_state.usuarios if u.get("pendente_atualizacao")]

            if pend_perfis:
                for idx, u in enumerate(pend_perfis):
                    p_data = u["pendente_atualizacao"]
                    st.markdown(f"#### 👤 **{u['nome']}** (`{u['usuario']}`)")

                    c_antes, c_depois = st.columns(2)
                    with c_antes:
                        st.markdown("**📌 Dados Atuais:**")
                        st.write(f"- **Categoria:** {u.get('categoria', '-')}")
                        st.write(f"- **Orientador:** {u.get('orientador', '-')}")
                        st.write(f"- **E-mail:** {u.get('email', '-')}")

                    with c_depois:
                        st.markdown("**✏️ Dados Solicitados:**")
                        st.write(f"- **Categoria:** {p_data.get('categoria', '-')}")
                        st.write(f"- **Orientador:** {p_data.get('orientador', '-')}")
                        st.write(f"- **E-mail:** {p_data.get('email', '-')}")

                    c_b1, c_b2 = st.columns([1, 1])
                    with c_b1:
                        if st.button("✅ Aprovar Mudança", key=f"ap_prf_{idx}", type="primary"):
                            u["categoria"] = p_data.get("categoria")
                            u["orientador"] = p_data.get("orientador")
                            u["orientador_status"] = "Aprovado"
                            u["email"] = p_data.get("email")
                            del u["pendente_atualizacao"]
                            salvar_dados(ARQUIVO_USUARIOS, st.session_state.usuarios)

                            for p in st.session_state.integrantes:
                                if p.get("Nome", "").strip().lower() == u["nome"].strip().lower():
                                    p["Categoria"] = p_data.get("categoria")
                                    p["Orientador"] = p_data.get("orientador")
                                    p["OrientadorStatus"] = "Aprovado"
                                    p["Email"] = p_data.get("email")

                            salvar_dados(ARQUIVO_INTEGRANTES, st.session_state.integrantes)
                            st.success("Perfil atualizado!")
                            st.rerun()

                    with c_b2:
                        if st.button("❌ Recusar Mudança", key=f"rec_prf_{idx}"):
                            del u["pendente_atualizacao"]
                            salvar_dados(ARQUIVO_USUARIOS, st.session_state.usuarios)
                            st.warning("Solicitação recusada.")
                            st.rerun()

                    st.markdown("---")
            else:
                st.info("Nenhuma solicitação de alteração de perfil pendente.")

        with tab_arq:
            st.subheader("Arquivos Pendentes")
            pend_arqs = [a for a in st.session_state.arquivos_db if a.get("status") == "Pendente"]

            if pend_arqs:
                for idx, a in enumerate(pend_arqs):
                    c_inf, c_b1, c_b2 = st.columns([3, 1, 1])
                    with c_inf:
                        st.write(f"📄 **{a['titulo']}** (Pasta: `{a.get('pasta', 'Geral')}`)")
                    with c_b1:
                        if st.button("✅ Aprovar", key=f"ap_arq_{idx}", type="primary"):
                            a["status"] = "Aprovado"
                            salvar_dados(ARQUIVO_ARQUIVOS, st.session_state.arquivos_db)
                            st.success("Arquivo publicado!")
                            st.rerun()
                    with c_b2:
                        if st.button("❌ Recusar", key=f"del_arq_p_{idx}"):
                            st.session_state.arquivos_db = [item for item in st.session_state.arquivos_db if item["id"] != a["id"]]
                            salvar_dados(ARQUIVO_ARQUIVOS, st.session_state.arquivos_db)
                            st.warning("Arquivo removido.")
                            st.rerun()
                    st.markdown("---")
            else:
                st.info("Nenhum arquivo pendente.")

        with tab_pops:
            st.subheader("POPs Pendentes")
            pend_pops = [p for p in st.session_state.pops_db if p.get("status") == "Pendente"]

            if pend_pops:
                for idx, p in enumerate(pend_pops):
                    c_inf, c_b1, c_b2 = st.columns([3, 1, 1])
                    with c_inf:
                        st.write(f"📝 **{p['codigo']} - {p['titulo']}**")
                    with c_b1:
                        if st.button("✅ Aprovar", key=f"ap_pop_{idx}", type="primary"):
                            p["status"] = "Aprovado"
                            salvar_dados(ARQUIVO_POPS, st.session_state.pops_db)
                            st.success("POP aprovado!")
                            st.rerun()
                    with c_b2:
                        if st.button("❌ Recusar", key=f"rec_pop_{idx}"):
                            st.session_state.pops_db = [item for item in st.session_state.pops_db if item.get("codigo") != p.get("codigo")]
                            salvar_dados(ARQUIVO_POPS, st.session_state.pops_db)
                            st.warning("POP recusado.")
                            st.rerun()
                    st.markdown("---")
            else:
                st.info("Nenhum POP pendente.")

    # --- 8. MEU PERFIL ---
    elif menu_selecionado == "👤 Meu perfil":
        st.title("👤 Meu Perfil e Configurações")

        integrante_reg = next(
            (p for p in st.session_state.integrantes if str(p.get("Nome", "")).strip().lower() == str(usr_atual_reg.get("nome", "")).strip().lower()),
            {}
        )

        st.subheader("Meus Dados Registrados")
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**Nome:** {usr_atual_reg.get('nome')}")
            st.write(f"**Usuário:** `{usr_atual_reg.get('usuario')}`")
            st.write(f"**Categoria:** {usr_atual_reg.get('categoria', '-')}")
            st.write(f"**Orientador:** {integrante_reg.get('Orientador', '-')}")
            st.write(f"**Coorientador:** {integrante_reg.get('Coorientador', '-')}")
        with c2:
            st.write(f"**Vínculo:** {usr_atual_reg.get('vinculo', '-')}")
            st.write(f"**Telefone:** {usr_atual_reg.get('telefone', '-')}")
            st.write(f"**E-mail:** {usr_atual_reg.get('email', '-')}")

        if usr_atual_reg.get("pendente_atualizacao"):
            st.warning("⚠️ Você possui uma solicitação de alteração de dados **PENDENTE** de aprovação do Administrador.")

        st.markdown("---")
        st.subheader("✏️ Solicitar Alteração de Dados de Perfil")

        idx_cat = CATEGORIAS_PADRAO.index(usr_atual_reg.get("categoria")) if usr_atual_reg.get("categoria") in CATEGORIAS_PADRAO else 0

        with st.form("form_edit_perfil"):
            nova_cat = st.selectbox("Categoria", CATEGORIAS_PADRAO, index=idx_cat)
            novo_vinc = st.text_input("Vínculo / Curso", value=usr_atual_reg.get("vinculo", "UFRRJ - Engenharia Química"))
            novo_tel = st.text_input("Telefone para Contato", value=usr_atual_reg.get("telefone", ""))
            novo_email = st.text_input("E-mail para Contato", value=usr_atual_reg.get("email", ""))
            novos_horarios = st.text_input("Dias e Horários no Laboratório", value=integrante_reg.get("DiasHorarios", "Não informado"))
            novo_lattes = st.text_input("Link do Currículo Lattes", value=integrante_reg.get("Lattes", "http://lattes.cnpq.br/"))

            btn_env_prof = st.form_submit_button("Enviar Alterações para Aprovação do Administrador", type="primary")

            if btn_env_prof:
                if not (novo_tel.strip() and novo_email.strip()):
                    st.error("Telefone e E-mail são obrigatórios.")
                else:
                    dados_novos = {
                        "categoria": nova_cat,
                        "orientador": integrante_reg.get("Orientador", "-"),
                        "vinculo": novo_vinc.strip(),
                        "telefone": novo_tel.strip(),
                        "email": novo_email.strip(),
                        "horarios": novos_horarios.strip(),
                        "lattes": novo_lattes.strip(),
                    }

                    usr_atual_reg["pendente_atualizacao"] = dados_novos
                    for u in st.session_state.usuarios:
                        if str(u.get("usuario")).lower() == str(usr_atual_reg["usuario"]).lower():
                            u["pendente_atualizacao"] = dados_novos
                            break

                    salvar_dados(ARQUIVO_USUARIOS, st.session_state.usuarios)
                    st.success("✅ Solicitação de alteração enviada com sucesso! Aguarde a aprovação do Administrador.")
                    st.rerun()
