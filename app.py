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

# --- ESTILIZAÇÃO VISUAL ---
st.markdown(
    """
    <style>
    .stApp {
        background-color: #F8FAFC;
    }
    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E2E8F0;
    }
    /* Estilização para botões do menu lateral alinhados à esquerda */
    [data-testid="stSidebar"] div.stButton > button {
        text-align: left !important;
        justify-content: flex-start !important;
        padding-left: 12px !important;
        width: 100% !important;
        margin-bottom: 2px !important;
    }
    h1, h2, h3 {
        color: #0F172A !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .sidebar-section {
        font-size: 0.72rem;
        font-weight: 800;
        color: #94A3B8;
        text-transform: uppercase;
        margin-top: 1.2rem;
        margin-bottom: 0.4rem;
        letter-spacing: 0.08em;
    }
    div.stButton > button:first-child {
        background-color: #2563EB;
        color: white;
        border-radius: 6px;
        border: none;
        font-weight: 600;
    }
    div.stButton > button:first-child:hover {
        background-color: #1D4ED8;
        color: white;
    }
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
        background-color: #CBD5E1;
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
        border-radius: 10px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        margin-bottom: 12px;
    }
    .aviso-card {
        background-color: #FFFFFF;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
        border-left: 5px solid #2563EB;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
    }
    .event-card {
        background-color: #FFFFFF;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
    }
    .pop-preview-card {
        background-color: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-left: 5px solid #2563EB;
        border-radius: 8px;
        padding: 18px;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    }
    .table-header {
        font-size: 0.75rem;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        padding-bottom: 8px;
        border-bottom: 1px solid #E2E8F0;
        margin-bottom: 12px;
    }
    .metric-container {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- PERSISTÊNCIA DE DADOS ---
ARQUIVO_INTEGRANTES = "integrantes.json"
ARQUIVO_AGENDA = "agenda.json"
ARQUIVO_USUARIOS = "usuarios.json"
ARQUIVO_ARQUIVOS = "arquivos.json"
ARQUIVO_PASTAS = "pastas.json"
ARQUIVO_POPS = "pops.json"
ARQUIVO_AVISOS = "avisos.json"

CATEGORIAS_PADRAO = [
    "Iniciação Científica",
    "Mestrado",
    "Doutorado",
    "Pós-Doutorado",
    "Orientador",
    "Técnico / Pesquisador",
]

CORES_GOOGLE_AGENDA = {
    "🔵 Azul (Reunião / Geral)": "#2563EB",
    "🟢 Verde (Ensaio / Experimento)": "#16A34A",
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
    },
    {
        "Nome": "Gabriela Mendes Farias Matos",
        "Categoria": "Mestrando",
        "Vínculo": "UFRRJ - Química Industrial",
        "Telefone": "(21) 99677-8065",
        "Email": "gbsmtsm@ufrrj.br",
        "DiasHorarios": "Ter e Qui - 09:00 às 18:00",
        "Lattes": "-",
        "Situação": "Ativo",
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
    },
    {
        "id": 2,
        "titulo": "🧪 Atualização dos Protocolos de POP",
        "conteudo": "Os POPs de espectrofotometria foram atualizados para a versão 2. Por favor, verifiquem no repositório.",
        "categoria": "Informativo",
        "cor": "#2563EB",
        "autor": "Eliane Pereira Cipolatti",
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
        "cor": "#2563EB",
        "descricao": "Discussão dos resultados de fermentação da semana.",
        "autor": "Gabriela Mendes Farias Matos"
    }
]

PASTAS_INICIAIS = [
    {"nome": "Geral", "descricao": "Arquivos gerais do laboratório", "criador": "admin", "status": "Aprovado"},
    {"nome": "POPs e Protocolos", "descricao": "Procedimentos Operacionais Padrão", "criador": "admin", "status": "Aprovado"},
    {"nome": "Artigos Científicos", "descricao": "Publicações e referências", "criador": "admin", "status": "Aprovado"},
    {"nome": "Manuais de Equipamentos", "descricao": "Guias de operação de máquinas", "criador": "admin", "status": "Aprovado"},
    {"nome": "FISPQ / Segurança", "descricao": "Fichas de segurança de reagentes", "criador": "admin", "status": "Aprovado"},
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
        "autor": "Eliane Pereira Cipolatti",
        "status": "Aprovado",
    }
]

def carregar_dados(arquivo, padrao):
    if os.path.exists(arquivo):
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                return json.load(f)
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
        ]

        sec_title_style = ParagraphStyle(
            'SecTitle',
            parent=styles['Heading2'],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor('#2563EB'),
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
            content_p = content.replace('\n', '<br/>')
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
        ]

        for tit, txt in secoes:
            draw.text((40, y), tit, fill="#2563EB")
            y += 20
            for line in txt.split("\n"):
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
    "categoria": "Mestrando",
    "vinculo": "UFRRJ - Química Industrial",
    "telefone": "(21) 99677-8065",
    "email": "gbsmtsm@ufrrj.br",
    "status": "Aprovado",
    "is_admin": True,
}]

# --- INICIALIZAÇÃO DE SESSÃO PERSISTENTE ---
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
            u
            for u in st.session_state.usuarios
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

# --- VALIDAÇÃO GLOBAL DE ACESSO (REVOGAÇÃO IMEDIATA AO SER EXCLUÍDO) ---
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


# --- TELA DE LOGIN, SOLICITAÇÃO DE ACESSO E RECUPERAÇÃO DE SENHA ---
if st.session_state.usuario_logado is None:
    st.title("🧪 Central de Pesquisa - Controle de Acesso ⚗️")

    aba_login, aba_cadastro, aba_recuperar = st.tabs([
        "Entrar no Sistema", 
        "Solicitar Acesso", 
        "🔑 Recuperar Senha"
    ])

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
                        st.session_state.usuarios = [
                            u for u in st.session_state.usuarios
                            if str(u.get("usuario", "")).strip().lower() != usr_clean
                            and str(u.get("nome", "")).strip().lower() != novo_nome.strip().lower()
                        ]

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
                        })
                        salvar_dados(ARQUIVO_USUARIOS, st.session_state.usuarios)

                        st.session_state.integrantes = [
                            p for p in st.session_state.integrantes
                            if str(p.get("Nome", "")).strip().lower() != novo_nome.strip().lower()
                        ]

                        st.session_state.integrantes.append({
                            "Nome": novo_nome.strip(),
                            "Categoria": nova_categoria,
                            "Vínculo": novo_vinculo.strip(),
                            "Telefone": novo_telefone.strip(),
                            "Email": novo_email.strip(),
                            "DiasHorarios": "Não informado",
                            "Lattes": "-",
                            "Situação": "Pendente",
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
                        st.success("✅ Senha redefinida com sucesso! Você já pode entrar com a nova senha na aba 'Entrar no Sistema'.")
                    else:
                        st.error("Nenhum usuário aprovado ou pendente foi encontrado com este Usuário/E-mail.")

# --- ÁREA LOGADA ---
else:
    usuario_atual = st.session_state.usuario_logado
    is_admin = usuario_atual.get("is_admin", False)

    # --- CÁLCULO DINÂMICO DE NOTIFICAÇÕES ---
    num_pend_usr = len([u for u in st.session_state.usuarios if u.get("status") == "Pendente"])
    num_pend_perfis = len([u for u in st.session_state.usuarios if u.get("pendente_atualizacao")])
    num_pend_arqs = len([a for a in st.session_state.arquivos_db if a.get("status") == "Pendente"])
    num_pend_pops = len([p for p in st.session_state.pops_db if p.get("status") == "Pendente"])
    num_pend_pastas = len([p for p in st.session_state.pastas_db if p.get("status") == "Pendente"])

    total_notif_admin = num_pend_usr + num_pend_perfis + num_pend_arqs + num_pend_pops + num_pend_pastas

    usr_atual_reg = next((u for u in st.session_state.usuarios if str(u.get("usuario")).lower() == str(usuario_atual["usuario"]).lower()), usuario_atual)
    notif_meu_perfil = 1 if usr_atual_reg.get("pendente_atualizacao") else 0

    hoje_str = datetime.now().strftime("%Y-%m-%d")
    notif_agenda_hoje = len([e for e in st.session_state.agenda if e.get("data") == hoje_str])
    notif_avisos = len(st.session_state.avisos_db)

    # --- BARRA LATERAL ORGANIZADA POR ÁREAS ---
    st.sidebar.markdown(
        """
        <div style="display: flex; align-items: center; gap: 10px; padding: 5px 0 15px 0;">
            <div style="background-color: #2563EB; color: white; border-radius: 8px; padding: 8px; font-size: 1.2rem; font-weight: bold;">
                ◆
            </div>
            <div>
                <h3 style="margin:0; font-size: 1.1rem; color: #0F172A !important;">Central de Pesquisa</h3>
                <span style="font-size: 0.75rem; color: #64748B;">Central do Laboratório</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Função auxiliar para renderizar botões da barra lateral
    def item_menu(nome_base, label_exibicao, count=0):
        is_sel = (st.session_state.menu_selecionado == nome_base)
        text_badge = f" 🔴 ({count})" if count > 0 else ""
        btn_label = f"{'▶ ' if is_sel else ''}{label_exibicao}{text_badge}"
        
        if st.sidebar.button(btn_label, key=f"btn_nav_{nome_base}", use_container_width=True, type="primary" if is_sel else "secondary"):
            st.session_state.menu_selecionado = nome_base
            st.rerun()

    # 1. PAINEL PRINCIPAL
    st.sidebar.markdown('<div class="sidebar-section">PAINEL PRINCIPAL</div>', unsafe_allow_html=True)
    item_menu("🏠 Página Inicial & Avisos", "🏠 Página Inicial & Avisos", notif_avisos)
    item_menu("📅 Agenda & Calendário", "📅 Agenda & Calendário", notif_agenda_hoje)

    # 2. GESTÃO DO LABORATÓRIO
    st.sidebar.markdown('<div class="sidebar-section">GESTÃO DO LABORATÓRIO</div>', unsafe_allow_html=True)
    item_menu("👥 Equipe", "👥 Equipe")
    item_menu("🎓 Orientados", "🎓 Orientados")
    item_menu("🕒 Presença no Laboratório", "🕒 Presença no Laboratório")

    # 3. CONHECIMENTO
    st.sidebar.markdown('<div class="sidebar-section">CONHECIMENTO</div>', unsafe_allow_html=True)
    item_menu("📁 Repositório de Arquivos", "📁 Repositório de Arquivos")
    item_menu("🏷️ Gerar QR Code de Amostras", "🏷️ Gerar QR Code de Amostras")
    item_menu("📝 Criador de POP", "📝 Criador de POP")

    # 4. CONFIGURAÇÕES
    st.sidebar.markdown('<div class="sidebar-section">CONFIGURAÇÕES</div>', unsafe_allow_html=True)
    if is_admin:
        item_menu("🛡️ Administração", "🛡️ Administração", total_notif_admin)
    item_menu("👤 Meu perfil", "👤 Meu perfil", notif_meu_perfil)

    menu_selecionado = st.session_state.menu_selecionado

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        f"""
        <div style="padding: 5px 0;">
            <div style="font-weight: bold; color: #0F172A; font-size: 0.9rem;">{usuario_atual['nome']}</div>
            <div style="font-size: 0.78rem; color: #64748B;">{'Administrador' if is_admin else 'Pesquisador'}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.sidebar.button("Sair da conta"):
        st.query_params.clear()
        st.session_state.usuario_logado = None
        st.rerun()

    # --- 0. PÁGINA INICIAL & AVISOS ---
    if menu_selecionado == "🏠 Página Inicial & Avisos":
        st.title("🏠 Painel Principal - Central de Pesquisa")
        st.caption(f"Bem-vindo(a), **{usuario_atual['nome']}**! Acompanhe os avisos e compromissos do laboratório.")

        m1, m2, m3, m4 = st.columns(4)
        m1.markdown(f"<div class='metric-container'><span style='font-size: 1.5rem; font-weight:bold; color:#2563EB;'>{len(st.session_state.integrantes)}</span><br/><span style='color:#64748B; font-size:0.85rem;'>Integrantes</span></div>", unsafe_allow_html=True)
        
        eventos_futuros = [e for e in st.session_state.agenda if e.get("data", "") >= hoje_str]
        m2.markdown(f"<div class='metric-container'><span style='font-size: 1.5rem; font-weight:bold; color:#16A34A;'>{len(eventos_futuros)}</span><br/><span style='color:#64748B; font-size:0.85rem;'>Próximos Eventos</span></div>", unsafe_allow_html=True)
        
        m3.markdown(f"<div class='metric-container'><span style='font-size: 1.5rem; font-weight:bold; color:#EA580C;'>{len(st.session_state.avisos_db)}</span><br/><span style='color:#64748B; font-size:0.85rem;'>Avisos Ativos</span></div>", unsafe_allow_html=True)
        
        pops_aprov = len([p for p in st.session_state.pops_db if p.get("status") == "Aprovado"])
        m4.markdown(f"<div class='metric-container'><span style='font-size: 1.5rem; font-weight:bold; color:#7C3AED;'>{pops_aprov}</span><br/><span style='color:#64748B; font-size:0.85rem;'>POPs Vigentes</span></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        col_left, col_right = st.columns([1.3, 1])

        with col_left:
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
                    c_hex = av.get("cor", "#2563EB")
                    st.markdown(
                        f"""
                        <div class="aviso-card" style="border-left-color: {c_hex};">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <h4 style="margin: 0; color: #0F172A;">{av['titulo']}</h4>
                                <span style="font-size: 0.75rem; background-color: #F1F5F9; padding: 2px 8px; border-radius: 10px; color: #475569; font-weight: 600;">
                                    {av.get('categoria', 'Geral')}
                                </span>
                            </div>
                            <p style="margin: 8px 0; color: #334155; font-size: 0.9rem;">{av['conteudo']}</p>
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
            st.subheader("📅 Próximas Reuniões & Compromissos")
            st.caption("Atividades agendadas no Calendário")

            eventos_ordenados = sorted(
                st.session_state.agenda,
                key=lambda x: (x.get("data", ""), x.get("hora_inicio", ""))
            )
            eventos_validos = [e for e in eventos_ordenados if e.get("data", "") >= hoje_str]

            if eventos_validos:
                for ev in eventos_validos[:5]:
                    cor_ev = ev.get("cor", "#2563EB")
                    try:
                        dt_obj = datetime.strptime(ev["data"], "%Y-%m-%d")
                        dt_formatada = dt_obj.strftime("%d/%m/%Y (%a)")
                    except Exception:
                        dt_formatada = ev.get("data", "-")

                    st.markdown(
                        f"""
                        <div class="event-card" style="border-left: 5px solid {cor_ev}; background-color: white;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <strong style="color: #0F172A; font-size: 0.95rem;">{ev['titulo']}</strong>
                                <span style="font-size: 0.75rem; font-weight: bold; color: {cor_ev};">{ev.get('tipo', 'Reunião')}</span>
                            </div>
                            <div style="font-size: 0.82rem; color: #475569; margin-top: 4px;">
                                🕒 <b>{dt_formatada}</b> das {ev.get('hora_inicio','--')} às {ev.get('hora_fim','--')}
                            </div>
                            <div style="font-size: 0.8rem; color: #64748B; margin-top: 4px;">
                                {ev.get('descricao', '')}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.info("Não há reuniões ou compromissos futuros agendados.")

    # --- 0.1 AGENDA & CALENDÁRIO ---
    elif menu_selecionado == "📅 Agenda & Calendário":
        st.title("📅 Agenda & Calendário de Atividades")
        st.caption("Organização de reuniões, uso de equipamentos e compromissos do grupo no estilo Google Agenda.")

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
                        bolinhas = "".join([f"<span style='color:{e.get('cor','#2563EB')}; font-size:1.2rem; line-height:1;'>●</span>" for e in evs_dia])
                        
                        bg_style = "background:#EFF6FF; border:1px solid #93C5FD;" if dia == datetime.now().day and mes_sel == mes_atual and ano_sel == ano_atual else "background:white; border:1px solid #E2E8F0;"
                        
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
                    cor_ev = ev.get("cor", "#2563EB")
                    dt_f = datetime.strptime(ev["data"], "%Y-%m-%d").strftime("%d/%m/%Y")
                    
                    c_ev1, c_ev2 = st.columns([4, 1])
                    with c_ev1:
                        st.markdown(
                            f"""
                            <div class="event-card" style="border-left: 6px solid {cor_ev};">
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
                        st.success("✅ Compromisso agendado com sucesso! Já está visível na Página Inicial e na Agenda.")
                        st.rerun()
                    else:
                        st.error("Informe o título do evento.")

    # --- 1. EQUIPE ---
    elif menu_selecionado == "👥 Equipe":
        st.title("Cadastro de Integrantes")

        c_busca, c_vazia = st.columns([2, 1])
        with c_busca:
            termo_busca = st.text_input("Pesquisar nome, vínculo ou curso", placeholder="Pesquisar nome, vínculo ou curso", label_visibility="collapsed")

        cat_filtro = st.selectbox("Categoria", ["Todos"] + CATEGORIAS_PADRAO, key="filtro_cat")

        if is_admin:
            with st.expander("➕ Cadastrar / Editar Integrante Manualmente"):
                with st.form("form_cad_int"):
                    f_nome = st.text_input("Nome Completo *")
                    f_cat = st.selectbox("Categoria", CATEGORIAS_PADRAO)
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
                                <div style="font-weight: 700; color: #0F172A; font-size: 0.9rem;">{nome_str}</div>
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
                        st.markdown(f"<a href='{lattes_str}' target='_blank' style='color:#2563EB; font-weight:600; text-decoration:none;'>Abrir currículo ↗</a>", unsafe_allow_html=True)
                    else:
                        st.write("-")

                with c6:
                    if sit_str == "Ativo":
                        st.markdown("<span class='badge-ativo'>Ativo</span>", unsafe_allow_html=True)
                    else:
                        st.markdown("<span class='badge-pendente'>Pendente</span>", unsafe_allow_html=True)

                with c7:
                    with st.popover("Ver ficha"):
                        st.markdown(f"### 👤 {nome_str}")
                        st.write(f"**Categoria:** {cat_str}")
                        st.write(f"**Vínculo:** {vinc_str}")
                        st.write(f"**Telefone:** {p.get('Telefone', '-')}")
                        st.write(f"**E-mail:** {email_str}")
                        st.write(f"**Horários:** {hor_str}")
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

                                st.warning(f"Integrante '{nome_str}' excluído com sucesso! Acesso revogado.")
                                st.rerun()

                st.markdown("<hr style='margin: 8px 0; border: none; border-top: 1px solid #F1F5F9;'/>", unsafe_allow_html=True)
        else:
            st.info("Nenhum integrante encontrado.")

    # --- 2. ORIENTADOS ---
    elif menu_selecionado == "🎓 Orientados":
        st.title("🎓 Orientados e Alunos")
        st.caption("Acompanhamento de alunos e projetos de orientação.")

        orientados = [
            p for p in st.session_state.integrantes
            if p.get("Categoria") in ["Iniciação Científica", "Mestrado", "Doutorado", "Pós-Doutorado"]
        ]

        if orientados:
            df_or = pd.DataFrame(orientados)
            cols_desejadas = ["Nome", "Categoria", "Vínculo", "Email", "Situação"]

            for col in cols_desejadas:
                if col not in df_or.columns:
                    if col == "Vínculo" and "Vinculo" in df_or.columns:
                        df_or["Vínculo"] = df_or["Vinculo"]
                    else:
                        df_or[col] = "-"

            st.dataframe(df_or[cols_desejadas], use_container_width=True)
        else:
            st.info("Nenhum orientado cadastrado no momento.")

    # --- 3. PRESENÇA NO LABORATÓRIO ---
    elif menu_selecionado == "🕒 Presença no Laboratório":
        st.title("🕒 Presença no Laboratório")
        st.caption("Escala e horários de presença dos pesquisadores.")

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
                                <h3 style="margin:0; font-size: 1.2rem; color:#0F172A;">📁 {nome_p}</h3>
                                <p style="margin: 5px 0; color: #64748B; font-size: 0.85rem;">{desc_p}</p>
                                <span style="background-color: #E2E8F0; padding: 2px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: bold; color: #334155;">
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
                                    <h4 style="margin:0; color:#2563EB;">📄 {doc['titulo']}</h4>
                                    <p style="margin:4px 0; color:#555;"><b>Enviado por:</b> {doc.get('autor', 'Desconhecido')} em {doc.get('data', '-')}</p>
                                    <p style="margin:4px 0; color:#666;"><i>{doc.get('descricao', '')}</i></p>
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
                                    with st.popover("🔄 Anexar / Reenviar arquivo original"):
                                        novo_arq = st.file_uploader("Selecione o arquivo para salvar neste registro", key=f"fix_up_{doc['id']}")
                                        if st.button("Salvar Ficheiro", key=f"btn_fix_up_{doc['id']}"):
                                            if novo_arq:
                                                doc["conteudo_b64"] = base64.b64encode(novo_arq.getvalue()).decode("utf-8")
                                                doc["nome_original"] = novo_arq.name
                                                doc["mime_type"] = novo_arq.type
                                                salvar_dados(ARQUIVO_ARQUIVOS, st.session_state.arquivos_db)
                                                st.success("Arquivo anexado com sucesso!")
                                                st.rerun()

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
                    if is_admin:
                        st.success("✅ Documento publicado!")
                    else:
                        st.success("✅ Documento enviado para aprovação do Administrador!")

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
                    if is_admin:
                        st.success("Pasta criada!")
                    else:
                        st.success("Solicitação de pasta enviada para aprovação!")
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

    # --- 6. CRIADOR E GESTÃO DE POPS ---
    elif menu_selecionado == "📝 Criador de POP":
        st.title("📝 Procedimentos Operacionais Padrão (POPs)")

        aba_pops_view, aba_pop_form = st.tabs([
            "📚 POPs Cadastrados e Prévias",
            "➕ Criar / Atualizar POP",
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
                                    <h3 style="margin: 0; color: #0F172A;">📝 {pop['titulo']}</h3>
                                    <span style="background-color: #DBEAFE; color: #1E40AF; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 0.85rem;">
                                        {pop['codigo']} | v{pop['versao']}
                                    </span>
                                </div>
                                <hr style="margin: 10px 0; border: none; border-top: 1px solid #E2E8F0;" />
                                <p style="margin: 4px 0;"><b>1. Objetivo:</b> {pop.get('objetivo', '-')}</p>
                                <p style="margin: 4px 0;"><b>2. Materiais & Equipamentos:</b> {pop.get('materiais', '-')}</p>
                                <p style="margin: 4px 0;"><b>3. Passo a Passo:</b> {pop.get('passos', '-').replace(chr(10), ' | ')}</p>
                                <p style="margin: 4px 0;"><b>4. Segurança / EPIs:</b> {pop.get('seguranca', '-')}</p>
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
                            if st.button("📂 Transferir para Repositório de Arquivos", key=f"trans_pop_{idx}"):
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
                                st.success("✅ POP publicado diretamente na pasta 'POPs e Protocolos' da Central de Arquivos!")

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

            modo_criacao = st.radio("Escolha a Ação", ["Criar Novo POP", "Atualizar POP Existente"], horizontal=True)

            tit_selecionado = ""
            versao_calculada = 1

            if modo_criacao == "Atualizar POP Existente":
                pops_existentes = [p["titulo"] for p in st.session_state.pops_db]
                if pops_existentes:
                    pop_sel_tit = st.selectbox("Selecione o POP que deseja Atualizar", pops_existentes)
                    pop_existente = next((p for p in st.session_state.pops_db if p["titulo"] == pop_sel_tit), None)
                    if pop_existente:
                        tit_selecionado = pop_existente["titulo"]
                        versao_calculada = pop_existente.get("versao", 1) + 1
                        st.info(f"ℹ️ Atualizando o POP existente. Esta ação criará a **Versão {versao_calculada}**.")
                else:
                    st.warning("Nenhum POP cadastrado para atualizar. Alterne para 'Criar Novo POP'.")

            else:
                opcoes_titulos_pop = POPS_PADRAO + ["✍️ Outro (Digitar manualmente)"]
                sel_pop_pre = st.selectbox("Selecione um Título Padrão ou Digite Manualmente", opcoes_titulos_pop)

                if sel_pop_pre == "✍️ Outro (Digitar manualmente)":
                    tit_selecionado = st.text_input("Digite o Título do POP *", "")
                else:
                    tit_selecionado = sel_pop_pre

            cod_auto = gerar_codigo_pop(tit_selecionado if tit_selecionado else "POP", versao_calculada)

            st.write(f"**Código / ID do POP (Gerado Automaticamente):** `{cod_auto}`")

            with st.form("form_pop"):
                obj_pop = st.text_area("1. Objetivo *", height=80, value="Padronizar o procedimento no laboratório.")
                mat_pop = st.text_area("2. Materiais & Equipamentos *", height=80, value="Equipamentos de proteção individual, reagentes e vidrarias.")
                passos_pop = st.text_area("3. Procedimento / Passo a Passo *", height=120, value="1. Ligar o equipamento.\n2. Calibrar conforme instrução.\n3. Executar o ensaio.")
                sec_pop = st.text_area("4. Segurança & EPIs *", height=80, value="Jaleco, luvas de nitrilo e óculos de proteção.")

                btn_salvar_pop = st.form_submit_button("💾 Salvar Documento POP", type="primary")

                if btn_salvar_pop:
                    if not (tit_selecionado and obj_pop and passos_pop):
                        st.error("Preencha todos os campos obrigatórios (*).")
                    else:
                        status_pop = "Aprovado" if is_admin else "Pendente"

                        st.session_state.pops_db = [
                            p for p in st.session_state.pops_db
                            if not (p["titulo"].strip().lower() == tit_selecionado.strip().lower() and p.get("versao") == versao_calculada)
                        ]

                        novo_pop_data = {
                            "codigo": cod_auto,
                            "titulo": tit_selecionado.strip(),
                            "versao": versao_calculada,
                            "objetivo": obj_pop.strip(),
                            "materiais": mat_pop.strip(),
                            "passos": passos_pop.strip(),
                            "seguranca": sec_pop.strip(),
                            "autor": usuario_atual["nome"],
                            "status": status_pop,
                        }

                        st.session_state.pops_db.append(novo_pop_data)
                        salvar_dados(ARQUIVO_POPS, st.session_state.pops_db)

                        if is_admin:
                            b64_pdf = base64.b64encode(gerar_pdf_pop(novo_pop_data)).decode("utf-8")
                            novo_id = max([a.get("id", 0) for a in st.session_state.arquivos_db], default=0) + 1
                            st.session_state.arquivos_db.append({
                                "id": novo_id,
                                "titulo": f"{cod_auto} - {tit_selecionado.strip()}",
                                "pasta": "POPs e Protocolos",
                                "descricao": f"Procedimento Operacional Padrão (Versão {versao_calculada}). Objetivo: {obj_pop.strip()}",
                                "nome_original": f"{cod_auto}.pdf",
                                "mime_type": "application/pdf",
                                "conteudo_b64": b64_pdf,
                                "autor": usuario_atual["nome"],
                                "data": datetime.now().strftime("%d/%m/%Y"),
                                "status": "Aprovado",
                            })
                            salvar_dados(ARQUIVO_ARQUIVOS, st.session_state.arquivos_db)
                            st.success(f"✅ POP '{cod_auto}' salvo e publicado na pasta 'POPs e Protocolos'!")
                        else:
                            st.success(f"✅ POP '{cod_auto}' enviado para aprovação do Administrador!")

                        st.rerun()

    # --- 7. ADMINISTRAÇÃO (CENTRAL DE APROVAÇÕES) ---
    elif menu_selecionado == "🛡️ Administração" and is_admin:
        st.title("🛡️ Central de Aprovações (Administrador)")

        tab_usr, tab_perfis, tab_arq, tab_pops, tab_pastas = st.tabs([
            "👤 Acessos de Usuários",
            "✏️ Alterações de Perfil",
            "📄 Arquivos Inseridos",
            "📝 POPs",
            "📁 Pastas",
        ])

        with tab_usr:
            st.subheader("Solicitações de Acesso Pendentes")
            pend_acessos = [u for u in st.session_state.usuarios if u.get("status") == "Pendente"]

            if pend_acessos:
                for idx, u in enumerate(pend_acessos):
                    c_inf, c_b1, c_b2 = st.columns([3, 1, 1])
                    with c_inf:
                        st.write(f"👤 **{u['nome']}** (Usuário: `{u['usuario']}`)")
                        st.caption(f"Categoria: {u.get('categoria','-')} | E-mail: {u.get('email','-')} | Vínculo: {u.get('vinculo','-')}")
                    with c_b1:
                        if st.button("✅ Aprovar", key=f"ap_usr_{idx}", type="primary"):
                            u["status"] = "Aprovado"
                            salvar_dados(ARQUIVO_USUARIOS, st.session_state.usuarios)

                            for p in st.session_state.integrantes:
                                if p.get("Nome", "").strip().lower() == u["nome"].strip().lower():
                                    p["Situação"] = "Ativo"
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
                st.info("Nenhuma solicitação de novo acesso pendente no momento.")

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
                        st.write(f"- **Vínculo:** {u.get('vinculo', '-')}")
                        st.write(f"- **Telefone:** {u.get('telefone', '-')}")
                        st.write(f"- **E-mail:** {u.get('email', '-')}")

                    with c_depois:
                        st.markdown("**✏️ Dados Solicitados:**")
                        st.write(f"- **Categoria:** {p_data.get('categoria', '-')}")
                        st.write(f"- **Vínculo:** {p_data.get('vinculo', '-')}")
                        st.write(f"- **Telefone:** {p_data.get('telefone', '-')}")
                        st.write(f"- **E-mail:** {p_data.get('email', '-')}")
                        st.write(f"- **Dias/Horários:** {p_data.get('horarios', '-')}")
                        st.write(f"- **Lattes:** {p_data.get('lattes', '-')}")

                    c_b1, c_b2 = st.columns([1, 1])
                    with c_b1:
                        if st.button("✅ Aprovar Mudança", key=f"ap_prf_{idx}", type="primary"):
                            u["categoria"] = p_data.get("categoria")
                            u["vinculo"] = p_data.get("vinculo")
                            u["telefone"] = p_data.get("telefone")
                            u["email"] = p_data.get("email")
                            del u["pendente_atualizacao"]
                            salvar_dados(ARQUIVO_USUARIOS, st.session_state.usuarios)

                            for p in st.session_state.integrantes:
                                if p.get("Nome", "").strip().lower() == u["nome"].strip().lower() or p.get("Email", "").strip().lower() == u["email"].strip().lower():
                                    p["Categoria"] = p_data.get("categoria")
                                    p["Vínculo"] = p_data.get("vinculo")
                                    p["Telefone"] = p_data.get("telefone")
                                    p["Email"] = p_data.get("email")
                                    p["DiasHorarios"] = p_data.get("horarios")
                                    p["Lattes"] = p_data.get("lattes")

                            salvar_dados(ARQUIVO_INTEGRANTES, st.session_state.integrantes)
                            st.success(f"Perfil de '{u['nome']}' atualizado com sucesso!")
                            st.rerun()

                    with c_b2:
                        if st.button("❌ Recusar Mudança", key=f"rec_prf_{idx}"):
                            del u["pendente_atualizacao"]
                            salvar_dados(ARQUIVO_USUARIOS, st.session_state.usuarios)
                            st.warning("Solicitação de alteração recusada.")
                            st.rerun()

                    st.markdown("---")
            else:
                st.info("Nenhuma solicitação de alteração de perfil pendente.")

        with tab_arq:
            st.subheader("Arquivos Pendentes de Publicação")
            pend_arqs = [a for a in st.session_state.arquivos_db if a.get("status") == "Pendente"]

            if pend_arqs:
                for idx, a in enumerate(pend_arqs):
                    c_inf, c_b1, c_b2 = st.columns([3, 1, 1])
                    with c_inf:
                        st.write(f"📄 **{a['titulo']}** (Pasta: `{a.get('pasta', 'Geral')}`)")
                        st.caption(f"Enviado por: {a.get('autor', '-')} em {a.get('data', '-')}")
                        st.caption(f"Descrição: {a.get('descricao', '-')}")
                    with c_b1:
                        if st.button("✅ Aprovar Arquivo", key=f"ap_arq_{idx}", type="primary"):
                            a["status"] = "Aprovado"
                            salvar_dados(ARQUIVO_ARQUIVOS, st.session_state.arquivos_db)
                            st.success(f"Arquivo '{a['titulo']}' publicado!")
                            st.rerun()
                    with c_b2:
                        if st.button("❌ Apagar Arquivo", key=f"del_arq_p_{idx}"):
                            st.session_state.arquivos_db = [item for item in st.session_state.arquivos_db if item["id"] != a["id"]]
                            salvar_dados(ARQUIVO_ARQUIVOS, st.session_state.arquivos_db)
                            st.warning("Arquivo removido.")
                            st.rerun()
                    st.markdown("---")
            else:
                st.info("Nenhum arquivo pendente de aprovação.")

        with tab_pops:
            st.subheader("POPs Pendentes de Aprovação")
            pend_pops = [p for p in st.session_state.pops_db if p.get("status") == "Pendente"]

            if pend_pops:
                for idx, p in enumerate(pend_pops):
                    c_inf, c_b1, c_b2 = st.columns([3, 1, 1])
                    with c_inf:
                        st.write(f"📝 **{p['codigo']} - {p['titulo']}**")
                        st.caption(f"Autor: {p.get('autor', '-')} | Objetivo: {p.get('objetivo', '-')}")
                    with c_b1:
                        if st.button("✅ Aprovar POP", key=f"ap_pop_{idx}", type="primary"):
                            p["status"] = "Aprovado"
                            salvar_dados(ARQUIVO_POPS, st.session_state.pops_db)

                            b64_pdf = base64.b64encode(gerar_pdf_pop(p)).decode("utf-8")
                            novo_id = max([a.get("id", 0) for a in st.session_state.arquivos_db], default=0) + 1
                            st.session_state.arquivos_db.append({
                                "id": novo_id,
                                "titulo": f"{p['codigo']} - {p['titulo']}",
                                "pasta": "POPs e Protocolos",
                                "descricao": f"Procedimento Operacional Padrão (Versão {p.get('versao',1)}). Autor: {p.get('autor')}",
                                "nome_original": f"{p['codigo']}.pdf",
                                "mime_type": "application/pdf",
                                "conteudo_b64": b64_pdf,
                                "autor": p.get("autor", "N/A"),
                                "data": datetime.now().strftime("%d/%m/%Y"),
                                "status": "Aprovado",
                            })
                            salvar_dados(ARQUIVO_ARQUIVOS, st.session_state.arquivos_db)

                            st.success(f"POP '{p['codigo']}' aprovado e publicado na Central de Arquivos!")
                            st.rerun()
                    with c_b2:
                        if st.button("❌ Recusar POP", key=f"rec_pop_{idx}"):
                            st.session_state.pops_db = [item for item in st.session_state.pops_db if item.get("codigo") != p.get("codigo")]
                            salvar_dados(ARQUIVO_POPS, st.session_state.pops_db)
                            st.warning("POP recusado e removido.")
                            st.rerun()
                    st.markdown("---")
            else:
                st.info("Nenhum POP pendente de aprovação.")

        with tab_pastas:
            st.subheader("Solicitações de Novas Pastas")
            pend_pastas = [p for p in st.session_state.pastas_db if p.get("status") == "Pendente"]

            if pend_pastas:
                for idx, pst in enumerate(pend_pastas):
                    c_inf, c_b1, c_b2 = st.columns([3, 1, 1])
                    with c_inf:
                        st.write(f"📁 **Pasta: {pst['nome']}**")
                        st.caption(f"Criador: {pst.get('criador', '-')} | Descrição: {pst.get('descricao', '-')}")
                    with c_b1:
                        if st.button("✅ Aprovar Pasta", key=f"ap_pst_{idx}", type="primary"):
                            pst["status"] = "Aprovado"
                            salvar_dados(ARQUIVO_PASTAS, st.session_state.pastas_db)
                            st.success(f"Pasta '{pst['nome']}' aprovada!")
                            st.rerun()
                    with c_b2:
                        if st.button("❌ Recusar Pasta", key=f"rec_pst_{idx}"):
                            st.session_state.pastas_db = [item for item in st.session_state.pastas_db if item["nome"] != pst["nome"]]
                            salvar_dados(ARQUIVO_PASTAS, st.session_state.pastas_db)
                            st.warning("Pasta recusada.")
                            st.rerun()
                    st.markdown("---")
            else:
                st.info("Nenhuma solicitação de pasta pendente.")

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
        with c2:
            st.write(f"**Vínculo:** {usr_atual_reg.get('vinculo', '-')}")
            st.write(f"**Telefone:** {usr_atual_reg.get('telefone', '-')}")
            st.write(f"**E-mail:** {usr_atual_reg.get('email', '-')}")

        if usr_atual_reg.get("pendente_atualizacao"):
            st.warning("⚠️ Você possui uma solicitação de alteração de dados **PENDENTE** de aprovação do Administrador.")

        st.markdown("---")
        st.subheader("✏️ Solicitar Alteração de Dados")

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
