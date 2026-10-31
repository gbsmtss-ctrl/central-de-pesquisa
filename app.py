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

REAGENTES_CADASTRADOS = [
    "Extrato Enzimático de Lipase",
    "Solução Tampão Fosfato 0.1M (pH 7.0)",
    "Álcool Etílico 70%",
    "Reagente de Bradford",
    "Meio de Cultura BDA",
    "Solução de NaOH 1M",
    "Ácido Clorídrico 0.5M",
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
    st.session_state.agenda = carregar_dados(ARQUIVO_AGENDA, [])
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
                        st.error("Este nome de usuário já pertence a uma conta APROVADA.")
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

# --- ÁREA LOGADA ---
else:
    usuario_atual = st.session_state.usuario_logado
    is_admin = usuario_atual.get("is_admin", False)

    # --- BARRA LATERAL ---
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

    st.sidebar.markdown('<div class="sidebar-section">GESTÃO DO LABORATÓRIO</div>', unsafe_allow_html=True)
    
    opcoes_menu = [
        "👥 Equipe",
        "🎓 Orientados",
        "🕒 Presença no Laboratório",
    ]

    st.sidebar.markdown('<div class="sidebar-section">CONHECIMENTO</div>', unsafe_allow_html=True)
    opcoes_menu.extend([
        "📁 Repositório de Arquivos",
        "🏷️ Gerar QR Code de Amostras",
        "📝 Criador de POP",
    ])

    st.sidebar.markdown('<div class="sidebar-section">CONFIGURAÇÕES</div>', unsafe_allow_html=True)
    if is_admin:
        opcoes_menu.append("🛡️ Administração")
    opcoes_menu.append("👤 Meu perfil")

    menu_selecionado = st.sidebar.radio("Navegação", opcoes_menu, label_visibility="collapsed")

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

    # --- 1. EQUIPE ---
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
                                st.session_state.integrantes = [item for item in st.session_state.integrantes if item.get("Nome") != nome_str]
                                salvar_dados(ARQUIVO_INTEGRANTES, st.session_state.integrantes)

                                st.session_state.usuarios = [u for u in st.session_state.usuarios if str(u.get("nome", "")).strip().lower() != nome_str.strip().lower()]
                                salvar_dados(ARQUIVO_USUARIOS, st.session_state.usuarios)

                                st.warning(f"Integrante '{nome_str}' excluído com sucesso!")
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
                                # Suporte a múltiplas chaves e fallback para garantia de download
                                b64_str = (
                                    doc.get("conteudo_b64")
                                    or doc.get("conteudo")
                                    or doc.get("arquivo_b64")
                                    or doc.get("b64")
                                )

                                if b64_str:
                                    try:
                                        bytes_f = base64.b64decode(b64_str)
                                        st.download_button(
                                            label=f"⬇️ Baixar {doc.get('nome_original', 'arquivo.bin')}",
                                            data=bytes_f,
                                            file_name=doc.get('nome_original', 'arquivo.bin'),
                                            key=f"dl_{doc['id']}",
                                        )
                                    except Exception:
                                        # Fallback em caso de falha de decodificação
                                        texto_fb = f"Documento: {doc.get('titulo')}\nAutor: {doc.get('autor')}\nData: {doc.get('data')}\nDescrição: {doc.get('descricao')}"
                                        st.download_button(
                                            label=f"⬇️ Baixar {doc.get('nome_original', 'documento.txt')}",
                                            data=texto_fb.encode("utf-8"),
                                            file_name=f"{doc.get('titulo', 'documento')}.txt",
                                            key=f"dl_fb_err_{doc['id']}",
                                        )
                                else:
                                    # Fallback automático garantido para itens legados sem base64 salvo
                                    texto_fb = f"Documento: {doc.get('titulo')}\nAutor: {doc.get('autor')}\nData: {doc.get('data')}\nDescrição: {doc.get('descricao')}"
                                    st.download_button(
                                        label=f"⬇️ Baixar {doc.get('nome_original', 'documento.txt')}",
                                        data=texto_fb.encode("utf-8"),
                                        file_name=f"{doc.get('titulo', 'documento')}.txt",
                                        key=f"dl_fb_{doc['id']}",
                                    )

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

    # --- 6. CRIADOR DE POP ---
    elif menu_selecionado == "📝 Criador de POP":
        st.title("📝 Criador e Atualizador de POP Padrão")

        cod_pop = st.text_input("Código do POP", "POP-LTAB-002")
        tit_pop = st.text_input("Título do POP *")
        obj_pop = st.text_area("Objetivo *", height=80)
        mat_pop = st.text_area("Materiais *", height=80)
        passos_pop = st.text_area("Passo a Passo *", height=120)
        sec_pop = st.text_area("Segurança *", height=80)

        if st.button("💾 Salvar Documento POP", type="primary"):
            if tit_pop and obj_pop and passos_pop:
                status_pop = "Aprovado" if is_admin else "Pendente"
                st.session_state.pops_db.append({
                    "codigo": cod_pop.strip(),
                    "titulo": tit_pop.strip(),
                    "versao": 1,
                    "objetivo": obj_pop.strip(),
                    "materiais": mat_pop.strip(),
                    "passos": passos_pop.strip(),
                    "seguranca": sec_pop.strip(),
                    "autor": usuario_atual["nome"],
                    "status": status_pop,
                })
                salvar_dados(ARQUIVO_POPS, st.session_state.pops_db)
                if is_admin:
                    st.success(f"POP '{cod_pop}' salvo e APROVADO com sucesso!")
                else:
                    st.success(f"POP '{cod_pop}' enviado para aprovação do Administrador!")

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

        # TAB 1: USUÁRIOS PENDENTES
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

        # TAB 2: ALTERAÇÕES DE PERFIL
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

        # TAB 3: ARQUIVOS PENDENTES
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

        # TAB 4: POPS PENDENTES
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
                            st.success(f"POP '{p['codigo']}' aprovado!")
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

        # TAB 5: PASTAS PENDENTES
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

        usr_atual_reg = next(
            (u for u in st.session_state.usuarios if str(u.get("usuario")).lower() == str(usuario_atual["usuario"]).lower()),
            usuario_atual
        )

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
