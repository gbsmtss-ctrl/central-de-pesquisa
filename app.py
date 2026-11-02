import base64
import calendar
from datetime import datetime, date, time
from io import BytesIO
import json
import os
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import streamlit as st

# --- IMPORTAÇÃO DO REPORTLAB PARA PDFS VETORIAIS DE ALTA RESOLUÇÃO ---
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    REPORTLAB_DISPONIVEL = True
except ImportError:
    REPORTLAB_DISPONIVEL = False

# --- IMPORTAÇÃO DO QRCODE ---
try:
    import qrcode
    QRCODE_DISPONIVEL = True
except ImportError:
    QRCODE_DISPONIVEL = False

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Central de Pesquisa", page_icon="🧪", layout="wide")

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

    .badge-ativo {{ background-color: #DCFCE7; color: #15803D; padding: 3px 10px; border-radius: 12px; font-weight: 700; font-size: 0.78rem; display: inline-block; }}
    .badge-pendente {{ background-color: #FEF3C7; color: #B45309; padding: 3px 10px; border-radius: 12px; font-weight: 700; font-size: 0.78rem; display: inline-block; }}
    .badge-urgente {{ background-color: #FEE2E2; color: #991B1B; padding: 3px 10px; border-radius: 12px; font-weight: 700; font-size: 0.78rem; display: inline-block; }}
    
    .drive-folder-card {{
        background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px;
        padding: 14px; text-align: left; transition: all 0.2s ease;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02); margin-bottom: 10px;
    }}
    .drive-folder-card:hover {{ border-color: {cor_primaria}; background-color: {cor_bg_light}; }}
    
    .pop-preview-card {{ background-color: #FFFFFF; border: 1px solid #CBD5E1; border-left: 4px solid {cor_primaria}; border-radius: 8px; padding: 16px; margin-bottom: 15px; }}
    .aviso-card {{ background-color: #FFFFFF; border-radius: 8px; padding: 14px 16px; margin-bottom: 10px; border-left: 4px solid {cor_primaria}; box-shadow: 0 1px 3px rgba(0,0,0,0.02); }}
    .event-card {{ background-color: #FFFFFF; border-radius: 8px; padding: 12px 14px; margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.02); border: 1px solid #E2E8F0; }}
    </style>
""",
    unsafe_allow_html=True,
)

# --- ARQUIVOS DE PERSISTÊNCIA JSON ---
ARQUIVO_INTEGRANTES = "integrantes.json"
ARQUIVO_AGENDA = "agenda.json"
ARQUIVO_USUARIOS = "usuarios.json"
ARQUIVO_ARQUIVOS = "arquivos.json"
ARQUIVO_PASTAS = "pastas.json"
ARQUIVO_POPS = "pops.json"
ARQUIVO_AVISOS = "avisos.json"
ARQUIVO_GRUPOS = "grupos_pesquisa.json"
ARQUIVO_REAGENTES = "reagentes_solucoes.json"

CATEGORIAS_PADRAO = ["Iniciação Científica", "Mestrado", "Doutorado", "Pós-Doutorado", "Orientador", "Técnico / Pesquisador"]

REAGENTES_PREDEFINIDOS_FISPQ = {
    "Álcool Etílico 99% (Absoluto P.A.)": {
        "formula": "C2H5OH",
        "fispq_resumo": "Líquido e vapores altamente inflamáveis (H225). Provoca irritação ocular grave (H319). Manter longe do calor/faíscas/chamas.",
        "epis": "Jaleco, luvas de nitrilo, óculos de proteção. Usar sob capela.",
        "validade_padrao_dias": 730
    },
    "Álcool Etílico 70%": {
        "formula": "C2H5OH / H2O",
        "fispq_resumo": "Líquido e vapores inflamáveis (H226). Provoca irritação ocular moderada. Manter frasco bem fechado.",
        "epis": "Jaleco, luvas de nitrilo e óculos de proteção.",
        "validade_padrao_dias": 365
    },
    "Ácido Clorídrico Concentrado (HCl 37%)": {
        "formula": "HCl",
        "fispq_resumo": "CORROSIVO (H314). Provoca queimaduras graves na pele e lesões oculares graves. Pode provocar irritação respiratória (H335).",
        "epis": "Capela de exaustão, luvas de nitrilo/neoprene espessas, óculos e jaleco.",
        "validade_padrao_dias": 365
    },
    "Hidróxido de Sódio 1M (NaOH)": {
        "formula": "NaOH",
        "fispq_resumo": "CORROSIVO (H314). Provoca queimaduras severas na pele e danos oculares graves. Reação exotérmica com água.",
        "epis": "Jaleco, luvas de nitrilo e óculos de segurança contra respingos.",
        "validade_padrao_dias": 180
    },
    "Solução Tampão Fosfato 0.1M (pH 7.0)": {
        "formula": "Na2HPO4 / NaH2PO4",
        "fispq_resumo": "Composto não classificado como perigoso segundo norma GHS. Evitar contato direto prolongado.",
        "epis": "Jaleco e luvas de procedimento.",
        "validade_padrao_dias": 90
    }
}

DESTINOS_ETIQUETAS = {
    "Microtubo / Eppendorf (0.5 a 2.0 mL) [25 x 15 mm]": (25, 15),
    "Tubo Falcon 15 mL [40 x 20 mm]": (40, 20),
    "Tubo Falcon 50 mL [50 x 25 mm]": (50, 25),
    "Frasco Médio / Erlenmeyer [60 x 30 mm]": (60, 30),
    "Frasco Grande / Bancada [75 x 45 mm]": (75, 45),
}

# --- FUNÇÕES DE LIMPEZA DE TEXTO E PERSISTÊNCIA ---
def sanitize_str(txt):
    if not txt:
        return ""
    s = str(txt)
    replacements = {'&': '&amp;', '<': '&lt;', '>': '&gt;'}
    for k, v in replacements.items():
        s = s.replace(k, v)
    return s

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

# --- GERADOR DE PDF VETORIAL PARA POP ---
def gerar_pdf_pop_oficial(pop_dict):
    if REPORTLAB_DISPONIVEL:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()
        story = []

        title_style = ParagraphStyle('POPTitle', parent=styles['Heading2'], fontSize=12, leading=15, textColor=colors.HexColor('#0F172A'), bold=True)
        norm_style = ParagraphStyle('POPNorm', parent=styles['Normal'], fontSize=9.5, leading=13, textColor=colors.HexColor('#334155'))

        header_data = [
            [Paragraph(f"<b>PROCEDIMENTO OPERACIONAL PADRÃO (POP)</b>", title_style), Paragraph(f"<b>CÓDIGO:</b> {sanitize_str(pop_dict['codigo'])}", norm_style)],
            [Paragraph(f"<b>Título:</b> {sanitize_str(pop_dict['titulo'])}", norm_style), Paragraph(f"<b>Versão:</b> {pop_dict['versao']}", norm_style)],
            [Paragraph(f"<b>Elaborado por:</b> {sanitize_str(pop_dict.get('autor', 'N/A'))}", norm_style), Paragraph(f"<b>Status:</b> {pop_dict.get('status', 'Aprovado')}", norm_style)]
        ]
        t_header = Table(header_data, colWidths=[360, 180])
        t_header.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F1F5F9')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('PADDING', (0,0), (-1,-1), 7),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(t_header)
        story.append(Spacer(1, 15))

        sections = [
            ("1. OBJETIVO", pop_dict.get("objetivo", "")),
            ("2. O QUE FAZER / PROCEDIMENTO (PASSO A PASSO)", pop_dict.get("passos", "")),
            ("3. MATERIAIS E EQUIPAMENTOS", pop_dict.get("materiais", "")),
            ("4. SEGURANÇA E EPIs", pop_dict.get("seguranca", "")),
            ("5. REFERÊNCIAS BIBLIOGRÁFICAS", pop_dict.get("referencias", "-")),
        ]

        sec_title_style = ParagraphStyle('SecTitle', parent=styles['Heading2'], fontSize=11, leading=14, textColor=colors.HexColor('#0E7490'), bold=True)

        for title, content in sections:
            story.append(Paragraph(title, sec_title_style))
            story.append(Spacer(1, 4))
            content_p = sanitize_str(content).replace('\n', '<br/>')
            story.append(Paragraph(content_p, norm_style))
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

# --- GERADOR DE PDF VETORIAL PARA PEDIDOS DE REQUISÇÃO (MÚLTIPLOS ITENS + LINK) ---
def gerar_pdf_solicitacao_item(solicitacao, nome_grupo, lider_nome, colider_nome):
    urgente_bool = solicitacao.get("urgente", False)
    urgente_str = "🚨 URGENTE" if urgente_bool else "📦 FLUXO PADRÃO (REGULAR)"
    razao_urgencia = solicitacao.get("razao_urgencia", "Não informada")
    solicitante_nome = solicitacao.get("solicitante", "Não informado")
    data_sol = solicitacao.get("data_solicitacao", datetime.now().strftime("%d/%m/%Y"))

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

        title_group_style = ParagraphStyle('GrpHeaderTitle', parent=styles['Normal'], fontSize=13, leading=16, textColor=colors.white, bold=True)
        sub_group_style = ParagraphStyle('GrpHeaderSub', parent=styles['Normal'], fontSize=9.5, leading=12, textColor=colors.HexColor('#E0F2FE'))
        
        lbl_style = ParagraphStyle('LblStyle', parent=styles['Normal'], fontSize=8.5, leading=11, textColor=colors.HexColor('#64748B'), bold=True)
        val_style = ParagraphStyle('ValStyle', parent=styles['Normal'], fontSize=9, leading=12, textColor=colors.HexColor('#0F172A'))
        urg_box_style = ParagraphStyle('UrgBox', parent=styles['Normal'], fontSize=9.5, leading=13, textColor=colors.HexColor('#991B1B') if urgente_bool else colors.HexColor('#15803D'), bold=True)
        
        tbl_hdr_style = ParagraphStyle('TblHdr', parent=styles['Normal'], fontSize=8.5, leading=11, textColor=colors.white, bold=True)
        tbl_cell_style = ParagraphStyle('TblCell', parent=styles['Normal'], fontSize=8.5, leading=11, textColor=colors.HexColor('#1E293B'))

        # CABEÇALHO DO GRUPO
        header_banner_data = [
            [
                Paragraph(f"GRUPO DE PESQUISA: {sanitize_str(nome_grupo).upper()}", title_group_style),
                Paragraph(f"<b>PEDIDO:</b> REQ-{solicitacao.get('id', 1):04d}<br/><b>DATA:</b> {data_sol}", sub_group_style)
            ]
        ]
        t_banner = Table(header_banner_data, colWidths=[380, 160])
        t_banner.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#0E7490')),
            ('PADDING', (0,0), (-1,-1), 8),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ]))
        story.append(t_banner)
        story.append(Spacer(1, 10))

        info_data = [
            [Paragraph("SOLICITANTE RESPONSÁVEL", lbl_style), Paragraph("LIDERANÇA DO GRUPO", lbl_style), Paragraph("STATUS DO PEDIDO", lbl_style)],
            [Paragraph(f"<b>{sanitize_str(solicitante_nome)}</b>", val_style), Paragraph(f"{sanitize_str(lider_nome)} / {sanitize_str(colider_nome)}", val_style), Paragraph(f"<b>{solicitacao.get('status', 'Pendente')}</b>", val_style)],
        ]
        t_info = Table(info_data, colWidths=[200, 200, 140])
        t_info.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#F1F5F9')),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t_info)
        story.append(Spacer(1, 8))

        urg_color_bg = colors.HexColor('#FEE2E2') if urgente_bool else colors.HexColor('#DCFCE7')
        urg_data = [
            [Paragraph(urgente_str, urg_box_style)],
            [Paragraph(f"<b>Justificativa / Motivo:</b> {sanitize_str(razao_urgencia)}", val_style)]
        ]
        t_urg = Table(urg_data, colWidths=[540])
        t_urg.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), urg_color_bg),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#FCA5A5') if urgente_bool else colors.HexColor('#86EFAC')),
            ('PADDING', (0,0), (-1,-1), 7),
        ]))
        story.append(t_urg)
        story.append(Spacer(1, 12))

        story.append(Paragraph("<b>RELAÇÃO DE ITENS E MATERIAIS SOLICITADOS:</b>", ParagraphStyle('SecHead', parent=styles['Heading3'], fontSize=10, textColor=colors.HexColor('#0F172A'), bold=True)))
        story.append(Spacer(1, 5))

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
            espec_text = sanitize_str(item_obj.get('especificacoes', '-'))
            link_text = sanitize_str(item_obj.get('link_preferencia', ''))
            
            detail_p = f"• {espec_text}"
            if link_text and str(link_text).strip():
                detail_p += f"<br/>• 🔗 <u>Link: {link_text[:50]}...</u>" if len(link_text) > 50 else f"<br/>• 🔗 <u>Link: {link_text}</u>"

            table_items_content.append([
                Paragraph(str(idx_i), tbl_cell_style),
                Paragraph(f"<b>{sanitize_str(item_obj.get('item', '-'))}</b>", tbl_cell_style),
                Paragraph(sanitize_str(item_obj.get('categoria_item', 'Geral')), tbl_cell_style),
                Paragraph(f"<b>{sanitize_str(item_obj.get('quantidade', '-'))}</b>", tbl_cell_style),
                Paragraph(detail_p, tbl_cell_style)
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
        story.append(Spacer(1, 30))

        sign_data = [
            [Paragraph("____________________________________________", val_style), Paragraph("____________________________________________", val_style)],
            [Paragraph(f"<b>{sanitize_str(solicitante_nome)}</b><br/>Solicitante Responsável", val_style), Paragraph(f"<b>{sanitize_str(lider_nome)}</b><br/>Liderança do Grupo", val_style)]
        ]
        t_sign = Table(sign_data, colWidths=[270, 270])
        t_sign.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('PADDING', (0,0), (-1,-1), 4)]))
        story.append(t_sign)

        doc.build(story)
        return buffer.getvalue()
    else:
        page = Image.new("RGB", (612, 792), "white")
        draw = ImageDraw.Draw(page)
        draw.text((30, 35), f"GRUPO DE PESQUISA: {nome_grupo.upper()}", fill="black")
        buf = BytesIO()
        page.save(buf, format="PDF")
        return buf.getvalue()

# --- GERADOR DE ETIQUETAS DE FRASCO DE ALTA RESOLUÇÃO (DPI 300) ---
def gerar_pdf_etiquetas_frasco(nome_amostra, id_amostra, data_prod, validade_txt, responsavel, fispq_txt, mm_w=40, mm_h=20, quantidade=12, qr_img_pil=None, grupo_nome=""):
    dpi = 300
    px_mm = dpi / 25.4
    
    page_w_px = int(210 * px_mm)
    page_h_px = int(297 * px_mm)

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

    qr_side_px = min(int(lbl_h_px * 0.82), int(lbl_w_px * 0.36))
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

        draw.rectangle([x, y, x + lbl_w_px, y + lbl_h_px], outline="#CBD5E1", width=2)

        if qr_resized:
            qr_x = x + int(2 * px_mm)
            qr_y = y + (lbl_h_px - qr_side_px) // 2
            current_page.paste(qr_resized, (qr_x, qr_y))
            text_x = qr_x + qr_side_px + int(2 * px_mm)
        else:
            text_x = x + int(2 * px_mm)

        text_y = y + int(1.8 * px_mm)

        draw.text((text_x, text_y), f"🧪 {nome_amostra[:22]}", fill="#0F172A")
        text_y += int(3.5 * px_mm)
        draw.text((text_x, text_y), f"ID: {id_amostra} | {grupo_nome[:14]}", fill="#334155")
        text_y += int(3.2 * px_mm)
        draw.text((text_x, text_y), f"🏭 Prod: {data_prod} | ⏳ Val: {validade_txt}", fill="#334155")
        text_y += int(3.2 * px_mm)
        draw.text((text_x, text_y), f"👤 Resp: {responsavel[:18]}", fill="#475569")
        
        if fispq_txt and mm_h >= 20:
            text_y += int(3.2 * px_mm)
            draw.text((text_x, text_y), f"⚠️ {fispq_txt[:26]}...", fill="#991B1B")

        x += lbl_w_px + spacing_x

    pages.append(current_page)

    pdf_buffer = BytesIO()
    if len(pages) == 1:
        pages[0].save(pdf_buffer, format="PDF", resolution=float(dpi))
    else:
        pages[0].save(pdf_buffer, format="PDF", resolution=float(dpi), save_all=True, append_images=pages[1:])

    return pdf_buffer.getvalue()

# --- INICIALIZAÇÃO ÚNICA DA SESSÃO ---
usuario_admin_padrao = [{
    "nome": "Gabriela Mendes Farias Matos", "usuario": "admin", "senha": "123", "categoria": "Mestrado",
    "vinculo": "UFRRJ - Química Industrial", "telefone": "(21) 99677-8065", "email": "gbsmtsm@ufrrj.br",
    "status": "Aprovado", "is_admin": True, "orientador": "Eliane Pereira Cipolatti"
}]

integrantes_padrao = [
    {"Nome": "Eliane Pereira Cipolatti", "Categoria": "Orientador", "Vínculo": "UFRRJ", "Telefone": "-", "Email": "eliane@ufrrj.br", "Situação": "Ativo"},
    {"Nome": "Gabriela Mendes Farias Matos", "Categoria": "Mestrado", "Vínculo": "UFRRJ", "Telefone": "-", "Email": "gbsmtsm@ufrrj.br", "Situação": "Ativo"}
]

grupos_padrao = [{
    "id": 1, "nome": "Biocatalise & Tecnologia Enzimática", "lider": "Eliane Pereira Cipolatti", "colider": "Gabriela Mendes Farias Matos",
    "status": "Aprovado", "solicitacoes_itens": []
}]

if "usuarios" not in st.session_state:
    st.session_state.usuarios = carregar_dados(ARQUIVO_USUARIOS, usuario_admin_padrao)
if "integrantes" not in st.session_state:
    st.session_state.integrantes = carregar_dados(ARQUIVO_INTEGRANTES, integrantes_padrao)
if "agenda" not in st.session_state:
    st.session_state.agenda = carregar_dados(ARQUIVO_AGENDA, [])
if "avisos_db" not in st.session_state:
    st.session_state.avisos_db = carregar_dados(ARQUIVO_AVISOS, [])
if "arquivos_db" not in st.session_state:
    st.session_state.arquivos_db = carregar_dados(ARQUIVO_ARQUIVOS, [])
if "pastas_db" not in st.session_state:
    st.session_state.pastas_db = carregar_dados(ARQUIVO_PASTAS, [{"nome": "Geral", "descricao": "Arquivos Gerais do Laboratório", "status": "Aprovado"}])
if "pops_db" not in st.session_state:
    st.session_state.pops_db = carregar_dados(ARQUIVO_POPS, [])
if "grupos_db" not in st.session_state:
    st.session_state.grupos_db = carregar_dados(ARQUIVO_GRUPOS, grupos_padrao)
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

if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = st.session_state.usuarios[0]

usuario_atual = st.session_state.usuario_logado
is_admin = usuario_atual.get("is_admin", False)

# --- NAVEGAÇÃO DA SIDEBAR ---
st.sidebar.markdown("### 🧪 Central de Pesquisa")

def render_menu_item(chave, rotulo):
    is_selected = (st.session_state.get("menu_selecionado") == chave)
    if st.sidebar.button(rotulo, key=f"nav_btn_{chave}", use_container_width=True, type="primary" if is_selected else "secondary"):
        st.session_state.menu_selecionado = chave
        st.rerun()

st.sidebar.markdown('<div class="sidebar-section">PAINEL PRINCIPAL</div>', unsafe_allow_html=True)
render_menu_item("🏠 Página Inicial & Avisos", "🏠 Página Inicial & Avisos")
render_menu_item("📅 Agenda & Calendário", "📅 Agenda & Calendário")

st.sidebar.markdown('<div class="sidebar-section">GESTÃO DO LABORATÓRIO</div>', unsafe_allow_html=True)
render_menu_item("👥 Equipe", "👥 Equipe")
render_menu_item("🔬 Grupo de Pesquisa", "🔬 Grupo de Pesquisa")

st.sidebar.markdown('<div class="sidebar-section">CONHECIMENTO & FERRAMENTAS</div>', unsafe_allow_html=True)
render_menu_item("📁 Repositório de Arquivos", "📁 Repositório de Arquivos")
render_menu_item("🏷️ Gerar QR Code de Amostras", "🏷️ Gerar QR Code de Amostras")
render_menu_item("📝 Criador de POP", "📝 Criador de POP")

menu_selecionado = st.session_state.menu_selecionado

# --- 1. PÁGINA INICIAL ---
if menu_selecionado == "🏠 Página Inicial & Avisos":
    st.title("🏠 Painel Geral de Pesquisa")
    st.caption(f"Bem-vindo(a), **{usuario_atual['nome']}**!")

    k1, k2, k3 = st.columns(3)
    with k1: st.markdown(f'<div class="kpi-card kpi-card-blue"><div><div class="kpi-val">{len(st.session_state.integrantes)}</div><div class="kpi-label">Integrantes</div></div></div>', unsafe_allow_html=True)
    with k2: st.markdown(f'<div class="kpi-card kpi-card-green"><div><div class="kpi-val">{len(st.session_state.grupos_db)}</div><div class="kpi-label">Grupos de Pesquisa</div></div></div>', unsafe_allow_html=True)
    with k3: st.markdown(f'<div class="kpi-card kpi-card-purple"><div><div class="kpi-val">{len(st.session_state.pops_db)}</div><div class="kpi-label">POPs Cadastrados</div></div></div>', unsafe_allow_html=True)

# --- 2. AGENDA & CALENDÁRIO ---
elif menu_selecionado == "📅 Agenda & Calendário":
    st.title("📅 Agenda & Calendário de Atividades")
    st.info("Organize aqui os compromissos, ensaios e reuniões do laboratório.")

# --- 3. EQUIPE ---
elif menu_selecionado == "👥 Equipe":
    st.title("👥 Integrantes do Laboratório")
    st.dataframe(pd.DataFrame(st.session_state.integrantes), use_container_width=True)

# --- 4. GRUPO DE PESQUISA (SOLICITAÇÕES DE MÚLTIPLOS ITENS + PDF) ---
elif menu_selecionado == "🔬 Grupo de Pesquisa":
    st.title("🔬 Área de Grupos de Pesquisa")

    grupos = st.session_state.grupos_db
    if not grupos:
        st.info("Nenhum grupo ativo.")
    else:
        grupo_ativo = grupos[0]
        st.subheader(f"🔬 Grupo: {grupo_ativo['nome']}")

        tab1, tab2 = st.tabs(["📋 Fila de Requisições de Compra", "➕ Criar Nova Requisição (Múltiplos Itens)"])

        with tab1:
            solicitacoes = grupo_ativo.get("solicitacoes_itens", [])
            if solicitacoes:
                for idx_sol, sol in enumerate(solicitacoes):
                    st.markdown(f"**Pedido REQ-{sol.get('id', idx_sol):04d}** - Solicitante: {sol.get('solicitante')} | Data: {sol.get('data_solicitacao')}")
                    pdf_bytes = gerar_pdf_solicitacao_item(sol, grupo_ativo['nome'], grupo_ativo.get('lider', '-'), grupo_ativo.get('colider', '-'))
                    st.download_button("📄 Baixar PDF do Pedido (Alta Resolução)", pdf_bytes, f"Requisicao_REQ{sol.get('id', idx_sol)}.pdf", "application/pdf", key=f"dl_sol_{idx_sol}")
                    st.markdown("---")
            else:
                st.info("Nenhuma requisição realizada ainda.")

        with tab2:
            st.markdown("#### 🛒 Carrinho do Pedido de Compra")
            with st.form("form_add_item_carrinho"):
                c1, c2, c3 = st.columns([2, 1, 1])
                with c1: it_nome = st.text_input("Item / Reagente / Vidraria *")
                with c2: it_cat = st.selectbox("Categoria", ["Reagentes", "Vidrarias", "Papel de Filtro", "Consumíveis", "Outros"])
                with c3: it_qtd = st.text_input("Quantidade *", "2 Frascos de 1L")
                it_espec = st.text_input("Especificações Técnicas (Pureza, Marca, etc.)", "Grau P.A. (Pureza >= 99.5%)")
                it_link = st.text_input("🔗 Link de Preferência de Compra (Opcional)", placeholder="https://...")
                
                if st.form_submit_button("🛒 Adicionar Item ao Pedido"):
                    if it_nome and it_qtd:
                        st.session_state.itens_carrinho_req.append({"item": it_nome, "categoria_item": it_cat, "quantidade": it_qtd, "especificacoes": it_espec, "link_preferencia": it_link})
                        st.success(f"Item '{it_nome}' adicionado!")
                        st.rerun()

            if st.session_state.itens_carrinho_req:
                st.markdown("##### 📋 Itens Atual no Carrinho:")
                st.dataframe(pd.DataFrame(st.session_state.itens_carrinho_req), use_container_width=True)
                
                with st.form("form_fechar_pedido"):
                    is_urg = st.checkbox("🚨 PEDIDO URGENTE?")
                    raz_urg = st.text_input("Justificativa / Motivo do Pedido *", "Necessário para ensaios da próxima semana.")
                    if st.form_submit_button("🚀 Finalizar Pedido e Gerar Requisição PDF", type="primary"):
                        novo_id = len(grupo_ativo.get("solicitacoes_itens", [])) + 1
                        if "solicitacoes_itens" not in grupo_ativo: grupo_ativo["solicitacoes_itens"] = []
                        grupo_ativo["solicitacoes_itens"].append({
                            "id": novo_id, "urgente": is_urg, "razao_urgencia": raz_urg,
                            "solicitante": usuario_atual["nome"], "data_solicitacao": datetime.now().strftime("%d/%m/%Y"),
                            "status": "Pendente", "itens": list(st.session_state.itens_carrinho_req)
                        })
                        salvar_dados(ARQUIVO_GRUPOS, st.session_state.grupos_db)
                        st.session_state.itens_carrinho_req = []
                        st.success("Pedido gerado com sucesso!")
                        st.rerun()

# --- 5. REPOSITÓRIO DE ARQUIVOS (ESTILO GOOGLE DRIVE) ---
elif menu_selecionado == "📁 Repositório de Arquivos":
    st.title("📁 Central de Arquivos & Documentos (Estilo Google Drive)")

    pastas = st.session_state.pastas_db

    if st.session_state.pasta_aberta_drive is None:
        st.subheader("📂 Pastas do Laboratório")
        cols_p = st.columns(3)
        for idx, pst in enumerate(pastas):
            nome_p = pst["nome"]
            qtd_files = sum(1 for a in st.session_state.arquivos_db if str(a.get("pasta", "")).strip().lower() == str(nome_p).strip().lower())
            with cols_p[idx % 3]:
                st.markdown(
                    f"""
                    <div class="drive-folder-card">
                        <h3 style="margin:0; font-size:1.1rem;">📁 {nome_p}</h3>
                        <p style="margin:4px 0; color:#64748B; font-size:0.85rem;">{pst.get('descricao','Sem descrição')}</p>
                        <span style="background-color:#E2E8F0; padding:2px 8px; border-radius:12px; font-size:0.75rem; font-weight:bold;">📄 {qtd_files} arquivo(s)</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                if st.button(f"📂 Abrir {nome_p}", key=f"open_f_{idx}", use_container_width=True):
                    st.session_state.pasta_aberta_drive = nome_p
                    st.rerun()
    else:
        nome_pasta_atual = st.session_state.pasta_aberta_drive
        c_top1, c_top2 = st.columns([3, 1])
        with c_top1: st.subheader(f"📁 Drive > {nome_pasta_atual}")
        with c_top2:
            if st.button("⬅️ Voltar", use_container_width=True):
                st.session_state.pasta_aberta_drive = None
                st.rerun()

        st.markdown("---")
        arqs_pasta = [a for a in st.session_state.arquivos_db if str(a.get("pasta", "")).strip().lower() == str(nome_pasta_atual).strip().lower()]

        if arqs_pasta:
            for doc in arqs_pasta:
                st.markdown(f"📄 **{doc['titulo']}** - *Enviado por {doc.get('autor')} em {doc.get('data')}*")
                b64_str = doc.get("conteudo_b64") or doc.get("b64")
                if b64_str:
                    bytes_f = base64.b64decode(b64_str)
                    st.download_button(f"⬇️ Baixar {doc.get('nome_original', 'arquivo.pdf')}", bytes_f, doc.get('nome_original', 'arquivo.pdf'), key=f"dl_doc_{doc['id']}")
                st.markdown("---")
        else:
            st.info("Nenhum arquivo nesta pasta.")

        with st.expander("📤 Upload de Novo Arquivo"):
            with st.form("form_upload_drive"):
                tit_file = st.text_input("Título do Documento *")
                file_up = st.file_uploader("Selecione o Arquivo *")
                if st.form_submit_button("📤 Enviar para o Drive", type="primary"):
                    if tit_file and file_up:
                        b64_f = base64.b64encode(file_up.getvalue()).decode("utf-8")
                        novo_id = len(st.session_state.arquivos_db) + 1
                        st.session_state.arquivos_db.append({
                            "id": novo_id, "titulo": tit_file.strip(), "pasta": nome_pasta_atual,
                            "nome_original": file_up.name, "conteudo_b64": b64_f,
                            "autor": usuario_atual["nome"], "data": datetime.now().strftime("%d/%m/%Y"), "status": "Aprovado"
                        })
                        salvar_dados(ARQUIVO_ARQUIVOS, st.session_state.arquivos_db)
                        st.success("Arquivo enviado com sucesso!")
                        st.rerun()

# --- 6. GERADOR DE ETIQUETAS DE FRASCO (PRODUÇÃO / FISPQ / VALIDADE) ---
elif menu_selecionado == "🏷️ Gerar QR Code de Amostras":
    st.title("🏷️ Gerador de Etiquetas & QR Code de Amostras")
    st.caption("Gere etiquetas de alta resolução com QR Code para frascos e microtubos.")

    col_f, col_p = st.columns([1.2, 1])

    with col_f:
        st.subheader("Configurar Etiqueta")
        reagente_pre = st.selectbox("Reagente / Solução", list(REAGENTES_PREDEFINIDOS_FISPQ.keys()))
        info_fispq = REAGENTES_PREDEFINIDOS_FISPQ[reagente_pre]

        id_amostra_f = f"REAG-{datetime.now().strftime('%Y%m%d')}-{st.session_state.seq_amostra:03d}"
        st.text_input("ID da Amostra", value=id_amostra_f, disabled=True)

        grupo_origem = st.selectbox("Grupo de Pesquisa", [g["nome"] for g in st.session_state.grupos_db])
        data_prod = st.date_input("🏭 Data de Produção", datetime.now().date())

        tipo_validade = st.radio("⏳ Validade", ["Data Específica", "Tempo Indeterminado"], horizontal=True)
        if tipo_validade == "Data Específica":
            dt_val = st.date_input("Data de Validade", datetime.now().date() + pd.Timedelta(days=info_fispq["validade_padrao_dias"]))
            validade_str = dt_val.strftime("%d/%m/%Y")
        else:
            validade_str = "Indeterminada"

        pesquisador_resp = st.text_input("👤 Responsável", value=usuario_atual["nome"])
        fispq_editada = st.text_area("⚠️ FISPQ (Frases de Perigo)", value=info_fispq["fispq_resumo"], height=70)

        tam_frasco = st.selectbox("Tamanho do Frasco", list(DESTINOS_ETIQUETAS.keys()), index=1)
        mm_w, mm_h = DESTINOS_ETIQUETAS[tam_frasco]
        qtd_imp = st.number_input("Quantidade na Folha A4", min_value=1, max_value=100, value=12)

    with col_p:
        st.subheader("👁️ Pré-visualização da Etiqueta")
        
        conteudo_qr = f"🧪 REAGENTE/SOLUÇÃO\n• Nome: {reagente_pre}\n• ID: {id_amostra_f}\n• Grupo: {grupo_origem}\n• Produção: {data_prod.strftime('%d/%m/%Y')}\n• Validade: {validade_str}\n• Resp: {pesquisador_resp}\n⚠️ FISPQ: {fispq_editada}"

        if QRCODE_DISPONIVEL:
            img_qr = qrcode.make(conteudo_qr)
            buf_qr = BytesIO()
            img_qr.save(buf_qr, format="PNG")
            st.image(buf_qr.getvalue(), caption="QR Code Isolado", width=160)

            pdf_etiquetas = gerar_pdf_etiquetas_frasco(
                nome_amostra=reagente_pre, id_amostra=id_amostra_f,
                data_prod=data_prod.strftime("%d/%m/%Y"), validade_txt=validade_str,
                responsavel=pesquisador_resp, fispq_txt=fispq_editada,
                mm_w=mm_w, mm_h=mm_h, quantidade=qtd_imp, qr_img_pil=img_qr, grupo_nome=grupo_origem
            )

            st.download_button(f"📄 Baixar PDF ({qtd_imp}x Etiquetas Vetoriais)", pdf_etiquetas, f"Etiquetas_{id_amostra_f}.pdf", "application/pdf", type="primary", use_container_width=True)

# --- 7. CRIADOR DE POP ---
elif menu_selecionado == "📝 Criador de POP":
    st.title("📝 Procedimentos Operacionais Padrão (POPs)")

    col_form, col_prev = st.columns([1.1, 1])

    with col_form:
        st.subheader("➕ Formulário do POP")
        tit_pop = st.text_input("Título do POP *", "Operação do Espectrofotômetro")
        cod_pop = gerar_codigo_pop(tit_pop)
        
        obj_pop = st.text_area("1. Objetivo *", "Padronizar o procedimento no laboratório.")
        passos_pop = st.text_area("2. O que Fazer / Passo a Passo *", "1. Ligar o equipamento.\n2. Calibrar o branco.\n3. Ler amostras.")
        mat_pop = st.text_area("3. Materiais e Equipamentos", "Cubetas, tampões e amostras.")
        seg_pop = st.text_area("4. Segurança & EPIs", "Jaleco, luvas e óculos de proteção.")

        if st.button("💾 Salvar POP e Gerar Oficial", type="primary"):
            if tit_pop and obj_pop and passos_pop:
                novo_pop = {
                    "codigo": cod_pop, "titulo": tit_pop, "versao": 1,
                    "objetivo": obj_pop, "passos": passos_pop, "materiais": mat_pop,
                    "seguranca": seg_pop, "autor": usuario_atual["nome"], "status": "Aprovado"
                }
                st.session_state.pops_db.append(novo_pop)
                salvar_dados(ARQUIVO_POPS, st.session_state.pops_db)
                st.success(f"POP {cod_pop} salvo com sucesso!")
                st.rerun()

    with col_prev:
        st.subheader("👁️ Pré-visualização")
        st.markdown(
            f"""
            <div class="pop-preview-card">
                <h3>📝 {tit_pop if tit_pop else 'Título do POP'}</h3>
                <small><b>CÓDIGO:</b> {cod_pop} | <b>Autor:</b> {usuario_atual['nome']}</small>
                <hr/>
                <p><b>1. Objetivo:</b><br/>{obj_pop}</p>
                <p><b>2. O Que Fazer (Passo a Passo):</b><br/>{passos_pop.replace(chr(10), '<br/>')}</p>
                <p><b>3. Materiais:</b><br/>{mat_pop}</p>
                <p><b>4. Segurança:</b><br/>{seg_pop}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        pop_temp = {"codigo": cod_pop, "titulo": tit_pop, "versao": 1, "objetivo": obj_pop, "passos": passos_pop, "materiais": mat_pop, "seguranca": seg_pop, "autor": usuario_atual["nome"]}
        pdf_pop_bytes = gerar_pdf_pop_oficial(pop_temp)
        st.download_button("📄 Baixar PDF do POP", pdf_pop_bytes, f"{cod_pop}.pdf", "application/pdf", use_container_width=True)
