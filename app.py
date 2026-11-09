import base64
import calendar
from datetime import datetime, date, time
from io import BytesIO
import json
import os
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import streamlit as st

# Configura a barra lateral para abrir expandida tanto no celular quanto no computador
st.set_page_config(
    page_title="Central de Pesquisa",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Tenta importar o ReportLab; caso não esteja instalado no Streamlit Cloud, usa fallback com PIL
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    REPORTLAB_DISPONIVEL = True
except ImportError:
    REPORTLAB_DISPONIVEL = False

# Tenta importar qrcode
try:
    import qrcode
    QRCODE_DISPONIVEL = True
except ImportError:
    QRCODE_DISPONIVEL = False

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
    footer {{visibility: hidden;}}
    [data-testid="stToolbar"] {{display: none;}}
    
    /* Deixa o cabeçalho transparente sem bloquear cliques na página */
    [data-testid="stHeader"] {{
        background-color: transparent !important;
        pointer-events: none !important;
        z-index: 100 !important;
    }}

    /* Reativa os cliques apenas para os elementos/botões dentro do cabeçalho */
    [data-testid="stHeader"] * {{
        pointer-events: auto !important;
    }}

    /* Fixa e destaca o botão de ABRIR a barra lateral no topo esquerdo em dispositivos móveis */
    [data-testid="stCollapsedControl"] {{
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        pointer-events: auto !important;
        z-index: 999999 !important;
        position: fixed !important;
        top: 10px !important;
        left: 10px !important;
        background-color: {cor_primaria} !important;
        border-radius: 8px !important;
        padding: 4px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.25) !important;
    }}

    [data-testid="stCollapsedControl"] button,
    [data-testid="stCollapsedControl"] svg {{
        color: #FFFFFF !important;
        fill: #FFFFFF !important;
    }}

    [data-testid="stSidebarCollapseButton"],
    button[data-testid="baseButton-header"] {{
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        pointer-events: auto !important;
        z-index: 999999 !important;
    }}
    
    .stApp {{ background-color: #F8FAFC; }}
    [data-testid="stSidebar"] {{ background-color: #FFFFFF; border-right: 1px solid #E2E8F0; }}
    
    [data-testid="stSidebar"] div.stButton > button {{
        text-align: left !important; justify-content: flex-start !important; padding: 8px 12px !important;
        width: 100% !important; margin-bottom: 3px !important; border-radius: 6px !important; font-size: 0.88rem !important;
        font-weight: 500 !important; transition: all 0.2s ease-in-out !important;
    }}
    
    [data-testid="stSidebar"] div.stButton > button[kind="secondary"] {{
        background-color: transparent !important; color: #475569 !important; border: none !important; box-shadow: none !important;
    }}
    [data-testid="stSidebar"] div.stButton > button[kind="secondary"]:hover {{
        background-color: {cor_bg_light} !important; color: {cor_primaria} !important;
    }}
    
    [data-testid="stSidebar"] div.stButton > button[kind="primary"] {{
        background-color: {cor_bg_light} !important; color: {cor_primaria} !important; font-weight: 700 !important;
        border-left: 4px solid {cor_primaria} !important; border-top: none !important; border-right: none !important; border-bottom: none !important;
        box-shadow: none !important;
    }}

    h1, h2, h3 {{ color: #0F172A !important; font-family: 'Segoe UI', Roboto, sans-serif; }}
    .sidebar-section {{ font-size: 0.70rem; font-weight: 800; color: #94A3B8; text-transform: uppercase; margin-top: 1.2rem; margin-bottom: 0.4rem; letter-spacing: 0.08em; }}
    
    .kpi-card {{
        border-radius: 10px; padding: 16px 20px; border: 1px solid #E2E8F0;
        display: flex; align-items: center; justify-content: space-between; box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }}
    .kpi-card-blue {{ background-color: #F0F9FF; border-left: 4px solid #0284C7; }}
    .kpi-card-green {{ background-color: #ECFDF5; border-left: 4px solid #059669; }}
    .kpi-card-amber {{ background-color: #FFFBEB; border-left: 4px solid #D97706; }}
    .kpi-card-purple {{ background-color: #F5F3FF; border-left: 4px solid #7C3AED; }}
    
    .kpi-val {{ font-size: 1.8rem; font-weight: 800; color: #0F172A; line-height: 1; }}
    .kpi-label {{ font-size: 0.82rem; font-weight: 600; color: #475569; margin-top: 4px; }}
    .kpi-icon {{ font-size: 2rem; opacity: 0.85; }}

    .badge-ativo {{ background-color: #DCFCE7; color: #15803D; padding: 3px 10px; border-radius: 12px; font-weight: 700; font-size: 0.78rem; display: inline-block; }}
    .badge-pendente {{ background-color: #FEF3C7; color: #B45309; padding: 3px 10px; border-radius: 12px; font-weight: 700; font-size: 0.78rem; display: inline-block; }}
    .badge-urgente {{ background-color: #FEE2E2; color: #991B1B; padding: 3px 10px; border-radius: 12px; font-weight: 700; font-size: 0.78rem; display: inline-block; }}
    .avatar-circle {{ width: 38px; height: 38px; border-radius: 50%; background-color: #E2E8F0; color: #334155; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; }}
    .css-card {{ background-color: white; padding: 16px; border-radius: 8px; border: 1px solid #E2E8F0; box-shadow: 0 1px 3px rgba(0,0,0,0.02); margin-bottom: 12px; }}
    .grp-card {{ background-color: white; padding: 18px; border-radius: 10px; border: 1px solid #CBD5E1; border-top: 4px solid {cor_primaria}; box-shadow: 0 2px 4px rgba(0,0,0,0.03); margin-bottom: 15px; height: 100%; }}
    .aviso-card {{ background-color: #FFFFFF; border-radius: 8px; padding: 14px 16px; margin-bottom: 10px; border-left: 4px solid {cor_primaria}; box-shadow: 0 1px 3px rgba(0,0,0,0.02); }}
    .event-card {{ background-color: #FFFFFF; border-radius: 8px; padding: 12px 14px; margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.02); border: 1px solid #E2E8F0; }}
    .pop-preview-card {{ background-color: #FFFFFF; border: 1px solid #CBD5E1; border-left: 4px solid {cor_primaria}; border-radius: 8px; padding: 16px; margin-bottom: 15px; }}
    .tree-orientador {{ background-color: #F8FAFC; border: 1px solid #E2E8F0; border-left: 4px solid {cor_primaria}; padding: 12px 16px; border-radius: 8px; margin-top: 15px; font-weight: bold; font-size: 0.95rem; color: #0F172A; }}
    .tree-orientado {{ background-color: #FFFFFF; border: 1px solid #E2E8F0; padding: 10px 14px; border-radius: 6px; margin-left: 24px; margin-top: 6px; display: flex; align-items: center; justify-content: space-between; }}
    .table-header {{ font-size: 0.72rem; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em; padding-bottom: 6px; border-bottom: 1px solid #E2E8F0; margin-bottom: 10px; }}
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
ARQUIVO_REAGENTES = "reagentes_solucoes.json"

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
        "colider": "Gabriela Mendes Farias Matos",
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
        "solicitacoes_itens": [
            {
                "id": 1,
                "item": "Álcool Etílico Absolute P.A.",
                "categoria_item": "Reagentes",
                "quantidade": "2 Frascos de 1L",
                "urgente": True,
                "razao_urgencia": "Necessário para extrações da próxima semana.",
                "especificacoes": "Grau P.A. (Pureza >= 99.5%)",
                "solicitante": "Gabriela Mendes Farias Matos",
                "data_solicitacao": datetime.now().strftime("%d/%m/%Y"),
                "status": "Pendente",
                "aprovado_por": "-"
            }
        ],
        "documentos": [],
        "mural": "📌 **Anotações do Grupo:** Apresentação da qualificação agendada para o próximo mês. Revisar dados do lote 3 de lipases."
    }
]

REAGENTES_SOLUCOES_INICIAIS = [
    {
        "nome": "Hidróxido de Sódio (NaOH)",
        "formula": "NaOH",
        "massa_molar": 39.997,
        "pureza_padrao": 98.0,
        "densidade_g_ml": None,
        "estado": "Sólido",
        "referencia": "Handbook of Chemistry and Physics"
    },
    {
        "nome": "Ácido Clorídrico Concentrado (HCl)",
        "formula": "HCl",
        "massa_molar": 36.46,
        "pureza_padrao": 37.0,
        "densidade_g_ml": 1.19,
        "estado": "Líquido",
        "referencia": "Sigma-Aldrich Technical Data"
    },
    {
        "nome": "Tampão Fosfato de Sódio (Na2HPO4)",
        "formula": "Na2HPO4",
        "massa_molar": 141.96,
        "pureza_padrao": 99.0,
        "densidade_g_ml": None,
        "estado": "Sólido",
        "referencia": "Standard Buffer Protocols"
    },
    {
        "nome": "Cloreto de Sódio (NaCl)",
        "formula": "NaCl",
        "massa_molar": 58.44,
        "pureza_padrao": 99.5,
        "densidade_g_ml": None,
        "estado": "Sólido",
        "referencia": "USP Grade Reagent"
    },
    {
        "nome": "Ácido Sulfúrico Concentrado (H2SO4)",
        "formula": "H2SO4",
        "massa_molar": 98.07,
        "pureza_padrao": 98.0,
        "densidade_g_ml": 1.84,
        "estado": "Líquido",
        "referencia": "Reagent Chemical Standards"
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

# --- FUNÇÕES DE GERAÇÃO DE PDF VETORIAL PADRONIZADAS ---

def gerar_pdf_pop(pop_dict):
    buffer = BytesIO()
    codigo = pop_dict.get('codigo', 'POP-DOC-v1')
    titulo = pop_dict.get('titulo', 'Documento sem título')
    versao = pop_dict.get('versao', 1)
    autor = pop_dict.get('autor', 'N/A')
    status = pop_dict.get('status', 'Aprovado')

    if REPORTLAB_DISPONIVEL:
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )
        styles = getSampleStyleSheet()
        story = []

        title_style = ParagraphStyle(
            'PopTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=13,
            textColor=colors.HexColor('#0F172A')
        )
        
        sec_title_style = ParagraphStyle(
            'PopSecTitle',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#0F172A'),
            spaceBefore=10,
            spaceAfter=4
        )

        body_style = ParagraphStyle(
            'PopBodyText',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor('#1E293B')
        )

        header_data = [
            [
                Paragraph("<b>PROCEDIMENTO OPERACIONAL PADRÃO (POP)</b>", title_style),
                Paragraph(f"<b>CÓDIGO:</b> {codigo}", title_style)
            ],
            [
                Paragraph(f"<b>Título:</b> {titulo}", title_style),
                Paragraph(f"<b>Versão:</b> {versao}", title_style)
            ],
            [
                Paragraph(f"<b>Elaborado por:</b> {autor}", title_style),
                Paragraph(f"<b>Status:</b> {status}", title_style)
            ]
        ]

        t_header = Table(header_data, colWidths=[360, 180])
        t_header.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#475569')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('PADDING', (0,0), (-1,-1), 6),
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ]))
        story.append(t_header)
        story.append(Spacer(1, 14))

        sections = [
            ("1. OBJETIVO", pop_dict.get("objetivo", "")),
            ("2. MATERIAIS E EQUIPAMENTOS", pop_dict.get("materiais", "")),
            ("3. PROCEDIMENTO/PASSO A PASSO", pop_dict.get("passos", "")),
            ("4. SEGURANÇA E EPIS", pop_dict.get("seguranca", "")),
            ("5. REFERÊNCIAS BIBLIOGRÁFICAS", pop_dict.get("referencias", "-")),
        ]

        for title, content in sections:
            if content:
                story.append(Paragraph(title, sec_title_style))
                content_p = str(content).replace('\n', '<br/>')
                story.append(Paragraph(content_p, body_style))
                story.append(Spacer(1, 4))

        doc.build(story)
        return buffer.getvalue()
    else:
        page = Image.new("RGB", (612, 792), "white")
        draw = ImageDraw.Draw(page)
        draw.rectangle([36, 36, 576, 116], fill="#F8FAFC", outline="#475569", width=1)
        draw.line([(36, 62.6), (576, 62.6)], fill="#CBD5E1", width=1)
        draw.line([(36, 89.3), (576, 89.3)], fill="#CBD5E1", width=1)
        draw.line([(396, 36), (396, 116)], fill="#CBD5E1", width=1)

        draw.text((44, 44), "PROCEDIMENTO OPERACIONAL PADRÃO (POP)", fill="black")
        draw.text((404, 44), f"CÓDIGO: {codigo}", fill="black")
        draw.text((44, 70), f"Título: {titulo}", fill="black")
        draw.text((404, 70), f"Versão: {versao}", fill="black")
        draw.text((44, 96), f"Elaborado por: {autor}", fill="black")
        draw.text((404, 96), f"Status: {status}", fill="black")

        y = 136
        secoes = [
            ("1. OBJETIVO", pop_dict.get("objetivo", "")),
            ("2. MATERIAIS E EQUIPAMENTOS", pop_dict.get("materiais", "")),
            ("3. PROCEDIMENTO/PASSO A PASSO", pop_dict.get("passos", "")),
            ("4. SEGURANÇA E EPIS", pop_dict.get("seguranca", "")),
            ("5. REFERÊNCIAS BIBLIOGRÁFICAS", pop_dict.get("referencias", "")),
        ]

        for tit, txt in secoes:
            draw.text((36, y), tit, fill="#0F172A")
            y += 20
            for line in str(txt).split("\n"):
                draw.text((46, y), line[:85], fill="#1E293B")
                y += 15
            y += 10

        page.save(buffer, format="PDF", resolution=72.0)
        return buffer.getvalue()
        

def gerar_pdf_solicitacao_item(solicitacao, nome_grupo, lider_nome, colider_nome):
    buffer = BytesIO()
    req_id = solicitacao.get('id', 1)
    req_data = solicitacao.get('data_solicitacao', '-')
    req_status = solicitacao.get('status', 'Pendente')
    urgente_str = "SIM (URGENTE)" if solicitacao.get("urgente") else "NÃO (PROCESSO PADRÃO)"
    codigo_req = f"REQ-{req_id:04d}"

    if REPORTLAB_DISPONIVEL:
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )
        styles = getSampleStyleSheet()
        story = []

        title_style = ParagraphStyle(
            'HeaderTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=13,
            textColor=colors.HexColor('#0F172A')
        )
        
        sec_title_style = ParagraphStyle(
            'ReqSecTitle',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#0F172A'),
            spaceBefore=10,
            spaceAfter=4
        )

        body_style = ParagraphStyle(
            'ReqBodyText',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor('#1E293B')
        )

        header_data = [
            [
                Paragraph("<b>REQUISIÇÃO DE REAGENTES E PRODUTOS</b>", title_style),
                Paragraph(f"<b>CÓDIGO:</b> {codigo_req}", title_style)
            ],
            [
                Paragraph(f"<b>Grupo de Pesquisa:</b> {nome_grupo}", title_style),
                Paragraph(f"<b>Data:</b> {req_data}", title_style)
            ],
            [
                Paragraph(f"<b>Solicitante:</b> {solicitacao.get('solicitante', '-')}", title_style),
                Paragraph(f"<b>Status:</b> {req_status}", title_style)
            ]
        ]
        t_header = Table(header_data, colWidths=[360, 180])
        t_header.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#475569')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('PADDING', (0,0), (-1,-1), 6),
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ]))
        story.append(t_header)
        story.append(Spacer(1, 14))

        sections = [
            ("1. ITEM E CATEGORIA SOLICITADA", f"• Item/Material Solicitado: {solicitacao.get('item', '-')}\n• Categoria: {solicitacao.get('categoria_item', 'Reagentes')}\n• Quantidade: {solicitacao.get('quantidade', '-')}"),
            ("2. URGÊNCIA E JUSTIFICATIVA", f"• Grau de Urgência: {urgente_str}\n• Razão/Justificativa: {solicitacao.get('razao_urgencia', '-')}"),
            ("3. ESPECIFICAÇÕES TÉCNICAS DO MATERIAL", str(solicitacao.get('especificacoes', '-'))),
            ("4. APROVAÇÃO E LIDERANÇA", f"• Liderança Responsável: {lider_nome} / {colider_nome}\n• Aprovado Por: {solicitacao.get('aprovado_por', '-')}"),
        ]

        for title, content in sections:
            if content:
                story.append(Paragraph(title, sec_title_style))
                content_p = str(content).replace('\n', '<br/>')
                story.append(Paragraph(content_p, body_style))
                story.append(Spacer(1, 4))

        story.append(Spacer(1, 30))
        sig_style = ParagraphStyle('SigText', parent=body_style, alignment=1)
        sig_data = [
            [Paragraph("____________________________________________", sig_style)],
            [Paragraph("<b>Assinatura do Líder / Colíder Responsável</b>", sig_style)]
        ]
        t_sig = Table(sig_data, colWidths=[540])
        t_sig.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(t_sig)

        doc.build(story)
        return buffer.getvalue()
    else:
        page = Image.new("RGB", (612, 792), "white")
        draw = ImageDraw.Draw(page)
        draw.rectangle([36, 36, 576, 116], fill="#F8FAFC", outline="#475569", width=1)
        draw.line([(36, 62.6), (576, 62.6)], fill="#CBD5E1", width=1)
        draw.line([(36, 89.3), (576, 89.3)], fill="#CBD5E1", width=1)
        draw.line([(396, 36), (396, 116)], fill="#CBD5E1", width=1)

        draw.text((44, 44), "REQUISIÇÃO DE REAGENTES E PRODUTOS", fill="black")
        draw.text((404, 44), f"CÓDIGO: {codigo_req}", fill="black")
        draw.text((44, 70), f"Grupo de Pesquisa: {nome_grupo}", fill="black")
        draw.text((404, 70), f"Data: {req_data}", fill="black")
        draw.text((44, 96), f"Solicitante: {solicitacao.get('solicitante', '-')}", fill="black")
        draw.text((404, 96), f"Status: {req_status}", fill="black")

        y = 136
        secoes = [
            ("1. ITEM E CATEGORIA SOLICITADA", f"Item/Material: {solicitacao.get('item', '-')}\nCategoria: {solicitacao.get('categoria_item', 'Reagentes')}\nQuantidade: {solicitacao.get('quantidade', '-')}"),
            ("2. URGÊNCIA E JUSTIFICATIVA", f"Urgência: {urgente_str}\nJustificativa: {solicitacao.get('razao_urgencia', '-')}"),
            ("3. ESPECIFICAÇÕES TÉCNICAS DO MATERIAL", str(solicitacao.get('especificacoes', '-'))),
            ("4. APROVAÇÃO E LIDERANÇA", f"Liderança: {lider_nome} / {colider_nome}\nAprovado por: {solicitacao.get('aprovado_por', '-')}"),
        ]

        for tit, txt in secoes:
            draw.text((36, y), tit, fill="#0F172A")
            y += 20
            for line in str(txt).split("\n"):
                draw.text((46, y), line[:85], fill="#1E293B")
                y += 15
            y += 10

        page.save(buffer, format="PDF", resolution=72.0)
        return buffer.getvalue()


# --- FUNÇÃO DE GERAÇÃO DE ETIQUETAS EM GRADE (AMOSTRAS E SOLUÇÕES) ---

def gerar_pdf_etiquetas(qr_img_pil, quantidade, mm_size, id_amostra="", dados_amostra=None):
    """
    Gera um PDF contendo a quantidade especificada de etiquetas em formato de grade/cartela.
    """
    if dados_amostra is None:
        dados_amostra = {}

    nome_amostra = dados_amostra.get("nome_amostra", "Amostra / Reagente")
    data_obtencao = dados_amostra.get("data_obtencao", "-")
    responsavel = dados_amostra.get("responsavel", "Pesquisador")

    buffer = BytesIO()
    
    # Conversão de mm para pontos PDF (1 mm = 2.83465 pt)
    size_pt = max(mm_size * 2.83465, 40)
    qr_box_size = size_pt * 0.55  # QR Code ocupa ~55% da etiqueta

    if REPORTLAB_DISPONIVEL:
        from reportlab.platypus import Image as RLImage, SimpleDocTemplate, Table, TableStyle, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors

        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=20,
            leftMargin=20,
            topMargin=20,
            bottomMargin=20
        )
        styles = getSampleStyleSheet()
        story = []

        # Preparar imagem do QR Code
        qr_temp_buffer = BytesIO()
        qr_img_pil.save(qr_temp_buffer, format="PNG")
        qr_temp_buffer.seek(0)

        # Estilo do texto compacto da etiqueta
        lbl_style = ParagraphStyle(
            'StickerText',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=max(6, min(9, mm_size * 0.25)),
            leading=max(7, min(10, mm_size * 0.28)),
            textColor=colors.HexColor('#0F172A'),
            alignment=1  # Centralizado
        )

        sub_lbl_style = ParagraphStyle(
            'StickerSubText',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=max(5, min(7, mm_size * 0.20)),
            leading=max(6, min(8, mm_size * 0.22)),
            textColor=colors.HexColor('#334155'),
            alignment=1
        )

        # Monta a célula de uma etiqueta individual
        def criar_celula_etiqueta():
            qr_stream = BytesIO(qr_temp_buffer.getvalue())
            qr_img = RLImage(qr_stream, width=qr_box_size, height=qr_box_size)
            txt_id = Paragraph(f"<b>{id_amostra}</b>", lbl_style)
            txt_nome = Paragraph(nome_amostra[:22], sub_lbl_style)
            txt_dt = Paragraph(data_obtencao, sub_lbl_style)
            
            t_cell = Table([[qr_img], [txt_id], [txt_nome], [txt_dt]], colWidths=[size_pt])
            t_cell.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
                ('PADDING', (0,0), (-1,-1), 2),
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FFFFFF')),
            ]))
            return t_cell

        # Calcular colunas por linha na folha A4 (largura útil = ~572pt)
        largura_util = 572
        colunas = max(1, int(largura_util // (size_pt + 8)))
        
        # Montar a grade com a quantidade solicitada
        etiquetas_celulas = [criar_celula_etiqueta() for _ in range(quantidade)]
        
        grade_matriz = []
        linha_atual = []
        for cell in etiquetas_celulas:
            linha_atual.append(cell)
            if len(linha_atual) == colunas:
                grade_matriz.append(linha_atual)
                linha_atual = []
        if linha_atual:
            while len(linha_atual) < colunas:
                linha_atual.append("")
            grade_matriz.append(linha_atual)

        t_grid = Table(grade_matriz, colWidths=[size_pt + 8] * colunas)
        t_grid.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('PADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(t_grid)

        doc.build(story)
        return buffer.getvalue()

    else:
        # Fallback usando PIL caso ReportLab não esteja disponível
        page = Image.new("RGB", (612, 792), "white")
        draw = ImageDraw.Draw(page)
        
        qr_resized = qr_img_pil.resize((int(qr_box_size), int(qr_box_size)), Image.Resampling.LANCZOS)
        
        cols = max(1, int(540 // (size_pt + 10)))
        x_init, y_init = 36, 36
        x, y = x_init, y_init
        
        for i in range(quantidade):
            draw.rectangle([x, y, x + size_pt, y + size_pt], outline="#CBD5E1", width=1)
            page.paste(qr_resized, (int(x + (size_pt - qr_box_size)/2), int(y + 4)))
            draw.text((x + 4, y + qr_box_size + 6), id_amostra[:12], fill="black")
            
            x += size_pt + 10
            if (i + 1) % cols == 0:
                x = x_init
                y += size_pt + 10

        page.save(buffer, format="PDF", resolution=72.0)
        return buffer.getvalue()


def gerar_pdf_etiqueta_solucao(nome_solucao, concentracao, data_preparo, responsavel, validade="-", quantidade=6, mm_size=30, observacoes=""):
    """
    Gera PDF de etiquetas padronizadas para frascos de soluções preparadas na calculadora.
    """
    conteudo_qr = (
        f"🧪 ETIQUETA DE SOLUÇÃO\n"
        f"Nome: {nome_solucao}\n"
        f"Concentração: {concentracao}\n"
        f"Data de Preparo: {data_preparo}\n"
        f"Validade: {validade}\n"
        f"Responsável: {responsavel}\n"
        f"Obs: {observacoes}"
    )
    
    if QRCODE_DISPONIVEL:
        qr_img = qrcode.make(conteudo_qr)
    else:
        qr_img = Image.new("RGB", (100, 100), "white")

    dados_amostra = {
        "nome_amostra": f"{nome_solucao} ({concentracao})",
        "data_obtencao": data_preparo,
        "responsavel": responsavel
    }

    return gerar_pdf_etiquetas(
        qr_img_pil=qr_img,
        quantidade=quantidade,
        mm_size=mm_size,
        id_amostra=f"SOL-{data_preparo.replace('/', '')}",
        dados_amostra=dados_amostra
    )
    
# --- USUÁRIOS E DADOS INICIAIS ---

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
    "orientador_status": "Aprovado",
    "google_calendar_url": ""
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
if "reagentes_solucoes" not in st.session_state:
    st.session_state.reagentes_solucoes = carregar_dados(ARQUIVO_REAGENTES, REAGENTES_SOLUCOES_INICIAIS)
if "grupos_autenticados" not in st.session_state:
    st.session_state.grupos_autenticados = []
if "grupo_ativo_id" not in st.session_state:
    st.session_state.grupo_ativo_id = None
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
                            "orientador_status": "Pendente" if orient_val != "-" else "Aprovado",
                            "google_calendar_url": ""
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

    num_pend_usr = len([u for u in st.session_state.usuarios if u.get("status") == "Pendente"])
    num_pend_perfis = len([u for u in st.session_state.usuarios if u.get("pendente_atualizacao")])
    num_pend_arqs = len([a for a in st.session_state.arquivos_db if a.get("status") == "Pendente"])
    num_pend_pops = len([p for p in st.session_state.pops_db if p.get("status") == "Pendente"])
    num_pend_pastas = len([p for p in st.session_state.pastas_db if p.get("status") == "Pendente"])
    num_pend_orient = len([p for p in st.session_state.integrantes if p.get("OrientadorStatus") == "Pendente"])
    
    num_pend_grupos = len([g for g in st.session_state.grupos_db if g.get("status") == "Pendente"])
    num_pend_membros_grp = sum([len(g.get("membros_pendentes", [])) for g in st.session_state.grupos_db])
    num_pend_itens_grp = sum([len([i for i in g.get("solicitacoes_itens", []) if i.get("status") == "Pendente"]) for g in st.session_state.grupos_db])

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

    st.sidebar.markdown('<div class="sidebar-section">PAINEL PRINCIPAL</div>', unsafe_allow_html=True)
    render_menu_item("🏠 Página Inicial & Avisos", "🏠 Página Inicial & Avisos", notif_avisos)
    render_menu_item("📅 Agenda & Calendário", "📅 Agenda & Calendário", notif_agenda_hoje)

    st.sidebar.markdown('<div class="sidebar-section">GESTÃO DO LABORATÓRIO</div>', unsafe_allow_html=True)
    render_menu_item("👥 Equipe", "👥 Equipe")
    render_menu_item("🎓 Orientados", "🎓 Orientados", num_pend_orient if is_admin else 0)
    render_menu_item("🔬 Grupo de Pesquisa", "🔬 Grupo de Pesquisa", (num_pend_grupos + num_pend_membros_grp + num_pend_itens_grp) if is_admin else num_pend_itens_grp)
    render_menu_item("🕒 Presença no Laboratório", "🕒 Presença no Laboratório")

    st.sidebar.markdown('<div class="sidebar-section">CONHECIMENTO & FERRAMENTAS</div>', unsafe_allow_html=True)
    render_menu_item("📁 Repositório de Arquivos", "📁 Repositório de Arquivos")
    render_menu_item("🏷️ Gerar QR Code de Amostras", "🏷️ Gerar QR Code de Amostras")
    render_menu_item("📝 Criador de POP", "📝 Criador de POP")
    render_menu_item("🧪 Calculadora de Soluções", "🧪 Calculadora de Soluções")

    st.sidebar.markdown('<div class="sidebar-section">CONFIGURAÇÕES</div>', unsafe_allow_html=True)
    if is_admin:
        render_menu_item("🛡️ Administração", "🛡️ Administração", total_notif_admin)
    render_menu_item("👤 Meu perfil", "👤 Meu perfil", notif_meu_perfil)

    st.sidebar.markdown('<div class="sidebar-section">🎨 APARÊNCIA DO APP</div>', unsafe_allow_html=True)
    novo_tema = st.sidebar.selectbox(
        "Cor do Tema",
        options=list(TEMAS_CORES.keys()),
        index=list(TEMAS_CORES.keys()).index(st.session_state.tema_cor),
        key="select_tema_sidebar"
    )

    if novo_tema != st.session_state.tema_cor:
        st.session_state.tema_cor = novo_tema
        st.rerun()

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

    # --- 0. PÁGINA INICIAL & AVISOS ---
    if menu_selecionado == "🏠 Página Inicial & Avisos":
        st.title("🏠 Painel Geral de Pesquisa")
        st.caption(f"Bem-vindo(a) de volta, **{usuario_atual['nome']}**! Acompanhe abaixo o resumo das atividades.")

        st.markdown("<br>", unsafe_allow_html=True)

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
                    st.info("Nenum aviso publicado no mural.")

        with col_right:
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
                        bg_style = f"background:{cor_bg_light}; border:1px solid {cor_border};" if dia == datetime.now().day and mes_sel == mes_atual and ano_sel == ano_atual else "background:white; border:1px solid #E2E8F0;"
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
                                <h4 style="margin: 0; color: #0F172A;">{ev.get('titulo', '-')}</h4>
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
                        st.markdown(f"<a href='{lattes_str}' target='_blank' style='color:{cor_primaria}; font-weight:600; text-decoration:none;'>Abrir Lattes ↗</a>", unsafe_allow_html=True)
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
                                <span style="color:{cor_primaria}; font-weight:bold;">└─ 🎓 {al['Nome']}</span> 
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

    # --- 2.1 GRUPOS DE PESQUISA ---
    elif menu_selecionado == "🔬 Grupo de Pesquisa":
        st.title("🔬 Área de Grupos de Pesquisa")
        st.caption("Acesso por cards visuais interativos. Qualquer pesquisador pode ser designado Líder ou Colíder pela equipe. Líderes e Colíderes possuem autonomia de gestão.")

        aba_grp_view, aba_grp_solicitar = st.tabs([
            "📊 Meus Grupos de Pesquisa",
            "➕ Solicitar Criação / Entrada em Grupo"
        ])

        lista_integrantes_nomes = [p["Nome"] for p in st.session_state.integrantes]

        with aba_grp_view:
            grupos_aprovados = [g for g in st.session_state.grupos_db if g.get("status") == "Aprovado"]

            if st.session_state.grupo_ativo_id is None:
                st.subheader("📌 Selecione um Grupo de Pesquisa para Acessar")
                st.caption("Clique no grupo desejado para abrir o painel de autenticação e conteúdo.")

                if grupos_aprovados:
                    cols_grp = st.columns(2)
                    for idx, g in enumerate(grupos_aprovados):
                        with cols_grp[idx % 2]:
                            is_mb = usuario_atual["nome"] in g.get("membros", [])
                            is_lid = (usuario_atual["nome"] == g.get("lider")) or (usuario_atual["nome"] == g.get("colider")) or is_admin
                            autenticado = (g["id"] in st.session_state.grupos_autenticados) or is_admin

                            badge_perm = "👑 Líder/Colíder" if is_lid else ("👤 Membro" if is_mb else "🔒 Não participante")
                            badge_auth = "🔓 Acesso Liberado" if autenticado else "🔑 Senha Necessária"

                            st.markdown(
                                f"""
                                <div class="grp-card">
                                    <div style="display:flex; justify-content:space-between; align-items:center;">
                                        <h3 style="margin:0; color:#0F172A; font-size:1.15rem;">🔬 {g.get('nome', 'Grupo')}</h3>
                                        <span class="badge-ativo" style="font-size:0.7rem;">{badge_auth}</span>
                                    </div>
                                    <p style="color:#475569; font-size:0.85rem; margin:8px 0; min-height:40px;">{g.get('descricao','')[:120]}...</p>
                                    <div style="font-size:0.78rem; color:#64748B; margin-bottom:10px;">
                                        👨‍🔬 <b>Líder:</b> {g.get('lider','-')}<br/>
                                        🤝 <b>Colíder:</b> {g.get('colider','-')}<br/>
                                        👥 <b>Membros:</b> {len(g.get('membros',[]))} | <b>Vínculo:</b> {badge_perm}
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                            if st.button(f"🚀 Abrir Painel do Grupo '{g.get('nome', '')}'", key=f"btn_open_grp_{g.get('id', idx)}", use_container_width=True, type="primary" if is_mb else "secondary"):
                                st.session_state.grupo_ativo_id = g["id"]
                                st.rerun()
                else:
                    st.info("Nenhum grupo de pesquisa aprovado cadastrado no momento.")
            else:
                grupo_ativo = next((g for g in grupos_aprovados if g["id"] == st.session_state.grupo_ativo_id), None)

                if not grupo_ativo:
                    st.session_state.grupo_ativo_id = None
                    st.rerun()

                c_back1, c_back2 = st.columns([3, 1])
                with c_back1:
                    st.subheader(f"🔬 Grupo: {grupo_ativo.get('nome', 'Sem nome')}")
                with c_back2:
                    if st.button("⬅️ Voltar para Lista de Grupos", use_container_width=True):
                        st.session_state.grupo_ativo_id = None
                        st.rerun()

                grp_id = grupo_ativo["id"]
                autenticado = (grp_id in st.session_state.grupos_autenticados) or is_admin

                if not autenticado:
                    with st.container(border=True):
                        st.warning(f"🔒 O Grupo **{grupo_ativo.get('nome', '')}** exige senha de acesso.")
                        with st.form(f"form_auth_grp_{grp_id}"):
                            senha_grp_input = st.text_input("Senha do Grupo", type="password")
                            btn_entrar_grp = st.form_submit_button("🔓 Desbloquear Acesso", type="primary")

                            if btn_entrar_grp:
                                if senha_grp_input == grupo_ativo.get("senha", ""):
                                    st.session_state.grupos_autenticados.append(grp_id)
                                    st.success("Acesso liberado!")
                                    st.rerun()
                                else:
                                    st.error("Senha incorreta.")
                else:
                    is_lider_ou_colider = is_admin or (usuario_atual["nome"] == grupo_ativo.get("lider")) or (usuario_atual["nome"] == grupo_ativo.get("colider"))

                    st.markdown(
                        f"""
                        <div class="css-card" style="border-left: 5px solid {cor_primaria};">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <h3 style="margin:0; color:#0F172A;">{grupo_ativo.get('nome', '')}</h3>
                                <span class="badge-ativo">{'👑 Painel do Líder/Colíder' if is_lider_ou_colider else '👤 Área do Membro'}</span>
                            </div>
                            <p style="color:#475569; margin: 6px 0; font-size:0.88rem;">{grupo_ativo.get('descricao', '')}</p>
                            <div style="font-size:0.82rem; color:#64748B;">
                                👨‍🔬 <b>Líder:</b> {grupo_ativo.get('lider', 'N/A')} | 🤝 <b>Colíder:</b> {grupo_ativo.get('colider', 'N/A')} | 👥 <b>Membros Totais:</b> {len(grupo_ativo.get('membros', []))}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    if is_lider_ou_colider:
                        with st.expander("⚙️ Gestão de Configurações, Líder e Colíder do Grupo"):
                            with st.form(f"form_edit_lideres_{grp_id}"):
                                ed_nome_g = st.text_input("Nome do Grupo", value=grupo_ativo.get("nome", ""))
                                ed_desc_g = st.text_area("Descrição do Grupo", value=grupo_ativo.get("descricao", ""))
                                
                                c_lid1, c_lid2 = st.columns(2)
                                idx_l = lista_integrantes_nomes.index(grupo_ativo.get("lider")) if grupo_ativo.get("lider") in lista_integrantes_nomes else 0
                                idx_c = lista_integrantes_nomes.index(grupo_ativo.get("colider")) if grupo_ativo.get("colider") in lista_integrantes_nomes else 0

                                with c_lid1:
                                    ed_lider_g = st.selectbox("Líder do Grupo (Selecionado da Equipe)", lista_integrantes_nomes, index=idx_l)
                                with c_lid2:
                                    ed_colider_g = st.selectbox("Colíder do Grupo (Selecionado da Equipe)", ["-"] + lista_integrantes_nomes, index=idx_c+1 if grupo_ativo.get("colider") in lista_integrantes_nomes else 0)

                                ed_senha_g = st.text_input("Senha de Acesso do Grupo", value=grupo_ativo.get("senha", "123"))
                                btn_salv_grp_edit = st.form_submit_button("💾 Salvar Configurações da Liderança", type="primary")

                                if btn_salv_grp_edit:
                                    grupo_ativo["nome"] = ed_nome_g.strip()
                                    grupo_ativo["descricao"] = ed_desc_g.strip()
                                    grupo_ativo["lider"] = ed_lider_g
                                    grupo_ativo["colider"] = "-" if ed_colider_g == "-" else ed_colider_g
                                    grupo_ativo["senha"] = ed_senha_g.strip()
                                    salvar_dados(ARQUIVO_GRUPOS, st.session_state.grupos_db)
                                    st.success("Configurações do grupo atualizadas com sucesso!")
                                    st.rerun()

                    sub_tab1, sub_tab2, sub_tab3, sub_tab4, sub_tab5 = st.tabs([
                        "📦 Solicitação de Itens",
                        "📅 Calendário do Grupo",
                        "📝 Mural & Anotações",
                        "👥 Membros do Grupo",
                        "📁 Documentos do Grupo"
                    ])

                    with sub_tab1:
                        st.subheader("📦 Solicitação de Itens e Materiais de Laboratório")
                        st.caption("Requisição de reagentes, vidrarias, papéis de filtro e insumos para aprovação do Líder/Colíder.")

                        st_sub1, st_sub2 = st.tabs(["📋 Fila de Solicitações", "➕ Criar Nova Requisição"])

                        with st_sub1:
                            solicitacoes = grupo_ativo.get("solicitacoes_itens", [])
                            if solicitacoes:
                                for idx_sol, sol in enumerate(solicitacoes):
                                    st_cor = "#059669" if sol.get("status") == "Aprovado" else ("#DC2626" if sol.get("status") == "Recusado" else "#D97706")
                                    badge_class = "badge-urgente" if sol.get("urgente") else "badge-ativo"
                                    urg_txt = "🚨 URGENTE" if sol.get("urgente") else "📦 PADRÃO"

                                    st.markdown(
                                        f"""
                                        <div class="event-card" style="border-left: 5px solid {st_cor};">
                                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                                <h4 style="margin:0; color:#0F172A;">{sol.get('item', 'Item sem nome')}</h4>
                                                <div>
                                                    <span class="{badge_class}">{urg_txt}</span>
                                                    <span style="font-size:0.78rem; font-weight:bold; color:{st_cor}; margin-left:6px;">[{sol.get('status','Pendente')}]</span>
                                                </div>
                                            </div>
                                            <div style="font-size:0.85rem; color:#475569; margin-top:6px;">
                                                🏷️ <b>Categoria:</b> {sol.get('categoria_item','Reagentes')} | 📦 <b>Quantidade:</b> {sol.get('quantidade', '-')}
                                            </div>
                                            <div style="font-size:0.82rem; color:#334155; margin-top:4px;">
                                                👤 <b>Solicitante:</b> {sol.get('solicitante', '-')} | 📅 <b>Data:</b> {sol.get('data_solicitacao', '-')}
                                            </div>
                                            <div style="font-size:0.82rem; color:#64748B; margin-top:4px;">
                                                ℹ️ <b>Razão da Urgência / Justificativa:</b> {sol.get('razao_urgencia','-')}
                                            </div>
                                            <div style="font-size:0.82rem; color:#64748B; margin-top:2px;">
                                                🔬 <b>Especificações Técnicas:</b> {sol.get('especificacoes','Não há especificação')}
                                            </div>
                                        </div>
                                        """,
                                        unsafe_allow_html=True
                                    )

                                    c_sol_btn1, c_sol_btn2, c_sol_btn3 = st.columns([1.5, 1, 1])

                                    with c_sol_btn1:
                                        pdf_sol_bytes = gerar_pdf_solicitacao_item(sol, grupo_ativo.get('nome', 'Grupo'), grupo_ativo.get('lider', 'Líder'), grupo_ativo.get('colider', '-'))
                                        st.download_button(
                                            "📄 Baixar PDF do Pedido",
                                            data=pdf_sol_bytes,
                                            file_name=f"Requisicao_{sol.get('id', idx_sol)}.pdf",
                                            mime="application/pdf",
                                            key=f"dl_sol_pdf_{grp_id}_{idx_sol}"
                                        )

                                    if is_lider_ou_colider and sol.get("status") == "Pendente":
                                        with c_sol_btn2:
                                            if st.button("✅ Aprovar", key=f"ap_sol_{grp_id}_{idx_sol}", type="primary"):
                                                sol["status"] = "Aprovado"
                                                sol["aprovado_por"] = usuario_atual["nome"]
                                                salvar_dados(ARQUIVO_GRUPOS, st.session_state.grupos_db)
                                                st.success("Pedido aprovado!")
                                                st.rerun()
                                        with c_sol_btn3:
                                            if st.button("❌ Recusar", key=f"rec_sol_{grp_id}_{idx_sol}"):
                                                sol["status"] = "Recusado"
                                                sol["aprovado_por"] = usuario_atual["nome"]
                                                salvar_dados(ARQUIVO_GRUPOS, st.session_state.grupos_db)
                                                st.warning("Pedido recusado.")
                                                st.rerun()

                                    st.markdown("---")
                            else:
                                st.info("Nenhuma solicitação de itens para este grupo de pesquisa.")

                        with st_sub2:
                            with st.form(f"form_nova_solicitacao_{grp_id}"):
                                item_nome = st.text_input("Item / Material Solicitado (ex: Álcool Etílico, Frasco Erlenmeyer 250mL, Papel Filtro 125mm) *")
                                cat_item = st.selectbox("Categoria do Item", ["Reagentes", "Vidrarias", "Papel de Filtro", "Consumíveis de Bancada", "Equipamentos", "Outros"])
                                qtd_item = st.text_input("Quantidade Desejada (ex: 2 Frascos de 1L, 5 caixas) *")

                                c_urg1, c_urg2 = st.columns([1, 2])
                                with c_urg1:
                                    is_urgente = st.checkbox("🚨 É URGENTE?")
                                with c_urg2:
                                    razao_urg = st.text_input("Razão da Urgência / Justificativa do Pedido *")

                                tem_espec = st.radio("Há especificações técnicas?", ["Não há especificação", "Sim, especificar abaixo"], horizontal=True)
                                txt_espec = st.text_area("Especificações Técnicas (Grau de pureza, marca, porosidade, etc.)", value="Grau P.A." if tem_espec != "Não há especificação" else "Não se aplica")

                                st.markdown("##### 👤 Identificação do Solicitante")
                                opt_solicitantes = lista_integrantes_nomes + ["✍️ Outro (Digitar manualmente)"]
                                idx_sol_def = lista_integrantes_nomes.index(usuario_atual["nome"]) if usuario_atual["nome"] in lista_integrantes_nomes else 0
                                sel_sol_tipo = st.selectbox("Selecione o Solicitante Cadastrado", opt_solicitantes, index=idx_sol_def)

                                if sel_sol_tipo == "✍️ Outro (Digitar manualmente)":
                                    nome_solicitante_final = st.text_input("Digite o Nome do Solicitante Manualmente *")
                                else:
                                    nome_solicitante_final = sel_sol_tipo

                                btn_enviar_sol = st.form_submit_button("🚀 Enviar Solicitação para Aprovação da Liderança", type="primary")

                                if btn_enviar_sol:
                                    if item_nome.strip() and qtd_item.strip() and razao_urg.strip() and nome_solicitante_final.strip():
                                        if "solicitacoes_itens" not in grupo_ativo:
                                            grupo_ativo["solicitacoes_itens"] = []

                                        novo_id_sol = max([s.get("id", 0) for s in grupo_ativo["solicitacoes_itens"]], default=0) + 1
                                        grupo_ativo["solicitacoes_itens"].append({
                                            "id": novo_id_sol,
                                            "item": item_nome.strip(),
                                            "categoria_item": cat_item,
                                            "quantidade": qtd_item.strip(),
                                            "urgente": is_urgente,
                                            "razao_urgencia": razao_urg.strip(),
                                            "especificacoes": txt_espec.strip() if tem_espec != "Não há especificação" else "Não se aplica",
                                            "solicitante": nome_solicitante_final.strip(),
                                            "data_solicitacao": datetime.now().strftime("%d/%m/%Y"),
                                            "status": "Pendente",
                                            "aprovado_por": "-"
                                        })
                                        salvar_dados(ARQUIVO_GRUPOS, st.session_state.grupos_db)
                                        st.success("✅ Solicitação cadastrada e enviada para o Líder/Colíder!")
                                        st.rerun()
                                    else:
                                        st.error("Preencha todos os campos obrigatórios (*).")

                    with sub_tab2:
                        st.subheader("📅 Calendário Exclusivo do Grupo")
                        c_ag1, c_ag2 = st.columns([1.5, 1])

                        with c_ag1:
                            st.markdown("##### 📋 Compromissos Agendados")
                            agenda_grp = grupo_ativo.get("agenda", [])
                            if agenda_grp:
                                for idx_a, ev in enumerate(agenda_grp):
                                    st.markdown(
                                        f"""
                                        <div class="event-card" style="border-left: 4px solid #059669;">
                                            <div style="font-weight:bold; color:#0F172A;">{ev.get('titulo', '-')}</div>
                                            <div style="font-size:0.82rem; color:#475569;">
                                                📅 <b>{ev.get('data', '-')}</b> das 🕒 <b>{ev.get('hora_inicio')} às {ev.get('hora_fim')}</b>
                                            </div>
                                            <div style="font-size:0.8rem; color:#64748B; margin-top:4px;">{ev.get('descricao', '')}</div>
                                            <div style="font-size:0.75rem; color:#94A3B8; margin-top:2px;">Criado por: {ev.get('autor','-')}</div>
                                        </div>
                                        """,
                                        unsafe_allow_html=True
                                    )
                                    if is_lider_ou_colider or ev.get("autor") == usuario_atual["nome"]:
                                        if st.button("🗑️ Remover Evento", key=f"del_ev_grp_{idx_a}"):
                                            grupo_ativo["agenda"].pop(idx_a)
                                            salvar_dados(ARQUIVO_GRUPOS, st.session_state.grupos_db)
                                            st.warning("Evento removido.")
                                            st.rerun()
                            else:
                                st.info("Nenhum evento agendado neste grupo.")

                        with c_ag2:
                            st.markdown("##### ➕ Novo Evento do Grupo")
                            with st.form(f"form_evento_grp_{grp_id}"):
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
                                    st.success("Evento adicionado!")
                                    st.rerun()

                    with sub_tab3:
                        st.subheader("📝 Mural & Projetos Internos do Grupo")
                        mural_atual = grupo_ativo.get("mural", "Nenhuma anotação postada ainda.")
                        st.markdown(f"<div class='css-card'>{mural_atual}</div>", unsafe_allow_html=True)

                        if is_lider_ou_colider:
                            with st.expander("✏️ Editar Mural e Anotações do Grupo"):
                                novo_mural = st.text_area("Escreva as anotações do grupo", value=mural_atual, height=150)
                                if st.button("💾 Atualizar Mural"):
                                    grupo_ativo["mural"] = novo_mural
                                    salvar_dados(ARQUIVO_GRUPOS, st.session_state.grupos_db)
                                    st.success("Mural atualizado!")
                                    st.rerun()

                    with sub_tab4:
                        st.subheader("👥 Integrantes do Grupo")
                        for mbr in grupo_ativo.get("membros", []):
                            papel = ""
                            if mbr == grupo_ativo.get("lider"):
                                papel = "👑 (Líder)"
                            elif mbr == grupo_ativo.get("colider"):
                                papel = "🤝 (Colíder)"
                            st.markdown(f"- 👨‍🔬 **{mbr}** {papel}")

                    with sub_tab5:
                        st.subheader("📁 Documentos Exclusivos do Grupo")
                        st.caption("Arquivos de pesquisa e relatórios compartilhados somente entre os integrantes deste grupo.")

                        arqs_grupo = grupo_ativo.get("documentos", [])
                        if arqs_grupo:
                            for idx_doc, doc_g in enumerate(arqs_grupo):
                                st.markdown(
                                    f"""
                                    <div class="css-card">
                                        <h4 style="margin:0; color:{cor_primaria};">📄 {doc_g.get('titulo', '-')}</h4>
                                        <p style="margin:4px 0; color:#555; font-size:0.85rem;"><b>Enviado por:</b> {doc_g.get('autor','-')} em {doc_g.get('data','-')}</p>
                                        <p style="margin:4px 0; color:#666; font-size:0.85rem;"><i>{doc_g.get('descricao','')}</i></p>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                                c_doc1, c_doc2 = st.columns([3, 1])
                                with c_doc1:
                                    if doc_g.get("b64"):
                                        bytes_g = base64.b64decode(doc_g["b64"])
                                        st.download_button(
                                            f"⬇️ Baixar {doc_g.get('nome_original', 'arquivo')}",
                                            data=bytes_g,
                                            file_name=doc_g.get('nome_original', 'arquivo.pdf'),
                                            mime=doc_g.get('mime_type', 'application/octet-stream'),
                                            key=f"dl_grp_doc_{grp_id}_{idx_doc}"
                                        )
                                with c_doc2:
                                    if is_lider_ou_colider or doc_g.get("autor") == usuario_atual["nome"]:
                                        if st.button("🗑️ Excluir", key=f"del_grp_doc_{grp_id}_{idx_doc}"):
                                            grupo_ativo["documentos"].pop(idx_doc)
                                            salvar_dados(ARQUIVO_GRUPOS, st.session_state.grupos_db)
                                            st.warning("Documento excluído.")
                                            st.rerun()
                        else:
                            st.info("Nenhum documento anexado a este grupo de pesquisa.")

                        with st.expander("📤 Enviar Documento para o Grupo"):
                            with st.form(f"form_up_doc_grp_{grp_id}"):
                                tit_doc_g = st.text_input("Título do Documento *")
                                desc_doc_g = st.text_area("Descrição / Observações")
                                file_doc_g = st.file_uploader("Selecione o Arquivo *")
                                btn_up_doc_g = st.form_submit_button("📤 Fazer Upload para o Grupo", type="primary")

                                if btn_up_doc_g:
                                    if tit_doc_g.strip() and file_doc_g:
                                        b64_file = base64.b64encode(file_doc_g.getvalue()).decode("utf-8")
                                        if "documentos" not in grupo_ativo:
                                            grupo_ativo["documentos"] = []

                                        grupo_ativo["documentos"].append({
                                            "id": len(grupo_ativo["documentos"]) + 1,
                                            "titulo": tit_doc_g.strip(),
                                            "descricao": desc_doc_g.strip(),
                                            "nome_original": file_doc_g.name,
                                            "mime_type": file_doc_g.type,
                                            "b64": b64_file,
                                            "autor": usuario_atual["nome"],
                                            "data": datetime.now().strftime("%d/%m/%Y")
                                        })
                                        salvar_dados(ARQUIVO_GRUPOS, st.session_state.grupos_db)
                                        st.success("Documento enviado ao repositório do grupo!")
                                        st.rerun()
                                    else:
                                        st.error("Informe o título e selecione um arquivo.")

        with aba_grp_solicitar:
            c_sol1, c_sol2 = st.columns(2)
            with c_sol1:
                with st.container(border=True):
                    st.subheader("➕ Solicitar Criação de Novo Grupo")
                    with st.form("form_novo_grupo_pesq"):
                        nome_novo_grp = st.text_input("Nome do Grupo de Pesquisa *")
                        desc_novo_grp = st.text_area("Descrição / Objetivos do Grupo *", height=100)
                        
                        idx_lider_init = lista_integrantes_nomes.index(usuario_atual["nome"]) if usuario_atual["nome"] in lista_integrantes_nomes else 0
                        lider_novo_grp = st.selectbox("Líder Solicitado", lista_integrantes_nomes, index=idx_lider_init)
                        colider_novo_grp = st.selectbox("Colíder Solicitado (Opcional)", ["-"] + lista_integrantes_nomes)
                        senha_novo_grp = st.text_input("Definir Senha de Acesso ao Grupo *", type="password", value="123")
                        btn_sol_grp = st.form_submit_button("🚀 Enviar Solicitação para o Admin", type="primary")

                        if btn_sol_grp:
                            if nome_novo_grp.strip() and desc_novo_grp.strip() and senha_novo_grp.strip():
                                novo_id_g = max([g.get("id", 0) for g in st.session_state.grupos_db], default=0) + 1
                                st.session_state.grupos_db.append({
                                    "id": novo_id_g,
                                    "nome": nome_novo_grp.strip(),
                                    "descricao": desc_novo_grp.strip(),
                                    "lider": lider_novo_grp,
                                    "colider": "-" if colider_novo_grp == "-" else colider_novo_grp,
                                    "senha": senha_novo_grp.strip(),
                                    "membros": [lider_novo_grp] if colider_novo_grp == "-" else list(set([lider_novo_grp, colider_novo_grp])),
                                    "status": "Pendente",
                                    "solicitante": usuario_atual["nome"],
                                    "membros_pendentes": [],
                                    "agenda": [],
                                    "solicitacoes_itens": [],
                                    "documentos": [],
                                    "mural": "Mural inicial do grupo."
                                })
                                salvar_dados(ARQUIVO_GRUPOS, st.session_state.grupos_db)
                                st.success("✅ Solicitação enviada para aprovação do Administrador!")
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
                        dict_g_outros = {g.get("nome", "Grupo"): g for g in grupos_aprovados_outros}
                        grp_entrar_nome = st.selectbox("Selecione o Grupo para Ingressar", list(dict_g_outros.keys()))

                        if st.button("📩 Solicitar Vínculo ao Grupo"):
                            grp_alvo = dict_g_outros[grp_entrar_nome]
                            if "membros_pendentes" not in grp_alvo:
                                grp_alvo["membros_pendentes"] = []

                            if usuario_atual["nome"] not in grp_alvo["membros_pendentes"]:
                                grp_alvo["membros_pendentes"].append(usuario_atual["nome"])
                                salvar_dados(ARQUIVO_GRUPOS, st.session_state.grupos_db)
                                st.success(f"Solicitação enviada aos Líderes do grupo '{grp_entrar_nome}'!")
                            else:
                                st.info("Você já possui uma solicitação pendente para este grupo.")
                    else:
                        st.info("Não há outros grupos disponíveis para solicitação.")

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
                    nome_p = pst.get("nome", "Pasta")
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
                                    st.session_state.pastas_db = [p for p in st.session_state.pastas_db if p.get("nome") != nome_p]
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
                                    <h4 style="margin:0; color:{cor_primaria};">📄 {doc.get('titulo', '-')}</h4>
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
                                            key=f"dl_{doc.get('id')}",
                                        )
                                    except Exception as e:
                                        st.error(f"Erro ao processar o arquivo: {e}")
                                else:
                                    st.warning("⚠️ Conteúdo do arquivo indisponível para download.")
                            with col_d2:
                                if is_admin or doc.get("autor") == usuario_atual["nome"]:
                                    if st.button("🗑️ Excluir", key=f"del_doc_{doc.get('id')}"):
                                        st.session_state.arquivos_db = [a for a in st.session_state.arquivos_db if a.get("id") != doc.get("id")]
                                        salvar_dados(ARQUIVO_ARQUIVOS, st.session_state.arquivos_db)
                                        st.warning(f"Arquivo '{doc.get('titulo')}' excluído.")
                                        st.rerun()
                            st.markdown("---")
                else:
                    st.info(f"Nenhum arquivo encontrado na pasta '{nome_pasta_atual}'.")

        with aba_upload:
            st.subheader("Enviar Documento")
            lista_nomes_pastas = [p.get("nome", "Geral") for p in pastas_aprovadas]
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

                if QRCODE_DISPONIVEL:
                    img = qrcode.make(conteudo_qr)
                    buffer = BytesIO()
                    img.save(buffer, format="PNG")
                    img_bytes = buffer.getvalue()
                    st.image(img_bytes, caption=f"Pré-visualização: {id_amostra}", width=220)
                    st.download_button("🖼️ Baixar QR Code (PNG)", img_bytes, f"QR_{id_amostra}.png", "image/png")
                    dados_amostra_dict = {
                        "nome_amostra": nome_amostra,
                        "data_obtencao": data_obtencao.strftime('%d/%m/%Y'),
                        "responsavel": responsavel_nome,
                        "telefone": responsavel_tel,
                        "email": responsavel_email,
                        "localizacao": localizacao,
                        "descricao": descricao,
                    }
                    pdf_etiquetas = gerar_pdf_etiquetas(img, qtd_etiquetas, tamanho_mm, id_amostra=id_amostra, dados_amostra=dados_amostra_dict)
                    st.download_button(f"📄 Baixar PDF ({qtd_etiquetas}x Etiquetas)", pdf_etiquetas, f"Etiquetas_{id_amostra}.pdf", "application/pdf")
                else:
                    st.warning("Biblioteca 'qrcode' não instalada para renderizar o código QR.")
                    
    # --- 6. CRIADOR DE POP ---
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
                                    <h3 style="margin: 0; color: #0F172A; font-size: 1.1rem;">📝 {pop.get('titulo', '-')}</h3>
                                    <span style="background-color: {cor_bg_light}; color: {cor_primaria}; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 0.82rem;">
                                        {pop.get('codigo', 'POP')} | v{pop.get('versao', 1)}
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
                                file_name=f"{pop.get('codigo', 'POP')}.pdf",
                                mime="application/pdf",
                                key=f"dl_pop_{idx}",
                            )

                        with c_pop2:
                            if st.button("📂 Publicar no Repositório", key=f"trans_pop_{idx}"):
                                b64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
                                novo_id = max([a.get("id", 0) for a in st.session_state.arquivos_db], default=0) + 1
                                st.session_state.arquivos_db.append({
                                    "id": novo_id,
                                    "titulo": f"{pop.get('codigo', 'POP')} - {pop.get('titulo', 'Documento')}",
                                    "pasta": "POPs e Protocolos",
                                    "descricao": f"Procedimento Operacional Padrão (Versão {pop.get('versao', 1)}). Objetivo: {pop.get('objetivo', '')}",
                                    "nome_original": f"{pop.get('codigo', 'POP')}.pdf",
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
                                    st.warning(f"POP '{pop.get('codigo')}' excluído.")
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
                    pops_existentes = [p.get("titulo", "") for p in st.session_state.pops_db if p.get("titulo")]
                    if pops_existentes:
                        pop_sel_tit = st.selectbox("Selecione o POP", pops_existentes)
                        pop_existente = next((p for p in st.session_state.pops_db if p.get("titulo") == pop_sel_tit), None)
                        if pop_existente:
                            tit_selecionado = pop_existente.get("titulo", "")
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

            with col_prev:
                st.markdown("### 👁️ Pré-visualização em Tempo Real")
                st.markdown(
                    f"""
                    <div class="pop-preview-card" style="border-left: 5px solid {cor_primaria}; background: #FFFFFF;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <h3 style="margin: 0; color: #0F172A; font-size: 1.05rem;">📝 {tit_selecionado if tit_selecionado else 'Título do POP'}</h3>
                            <span style="background-color: {cor_bg_light}; color: {cor_primaria}; padding: 4px 8px; border-radius: 6px; font-weight: bold; font-size: 0.8rem;">
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

    # --- 6.1 CALCULADORA DE PREPARO DE SOLUÇÕES DE USO GERAL ---
    elif menu_selecionado == "🧪 Calculadora de Soluções":
        st.title("🧪 Calculadora de Preparo de Soluções de Uso Geral")
        st.caption("Cálculo rápido para pesagem e diluição de reagentes no laboratório com banco de compostos e referências técnicas.")

        aba_calc_molar, aba_calc_diluicao, aba_reagentes_ref = st.tabs([
            "🧮 Concentração Molar / Pesagem",
            "🧪 Diluição (C1·V1 = C2·V2)",
            "📚 Banco de Reagentes & Referências"
        ])

        with aba_calc_molar:
            st.subheader("🧮 Cálculo de Massa / Volume para Solução Molar ou % (m/v)")
            
            reagentes_lista = st.session_state.reagentes_solucoes
            nomes_reagentes = [r.get("nome", "Reagente") for r in reagentes_lista] + ["✍️ Outro (Digitar Manualmente)"]
            
            sel_r = st.selectbox("Selecione o Reagente / Composto", nomes_reagentes)
            if sel_r == "✍️ Outro (Digitar Manualmente)":
                nome_reagente_custom = st.text_input("Nome do Reagente / Composto Personalizado *", "Solução Especial")
            else:
                nome_reagente_custom = sel_r

            reagente_obj = next((r for r in reagentes_lista if r.get("nome") == sel_r), None)

            c_inp1, c_inp2, c_inp3 = st.columns(3)
            with c_inp1:
                val_mm = reagente_obj.get("massa_molar", 40.0) if reagente_obj else 40.0
                massa_molar_in = st.number_input("Massa Molar (g/mol) *", min_value=0.1, value=float(val_mm), step=0.1)

            with c_inp2:
                val_pur = reagente_obj.get("pureza_padrao", 100.0) if reagente_obj else 100.0
                pureza_in = st.number_input("Pureza do Reagente (%) *", min_value=1.0, max_value=100.0, value=float(val_pur), step=0.5)

            with c_inp3:
                val_dens = reagente_obj.get("densidade_g_ml") if (reagente_obj and reagente_obj.get("densidade_g_ml")) else 1.0
                densidade_in = st.number_input("Densidade (g/mL) [Reagentes Líquidos]", min_value=0.1, value=float(val_dens), step=0.01)

            st.markdown("---")
            c_calc1, c_calc2 = st.columns(2)
            with c_calc1:
                molaridade_desejada = st.number_input("Concentração Molar Desejada (M ou mol/L) *", min_value=0.001, value=0.1, step=0.05, format="%.3f")
            with c_calc2:
                volume_desejado_ml = st.number_input("Volume Final Desejado (mL) *", min_value=1.0, value=500.0, step=50.0)

            vol_litros = volume_desejado_ml / 1000.0
            massa_teorica = molaridade_desejada * massa_molar_in * vol_litros
            massa_real_g = massa_teorica / (pureza_in / 100.0)
            vol_liquido_ml = massa_real_g / densidade_in if densidade_in else None

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(
                f"""
                <div class="pop-preview-card" style="border-left: 5px solid {cor_primaria};">
                    <h3 style="margin:0; color:#0F172A;">📊 Resultado do Preparo:</h3>
                    <hr style="margin:8px 0; border:none; border-top:1px solid #CBD5E1;"/>
                    <p style="font-size:1.1rem; color:#0E7490; margin:4px 0;">
                        ⚖️ <b>Massa a ser pesada:</b> <span style="font-size:1.4rem; font-weight:800; color:#0F172A;">{massa_real_g:.4f} g</span>
                    </p>
                    {f'<p style="font-size:1.0rem; color:#059669; margin:4px 0;">🧪 <b>Se reagente líquido, pipetar:</b> <span style="font-size:1.3rem; font-weight:800; color:#0F172A;">{vol_liquido_ml:.3f} mL</span></p>' if (reagente_obj and reagente_obj.get("estado") == "Líquido") else ''}
                    <div style="font-size:0.85rem; color:#475569; margin-top:8px;">
                        • <b>Massa Teórica (100% puro):</b> {massa_teorica:.4f} g<br/>
                        • <b>Volume de Solvente:</b> Transferir a quantidade para balão volumétrico de <b>{volume_desejado_ml:.0f} mL</b> e avolmar com água destilada/deionizada.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown("##### 🏷️ Gerar Etiquetas da Solução Preparada")
            c_sol_et1, c_sol_et2 = st.columns(2)
            with c_sol_et1:
                qtd_et_sol = st.number_input("Quantidade de Etiquetas", min_value=1, max_value=50, value=6, key="qtd_et_molar")
            with c_sol_et2:
                tam_et_sol = st.selectbox("Tamanho do Frasco", list(DESTINOS_ETIQUETAS.keys()), index=3, key="tam_et_molar")
            
            pdf_sol_bytes = gerar_pdf_etiqueta_solucao(
                nome_solucao=sel_r if sel_r != "✍️ Outro (Digitar Manualmente)" else "Solução Personalizada",
                concentracao=f"{molaridade_desejada:.3f} M",
                data_preparo=datetime.now().strftime("%d/%m/%Y"),
                responsavel=usuario_atual["nome"],
                quantidade=qtd_et_sol,
                mm_size=DESTINOS_ETIQUETAS[tam_et_sol]
            )
            
            st.download_button(
                label="📄 Baixar PDF de Etiquetas da Solução",
                data=pdf_sol_bytes,
                file_name=f"Etiquetas_Solucao_{sel_r}.pdf",
                mime="application/pdf",
                key="btn_dl_etiqueta_molar"
            )

        with aba_calc_diluicao:
            st.subheader("🧪 Calculadora de Diluição de Soluções Concentradas (C₁ · V₁ = C₂ · V₂)")
            
            c_d1, c_d2 = st.columns(2)
            with c_d1:
                st.markdown("##### 📌 Solução Estoque (Concentrada)")
                c1_in = st.number_input("Concentração Estoque (C₁) *", min_value=0.001, value=1.0, step=0.1)

            with c_d2:
                st.markdown("##### 🎯 Solução Desejada (Diluída)")
                c2_in = st.number_input("Concentração Final (C₂) *", min_value=0.0001, value=0.1, step=0.01)
                v2_in = st.number_input("Volume Final Desejado (V₂ em mL) *", min_value=1.0, value=250.0, step=10.0)

            if c1_in <= c2_in:
                st.error("⚠️ A concentração inicial (C₁) deve ser MAIOR que a concentração desejada (C₂).")
            else:
                v1_ml = (c2_in * v2_in) / c1_in
                v_solvente = v2_in - v1_ml

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(
                    f"""
                    <div class="pop-preview-card" style="border-left: 5px solid #059669;">
                        <h3 style="margin:0; color:#0F172A;">📋 Instrução de Diluição:</h3>
                        <hr style="margin:8px 0; border:none; border-top:1px solid #CBD5E1;"/>
                        <p style="font-size:1.05rem; color:#059669; margin:4px 0;">
                            🧪 <b>Volume da Solução Estoque (V₁):</b> <span style="font-size:1.4rem; font-weight:800; color:#0F172A;">{v1_ml:.2f} mL</span>
                        </p>
                        <p style="font-size:1.05rem; color:#0E7490; margin:4px 0;">
                            💧 <b>Volume de Solvente a Adicionar:</b> <span style="font-size:1.4rem; font-weight:800; color:#0F172A;">{v_solvente:.2f} mL</span>
                        </p>
                        <div style="font-size:0.85rem; color:#475569; margin-top:8px;">
                            <b>Procedimento:</b> Pipetar {v1_ml:.2f} mL da solução estoque {c1_in}M, transferir para balão de {v2_in:.0f} mL e completar o volume com solvente até o traço de aferição.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        with aba_reagentes_ref:
            st.subheader("📚 Banco de Reagentes & Referências Técnicas Cadastradas")
            
            df_reag = pd.DataFrame(st.session_state.reagentes_solucoes)
            st.dataframe(df_reag, use_container_width=True)

            with st.expander("➕ Cadastrar Novo Reagente / Composto no Banco"):
                with st.form("form_add_reagente"):
                    r_nome = st.text_input("Nome do Reagente *", "Cloreto de Potássio (KCl)")
                    r_formula = st.text_input("Fórmula Química", "KCl")
                    r_mm = st.number_input("Massa Molar (g/mol) *", min_value=0.1, value=74.55)
                    r_pur = st.number_input("Pureza Padrão (%)", min_value=1.0, max_value=100.0, value=99.0)
                    r_est = st.selectbox("Estado Físico", ["Sólido", "Líquido"])
                    r_dens = st.number_input("Densidade (g/mL)", min_value=0.1, value=1.0) if r_est == "Líquido" else None
                    r_ref = st.text_input("Referência / Fonte", "Handbook of Chemistry / Rótulo do Reagente")

                    btn_salv_reag = st.form_submit_button("💾 Salvar Reagente no Banco", type="primary")

                    if btn_salv_reag:
                        if r_nome.strip():
                            st.session_state.reagentes_solucoes.append({
                                "nome": r_nome.strip(),
                                "formula": r_formula.strip(),
                                "massa_molar": float(r_mm),
                                "pureza_padrao": float(r_pur),
                                "densidade_g_ml": float(r_dens) if r_dens else None,
                                "estado": r_est,
                                "referencia": r_ref.strip()
                            })
                            salvar_dados(ARQUIVO_REAGENTES, st.session_state.reagentes_solucoes)
                            st.success(f"Reagente '{r_nome}' cadastrado!")
                            st.rerun()

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
                        st.write(f"👤 **{u.get('nome', '-')}** (Usuário: `{u.get('usuario', '-')}`)")
                        st.caption(f"Categoria: {u.get('categoria','-')} | Orientador: {u.get('orientador','-')} | E-mail: {u.get('email','-')}")
                    with c_b1:
                        if st.button("✅ Aprovar", key=f"ap_usr_{idx}", type="primary"):
                            u["status"] = "Aprovado"
                            salvar_dados(ARQUIVO_USUARIOS, st.session_state.usuarios)
                            for p in st.session_state.integrantes:
                                if p.get("Nome", "").strip().lower() == str(u.get("nome", "")).strip().lower():
                                    p["Situação"] = "Ativo"
                                    if p.get("OrientadorStatus") == "Pendente":
                                        p["OrientadorStatus"] = "Aprovado"
                            salvar_dados(ARQUIVO_INTEGRANTES, st.session_state.integrantes)
                            st.success(f"Acesso aprovado para {u.get('nome')}!")
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
            lista_professores = ["-"] + [p["Nome"] for p in st.session_state.integrantes if p.get("Categoria") == "Orientador"]
            lista_alunos_cad = [p for p in st.session_state.integrantes if p.get("Categoria") in ["Iniciação Científica", "Mestrado", "Doutorado", "Pós-Doutorado"]]

            if lista_alunos_cad:
                dict_alunos = {f"{a.get('Nome', '-') } ({a.get('Categoria', '-')})": a for a in lista_alunos_cad}
                aluno_sel_lbl = st.selectbox("Selecione o Aluno / Pesquisador *", list(dict_alunos.keys()))
                aluno_objeto = dict_alunos[aluno_sel_lbl]

                with st.form("form_admin_orientacao"):
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
                            if u.get("nome", "").strip().lower() == str(aluno_objeto.get("Nome", "")).strip().lower():
                                u["orientador"] = orient_escolhido
                                u["coorientador"] = coorient_escolhido
                                u["orientador_status"] = "Aprovado"
                        salvar_dados(ARQUIVO_USUARIOS, st.session_state.usuarios)

                        st.success(f"Vínculos atualizados para {aluno_objeto.get('Nome')}!")
                        st.rerun()

            st.markdown("---")
            st.subheader("Solicitações Pendentes de Orientação")
            pend_orient_list = [p for p in st.session_state.integrantes if p.get("OrientadorStatus") == "Pendente"]

            if pend_orient_list:
                for idx, al in enumerate(pend_orient_list):
                    c_inf, c_b1, c_b2 = st.columns([3, 1, 1])
                    with c_inf:
                        st.write(f"🎓 **Aluno(a):** {al.get('Nome', '-')} ({al.get('Categoria', '-')})")
                        st.write(f"👨‍🏫 **Orientador Solicitado:** `{al.get('Orientador', '-')}`")
                    with c_b1:
                        if st.button("✅ Aprovar Vínculo", key=f"ap_or_{idx}", type="primary"):
                            al["OrientadorStatus"] = "Aprovado"
                            salvar_dados(ARQUIVO_INTEGRANTES, st.session_state.integrantes)
                            for u in st.session_state.usuarios:
                                if u.get("nome", "").strip().lower() == str(al.get("Nome", "")).strip().lower():
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
            grps_pendentes = [g for g in st.session_state.grupos_db if g.get("status") == "Pendente"]

            if grps_pendentes:
                for idx, g in enumerate(grps_pendentes):
                    c_inf, c_b1, c_b2 = st.columns([3, 1, 1])
                    with c_inf:
                        st.write(f"🔬 **Grupo:** {g.get('nome', '-')}")
                        st.caption(f"Líder: {g.get('lider', '-')} | Colíder: {g.get('colider','-')} | Senha: `{g.get('senha', '-')}`")
                    with c_b1:
                        if st.button("✅ Aprovar Grupo", key=f"ap_grp_{idx}", type="primary"):
                            g["status"] = "Aprovado"
                            salvar_dados(ARQUIVO_GRUPOS, st.session_state.grupos_db)
                            st.success(f"Grupo '{g.get('nome')}' aprovado!")
                            st.rerun()
                    with c_b2:
                        if st.button("❌ Recusar Grupo", key=f"rec_grp_{idx}"):
                            st.session_state.grupos_db = [item for item in st.session_state.grupos_db if item.get("id") != g.get("id")]
                            salvar_dados(ARQUIVO_GRUPOS, st.session_state.grupos_db)
                            st.warning("Solicitação recusada.")
                            st.rerun()
                    st.markdown("---")
            else:
                st.info("Nenhuma solicitação de criação de grupo pendente.")

        with tab_perfis:
            st.subheader("Solicitações de Atualização de Perfil")
            pend_perfis = [u for u in st.session_state.usuarios if u.get("pendente_atualizacao")]

            if pend_perfis:
                for idx, u in enumerate(pend_perfis):
                    p_data = u["pendente_atualizacao"]
                    st.markdown(f"#### 👤 **{u.get('nome', '-')}** (`{u.get('usuario', '-')}`)")
                    c_antes, c_depois = st.columns(2)
                    with c_antes:
                        st.markdown("**📌 Dados Atuais:**")
                        st.write(f"- **Categoria:** {u.get('categoria', '-')}")
                        st.write(f"- **E-mail:** {u.get('email', '-')}")
                    with c_depois:
                        st.markdown("**✏️ Dados Solicitados:**")
                        st.write(f"- **Categoria:** {p_data.get('categoria', '-')}")
                        st.write(f"- **E-mail:** {p_data.get('email', '-')}")

                    c_b1, c_b2 = st.columns([1, 1])
                    with c_b1:
                        if st.button("✅ Aprovar Mudança", key=f"ap_prf_{idx}", type="primary"):
                            u["categoria"] = p_data.get("categoria")
                            u["orientador"] = p_data.get("orientador")
                            u["email"] = p_data.get("email")
                            del u["pendente_atualizacao"]
                            salvar_dados(ARQUIVO_USUARIOS, st.session_state.usuarios)
                            for p in st.session_state.integrantes:
                                if p.get("Nome", "").strip().lower() == str(u.get("nome", "")).strip().lower():
                                    p["Categoria"] = p_data.get("categoria")
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
                        st.write(f"📄 **{a.get('titulo', '-')}** (Pasta: `{a.get('pasta', 'Geral')}`)")
                    with c_b1:
                        if st.button("✅ Aprovar", key=f"ap_arq_{idx}", type="primary"):
                            a["status"] = "Aprovado"
                            salvar_dados(ARQUIVO_ARQUIVOS, st.session_state.arquivos_db)
                            st.success("Arquivo publicado!")
                            st.rerun()
                    with c_b2:
                        if st.button("❌ Recusar", key=f"del_arq_p_{idx}"):
                            st.session_state.arquivos_db = [item for item in st.session_state.arquivos_db if item.get("id") != a.get("id")]
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
                        st.write(f"📝 **{p.get('codigo', 'POP')} - {p.get('titulo', '-')}**")
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

        sub_p1, sub_p2 = st.tabs(["📌 Meus Dados & Edição", "🗓️ Meu Calendário Integrado & Google Agenda"])

        with sub_p1:
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

        with sub_p2:
            st.subheader("🗓️ Meu Calendário Pessoal Integrado")
            st.caption("Consolidação dos eventos da Agenda do Laboratório + Compromissos dos seus Grupos de Pesquisa.")

            meus_eventos_lab = st.session_state.agenda

            meus_eventos_grupos = []
            for g in st.session_state.grupos_db:
                if usuario_atual["nome"] in g.get("membros", []) or usuario_atual["nome"] == g.get("lider") or usuario_atual["nome"] == g.get("colider"):
                    for ev_g in g.get("agenda", []):
                        ev_copy = dict(ev_g)
                        ev_copy["origem_grupo"] = g.get("nome", "Grupo")
                        meus_eventos_grupos.append(ev_copy)

            st.markdown("##### 📌 Próximos Compromissos Vinculados")
            if meus_eventos_lab or meus_eventos_grupos:
                for ev in meus_eventos_lab[:4]:
                    st.markdown(
                        f"""
                        <div class="event-card" style="border-left:4px solid #0284C7;">
                            <b>[Laboratório Geral]</b> {ev.get('titulo', '-')} ({ev.get('data')} - {ev.get('hora_inicio')} às {ev.get('hora_fim')})
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                for ev_g in meus_eventos_grupos[:4]:
                    st.markdown(
                        f"""
                        <div class="event-card" style="border-left:4px solid #059669;">
                            <b>[{ev_g.get('origem_grupo')}]</b> {ev_g.get('titulo', '-')} ({ev_g.get('data')} - {ev_g.get('hora_inicio')} às {ev_g.get('hora_fim')})
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            else:
                st.info("Nenhum evento vinculado no momento.")

            st.markdown("---")
            st.subheader("🔗 Sincronização Individual com Google Agenda")
            st.caption("Insira o link público de incorporação (embed HTML ou iCal) da sua agenda do Google para visualização individual no seu perfil.")

            url_gcal_atual = usr_atual_reg.get("google_calendar_url", "")
            
            with st.form("form_gcal_sync"):
                nova_url_gcal = st.text_input("Link / URL de Incorporação do Google Agenda", value=url_gcal_atual, placeholder="https://calendar.google.com/calendar/embed?src=...")
                btn_salv_gcal = st.form_submit_button("💾 Salvar Link da Minha Agenda", type="primary")

                if btn_salv_gcal:
                    usr_atual_reg["google_calendar_url"] = nova_url_gcal.strip()
                    for u in st.session_state.usuarios:
                        if str(u.get("usuario")).lower() == str(usr_atual_reg["usuario"]).lower():
                            u["google_calendar_url"] = nova_url_gcal.strip()
                            break
                    salvar_dados(ARQUIVO_USUARIOS, st.session_state.usuarios)
                    st.success("Link do Google Agenda salvo no seu perfil individual!")
                    st.rerun()

            if url_gcal_atual:
                st.markdown("##### 📅 Sua Google Agenda Sincronizada:")
                if "iframe" in url_gcal_atual.lower():
                    st.components.v1.html(url_gcal_atual, height=450, scrolling=True)
                elif url_gcal_atual.startswith("http"):
                    st.markdown(f"<iframe src='{url_gcal_atual}' style='border: 0; width: 100%; height: 450px;' frameborder='0' scrolling='no'></iframe>", unsafe_allow_html=True)
                else:
                    st.info("Formato de URL do Google Agenda salvo.")
