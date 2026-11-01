import streamlit as st
from config import (
    aplicar_estilos_css, carregar_dados, ARQUIVO_USUARIOS, ARQUIVO_INTEGRANTES,
    ARQUIVO_AGENDA, ARQUIVO_AVISOS, ARQUIVO_ARQUIVOS, ARQUIVO_PASTAS, ARQUIVO_POPS,
    ARQUIVO_GRUPOS, INTEGRANTES_INICIAIS, AGENDA_INICIAL, AVISOS_INICIAIS,
    PASTAS_INICIAIS, POPS_INICIAIS, GRUPOS_INICIAIS, usuario_admin_padrao
)
from paginas import home, grupos

st.set_page_config(page_title="Central de Pesquisa", page_icon="🧪", layout="wide")
aplicar_estilos_css()

# --- SESSÃO GLOBAL ---
if "usuarios" not in st.session_state:
    st.session_state.usuarios = carregar_dados(ARQUIVO_USUARIOS, usuario_admin_padrao)
if "integrantes" not in st.session_state:
    st.session_state.integrantes = carregar_dados(ARQUIVO_INTEGRANTES, INTEGRANTES_INICIAIS)
if "agenda" not in st.session_state:
    st.session_state.agenda = carregar_dados(ARQUIVO_AGENDA, AGENDA_INICIAL)
if "avisos_db" not in st.session_state:
    st.session_state.avisos_db = carregar_dados(ARQUIVO_AVISOS, AVISOS_INICIAIS)
if "pops_db" not in st.session_state:
    st.session_state.pops_db = carregar_dados(ARQUIVO_POPS, POPS_INICIAIS)
if "grupos_db" not in st.session_state:
    st.session_state.grupos_db = carregar_dados(ARQUIVO_GRUPOS, GRUPOS_INICIAIS)
if "grupos_autenticados" not in st.session_state:
    st.session_state.grupos_autenticados = []
if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = st.session_state.usuarios[0] # Login automático padrão para testes

usuario_atual = st.session_state.usuario_logado
is_admin = usuario_atual.get("is_admin", False)

# MENU LATERAL
st.sidebar.title("🧪 Central de Pesquisa")
menu_selecionado = st.sidebar.radio("Navegação", ["🏠 Página Inicial & Avisos", "🔬 Grupo de Pesquisa"])

# ROTEAMENTO DAS PÁGINAS
if menu_selecionado == "🏠 Página Inicial & Avisos":
    home.render_pagina_home(usuario_atual, is_admin)
elif menu_selecionado == "🔬 Grupo de Pesquisa":
    grupos.render_pagina_grupos(usuario_atual, is_admin)
