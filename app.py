import base64
import calendar
from datetime import datetime, time
from io import BytesIO
import json
import os
import pandas as pd
from PIL import Image, ImageDraw
import qrcode
import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Central LTAB - Gestão do Laboratório",
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
    .table-row {
        background-color: white;
        padding: 12px 16px;
        border-radius: 8px;
        border: 1px solid #F1F5F9;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- SISTEMA DE PERSISTÊNCIA DE DADOS ---
ARQUIVO_INTEGRANTES = "integrantes.json"
ARQUIVO_AGENDA = "agenda.json"
ARQUIVO_USUARIOS = "usuarios.json"
ARQUIVO_ARQUIVOS = "arquivos.json"
ARQUIVO_PASTAS = "pastas.json"
ARQUIVO_POPS = "pops.json"

CATEGORIAS_PADRAO = [
    "Iniciação Científica",
    "Mestrado",
    "Doutorado",
    "Pós-Doutorado",
    "Orientador",
    "Técnico / Pesquisador",
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
        "DiasHorarios": "Não informado",
        "Lattes": "http://lattes.cnpq.br/",
        "Situação": "Ativo",
    },
    {
        "Nome": "Gabriela Mendes Farias Matos",
        "Categoria": "Mestrando",
        "Vínculo": "UFRRJ - Química Industrial",
        "Telefone": "(21) 99677-8065",
        "Email": "gbsmtsm@ufrrj.br",
        "DiasHorarios": "Não informado",
        "Lattes": "-",
        "Situação": "Ativo",
    },
    {
        "Nome": "Isabela de Souza Marques Couto",
        "Categoria": "Mestrando",
        "Vínculo": "UFRRJ - Engenharia Química",
        "Telefone": "(21) 98888-8888",
        "Email": "isabelamarques.couto@hotmail.com",
        "DiasHorarios": "Não informado",
        "Lattes": "-",
        "Situação": "Ativo",
    },
    {
        "Nome": "Larissa Maria Souza de Carvalho",
        "Categoria": "Mestrando",
        "Vínculo": "UFRRJ - Engenharia Química / Mestrado",
        "Telefone": "(21) 97777-7777",
        "Email": "larissamana@ufrrj.br",
        "DiasHorarios": "Ter 10:30-17:00 - Qua 08:00-17:00",
        "Lattes": "-",
        "Situação": "Ativo",
    },
    {
        "Nome": "Lucas de Oliveira Santos",
        "Categoria": "Mestrando",
        "Vínculo": "UFRRJ - Engenharia Química",
        "Telefone": "(21) 96666-6666",
        "Email": "lucaslidor@hotmail.com",
        "DiasHorarios": "Seg 08:00-12:00 - Ter 09:00-17:00 - Qua 08:00-17:00 - Qui 13:00-17:00 - Sex 08:00-17:00",
        "Lattes": "http://lattes.cnpq.br/",
        "Situação": "Ativo",
    },
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
        "codigo": "POP-LTAB-001",
        "titulo": "Operação e Higienização do Espectrofotômetro",
        "versao": 1,
        "objetivo": "Padronizar a operação e limpeza do equipamento para garantir medições precisas.",
        "materiais": "Cubetas de quartzo, álcool 70%, lenço de papel macio, tampões.",
        "passos": "1. Ligar o equipamento 15 minutos antes da leitura.\n2. Ajustar o comprimento de onda.\n3. Realizar o branco com a solução controle.\n4. Ler amostras em triplicata.\n5. Higienizar as cubetas após o uso.",
        "seguranca": "Uso obrigatório de jaleco, luvas de nitrilo e óculos de proteção.",
        "autor": "Eliane Pereira Cipolatti",
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
    "vinculo": "UFRRJ",
    "telefone": "(21) 99677-8065",
    "email": "gbsmtsm@ufrrj.br",
    "status": "Aprovado",
    "is_admin": True,
}]

# --- INICIALIZAÇÃO DE SESSÃO PERSISTENTE NO SESSION_STATE ---
if "usuarios" not in st.session_state:
    st.session_state.usuarios = carregar_dados(ARQUIVO_USUARIOS, usuario_admin_padrao)
if "integrantes" not in st.session_state:
    st.session_state.integrantes = carregar_dados(ARQUIVO_INTEGRANTES, INTEGRANTES_INICIAIS)
if "agenda" not in st.session_state:
    st.session_state.agenda = carregar_dados(ARQUIVO_AGENDA, [])
if "arquivos_db" not in st.session_state:
    st.session_state.arquivos_db = carregar_dados(ARQUIVO_ARQUIVOS, [])
if "pastas_db" not in st.session_state:
    st.session_state.pastas_db = carregar_dados(ARQUIVO_PASTAS, PASTAS_INICIAIS)
if "pops_db" not in st.session_state:
    st.session_state.pops_db = carregar_dados(ARQUIVO_POPS, POPS_INICIAIS)
if "pasta_aberta_drive" not in st.session_state:
    st.session_state.pasta_aberta_drive = None

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


# --- TELA DE LOGIN E SOLICITAÇÃO DE ACESSO ---
if st.session_state.usuario_logado is None:
    st.title("🧪 Central de Pesquisa - Controle de Acesso ⚗️")

    aba_login, aba_cadastro = st.tabs(["Entrar no Sistema", "Solicitar Acesso"])

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
                            st.warning(
                                "⚠️ O seu cadastro está PENDENTE de aprovação. Peça ao Administrador que aprove o acesso na 'Central de Aprovações'."
                            )
                        else:
                            st.error("❌ Sua solicitação de acesso foi recusada. Você pode tentar se cadastrar novamente na aba 'Solicitar Acesso'.")
                    else:
                        st.error("Senha incorreta.")
                else:
                    st.error("Usuário não encontrado.")

    with aba_cadastro:
        st.subheader("Pedir Permissão de Acesso")
        with st.form("form_solicitar_acesso"):
            novo_nome = st.text_input("Nome Completo *")
            nova_categoria = st.selectbox("Categoria *", CATEGORIAS_PADRAO)
            novo_vinculo = st.text_input("Vínculo / Curso *", "UFRRJ - Engenharia de Alimentos")
            novo_telefone = st.text_input("Telefone para Contato *")
            novo_email = st.text_input("E-mail para Contato *")
            novo_usuario = st.text_input("Usuário Desejado (ex: gabriela matos) *")
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
                        st.error("Este nome de usuário já pertence a uma conta APROVADA. Tente fazer o login na aba 'Entrar no Sistema'.")
                    else:
                        st.session_state.usuarios = [
                            u for u in st.session_state.usuarios
                            if str(u.get("usuario", "")).strip().lower() != usr_clean
                            and str(u.get("nome", "")).strip().lower() != novo_nome.strip().lower()
                        ]

                        novo_user_dict = {
                            "nome": novo_nome.strip(),
                            "usuario": novo_usuario.strip(),
                            "senha": nova_senha,
                            "categoria": nova_categoria,
                            "vinculo": novo_vinculo.strip(),
                            "telefone": novo_telefone.strip(),
                            "email": novo_email.strip(),
                            "status": "Pendente",
                            "is_admin": False,
                        }
                        st.session_state.usuarios.append(novo_user_dict)
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

                        st.success(f"Solicitação enviada com sucesso! Aguarde a aprovação do Administrador.")

# --- ÁREA LOGADA ---
else:
    usuario_atual = st.session_state.usuario_logado
    is_admin = usuario_atual.get("is_admin", False)

    # --- BARRA LATERAL CONFORME A IMAGEM ---
    st.sidebar.markdown(
        """
        <div style="display: flex; align-items: center; gap: 10px; padding: 5px 0 15px 0;">
            <div style="background-color: #3B82F6; color: white; border-radius: 8px; padding: 8px; font-size: 1.2rem; font-weight: bold;">
                ◆
            </div>
            <div>
                <h3 style="margin:0; font-size: 1.1rem; color: #0F172A !important;">Central LTAB</h3>
                <span style="font-size: 0.75rem; color: #64748B;">Central do Laboratório</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.markdown('<div class="sidebar-section">GESTÃO DO LABORATÓRIO</div>', unsafe_allow_html=True)
    
    opcoes_menu = [
        "👥 Equipe",
        "🎓 Orientados",
        "🕒 Presença no Laboratório",
        "📋 Afastamentos",
        "🔬 Equipamentos",
        "🧪 Reagentes e Insumos",
    ]

    st.sidebar.markdown('<div class="sidebar-section">CONHECIMENTO</div>', unsafe_allow_html=True)
    opcoes_menu.extend([
        "📖 Biblioteca Digital",
        "🏷️ Gerar QR Code de Amostras",
        "📝 Criador de POP",
    ])

    st.sidebar.markdown('<div class="sidebar-section">CONFIGURAÇÕES</div>', unsafe_allow_html=True)
    if is_admin:
        opcoes_menu.append("🛡️ Administração")
    opcoes_menu.append("👤 Meu perfil")

    menu_selecionado = st.sidebar.radio("Navegação", opcoes_menu, label_visibility="collapsed")

    # Rodapé da Sidebar com usuário e logout exatamente como na imagem
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

    # --- TELA 1: EQUIPE (CADASTRO DE INTEGRANTES - IDÊNTICO À IMAGEM) ---
    if menu_selecionado == "👥 Equipe":
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
                    f_vinc = st.text_input("Vínculo / Curso", "UFRRJ - Engenharia de Alimentos")
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

        # Filtragem dos dados
        integrantes_filtrados = st.session_state.integrantes

        if cat_filtro != "Todos":
            integrantes_filtrados = [p for p in integrantes_filtrados if p.get("Categoria") == cat_filtro]

        if termo_busca.strip():
            tb = termo_busca.lower().strip()
            integrantes_filtrados = [
                p for p in integrantes_filtrados
                if tb in str(p.get("Nome", "")).lower()
                or tb in str(p.get("Vínculo", "")).lower()
                or tb in str(p.get("Email", "")).lower()
            ]

        st.markdown("<br>", unsafe_allow_html=True)

        # Cabeçalho da Tabela
        col_hdr = st.columns([2.5, 1.2, 1.8, 1.8, 1.0, 0.8, 1.2])
        col_hdr[0].markdown("<div class='table-header'>INTEGRANTE</div>", unsafe_allow_html=True)
        col_hdr[1].markdown("<div class='table-header'>CATEGORIA</div>", unsafe_allow_html=True)
        col_hdr[2].markdown("<div class='table-header'>VÍNCULO / CURSO</div>", unsafe_allow_html=True)
        col_hdr[3].markdown("<div class='table-header'>DIAS E HORÁRIOS</div>", unsafe_allow_html=True)
        col_hdr[4].markdown("<div class='table-header'>LATTES</div>", unsafe_allow_html=True)
        col_hdr[5].markdown("<div class='table-header'>SITUAÇÃO</div>", unsafe_allow_html=True)
        col_hdr[6].markdown("<div class='table-header'></div>", unsafe_allow_html=True)

        # Linhas da Tabela formatadas conforme a imagem
        if integrantes_filtrados:
            for idx, p in enumerate(integrantes_filtrados):
                c1, c2, c3, c4, c5, c6, c7 = st.columns([2.5, 1.2, 1.8, 1.8, 1.0, 0.8, 1.2])

                nome_str = p.get("Nome", "-")
                email_str = p.get("Email", "-")
                cat_str = p.get("Categoria", "-")
                vinc_str = p.get("Vínculo", "-")
                hor_str = p.get("DiasHorarios", "Não informado")
                lattes_str = p.get("Lattes", "-")
                sit_str = p.get("Situação", "Ativo")

                # Iniciais para Avatar
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
                                st.session_state.integrantes = [item for item in st.session_state.integrantes if item.get("Nome") != nome_str]
                                salvar_dados(ARQUIVO_INTEGRANTES, st.session_state.integrantes)
                                st.warning("Integrante removido!")
                                st.rerun()

                st.markdown("<hr style='margin: 8px 0; border: none; border-top: 1px solid #F1F5F9;'/>", unsafe_allow_html=True)
        else:
            st.info("Nenhum integrante encontrado.")

    # --- TELA 2: ORIENTADOS ---
    elif menu_selecionado == "🎓 Orientados":
        st.title("🎓 Orientados e Alunos")
        st.caption("Acompanhamento de alunos e projetos de orientação.")
        orientados = [p for p in st.session_state.integrantes if p.get("Categoria") in ["Iniciação Científica", "Mestrado", "Doutorado", "Pós-Doutorado"]]
        if orientados:
            st.dataframe(pd.DataFrame(orientados)[["Nome", "Categoria", "Vínculo", "Email", "Situação"]], use_container_width=True)
        else:
            st.info("Nenhum orientado cadastrado.")

    # --- TELA 3: PRESENÇA NO LABORATÓRIO ---
    elif menu_selecionado == "🕒 Presença no Laboratório":
        st.title("🕒 Presença no Laboratório")
        st.caption("Escala e horários de presença dos pesquisadores.")
        df_presenca = pd.DataFrame(st.session_state.integrantes)[["Nome", "Categoria", "DiasHorarios"]]
        st.dataframe(df_presenca, use_container_width=True)

    # --- TELA 4: AFASTAMENTOS ---
    elif menu_selecionado == "📋 Afastamentos":
        st.title("📋 Registro de Afastamentos e Licenças")
        st.info("Nenhum afastamento registrado no momento.")

    # --- TELA 5: EQUIPAMENTOS ---
    elif menu_selecionado == "🔬 Equipamentos":
        st.title("🔬 Equipamentos do Laboratório")
        st.caption("Lista e status operacional dos equipamentos.")
        st.write("• **Espectrofotômetro** - Operacional")
        st.write("• **Autoclave** - Operacional")
        st.write("• **Centrífuga** - Operacional")

    # --- TELA 6: REAGENTES E INSUMOS ---
    elif menu_selecionado == "🧪 Reagentes e Insumos":
        st.title("🧪 Reagentes & Insumos")
        st.caption("Controle de estoque de reagentes e FISPQ.")
        st.info("Consulte a pasta FISPQ na Biblioteca Digital para fichas de segurança.")

    # --- TELA 7: BIBLIOTECA DIGITAL (REPOSITÓRIO DE ARQUIVOS) ---
    elif menu_selecionado == "📖 Biblioteca Digital":
        st.title("📖 Biblioteca Digital & Repositório de Arquivos")

        aba_docs, aba_upload, aba_nova_pasta = st.tabs([
            "📂 Drive de Arquivos",
            "📥 Enviar Arquivo",
            "📁 Nova Pasta",
        ])

        pastas_aprovadas = [p for p in st.session_state.pastas_db if p.get("status") == "Aprovado"]

        with aba_docs:
            if st.session_state.pasta_aberta_drive is None:
                st.subheader("📂 Pastas do Laboratório")
                cols = st.columns(3)
                for idx, pst in enumerate(pastas_aprovadas):
                    nome_p = pst["nome"]
                    desc_p = pst.get("descricao", "Sem descrição")
                    qtd_files = sum(1 for a in st.session_state.arquivos_db if str(a.get("pasta")).strip().lower() == str(nome_p).strip().lower() and a.get("status") == "Aprovado")
                    
                    with cols[idx % 3]:
                        st.markdown(
                            f"""
                            <div class="css-card">
                                <h3>📁 {nome_p}</h3>
                                <p style='color:#64748B; font-size:0.85rem;'>{desc_p}</p>
                                <span style='background:#E2E8F0; padding:2px 8px; border-radius:10px; font-size:0.8rem;'>📄 {qtd_files} arquivo(s)</span>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        if st.button(f"Abrir {nome_p}", key=f"open_f_{idx}"):
                            st.session_state.pasta_aberta_drive = nome_p
                            st.rerun()
            else:
                nome_pasta_atual = st.session_state.pasta_aberta_drive
                st.button("⬅️ Voltar para Pastas", on_click=lambda: st.session_state.update({"pasta_aberta_drive": None}))
                st.subheader(f"📂 Pasta: {nome_pasta_atual}")

                arqs = [a for a in st.session_state.arquivos_db if str(a.get("pasta")).strip().lower() == str(nome_pasta_atual).strip().lower() and a.get("status") == "Aprovado"]
                if arqs:
                    for doc in arqs:
                        st.markdown(f"**📄 {doc['titulo']}** | *Enviado por {doc.get('autor','-')}*")
                        if "conteudo_b64" in doc:
                            bytes_f = base64.b64decode(doc["conteudo_b64"])
                            st.download_button(f"⬇️ Baixar {doc.get('nome_original')}", bytes_f, file_name=doc.get('nome_original'), key=f"dl_{doc['id']}")
                        st.markdown("---")
                else:
                    st.info("Nenhum arquivo nesta pasta.")

        with aba_upload:
            tit_doc = st.text_input("Título do Documento")
            pasta_doc = st.selectbox("Pasta", [p["nome"] for p in pastas_aprovadas])
            desc_doc = st.text_area("Descrição")
            arq_up = st.file_uploader("Ficheiro")

            if st.button("Confirmar Envio", type="primary"):
                if tit_doc and arq_up:
                    b64_str = base64.b64encode(arq_up.getvalue()).decode("utf-8")
                    novo_id = max([a.get("id", 0) for a in st.session_state.arquivos_db], default=0) + 1
                    st.session_state.arquivos_db.append({
                        "id": novo_id,
                        "titulo": tit_doc,
                        "pasta": pasta_doc,
                        "descricao": desc_doc,
                        "nome_original": arq_up.name,
                        "conteudo_b64": b64_str,
                        "autor": usuario_atual["nome"],
                        "data": datetime.now().strftime("%d/%m/%Y"),
                        "status": "Aprovado" if is_admin else "Pendente",
                    })
                    salvar_dados(ARQUIVO_ARQUIVOS, st.session_state.arquivos_db)
                    st.success("Documento enviado com sucesso!")

        with aba_nova_pasta:
            np_nome = st.text_input("Nome da Pasta")
            np_desc = st.text_input("Descrição")
            if st.button("Criar Pasta"):
                if np_nome:
                    st.session_state.pastas_db.append({"nome": np_nome, "descricao": np_desc, "criador": usuario_atual["nome"], "status": "Aprovado" if is_admin else "Pendente"})
                    salvar_dados(ARQUIVO_PASTAS, st.session_state.pastas_db)
                    st.success("Pasta solicitada!")

    # --- TELA 8: GERAR QR CODE ---
    elif menu_selecionado == "🏷️ Gerar QR Code de Amostras":
        st.title("🧪 Gerador de QR Code de Amostras")
        id_amostra = st.text_input("Código / ID da Amostra", "AMS-2026-001")
        nome_amostra = st.text_input("Nome da Amostra", "Extrato Enzimático")
        data_obtencao = st.date_input("Data de Obtenção", datetime.now().date())
        responsavel = st.text_input("Responsável", usuario_atual["nome"])
        localizacao = st.text_input("Armazenamento", "Freezer -20°C")
        dest_selecionado = st.selectbox("Destino", list(DESTINOS_ETIQUETAS.keys()))
        tamanho_mm = DESTINOS_ETIQUETAS[dest_selecionado]
        qtd_etiquetas = st.number_input("Quantidade", 1, 100, 6)

        if st.button("Gerar QR Code", type="primary"):
            conteudo_qr = f"ID: {id_amostra}\nNOME: {nome_amostra}\nRESPONSÁVEL: {responsavel}\nLOCAL: {localizacao}"
            img = qrcode.make(conteudo_qr)
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            img_bytes = buffer.getvalue()

            st.image(img_bytes, width=200)
            st.download_button("🖼️ Baixar PNG", img_bytes, f"QR_{id_amostra}.png", "image/png")
            pdf_bytes = gerar_pdf_etiquetas(img, qtd_etiquetas, tamanho_mm, id_amostra=id_amostra)
            st.download_button("📄 Baixar PDF Etiquetas", pdf_bytes, f"Etiquetas_{id_amostra}.pdf", "application/pdf")

    # --- TELA 9: CRIADOR DE POP ---
    elif menu_selecionado == "📝 Criador de POP":
        st.title("📝 Criador e Atualizador de POP")
        cod_pop = st.text_input("Código POP", "POP-LTAB-002")
        tit_pop = st.text_input("Título do POP")
        obj_pop = st.text_area("Objetivo")
        mat_pop = st.text_area("Materiais")
        passos_pop = st.text_area("Passo a Passo")
        sec_pop = st.text_area("Segurança")

        if st.button("💾 Salvar POP", type="primary"):
            if tit_pop and obj_pop:
                st.session_state.pops_db.append({
                    "codigo": cod_pop,
                    "titulo": tit_pop,
                    "versao": 1,
                    "objetivo": obj_pop,
                    "materiais": mat_pop,
                    "passos": passos_pop,
                    "seguranca": sec_pop,
                    "autor": usuario_atual["nome"],
                })
                salvar_dados(ARQUIVO_POPS, st.session_state.pops_db)
                st.success(f"POP '{cod_pop}' salvo com sucesso!")

    # --- TELA 10: ADMINISTRAÇÃO / CENTRAL DE APROVAÇÕES ---
    elif menu_selecionado == "🛡️ Administração" and is_admin:
        st.title("🛡️ Painel de Administração & Aprovações")
        st.subheader("Solicitações de Acesso Pendentes")
        pendentes = [u for u in st.session_state.usuarios if u.get("status") == "Pendente"]
        if pendentes:
            for idx, u in enumerate(pendentes):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.write(f"👤 **{u['nome']}** ({u['email']})")
                with c2:
                    if st.button("Aprovar", key=f"ap_{idx}"):
                        u["status"] = "Aprovado"
                        salvar_dados(ARQUIVO_USUARIOS, st.session_state.usuarios)
                        st.success("Acesso liberado!")
                        st.rerun()
        else:
            st.info("Nenhuma aprovação pendente.")

    # --- TELA 11: MEU PERFIL ---
    elif menu_selecionado == "👤 Meu perfil":
        st.title("👤 Meu Perfil")
        st.write(f"**Nome:** {usuario_atual['nome']}")
        st.write(f"**Usuário:** {usuario_atual['usuario']}")
        st.write(f"**E-mail:** {usuario_atual['email']}")
        st.write(f"**Vínculo:** {usuario_atual.get('vinculo','-')}")
