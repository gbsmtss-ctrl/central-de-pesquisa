import json
import os
from io import BytesIO
from PIL import Image, ImageDraw
import qrcode

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    REPORTLAB_DISPONIVEL = True
except ImportError:
    REPORTLAB_DISPONIVEL = False

ARQUIVO_INTEGRANTES = "integrantes.json"
ARQUIVO_AGENDA = "agenda.json"
ARQUIVO_USUARIOS = "usuarios.json"
ARQUIVO_ARQUIVOS = "arquivos.json"
ARQUIVO_PASTAS = "pastas.json"
ARQUIVO_POPS = "pops.json"
ARQUIVO_AVISOS = "avisos.json"
ARQUIVO_GRUPOS = "grupos_pesquisa.json"

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
        draw.text((40, 40), f"POP - {pop_dict['codigo']} - {pop_dict['titulo']}", fill="black")
        buf = BytesIO()
        page.save(buf, format="PDF")
        return buf.getvalue()
