import base64
import calendar
from datetime import datetime, date, time
from io import BytesIO
import json
import os
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import streamlit as st

# Tenta importar o ReportLab; caso não esteja instalado, usa fallback estruturado
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, HRFlowable
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
    header {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    [data-testid="stHeader"] {{display: none;}}
    [data-testid="stToolbar"] {{display: none;}}
    
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

REAGENTES_PREDEFINIDOS_FISPQ = {
    "Álcool Etílico 99% (Absoluto P.A.)": {
        "formula": "C2H5OH",
        "fispq_resumo": "Líquido e vapores altamente inflamáveis (H225). Provoca irritação ocular grave (H319). Manter longe do calor/faíscas/chamas.",
        "epis": "Jaleco, luvas de nitrilo, óculos de proteção. Usar sob capela.",
        "validade_dias": 730
    },
    "Álcool Etílico 70%": {
        "formula": "C2H5OH / H2O",
        "fispq_resumo": "Líquido e vapores inflamáveis (H226). Provoca irritação ocular moderada. Manter frasco bem fechado.",
        "epis": "Jaleco, luvas de nitrilo e óculos de proteção.",
        "validade_dias": 365
    },
    "Ácido Clorídrico Concentrado (HCl 37%)": {
        "formula": "HCl",
        "fispq_resumo": "CORROSIVO (H314). Provoca queimaduras graves na pele e lesões oculares graves. Pode provocar irritação respiratória (H335).",
        "epis": "Capela de exaustão, luvas de nitrilo/neoprene espessas, óculos e jaleco.",
        "validade_dias": 365
    },
    "Hidróxido de Sódio 1M (NaOH)": {
        "formula": "NaOH",
        "fispq_resumo": "CORROSIVO (H314). Provoca queimaduras severas na pele e danos oculares graves. Reação exotérmica com água.",
        "epis": "Jaleco, luvas de nitrilo e óculos de segurança contra respingos.",
        "validade_dias": 180
    },
    "Solução Tampão Fosfato 0.1M (pH 7.0)": {
        "formula": "Na2HPO4 / NaH2PO4",
        "fispq_resumo": "Composto não classificado como perigoso segundo norma GHS. Evitar contato direto prolongado com olhos e pele.",
        "epis": "Jaleco e luvas de procedimento.",
        "validade_dias": 90
    },
    "Reagente de Bradford": {
        "formula": "Coomassie Blue / H3PO4 / C2H5OH",
        "fispq_resumo": "Contém ácido fosfórico e etanol. Provoca queimaduras na pele e lesões oculares. Conservar sob refrigeração (4°C).",
        "epis": "Jaleco, luvas de nitrilo e óculos de proteção.",
        "validade_dias": 120
    },
    "Extrato Enzimático de Lipase": {
        "formula": "Proteína Enzimática",
        "fispq_resumo": "Pode provocar sintomas alérgicos ou de asma se inalado (H334). Manter mantido sob refrigeração (-20°C ou 4°C).",
        "epis": "Jaleco, luvas e máscara cirúrgica/N95 no manuseio do pó.",
        "validade_dias": 60
    }
}

DESTINOS_ETIQUETAS = {
    "Microtubo / Eppendorf (0.5 mL a 2.0 mL) [25 x 15 mm]": (25, 15),
    "Tubo Falcon Pequeno (15 mL) [40 x 20 mm]": (40, 20),
    "Tubo Falcon Grande (50 mL) [50 x 25 mm]": (50, 25),
    "Frasco Médio / Erlenmeyer / Béquer [60 x 30 mm]": (60, 30),
    "Frasco Grande / Bancada / Equipamento [75 x 45 mm]": (75, 45),
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
        "agenda": [],
        "solicitacoes_itens": [
            {
                "id": 1,
                "solicitante": "Gabriela Mendes Farias Matos",
                "data_solicitacao": datetime.now().strftime("%d/%m/%Y"),
                "urgente": True,
                "razao_urgencia": "Necessário para extrações enzimáticas na próxima semana.",
                "status": "Pendente",
                "aprovado_por": "-",
                "itens": [
                    {
                        "item": "Álcool Etílico Absolute P.A.",
                        "categoria_item": "Reagentes",
                        "quantidade": "2 Frascos de 1L",
                        "especificacoes": "Grau P.A. (Pureza >= 99.5%)",
                        "link_preferencia": "https://www.sigmaaldrich.com/"
                    },
                    {
                        "item": "Papel de Filtro Qualitativo 12.5cm",
                        "categoria_item": "Papel de Filtro",
                        "quantidade": "1 Caixa (100 un)",
                        "especificacoes": "Porosidade média (8 µm)",
                        "link_preferencia": ""
                    }
                ]
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
        t_header.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F1F5F9')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
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

        sec_title_style = ParagraphStyle('SecTitle', parent=styles['Heading2'], fontSize=11, leading=14, textColor=colors.HexColor('#0E7490'), bold=True)
        body_style = ParagraphStyle('BodyTextCustom', parent=styles['Normal'], fontSize=9.5, leading=13.5, textColor=colors.HexColor('#334155'))

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
        draw.text((40, 40), f"POP - {pop_dict['codigo']}", fill="black")
        buf = BytesIO()
        page.save(buf, format="PDF")
        return buf.getvalue()

# --- NOVO PDF REFORMULADO DE REQUISIÇÃO (MÚLTIPLOS ITENS + LINK + CORREÇÃO DE DESIGN) ---
def gerar_pdf_solicitacao_item(solicitacao, nome_grupo, lider_nome, colider_nome):
    urgente_bool = solicitacao.get("urgente", False)
    urgente_str = "🚨 SOLICITAÇÃO URGENTE" if urgente_bool else "📦 FLUXO PADRÃO (REGULAR)"
    razao_urgencia = solicitacao.get("razao_urgencia", "Não informada")
    solicitante_nome = solicitacao.get("solicitante", "Não informado")
    data_sol = solicitacao.get("data_solicitacao", datetime.now().strftime("%d/%m/%Y"))

    # Suporte a múltiplos itens ou item único legado
    lista_itens = solicitacao.get("itens", [])
    if not lista_itens and "item" in solicitacao:
        lista_itens = [{
            "item": solicitacao.get("item", "-"),
            "categoria_item": solicitacao.get("categoria_item", "Reagentes"),
            "quantidade": solicitacao.get("quantidade", "-"),
            "especificacoes": solicitacao.get("especificacoes", "-"),
            "link_preferencia": solicitacao.get("link_preferencia", "")
        }]

    if REPORTLAB_DISPONIVEL:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()
        story = []

        # Estilos Customizados
        title_group_style = ParagraphStyle('GrpHeaderTitle', parent=styles['Normal'], fontSize=14, leading=18, textColor=colors.white, bold=True)
        sub_group_style = ParagraphStyle('GrpHeaderSub', parent=styles['Normal'], fontSize=10, leading=13, textColor=colors.HexColor('#E0F2FE'))
        
        lbl_style = ParagraphStyle('LblStyle', parent=styles['Normal'], fontSize=9, leading=12, textColor=colors.HexColor('#64748B'), bold=True)
        val_style = ParagraphStyle('ValStyle', parent=styles['Normal'], fontSize=9.5, leading=13, textColor=colors.HexColor('#0F172A'))
        
        urg_box_style = ParagraphStyle('UrgBox', parent=styles['Normal'], fontSize=10, leading=13, 
                                       textColor=colors.HexColor('#991B1B') if urgente_bool else colors.HexColor('#15803D'), bold=True)
        
        tbl_hdr_style = ParagraphStyle('TblHdr', parent=styles['Normal'], fontSize=9, leading=11, textColor=colors.white, bold=True)
        tbl_cell_style = ParagraphStyle('TblCell', parent=styles['Normal'], fontSize=8.5, leading=11, textColor=colors.HexColor('#1E293B'))
        link_cell_style = ParagraphStyle('LinkCell', parent=styles['Normal'], fontSize=8, leading=10, textColor=colors.HexColor('#0284C7'))

        # 1. BANNER DO CABEÇALHO COM NOME DO GRUPO DE PESQUISA
        header_banner_data = [
            [
                Paragraph(f"<b>🔬 GRUPO DE PESQUISA: {nome_grupo.upper()}</b>", title_group_style),
                Paragraph(f"<b>PEDIDO Nº:</b> REQ-{solicitacao.get('id', 1):04d}<br/><b>DATA:</b> {data_sol}", sub_group_style)
            ]
        ]
        t_banner = Table(header_banner_data, colWidths=[380, 160])
        t_banner.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#0E7490')),
            ('PADDING', (0,0), (-1,-1), 10),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ]))
        story.append(t_banner)
        story.append(Spacer(1, 12))

        # 2. INFORMAÇÕES DO SOLICITANTE E LIDERANÇA
        info_data = [
            [Paragraph("SOLICITANTE RESPONSÁVEL", lbl_style), Paragraph("LIDERANÇA DO GRUPO", lbl_style), Paragraph("STATUS DO PEDIDO", lbl_style)],
            [Paragraph(f"<b>{solicitante_nome}</b>", val_style), Paragraph(f"{lider_nome} / {colider_nome}", val_style), Paragraph(f"<b>{solicitacao.get('status', 'Pendente')}</b>", val_style)],
        ]
        t_info = Table(info_data, colWidths=[200, 200, 140])
        t_info.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#F1F5F9')),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t_info)
        story.append(Spacer(1, 10))

        # 3. QUADRO DE URGÊNCIA E JUSTIFICATIVA
        urg_color_bg = colors.HexColor('#FEE2E2') if urgente_bool else colors.HexColor('#DCFCE7')
        urg_data = [
            [Paragraph(urgente_str, urg_box_style)],
            [Paragraph(f"<b>Justificativa / Razão do Pedido:</b> {razao_urgencia}", val_style)]
        ]
        t_urg = Table(urg_data, colWidths=[540])
        t_urg.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), urg_color_bg),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#FCA5A5') if urgente_bool else colors.HexColor('#86EFAC')),
            ('PADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(t_urg)
        story.append(Spacer(1, 15))

        # 4. TABELA DE ITENS SOLICITADOS (MÚLTIPLOS ITENS)
        story.append(Paragraph("<b>RELAÇÃO DE MATERIAIS / REAGENTES / VIDRARIAS SOLICITADAS:</b>", ParagraphStyle('SecHead', parent=styles['Heading3'], fontSize=10, textColor=colors.HexColor('#0F172A'), bold=True)))
        story.append(Spacer(1, 6))

        table_items_content = [
            [
                Paragraph("#", tbl_hdr_style),
                Paragraph("ITEM / MATERIAL", tbl_hdr_style),
                Paragraph("CATEGORIA", tbl_hdr_style),
                Paragraph("QTD", tbl_hdr_style),
                Paragraph("ESPECIFICAÇÕES & LINK PREFERENCIAL", tbl_hdr_style)
            ]
        ]

        for idx_i, item_obj in enumerate(lista_itens, 1):
            espec_text = item_obj.get('especificacoes', '-')
            link_text = item_obj.get('link_preferencia', '')
            
            detail_p = f"• {espec_text}"
            if link_text and str(link_text).strip():
                detail_p += f"<br/>• 🔗 <u>Link: {link_text[:55]}...</u>" if len(link_text) > 55 else f"<br/>• 🔗 <u>Link: {link_text}</u>"

            table_items_content.append([
                Paragraph(str(idx_i), tbl_cell_style),
                Paragraph(f"<b>{item_obj.get('item', '-')}</b>", tbl_cell_style),
                Paragraph(item_obj.get('categoria_item', 'Geral'), tbl_cell_style),
                Paragraph(f"<b>{item_obj.get('quantidade', '-')}</b>", tbl_cell_style),
                Paragraph(detail_p, link_cell_style if link_text else tbl_cell_style)
            ])

        t_items = Table(table_items_content, colWidths=[25, 160, 95, 60, 200])
        t_items.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0E7490')),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
            ('PADDING', (0,0), (-1,-1), 6),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(t_items)
        story.append(Spacer(1, 35))

        # 5. ASSINATURAS E APRECIAÇÃO
        sign_data = [
            [Paragraph("____________________________________________", val_style), Paragraph("____________________________________________", val_style)],
            [Paragraph(f"<b>{solicitante_nome}</b><br/>Solicitante Responsável", val_style), Paragraph(f"<b>{lider_nome}</b><br/>Liderança de {nome_grupo}", val_style)]
        ]
        t_sign = Table(sign_data, colWidths=[270, 270])
        t_sign.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('PADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(t_sign)

        doc.build(story)
        return buffer.getvalue()
    else:
        # Fallback alternativo limpo caso reportlab não esteja disponível
        page = Image.new("RGB", (612, 792), "white")
        draw = ImageDraw.Draw(page)
        draw.rectangle([20, 20, 592, 70], fill="#0E7490")
        draw.text((30, 35), f"GRUPO DE PESQUISA: {nome_grupo.upper()}", fill="white")
        draw.text((30, 85), f"Solicitante: {solicitante_nome} | Data: {data_sol}", fill="black")
        draw.text((30, 110), f"Urgencia: {urgente_str} - Razao: {razao_urgencia}", fill="red" if urgente_bool else "green")
        
        y = 150
        draw.text((30, y), "ITENS SOLICITADOS:", fill="black")
        y += 20
        for idx_i, itm in enumerate(lista_itens, 1):
            draw.text((40, y), f"{idx_i}. {itm.get('item')} | Qtd: {itm.get('quantidade')} | Cat: {itm.get('categoria_item')}", fill="black")
            y += 18
            if itm.get('link_preferencia'):
                draw.text((50, y), f"Link: {itm.get('link_preferencia')[:60]}", fill="blue")
                y += 18

        buf = BytesIO()
        page.save(buf, format="PDF")
        return buf.getvalue()

# --- GERADOR DE ETIQUETAS OTIMIZADO PARA IMPRESSÃO EM FRASCOS E MICROTUBOS ---
def gerar_pdf_etiquetas_frasco(nome_amostra, id_amostra, data_nasc, responsavel, fispq_txt, mm_w=40, mm_h=20, quantidade=12, qr_img_pil=None, grupo_nome=""):
    dpi = 300
    px_mm = dpi / 25.4
    
    page_w_px = int(210 * px_mm) # A4 Largura
    page_h_px = int(297 * px_mm) # A4 Altura

    lbl_w_px = int(mm_w * px_mm)
    lbl_h_px = int(mm_h * px_mm)
    
    margin_px = int(8 * px_mm)
    spacing_x = int(3 * px_mm)
    spacing_y = int(3 * px_mm)

    pages = []
    current_page = Image.new("RGB", (page_w_px, page_h_px), "white")
    draw = ImageDraw.Draw(current_page)

    x = margin_px
    y = margin_px

    # Redimensiona QR Code para caber na etiqueta do frasco
    qr_side_px = min(int(lbl_h_px * 0.82), int(lbl_w_px * 0.38))
    qr_resized = qr_img_pil.resize((qr_side_px, qr_side_px)) if qr_img_pil else None

    for idx in range(quantidade):
        if x + lbl_w_px > page_w_px - margin_px:
            x = margin_px
            y += lbl_h_px + spacing_y

        if y + lbl_h_px > page_h_px - margin_px:
            pages.append(current_page)
            current_page = Image.new("RGB", (page_w_px, page_h_px), "white")
            draw = ImageDraw.Draw(current_page)
            x = margin_px
            y = margin_px

        # Borda tracejada/fina de corte para a etiqueta
        draw.rectangle([x, y, x + lbl_w_px, y + lbl_h_px], outline="#CBD5E1", width=2)

        # Insere o código QR
        if qr_resized:
            qr_x = x + int(2 * px_mm)
            qr_y = y + (lbl_h_px - qr_side_px) // 2
            current_page.paste(qr_resized, (qr_x, qr_y))
            text_x = qr_x + qr_side_px + int(2 * px_mm)
        else:
            text_x = x + int(2 * px_mm)

        text_y = y + int(2 * px_mm)

        # Informações da Etiqueta no Frasco (Renderização em alta resolução)
        draw.text((text_x, text_y), f"🧪 {nome_amostra[:22]}", fill="#0F172A")
        text_y += int(3.6 * px_mm)
        draw.text((text_x, text_y), f"ID: {id_amostra} | Nasc: {data_nasc}", fill="#334155")
        text_y += int(3.2 * px_mm)
        draw.text((text_x, text_y), f"Resp: {responsavel[:18]}", fill="#475569")
        
        if fispq_txt and mm_h >= 20:
            text_y += int(3.2 * px_mm)
            draw.text((text_x, text_y), f"⚠️ {fispq_txt[:26]}...", fill="#991B1B")

        x += lbl_w_px + spacing_x

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
if "itens_carrinho_req" not in st.session_state:
    st.session_state.itens_carrinho_req = []
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
                    usr_alvo = next((u for u in st.session_state.usuarios if str(u.get("usuario", "")).strip().lower() == ident_clean or str(u.get("email", "")).strip().lower() == ident_clean), None)
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

    # Notificações
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

        if st.sidebar.button(display_label, key=f"nav_btn_{chave}", use_container_width=True, type="primary" if is_selected else "secondary"):
            st.session_state.menu_selecionado = chave
            st.rerun()

    # Seções Agrupadas
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

    # SELETOR DE COR DO TEMA NA SIDEBAR
    st.sidebar.markdown('<div class="sidebar-section">🎨 APARÊNCIA DO APP</div>', unsafe_allow_html=True)
    novo_tema = st.sidebar.selectbox("Cor do Tema", options=list(TEMAS_CORES.keys()), index=list(TEMAS_CORES.keys()).index(st.session_state.tema_cor), key="select_tema_sidebar")

    if novo_tema != st.session_state.tema_cor:
        st.session_state.tema_cor = novo_tema
        st.rerun()

    menu_selecionado = st.session_state.menu_selecionado

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**{usuario_atual['nome']}**<br/><span style='font-size:0.8rem; color:#64748B;'>{'Administrador' if is_admin else 'Pesquisador'}</span>", unsafe_allow_html=True)

    if st.sidebar.button("🚪 Sair da conta"):
        st.query_params.clear()
        st.session_state.usuario_logado = None
        st.rerun()

    # --- 0. PÁGINA INICIAL & AVISOS ---
    if menu_selecionado == "🏠 Página Inicial & Avisos":
        st.title("🏠 Painel Geral de Pesquisa")
        st.caption(f"Bem-vindo(a) de volta, **{usuario_atual['nome']}**!")

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        with kpi1:
            st.markdown(f'<div class="kpi-card kpi-card-blue"><div><div class="kpi-val">{len(st.session_state.integrantes)}</div><div class="kpi-label">Integrantes</div></div><div class="kpi-icon">👥</div></div>', unsafe_allow_html=True)
        with kpi2:
            eventos_futuros = [e for e in st.session_state.agenda if e.get("data", "") >= hoje_str]
            st.markdown(f'<div class="kpi-card kpi-card-green"><div><div class="kpi-val">{len(eventos_futuros)}</div><div class="kpi-label">Próximos Eventos</div></div><div class="kpi-icon">📅</div></div>', unsafe_allow_html=True)
        with kpi3:
            st.markdown(f'<div class="kpi-card kpi-card-amber"><div><div class="kpi-val">{len(st.session_state.avisos_db)}</div><div class="kpi-label">Avisos Ativos</div></div><div class="kpi-icon">📢</div></div>', unsafe_allow_html=True)
        with kpi4:
            pops_aprov = len([p for p in st.session_state.pops_db if p.get("status") == "Aprovado"])
            st.markdown(f'<div class="kpi-card kpi-card-purple"><div><div class="kpi-val">{pops_aprov}</div><div class="kpi-label">POPs Vigentes</div></div><div class="kpi-icon">📝</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col_left, col_right = st.columns([1.3, 1])

        with col_left:
            with st.container(border=True):
                st.subheader("📢 Mural de Avisos do Laboratório")
                if is_admin:
                    with st.expander("➕ Publicar Novo Aviso"):
                        with st.form("form_novo_aviso"):
                            tit_aviso = st.text_input("Título do Aviso *")
                            cat_aviso = st.selectbox("Categoria", ["Informativo", "Manutenção", "Urgente", "Segurança", "Eventos"])
                            cor_aviso = st.selectbox("Cor", list(CORES_GOOGLE_AGENDA.keys()))
                            txt_aviso = st.text_area("Conteúdo *", height=100)
                            if st.form_submit_button("📌 Publicar Aviso", type="primary"):
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
                                    st.success("Aviso publicado!")
                                    st.rerun()

                for av in st.session_state.avisos_db:
                    st.markdown(f'<div class="aviso-card" style="border-left-color: {av.get("cor", "#0E7490")};"><h4>{av["titulo"]}</h4><p>{av["conteudo"]}</p><small>Por {av.get("autor")} em {av.get("data")}</small></div>', unsafe_allow_html=True)

        with col_right:
            with st.container(border=True):
                st.subheader("📅 Próximas Reuniões")
                for ev in st.session_state.agenda[:5]:
                    st.markdown(f'<div class="event-card" style="border-left: 4px solid {ev.get("cor","#0284C7")};"><b>{ev["titulo"]}</b><br/><small>{ev.get("data")} ({ev.get("hora_inicio")} às {ev.get("hora_fim")})</small></div>', unsafe_allow_html=True)

    # --- 0.1 AGENDA & CALENDÁRIO ---
    elif menu_selecionado == "📅 Agenda & Calendário":
        st.title("📅 Agenda & Calendário de Atividades")
        st.caption("Organização de reuniões e compromissos estilo Google Agenda.")

    # --- 1. EQUIPE ---
    elif menu_selecionado == "👥 Equipe":
        st.title("👥 Todos os Integrantes do Laboratório")

    # --- 2. ORIENTADOS ---
    elif menu_selecionado == "🎓 Orientados":
        st.title("🎓 Orientados e Alunos por Sequência de Orientador")

    # --- 2.1 GRUPOS DE PESQUISA (SUPORTE A MÚLTIPLOS ITENS E LINK PREFERENCIAL) ---
    elif menu_selecionado == "🔬 Grupo de Pesquisa":
        st.title("🔬 Área de Grupos de Pesquisa")
        st.caption("Gestão do grupo, solicitação de múltiplos itens, avisos e documentos.")

        aba_grp_view, aba_grp_solicitar = st.tabs(["📊 Meus Grupos de Pesquisa", "➕ Criar Novo Grupo"])

        lista_integrantes_nomes = [p["Nome"] for p in st.session_state.integrantes]

        with aba_grp_view:
            grupos_aprovados = [g for g in st.session_state.grupos_db if g.get("status") == "Aprovado"]

            if st.session_state.grupo_ativo_id is None:
                st.subheader("📌 Selecione um Grupo de Pesquisa para Acessar")
                if grupos_aprovados:
                    cols_grp = st.columns(2)
                    for idx, g in enumerate(grupos_aprovados):
                        with cols_grp[idx % 2]:
                            st.markdown(f'<div class="grp-card"><h3>🔬 {g["nome"]}</h3><p>{g.get("descricao")}</p><small><b>Líder:</b> {g.get("lider")} | <b>Colíder:</b> {g.get("colider")}</small></div>', unsafe_allow_html=True)
                            if st.button(f"🚀 Abrir Painel do Grupo '{g['nome']}'", key=f"btn_open_grp_{g['id']}", use_container_width=True):
                                st.session_state.grupo_ativo_id = g["id"]
                                st.rerun()
            else:
                grupo_ativo = next((g for g in grupos_aprovados if g["id"] == st.session_state.grupo_ativo_id), None)
                if not grupo_ativo:
                    st.session_state.grupo_ativo_id = None
                    st.rerun()

                c_back1, c_back2 = st.columns([3, 1])
                with c_back1:
                    st.subheader(f"🔬 Grupo: {grupo_ativo['nome']}")
                with c_back2:
                    if st.button("⬅️ Voltar para Lista", use_container_width=True):
                        st.session_state.grupo_ativo_id = None
                        st.rerun()

                grp_id = grupo_ativo["id"]
                is_lider_ou_colider = is_admin or (usuario_atual["nome"] == grupo_ativo.get("lider")) or (usuario_atual["nome"] == grupo_ativo.get("colider"))

                sub_tab1, sub_tab2, sub_tab3 = st.tabs(["📦 Solicitação de Itens (Pedido Completo)", "📝 Mural", "👥 Membros"])

                # ABA DE SOLICITAÇÃO COM SUPORTE A MÚLTIPLOS ITENS E LINK PREFERENCIAL
                with sub_tab1:
                    st.subheader("📦 Requisição de Reagentes, Vidrarias e Materiais")
                    st.caption("Adicione múltiplos itens à sua lista e gere uma única requisição em PDF de alta qualidade.")

                    st_sub1, st_sub2 = st.tabs(["📋 Fila de Pedidos Realizados", "➕ Criar Nova Requisição (Múltiplos Itens)"])

                    with st_sub1:
                        solicitacoes = grupo_ativo.get("solicitacoes_itens", [])
                        if solicitacoes:
                            for idx_sol, sol in enumerate(solicitacoes):
                                st_cor = "#059669" if sol.get("status") == "Aprovado" else ("#DC2626" if sol.get("status") == "Recusado" else "#D97706")
                                urg_txt = "🚨 URGENTE" if sol.get("urgente") else "📦 FLUXO PADRÃO"

                                # Garante formato de múltiplos itens
                                list_itms = sol.get("itens", [])
                                if not list_itms and "item" in sol:
                                    list_itms = [{"item": sol.get("item"), "quantidade": sol.get("quantidade"), "categoria_item": sol.get("categoria_item"), "especificacoes": sol.get("especificacoes"), "link_preferencia": sol.get("link_preferencia", "")}]

                                st.markdown(
                                    f"""
                                    <div class="event-card" style="border-left: 5px solid {st_cor};">
                                        <div style="display:flex; justify-content:space-between;">
                                            <h4 style="margin:0;">📦 Pedido REQ-{sol.get('id', idx_sol):04d} ({len(list_itms)} iten(s))</h4>
                                            <span style="font-weight:bold; color:{st_cor};">[{sol.get('status','Pendente')}] - {urg_txt}</span>
                                        </div>
                                        <div style="font-size:0.85rem; color:#475569; margin-top:4px;">
                                            👤 <b>Solicitante:</b> {sol.get('solicitante')} | 📅 <b>Data:</b> {sol.get('data_solicitacao')}
                                        </div>
                                        <div style="font-size:0.82rem; color:#334155; margin-top:4px;">
                                            ℹ️ <b>Motivo/Justificativa:</b> {sol.get('razao_urgencia','-')}
                                        </div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )

                                c_sol_btn1, c_sol_btn2, c_sol_btn3 = st.columns([1.5, 1, 1])

                                with c_sol_btn1:
                                    pdf_sol_bytes = gerar_pdf_solicitacao_item(sol, grupo_ativo['nome'], grupo_ativo.get('lider'), grupo_ativo.get('colider'))
                                    st.download_button(
                                        "📄 Baixar PDF do Pedido (Alta Resolução)",
                                        data=pdf_sol_bytes,
                                        file_name=f"Requisicao_{grupo_ativo['nome']}_REQ{sol.get('id', idx_sol)}.pdf",
                                        mime="application/pdf",
                                        key=f"dl_sol_pdf_{grp_id}_{idx_sol}"
                                    )

                                if is_lider_ou_colider and sol.get("status") == "Pendente":
                                    with c_sol_btn2:
                                        if st.button("✅ Aprovar", key=f"ap_sol_{grp_id}_{idx_sol}", type="primary"):
                                            sol["status"] = "Aprovado"
                                            sol["aprovado_por"] = usuario_atual["nome"]
                                            salvar_dados(ARQUIVO_GRUPOS, st.session_state.grupos_db)
                                            st.success("Pedido Aprovado!")
                                            st.rerun()
                                    with c_sol_btn3:
                                        if st.button("❌ Recusar", key=f"rec_sol_{grp_id}_{idx_sol}"):
                                            sol["status"] = "Recusado"
                                            sol["aprovado_por"] = usuario_atual["nome"]
                                            salvar_dados(ARQUIVO_GRUPOS, st.session_state.grupos_db)
                                            st.warning("Pedido Recusado.")
                                            st.rerun()
                                st.markdown("---")
                        else:
                            st.info("Nenhuma requisição efetuada para este grupo.")

                    with st_sub2:
                        st.markdown("#### 🛒 Carrinho do Pedido de Compra / Requisição")
                        
                        with st.form(f"form_add_item_carrinho_{grp_id}"):
                            st.markdown("##### ➕ Adicionar Item ao Pedido")
                            c_i1, c_i2, c_i3 = st.columns([2.5, 1.2, 1.2])
                            with c_i1:
                                item_nome_in = st.text_input("Nome do Item / Reagente / Vidraria *")
                            with c_i2:
                                item_cat_in = st.selectbox("Categoria", ["Reagentes", "Vidrarias", "Papel de Filtro", "Consumíveis", "Equipamentos", "Outros"])
                            with c_i3:
                                item_qtd_in = st.text_input("Quantidade *", "2 Frascos de 1L")

                            item_espec_in = st.text_input("Especificações Técnicas (Pureza, Marca, Tamanho, etc.)", "Grau P.A. (Pureza >= 99.5%)")
                            item_link_in = st.text_input("🔗 Link de Preferência de Compra (Opcional)", placeholder="https://www.sigmaaldrich.com/BR/pt/product/...")

                            btn_add_item = st.form_submit_button("🛒 Adicionar Este Item ao Carrinho")

                            if btn_add_item:
                                if item_nome_in.strip() and item_qtd_in.strip():
                                    st.session_state.itens_carrinho_req.append({
                                        "item": item_nome_in.strip(),
                                        "categoria_item": item_cat_in,
                                        "quantidade": item_qtd_in.strip(),
                                        "especificacoes": item_espec_in.strip(),
                                        "link_preferencia": item_link_in.strip()
                                    })
                                    st.success(f"Item '{item_nome_in}' adicionado ao carrinho!")
                                    st.rerun()
                                else:
                                    st.error("Preencha o nome do item e a quantidade.")

                        # EXIBE CARRINHO ATUAL
                        if st.session_state.itens_carrinho_req:
                            st.markdown("##### 📋 Itens Atual no Pedido:")
                            df_carrinho = pd.DataFrame(st.session_state.itens_carrinho_req)
                            st.dataframe(df_carrinho[["item", "categoria_item", "quantidade", "especificacoes", "link_preferencia"]], use_container_width=True)

                            if st.button("🗑️ Esvaziar Carrinho"):
                                st.session_state.itens_carrinho_req = []
                                st.rerun()

                            st.markdown("---")
                            st.markdown("##### 🚀 Dados Finais da Requisição")
                            with st.form(f"form_fechar_pedido_{grp_id}"):
                                c_urg1, c_urg2 = st.columns([1, 2])
                                with c_urg1:
                                    is_urgente = st.checkbox("🚨 PEDIDO URGENTE?")
                                with c_urg2:
                                    razao_urg = st.text_input("Razão da Urgência / Justificativa *", "Necessário para ensaios da próxima semana.")

                                opt_solicitantes = lista_integrantes_nomes
                                idx_sol_def = lista_integrantes_nomes.index(usuario_atual["nome"]) if usuario_atual["nome"] in lista_integrantes_nomes else 0
                                sel_sol_tipo = st.selectbox("Solicitante Responsável", opt_solicitantes, index=idx_sol_def)

                                btn_enviar_pedido_completo = st.form_submit_button("🚀 Finalizar e Gerar Requisição Oficial", type="primary")

                                if btn_enviar_pedido_completo:
                                    if razao_urg.strip() and sel_sol_tipo:
                                        if "solicitacoes_itens" not in grupo_ativo:
                                            grupo_ativo["solicitacoes_itens"] = []

                                        novo_id_sol = max([s.get("id", 0) for s in grupo_ativo["solicitacoes_itens"]], default=0) + 1
                                        grupo_ativo["solicitacoes_itens"].append({
                                            "id": novo_id_sol,
                                            "urgente": is_urgente,
                                            "razao_urgencia": razao_urg.strip(),
                                            "solicitante": sel_sol_tipo,
                                            "data_solicitacao": datetime.now().strftime("%d/%m/%Y"),
                                            "status": "Pendente",
                                            "aprovado_por": "-",
                                            "itens": list(st.session_state.itens_carrinho_req)
                                        })
                                        salvar_dados(ARQUIVO_GRUPOS, st.session_state.grupos_db)
                                        st.session_state.itens_carrinho_req = []
                                        st.success("✅ Pedido completo gerado com sucesso!")
                                        st.rerun()
                                    else:
                                        st.error("Preencha a justificativa e o solicitante.")
                        else:
                            st.info("O carrinho está vazio. Adicione pelo menos um item acima para fechar a requisição.")

                with sub_tab2:
                    st.subheader("📝 Mural do Grupo")
                    st.write(grupo_ativo.get("mural", "Sem anotações."))

                with sub_tab3:
                    st.subheader("👥 Integrantes do Grupo")
                    for m in grupo_ativo.get("membros", []):
                        st.write(f"- {m}")

        with aba_grp_solicitar:
            st.subheader("➕ Solicitar Criação de Novo Grupo")

    # --- 3. PRESENÇA NO LABORATÓRIO ---
    elif menu_selecionado == "🕒 Presença no Laboratório":
        st.title("🕒 Presença no Laboratório")

    # --- 4. REPOSITÓRIO DE ARQUIVOS ---
    elif menu_selecionado == "📁 Repositório de Arquivos":
        st.title("📁 Central de Arquivos & Documentos")

    # --- 5. GERAR QR CODE E ETIQUETAS COM FISPQ (ÁREA DE CONHECIMENTO E FERRAMENTAS) ---
    elif menu_selecionado == "🏷️ Gerar QR Code de Amostras":
        st.title("🏷️ Gerador de Etiquetas & QR Code de Amostras")
        st.caption("Crie etiquetas otimizadas e compactas para frascos de laboratório, microtubos, reagentes e soluções.")

        tab_etq_pre, tab_etq_custom = st.tabs([
            "🏷️ Reagentes Pré-definidos & FISPQ (Ex: Álcool 99%)",
            "✍️ Etiqueta Customizada / Amostra Genérica"
        ])

        # ABA DE ETIQUETAS PRÉ-DEFINIDAS COM FISPQ E DATA DE NASCIMENTO
        with tab_etq_pre:
            col_pre_f, col_pre_p = st.columns([1.2, 1])

            with col_pre_f:
                st.subheader("Selecione o Reagente / Amostra Pré-definida")
                
                reagente_pre = st.selectbox("Reagente / Solução Padrão", list(REAGENTES_PREDEFINIDOS_FISPQ.keys()))
                info_fispq = REAGENTES_PREDEFINIDOS_FISPQ[reagente_pre]

                id_gerado_fispq = f"REAG-{datetime.now().strftime('%Y%m%d')}-{st.session_state.seq_amostra:03d}"
                c_id_f1, c_id_f2 = st.columns([3, 1])
                with c_id_f1:
                    id_amostra_f = st.text_input("Código / Lote da Amostra", value=id_gerado_fispq, key="id_fispq_inp")
                with c_id_f2:
                    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                    if st.button("🔄 Novo ID", key="btn_new_id_fispq"):
                        st.session_state.seq_amostra += 1
                        st.rerun()

                c_dt1, c_dt2 = st.columns(2)
                with c_dt1:
                    data_nascimento = st.date_input("🎂 Data de Nascimento / Obtenção da Amostra", datetime.now().date(), key="dt_nasc_fispq")
                with c_dt2:
                    validade_calc = datetime.now().date() + pd.Timedelta(days=info_fispq["validade_dias"])
                    data_validade = st.date_input("⏳ Data de Validade", validade_calc, key="dt_val_fispq")

                grupos_nomes = [g["nome"] for g in st.session_state.grupos_db if g.get("status") == "Aprovado"]
                grupo_origem = st.selectbox("Grupo de Pesquisa Responsável", ["Geral / Laboratório"] + grupos_nomes)
                pesquisador_resp = st.selectbox("Pesquisador Responsável pelo Preparo", [p["Nome"] for p in st.session_state.integrantes], key="resp_fispq")

                st.markdown("##### ⚠️ Informações Automáticas da FISPQ (MSDS)")
                fispq_editada = st.text_area("Frases de Risco e Perigo FISPQ", value=info_fispq["fispq_resumo"], height=70)

                st.markdown("##### 📏 Tamanho do Frasco / Dimensão da Etiqueta")
                tam_frasco_label = st.selectbox("Tamanho do Frasco para Colar", list(DESTINOS_ETIQUETAS.keys()), index=1)
                mm_w, mm_h = DESTINOS_ETIQUETAS[tam_frasco_label]

                qtd_imprimir = st.number_input("Quantidade de Etiquetas na Folha A4", min_value=1, max_value=100, value=12, key="qtd_fispq")

            with col_pre_p:
                st.subheader("👁️ Pré-visualização da Etiqueta")

                conteudo_qr_fispq = (
                    f"🧪 REAGENTE/SOLUÇÃO FISPQ\n"
                    f"------------------------\n"
                    f"• Nome: {reagente_pre}\n"
                    f"• ID/Lote: {id_amostra_f}\n"
                    f"• D.Nascimento: {data_nascimento.strftime('%d/%m/%Y')}\n"
                    f"• Validade: {data_validade.strftime('%d/%m/%Y')}\n"
                    f"• Grupo: {grupo_origem}\n"
                    f"• Resp: {pesquisador_resp}\n"
                    f"------------------------\n"
                    f"⚠️ FISPQ: {fispq_editada}"
                )

                if QRCODE_DISPONIVEL:
                    img_qr_f = qrcode.make(conteudo_qr_fispq)
                    buffer_qr = BytesIO()
                    img_qr_f.save(buffer_qr, format="PNG")
                    img_qr_bytes = buffer_qr.getvalue()

                    st.image(img_qr_bytes, caption=f"QR Code: {reagente_pre}", width=180)

                    st.markdown(
                        f"""
                        <div class="pop-preview-card" style="border-left: 4px solid #0E7490; background:#FFF;">
                            <div style="font-weight:bold; color:#0F172A; font-size:0.95rem;">🧪 {reagente_pre}</div>
                            <div style="font-size:0.8rem; color:#334155;">ID: <b>{id_amostra_f}</b> | Grupo: {grupo_origem}</div>
                            <div style="font-size:0.8rem; color:#334155;">🎂 <b>Nascimento:</b> {data_nascimento.strftime('%d/%m/%Y')}</div>
                            <div style="font-size:0.8rem; color:#334155;">⏳ <b>Validade:</b> {data_validade.strftime('%d/%m/%Y')}</div>
                            <div style="font-size:0.8rem; color:#475569;">👤 Resp: {pesquisador_resp}</div>
                            <div style="font-size:0.75rem; color:#991B1B; margin-top:4px;">⚠️ <b>FISPQ:</b> {fispq_editada[:80]}...</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    pdf_frasco_bytes = gerar_pdf_etiquetas_frasco(
                        nome_amostra=reagente_pre,
                        id_amostra=id_amostra_f,
                        data_nasc=data_nascimento.strftime('%d/%m/%Y'),
                        responsavel=pesquisador_resp,
                        fispq_txt=fispq_editada,
                        mm_w=mm_w,
                        mm_h=mm_h,
                        quantidade=qtd_imprimir,
                        qr_img_pil=img_qr_f,
                        grupo_nome=grupo_origem
                    )

                    st.download_button(
                        f"📄 Baixar PDF de Etiquetas ({qtd_imprimir}x para Frasco {mm_w}x{mm_h}mm)",
                        data=pdf_frasco_bytes,
                        file_name=f"Etiquetas_Frasco_{id_amostra_f}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

        # ABA DE ETIQUETA CUSTOMIZADA
        with tab_etq_custom:
            col_f, col_q = st.columns([1.2, 1])

            with col_f:
                id_gerado_auto = f"AMS-{datetime.now().strftime('%Y%m%d')}-{st.session_state.seq_amostra:03d}"
                id_amostra = st.text_input("Código / ID da Amostra", value=id_gerado_auto, key="id_custom_inp")
                nome_amostra = st.text_input("Nome da Amostra / Reagente Personalizado", "Amostra Enzimática - Lote A")
                data_obtencao = st.date_input("Data de Obtenção / Preparo", datetime.now().date(), key="dt_cust_inp")
                responsavel_nome = st.selectbox("Pesquisador Responsável", [p["Nome"] for p in st.session_state.integrantes], key="resp_cust_inp")
                descricao = st.text_area("Descrição / Protocolo", value="Amostra obtida via fermentação estado sólido.")
                qtd_etiquetas = st.number_input("Quantidade de Etiquetas", min_value=1, max_value=100, value=6, key="qtd_cust_inp")

            with col_q:
                conteudo_qr = f"📋 FICHA DA AMOSTRA\n------------------------\n• ID: {id_amostra}\n• Amostra: {nome_amostra}\n• Data: {data_obtencao.strftime('%d/%m/%Y')}\n• Resp: {responsavel_nome}\n------------------------\n• Descrição:\n{descricao}"

                if QRCODE_DISPONIVEL:
                    img = qrcode.make(conteudo_qr)
                    buffer = BytesIO()
                    img.save(buffer, format="PNG")
                    img_bytes = buffer.getvalue()
                    st.image(img_bytes, caption=f"Pré-visualização: {id_amostra}", width=180)

                    pdf_custom_bytes = gerar_pdf_etiquetas_frasco(
                        nome_amostra=nome_amostra,
                        id_amostra=id_amostra,
                        data_nasc=data_obtencao.strftime('%d/%m/%Y'),
                        responsavel=responsavel_nome,
                        fispq_txt=descricao,
                        mm_w=40,
                        mm_h=20,
                        quantidade=qtd_etiquetas,
                        qr_img_pil=img
                    )
                    st.download_button(f"📄 Baixar PDF ({qtd_etiquetas}x Etiquetas)", pdf_custom_bytes, f"Etiquetas_{id_amostra}.pdf", "application/pdf")

    # --- 6. CRIADOR DE POP ---
    elif menu_selecionado == "📝 Criador de POP":
        st.title("📝 Procedimentos Operacionais Padrão (POPs)")

    # --- 6.1 CALCULADORA DE PREPARO DE SOLUÇÕES ---
    elif menu_selecionado == "🧪 Calculadora de Soluções":
        st.title("🧪 Calculadora de Soluções")

    # --- 7. ADMINISTRAÇÃO ---
    elif menu_selecionado == "🛡️ Administração" and is_admin:
        st.title("🛡️ Central de Administração")

    # --- 8. MEU PERFIL ---
    elif menu_selecionado == "👤 Meu perfil":
        st.title("👤 Meu Perfil e Configurações")
