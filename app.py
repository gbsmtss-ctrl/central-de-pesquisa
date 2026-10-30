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

# --- ESTILIZAÇÃO VISUAL (AZUL CLARO, BRANCO E CARDS) ---
st.markdown(
    """
    <style>
    /* Fundo principal da aplicação em azul super claro */
    .stApp {
        background-color: #F4F8FB;
    }
    /* Estilo da barra lateral (Sidebar) em azul claro */
    [data-testid="stSidebar"] {
        background-color: #EBF3FA;
        border-right: 1px solid #D6E4F0;
    }
    /* Cor dos títulos principais */
    h1, h2, h3 {
        color: #0D47A1 !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    /* Subtítulos de seções na barra lateral */
    .sidebar-section {
        font-size: 0.75rem;
        font-weight: 700;
        color: #5C768D;
        text-transform: uppercase;
        margin-top: 1.2rem;
        margin-bottom: 0.3rem;
        letter-spacing: 0.05em;
    }
    /* Botões primários em azul vibrante */
    div.stButton > button:first-child {
        background-color: #1E88E5;
        color: white;
        border-radius: 8px;
        border: none;
        font-weight: bold;
    }
    div.stButton > button:first-child:hover {
        background-color: #1565C0;
        color: white;
    }
    /* Cards brancos elegantes */
    .css-card {
        background-color: white;
        padding: 18px;
        border-radius: 10px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        margin-bottom: 15px;
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
PASTA_UPLOADS = "uploads"

os.makedirs(PASTA_UPLOADS, exist_ok=True)

CATEGORIAS_PADRAO = [
    "Iniciação Científica",
    "Mestrado",
    "Doutorado",
    "Pós-Doutorado",
    "Orientador",
    "Técnico / Pesquisador",
]

DESTINOS_ETIQUETAS = {
    "Tubo Eppendorf (0.5 mL / 1.5 mL / 2.0 mL)": 15,  # mm
    "Tubo Falcon (15 mL)": 22,  # mm
    "Tubo Falcon (50 mL)": 30,  # mm
    "Frasco / Béquer / Erlenmeyer": 45,  # mm
    "Bancada / Equipamento / Prateleira": 65,  # mm
}

PASTAS_INICIAIS = [
    {
        "nome": "Geral",
        "descricao": "Arquivos gerais do laboratório",
        "criador": "admin",
        "status": "Aprovado",
    },
    {
        "nome": "POPs e Protocolos",
        "descricao": "Procedimentos Operacionais Padrão",
        "criador": "admin",
        "status": "Aprovado",
    },
    {
        "nome": "Artigos Científicos",
        "descricao": "Publicações e referências",
        "criador": "admin",
        "status": "Aprovado",
    },
    {
        "nome": "Manuais de Equipamentos",
        "descricao": "Guias de operação de máquinas",
        "criador": "admin",
        "status": "Aprovado",
    },
    {
        "nome": "FISPQ / Segurança",
        "descricao": "Fichas de segurança de reagentes",
        "criador": "admin",
        "status": "Aprovado",
    },
]

POPS_INICIAIS = [
    {
        "codigo": "POP-LTAB-001",
        "titulo": "Operação e Higienização do Espectrofotômetro",
        "versao": 1,
        "objetivo": (
            "Padronizar a operação e limpeza do equipamento para garantir"
            " medições precisas."
        ),
        "materiais": (
            "Cubetas de quartzo, álcool 70%, lenço de papel macio, tampões."
        ),
        "passos": (
            "1. Ligar o equipamento 15 minutos antes da leitura.\n2. Ajustar o"
            " comprimento de onda.\n3. Realizar o branco com a solução"
            " controle.\n4. Ler amostras em triplicata.\n5. Higienizar as"
            " cubetas após o uso."
        ),
        "seguranca": (
            "Uso obrigatório de jaleco, luvas de nitrilo e óculos de proteção."
        ),
        "autor": "Eliane Pereira Cipolatti",
    },
    {
        "codigo": "POP-LTAB-002",
        "titulo": "Preparo de Soluções e Tampões",
        "versao": 1,
        "objetivo": (
            "Padronizar o preparo de soluções aquosas e tampões de uso prévio."
        ),
        "materiais": (
            "Balança analítica, Becker, Pisseta com água destilada, Peagametro."
        ),
        "passos": (
            "1. Calcular e pesará a massa de reagente necessária.\n2. Dissolver"
            " em béquer com água destilada sob agitação.\n3. Ajustar o pH no"
            " peagâmetro.\n4. Transferir para balão volumétrico e aferir o"
            " volume."
        ),
        "seguranca": (
            "Jaleco, luvas, óculos de proteção e manipulação em capela se"
            " volátil."
        ),
        "autor": "Eliane Pereira Cipolatti",
    },
]


def carregar_dados(arquivo, padrao):
  """Carrega os dados salvos em arquivo JSON diretamente do disco."""
  if os.path.exists(arquivo):
    try:
      with open(arquivo, "r", encoding="utf-8") as f:
        return json.load(f)
    except Exception:
      return padrao
  return padrao


def salvar_dados(arquivo, dados):
  """Salva a lista atualizada no arquivo JSON."""
  with open(arquivo, "w", encoding="utf-8") as f:
    json.dump(dados, f, ensure_ascii=False, indent=4)


def gerar_pdf_etiquetas(qr_img_pil, quantidade, mm_size):
  """Gera um documento PDF em A4 com a grade de etiquetas dimensionadas."""
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

  qr_resized = qr_img_pil.resize((label_px, label_px))

  for _ in range(quantidade):
    if x + label_px > page_w - margin_px:
      x = margin_px
      y += label_px + spacing_px

    if y + label_px > page_h - margin_px:
      pages.append(current_page)
      current_page = Image.new("RGB", (page_w, page_h), "white")
      draw = ImageDraw.Draw(current_page)
      x = margin_px
      y = margin_px

    current_page.paste(qr_resized, (x, y))
    draw.rectangle(
        [x, y, x + label_px, y + label_px], outline="lightgray", width=1
    )
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
    "nome": "Administrador",
    "usuario": "admin",
    "senha": "123",
    "categoria": "Orientador",
    "vinculo": "UFRRJ",
    "telefone": "(21) 99999-9999",
    "email": "admin@ufrrj.br",
    "status": "Aprovado",
    "is_admin": True,
}]

# --- LIMPEZA DE USUÁRIOS NÃO OFICIAIS (Manter apenas quem está na planilha oficial de integrantes) ---
integrantes_oficiais = carregar_dados(
    ARQUIVO_INTEGRANTES,
    [{
        "Nome": "Eliane Pereira Cipolatti",
        "Categoria": "Orientador",
        "Vínculo": "UFRRJ - Engenharia de Alimentos",
        "Telefone": "(21) 99999-9999",
        "Email": "eliane@ufrrj.br",
        "Situação": "Ativo",
    }],
)
nomes_na_planilha = [
    p["Nome"].strip().lower() for p in integrantes_oficiais if "Nome" in p
]

usuarios_carregados = carregar_dados(ARQUIVO_USUARIOS, usuario_admin_padrao)
usuarios_limpos = [
    u
    for u in usuarios_carregados
    if u.get("is_admin")
    or u.get("nome", "").strip().lower() in nomes_na_planilha
]
salvar_dados(ARQUIVO_USUARIOS, usuarios_limpos)

st.session_state.integrantes = integrantes_oficiais
st.session_state.usuarios = usuarios_limpos
st.session_state.agenda = carregar_dados(ARQUIVO_AGENDA, [])
st.session_state.arquivos_db = carregar_dados(ARQUIVO_ARQUIVOS, [])
st.session_state.pastas_db = carregar_dados(ARQUIVO_PASTAS, PASTAS_INICIAIS)
st.session_state.pops_db = carregar_dados(ARQUIVO_POPS, POPS_INICIAIS)

# Sessão persistente via parâmetro da URL
if "usr" in st.query_params:
  usr_param = st.query_params["usr"]
  lista_usrs = carregar_dados(ARQUIVO_USUARIOS, usuario_admin_padrao)
  usr_encontrado = next(
      (
          u
          for u in lista_usrs
          if u["usuario"].lower() == usr_param.lower()
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
        usuarios_frescos = carregar_dados(
            ARQUIVO_USUARIOS, usuario_admin_padrao
        )
        usr_clean = user_input.strip().lower()
        usuario_encontrado = None

        for u in usuarios_frescos:
          u_usr = u.get("usuario", "").strip().lower()
          u_email = u.get("email", "").strip().lower()
          u_nome = u.get("nome", "").strip().lower()

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
                  "⚠️ O seu cadastro está PENDENTE de aprovação. Peça ao"
                  " Administrador que aprove o acesso na 'Central de"
                  " Aprovações'."
              )
            else:
              st.error(
                  "❌ Sua solicitação de acesso foi recusada. Você pode tentar"
                  " se cadastrar novamente na aba 'Solicitar Acesso'."
              )
          else:
            st.error("Senha incorreta.")
        else:
          st.error("Usuário não encontrado.")

  with aba_cadastro:
    st.subheader("Pedir Permissão de Acesso")
    with st.form("form_solicitar_acesso"):
      novo_nome = st.text_input("Nome Completo *")
      nova_categoria = st.selectbox("Categoria *", CATEGORIAS_PADRAO)
      novo_vinculo = st.text_input(
          "Vínculo / Curso *", "UFRRJ - Engenharia de Alimentos"
      )
      novo_telefone = st.text_input("Telefone para Contato *")
      novo_email = st.text_input("E-mail para Contato *")
      novo_usuario = st.text_input("Usuário Desejado (ex: gabriela matos) *")
      nova_senha = st.text_input("Criar Senha *", type="password")
      btn_solicitar = st.form_submit_button("Enviar Solicitação")

      if btn_solicitar:
        if not (
            novo_nome
            and novo_usuario
            and nova_senha
            and novo_vinculo
            and novo_telefone
            and novo_email
        ):
          st.error("Por favor, preencha todos os campos obrigatórios (*).")
        else:
          usr_clean = novo_usuario.strip().lower()
          usuarios_atuais = carregar_dados(
              ARQUIVO_USUARIOS, usuario_admin_padrao
          )

          ja_aprovado = any(
              u["usuario"].strip().lower() == usr_clean
              and u.get("status") == "Aprovado"
              for u in usuarios_atuais
          )

          if ja_aprovado:
            st.error(
                "Este nome de usuário já pertence a uma conta APROVADA. Tente"
                " fazer o login na aba 'Entrar no Sistema'."
            )
          else:
            usuarios_filtrados = [
                u
                for u in usuarios_atuais
                if u["usuario"].strip().lower() != usr_clean
                and u["nome"].strip().lower() != novo_nome.strip().lower()
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
            usuarios_filtrados.append(novo_user_dict)
            salvar_dados(ARQUIVO_USUARIOS, usuarios_filtrados)

            integrantes_atuais = carregar_dados(ARQUIVO_INTEGRANTES, [])
            integrantes_filtrados = [
                p
                for p in integrantes_atuais
                if p["Nome"].strip().lower() != novo_nome.strip().lower()
            ]

            integrantes_filtrados.append({
                "Nome": novo_nome.strip(),
                "Categoria": nova_categoria,
                "Vínculo": novo_vinculo.strip(),
                "Telefone": novo_telefone.strip(),
                "Email": novo_email.strip(),
                "Situação": "Pendente",
            })
            salvar_dados(ARQUIVO_INTEGRANTES, integrantes_filtrados)

            st.success(
                f"Solicitação enviada com sucesso! O nome '{novo_nome.strip()}'"
                " foi adicionado à lista de integrantes."
                " Aguarde a aprovação do Administrador para realizar o login."
            )

# --- ÁREA LOGADA (SISTEMA PRINCIPAL) ---
else:
  usuario_atual = st.session_state.usuario_logado
  is_admin = usuario_atual.get("is_admin", False)

  st.sidebar.title("🧪 Central LTAB")
  st.sidebar.caption("Laboratório de Pesquisa & Desenvolvimento")

  st.sidebar.markdown(
      '<div class="sidebar-section">VISÃO GERAL</div>', unsafe_allow_html=True
  )
  opcoes_menu = ["🏠 Início / Visão Geral", "📅 Agenda & Compromissos"]

  st.sidebar.markdown(
      '<div class="sidebar-section">GESTÃO DO LABORATÓRIO</div>',
      unsafe_allow_html=True,
  )
  if is_admin:
    opcoes_menu.append("👥 Gestão de Integrantes")
    opcoes_menu.append("🔑 Central de Aprovações")
  else:
    opcoes_menu.append("👥 Equipe do Laboratório")

  st.sidebar.markdown(
      '<div class="sidebar-section">FERRAMENTAS & DOCUMENTOS</div>',
      unsafe_allow_html=True,
  )
  opcoes_menu.append("🏷️ Gerar QR Code de Amostras")
  opcoes_menu.append("📁 Repositório de Arquivos")
  opcoes_menu.append("📝 Criador de POP Padrão")

  st.sidebar.markdown(
      '<div class="sidebar-section">MINHA CONTA</div>', unsafe_allow_html=True
  )
  opcoes_menu.append("👤 Meu Perfil")

  menu_selecionado = st.sidebar.radio("Navegação:", opcoes_menu)

  st.sidebar.markdown("---")
  st.sidebar.write(f"Usuário: **{usuario_atual['nome']}**")
  if is_admin:
    st.sidebar.caption("🟢 **Administrador**")
  else:
    st.sidebar.caption("🔵 Pesquisador")

  if st.sidebar.button("🚪 Sair da conta"):
    st.query_params.clear()
    st.session_state.usuario_logado = None
    st.rerun()

  # --- 1. VISÃO GERAL ---
  if menu_selecionado == "🏠 Início / Visão Geral":
    st.title("Visão geral")
    st.caption("Informações e recursos do Laboratório de Pesquisa.")

    with st.container():
      st.markdown(
          """
            <div style="background-color: #FFF9E6; border-left: 5px solid #FFC107; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                <h4 style="margin:0; color: #856404;">📣 AVISOS IMPORTANTES</h4>
                <p style="margin:5px 0 0 0; color: #856404;">
                    Mantenham o Lattes atualizado e lembrem-se de registrar o uso das bancadas e equipamentos na agenda.
                </p>
            </div>
            """,
          unsafe_allow_html=True,
      )

    integrantes_vis = carregar_dados(ARQUIVO_INTEGRANTES, [])
    agenda_vis = carregar_dados(ARQUIVO_AGENDA, [])

    col_m1, col_m2, col_m3 = st.columns(3)
    ativos_cnt = sum(
        1 for p in integrantes_vis if p.get("Situação") == "Ativo"
    )
    alunos_cnt = sum(
        1
        for p in integrantes_vis
        if p.get("Categoria") != "Orientador" and p.get("Situação") == "Ativo"
    )
    agenda_cnt = len(agenda_vis)

    col_m1.metric("Integrantes Ativos", ativos_cnt)
    col_m2.metric("Pesquisadores / Alunos", alunos_cnt)
    col_m3.metric("Agendamentos Ativos", agenda_cnt)

    st.markdown("---")

    col_esq, col_dir = st.columns([1.2, 1])

    with col_esq:
      st.subheader("📋 Tabela de Integrantes do Laboratório")
      if integrantes_vis:
        df_int = pd.DataFrame(integrantes_vis)
        cols_viz = [
            "Nome",
            "Categoria",
            "Vínculo",
            "Telefone",
            "Email",
            "Situação",
        ]
        for col in cols_viz:
          if col not in df_int.columns:
            df_int[col] = "-"
        st.dataframe(df_int[cols_viz], use_container_width=True)
      else:
        st.info("Nenhum integrante cadastrado.")

    with col_dir:
      st.subheader("📅 Próximos Compromissos")
      if agenda_vis:
        df_ag = pd.DataFrame(agenda_vis)
        st.dataframe(
            df_ag[["Data", "Início", "Título", "Responsável"]].tail(5),
            use_container_width=True,
        )
      else:
        st.info("Nenhum compromisso agendado recentemente.")

  # --- 2. AGENDA & COMPROMISSOS ---
  elif menu_selecionado == "📅 Agenda & Compromissos":
    st.title("📅 Agenda do Laboratório")

    col_esq, col_dir = st.columns([1, 1.2])

    with col_esq:
      st.subheader("➕ Agendar Horário / Equipamento")
      with st.form("form_agenda"):
        titulo = st.text_input(
            "Título do Compromisso", "Uso do Espectrofotômetro"
        )
        data_evento = st.date_input("Data do Evento", datetime.now().date())

        c1, c2 = st.columns(2)
        with c1:
          hora_inicio = st.time_input("Horário Inicial", time(9, 0))
        with c2:
          hora_fim = st.time_input("Horário Final", time(11, 0))

        equipamento = st.selectbox(
            "Equipamento / Bancada",
            [
                "Bancada A",
                "Bancada B",
                "Espectrofotômetro",
                "Autoclave",
                "Centrífuga",
                "Reunião de Grupo",
            ],
        )

        integrantes_ag = carregar_dados(ARQUIVO_INTEGRANTES, [])
        lista_resp = [p["Nome"] for p in integrantes_ag if p.get("Nome")]
        responsavel = (
            st.selectbox("Pesquisador Responsável", lista_resp)
            if lista_resp
            else st.text_input("Pesquisador Responsável")
        )

        obs = st.text_input("Observações / Detalhes", "Análise de amostras")
        btn_agendar = st.form_submit_button("Confirmar Agendamento")

        if btn_agendar and titulo:
          agenda_fresca = carregar_dados(ARQUIVO_AGENDA, [])
          novo_evento = {
              "ID": len(agenda_fresca) + 1,
              "Título": titulo,
              "Data": data_evento.strftime("%Y-%m-%d"),
              "Início": hora_inicio.strftime("%H:%M"),
              "Término": hora_fim.strftime("%H:%M"),
              "Equipamento": equipamento,
              "Responsável": responsavel,
              "criador": usuario_atual["usuario"],
              "Observações": obs,
          }
          agenda_fresca.append(novo_evento)
          salvar_dados(ARQUIVO_AGENDA, agenda_fresca)
          st.success("Evento agendado com sucesso!")
          st.rerun()

    with col_dir:
      st.subheader("🗓️ Consultar Compromissos por Data")
      data_consulta = st.date_input(
          "Selecione o dia:", datetime.now().date(), key="dt_cons"
      )
      data_str = data_consulta.strftime("%Y-%m-%d")

      agenda_cons = carregar_dados(ARQUIVO_AGENDA, [])
      eventos_dia = [e for e in agenda_cons if e["Data"] == data_str]

      if eventos_dia:
        for ev in eventos_dia:
          with st.expander(
              f"⏰ {ev['Início']} - {ev['Término']} | {ev['Título']}"
          ):
            st.write(f"**Local:** {ev['Equipamento']}")
            st.write(f"**Responsável:** {ev['Responsável']}")
            st.write(f"**Observações:** {ev['Observações']}")
      else:
        st.info("Nenhum agendamento para este dia.")

    st.markdown("---")
    st.subheader("📋 Lista Completa de Agendamentos")

    agenda_full = carregar_dados(ARQUIVO_AGENDA, [])
    if agenda_full:
      df_ag_full = pd.DataFrame(agenda_full)
      st.dataframe(
          df_ag_full[
              [
                  "Data",
                  "Início",
                  "Término",
                  "Título",
                  "Equipamento",
                  "Responsável",
                  "Observações",
              ]
          ].sort_values(by=["Data", "Início"]),
          use_container_width=True,
      )

      st.markdown("### ❌ Cancelar / Excluir Agendamento")

      if is_admin:
        meus_eventos = agenda_full
      else:
        meus_eventos = [
            e
            for e in agenda_full
            if e.get("criador") == usuario_atual["usuario"]
            or e.get("Responsável", "").lower()
            == usuario_atual["nome"].lower()
        ]

      if meus_eventos:
        opcoes_c = [
            f"ID {e['ID']} - {e['Data']} [{e['Início']}] {e['Título']}"
            f" ({e.get('Responsável', '-')})"
            for e in meus_eventos
        ]
        sel_c = st.selectbox("Selecione o agendamento para remover:", opcoes_c)

        if st.button("Remover Agendamento", type="primary"):
          id_del = int(sel_c.split(" ")[1])
          agenda_restante = [e for e in agenda_full if e["ID"] != id_del]
          salvar_dados(ARQUIVO_AGENDA, agenda_restante)
          st.success("Agendamento cancelado com sucesso!")
          st.rerun()
      else:
        st.caption("Você não possui agendamentos cadastrados para cancelar.")

  # --- 3. GESTÃO DE INTEGRANTES / EQUIPE ---
  elif menu_selecionado in [
      "👥 Gestão de Integrantes",
      "👥 Equipe do Laboratório",
  ]:
    st.title("👥 Integrantes do Laboratório")

    integrantes_atuais = carregar_dados(ARQUIVO_INTEGRANTES, [])

    if is_admin:
      st.subheader("➕ Cadastrar ou Editar Integrante Manualmente")
      with st.form("form_cad_int"):
        nome = st.text_input("Nome Completo")
        categoria = st.selectbox("Categoria", CATEGORIAS_PADRAO)
        vinculo = st.text_input(
            "Vínculo / Curso", "UFRRJ - Engenharia de Alimentos"
        )
        telefone = st.text_input("Telefone de Contato")
        email = st.text_input("E-mail de Contato")
        situacao = st.selectbox("Situação", ["Ativo", "Pendente", "Inativo"])
        btn_salv = st.form_submit_button("Salvar Integrante")

        if btn_salv and nome:
          existente = next(
              (
                  p
                  for p in integrantes_atuais
                  if p["Nome"].lower() == nome.strip().lower()
              ),
              None,
          )
          if existente:
            existente["Categoria"] = categoria
            existente["Vínculo"] = vinculo
            existente["Telefone"] = telefone
            existente["Email"] = email
            existente["Situação"] = situacao
          else:
            integrantes_atuais.append({
                "Nome": nome.strip(),
                "Categoria": categoria,
                "Vínculo": vinculo,
                "Telefone": telefone,
                "Email": email,
                "Situação": situacao,
            })

          salvar_dados(ARQUIVO_INTEGRANTES, integrantes_atuais)
          st.success(f"Integrante {nome} salvo com sucesso!")
          st.rerun()

      st.markdown("---")
      st.subheader("🗑️ Remover Integrante")
      lista_nomes = [p["Nome"] for p in integrantes_atuais]
      if lista_nomes:
        sel_rem = st.selectbox("Selecione quem deseja remover:", lista_nomes)
        if st.button("Excluir das Listas", type="primary"):
          integrantes_limpos = [
              p for p in integrantes_atuais if p["Nome"] != sel_rem
          ]
          salvar_dados(ARQUIVO_INTEGRANTES, integrantes_limpos)

          usrs_atuais = carregar_dados(ARQUIVO_USUARIOS, usuario_admin_padrao)
          usrs_limpos = [
              u for u in usrs_atuais if u["nome"].lower() != sel_rem.lower()
          ]
          salvar_dados(ARQUIVO_USUARIOS, usrs_limpos)

          st.success(f"Integrante '{sel_rem}' removido!")
          st.rerun()

    else:
      df_eq = pd.DataFrame(integrantes_atuais)
      st.dataframe(df_eq, use_container_width=True)

  # --- 4. GERAR QR CODE DE AMOSTRAS ---
  elif menu_selecionado == "🏷️ Gerar QR Code de Amostras":
    st.title("🧪 Gerador de QR Code de Amostras & Etiquetas")

    col_f, col_q = st.columns([1.2, 1])

    with col_f:
      id_amostra = st.text_input("Código / ID da Amostra", "AMS-2026-001")
      nome_amostra = st.text_input(
          "Nome da Amostra / Reagente", "Extrato Enzimático de Lipase"
      )
      data_obtencao = st.date_input(
          "Data de Obtenção / Produção", datetime.now().date()
      )

      integrantes_qr = carregar_dados(ARQUIVO_INTEGRANTES, [])
      lista_cadastrados = [p["Nome"] for p in integrantes_qr if p.get("Nome")]

      # Opção de digitar manualmente no topo para fácil acesso
      opcoes_resp = ["✍️ Digitar nome manualmente..."] + lista_cadastrados
      sel_resp = st.selectbox("Pesquisador Responsável", opcoes_resp)

      tel_resp = "-"
      email_resp = "-"

      if sel_resp == "✍️ Digitar nome manualmente...":
        responsavel = st.text_input(
            "Nome do Pesquisador Responsável *", "Gabriela Mendes Farias Matos"
        )
        tel_resp = st.text_input("Telefone do Responsável")
        email_resp = st.text_input("E-mail do Responsável")
      else:
        responsavel = sel_resp
        integrante_sel = next(
            (p for p in integrantes_qr if p["Nome"] == sel_resp), None
        )
        if integrante_sel:
          tel_resp = integrante_sel.get("Telefone", "-")
          email_resp = integrante_sel.get("Email", "-")
          st.info(
              f"📞 **Contatos do Responsável:**\n- **Telefone:**"
              f" {tel_resp}\n- **E-mail:** {email_resp}"
          )

      localizacao = st.text_input(
          "Local de Armazenamento", "Freezer -20°C / Caixa 3 / Posição B4"
      )

      st.markdown("---")
      st.subheader("🖨️ Configurações para Impressão")
      c_dest, c_qtd = st.columns([1.5, 1])
      with c_dest:
        dest_selecionado = st.selectbox(
            "Onde vai pôr o QR Code?", list(DESTINOS_ETIQUETAS.keys())
        )
        tamanho_mm = DESTINOS_ETIQUETAS[dest_selecionado]
        st.caption(
            f"📐 Tamanho sugerido para este recipiente: **{tamanho_mm} x"
            f" {tamanho_mm} mm**"
        )

      with c_qtd:
        qtd_etiquetas = st.number_input(
            "Quantidade de Etiquetas", min_value=1, max_value=100, value=6
        )

      descricao = st.text_area(
          "Descrição Detalhada / Protocolo",
          value=(
              "Extrato obtido via fermentação estado sólido. Tampão fosfato"
              " 0.1M pH 7.0."
          ),
          height=80,
      )
      gerar = st.button("Gerar Etiqueta QR Code")

    with col_q:
      if gerar or id_amostra:
        conteudo_qr = (
            "=== FICHA DA AMOSTRA ===\n"
            f"ID: {id_amostra}\n"
            f"NOME: {nome_amostra}\n"
            f"RESPONSÁVEL: {responsavel}\n"
            f"CONTATO: Tel {tel_resp} | Email {email_resp}\n"
            f"DATA OBTENÇÃO: {data_obtencao.strftime('%d/%m/%Y')}\n"
            f"LOCAL: {localizacao}\n"
            "------------------------\n"
            f"DESCRIÇÃO:\n{descricao}\n"
            "========================"
        )

        img = qrcode.make(conteudo_qr)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_bytes = buffer.getvalue()

        st.image(
            img_bytes, caption=f"Pré-visualização: {id_amostra}", width=240
        )

        st.download_button(
            label="🖼️ Baixar QR Code em Imagem (PNG)",
            data=img_bytes,
            file_name=f"QR_{id_amostra}.png",
            mime="image/png",
        )

        pdf_etiquetas = gerar_pdf_etiquetas(img, qtd_etiquetas, tamanho_mm)

        st.download_button(
            label=f"📄 Baixar PDF para Impressão ({qtd_etiquetas}x Etiquetas)",
            data=pdf_etiquetas,
            file_name=f"Etiquetas_{id_amostra}_{tamanho_mm}mm.pdf",
            mime="application/pdf",
            type="primary",
        )

  # --- 5. REPOSITÓRIO DE ARQUIVOS ---
  elif menu_selecionado == "📁 Repositório de Arquivos":
    st.title("📁 Central de Arquivos & Documentos")

    aba_docs, aba_upload, aba_nova_pasta = st.tabs(
        ["📚 Documentos por Pasta", "📥 Enviar Arquivo", "📁 Solicitar Nova Pasta"]
    )

    pastas_atuais = carregar_dados(ARQUIVO_PASTAS, PASTAS_INICIAIS)
    pastas_aprovadas = [
        p["nome"] for p in pastas_atuais if p.get("status") == "Aprovado"
    ]

    with aba_docs:
      st.subheader("Biblioteca de Documentos do Laboratório")

      col_f1, col_f2 = st.columns([1, 2])
      with col_f1:
        pasta_filtro = st.selectbox(
            "Filtrar por Pasta:", ["Todas as Pastas"] + pastas_aprovadas
        )

      arquivos_atuais = carregar_dados(ARQUIVO_ARQUIVOS, [])
      aprovados_arq = [
          a for a in arquivos_atuais if a.get("status") == "Aprovado"
      ]

      if pasta_filtro != "Todas as Pastas":
        aprovados_arq = [
            a for a in aprovados_arq if a.get("pasta") == pasta_filtro
        ]

      if aprovados_arq:
        for doc in aprovados_arq:
          with st.container():
            st.markdown(
                f"""
                        <div class="css-card">
                            <h4 style="margin:0; color:#0D47A1;">📄 {doc['titulo']}</h4>
                            <p style="margin:4px 0; color:#555;"><b>Pasta:</b> {doc.get('pasta', 'Geral')} | <b>Enviado por:</b> {doc['autor']} em {doc['data']}</p>
                            <p style="margin:4px 0; color:#666;"><i>{doc['descricao']}</i></p>
                        </div>
                        """,
                unsafe_allow_html=True,
            )

            caminho_arq = doc.get("caminho")
            if caminho_arq and os.path.exists(caminho_arq):
              with open(caminho_arq, "rb") as f:
                bytes_f = f.read()
              st.download_button(
                  label=f"⬇️ Baixar {doc['nome_original']}",
                  data=bytes_f,
                  file_name=doc["nome_original"],
                  key=f"dl_{doc['id']}",
              )
            else:
              st.caption("Ficheiro indisponível no servidor.")
            st.markdown("---")
      else:
        st.info("Nenhum documento encontrado nesta pasta.")

    with aba_upload:
      st.subheader("Enviar Arquivo para Avaliação do Administrador")
      with st.form("form_upload_arq"):
        tit_doc = st.text_input("Título do Documento *")
        pasta_doc = st.selectbox("Selecione a Pasta *", pastas_aprovadas)
        desc_doc = st.text_area("Descrição / Detalhes do Arquivo *", height=80)
        arq_up = st.file_uploader(
            "Selecione o Ficheiro (PDF, DOCX, XLSX, PNG, JPG, CSV, TXT) *",
            type=["pdf", "docx", "xlsx", "png", "jpg", "csv", "txt"],
        )

        btn_enviar_doc = st.form_submit_button("Enviar Documento")

        if btn_enviar_doc:
          if not (tit_doc and desc_doc and arq_up):
            st.error("Preencha todos os campos e selecione um ficheiro.")
          else:
            data_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_seguro = f"{data_str}_{arq_up.name}"
            caminho_final = os.path.join(PASTA_UPLOADS, nome_seguro)

            with open(caminho_final, "wb") as f:
              f.write(arq_up.getbuffer())

            arquivos_atuais = carregar_dados(ARQUIVO_ARQUIVOS, [])
            novo_registro_arq = {
                "id": len(arquivos_atuais) + 1,
                "titulo": tit_doc.strip(),
                "pasta": pasta_doc,
                "descricao": desc_doc.strip(),
                "nome_original": arq_up.name,
                "caminho": caminho_final,
                "autor": usuario_atual["nome"],
                "data": datetime.now().strftime("%d/%m/%Y"),
                "status": "Pendente",
            }

            arquivos_atuais.append(novo_registro_arq)
            salvar_dados(ARQUIVO_ARQUIVOS, arquivos_atuais)

            st.success(
                "Documento enviado com sucesso! Ele aparecerá no repositório"
                " após a aprovação do Administrador."
            )

    with aba_nova_pasta:
      st.subheader("Solicitar Criação de Nova Pasta")
      with st.form("form_nova_pasta"):
        nome_pasta = st.text_input("Nome da Nova Pasta (ex: Cromatografia) *")
        desc_pasta = st.text_input("Descrição / Finalidade da Pasta *")
        btn_pasta = st.form_submit_button("Enviar Solicitação de Pasta")

        if btn_pasta:
          if not (nome_pasta and desc_pasta):
            st.error("Preencha o nome e a descrição da nova pasta.")
          else:
            p_clean = nome_pasta.strip()
            pastas_atuais = carregar_dados(ARQUIVO_PASTAS, PASTAS_INICIAIS)
            ja_existe = any(
                p["nome"].lower() == p_clean.lower() for p in pastas_atuais
            )

            if ja_existe:
              st.error("Esta pasta já existe ou foi solicitada previamente.")
            else:
              pastas_atuais.append({
                  "nome": p_clean,
                  "descricao": desc_pasta.strip(),
                  "criador": usuario_atual["nome"],
                  "status": "Pendente",
              })
              salvar_dados(ARQUIVO_PASTAS, pastas_atuais)
              st.success(
                  f"Solicitação para criar a pasta '{p_clean}' enviada com"
                  " sucesso! Aguarde a aprovação do Administrador."
              )

  # --- 6. CRIADOR DE POP PADRÃO ---
  elif menu_selecionado == "📝 Criador de POP Padrão":
    st.title("📝 Criador e Atualizador de POP Padrão")
    st.caption(
        "Gere novos POPs ou atualize versões existentes. O sistema verifica"
        " automaticamente duplicidades de nomes."
    )

    pops_atuais = carregar_dados(ARQUIVO_POPS, POPS_INICIAIS)
    busca_pop = st.text_input(
        "🔎 Buscar POP existente por título ou código:", ""
    )

    pops_filtrados = pops_atuais
    if busca_pop.strip():
      pops_filtrados = [
          p
          for p in pops_atuais
          if busca_pop.lower() in p["codigo"].lower()
          or busca_pop.lower() in p["titulo"].lower()
      ]

    opcoes_pops = [
        f"{p['codigo']} - {p['titulo']}" for p in pops_filtrados
    ] + ["➕ Cadastrar Novo POP..."]

    sel_pop_opcao = st.selectbox(
        "Selecione um POP para Atualizar ou Crie um Novo:", opcoes_pops
    )

    if sel_pop_opcao == "➕ Cadastrar Novo POP...":
      is_novo = True
      num_pop = len(pops_atuais) + 1
      cod_pop = f"POP-LTAB-{num_pop:03d}"
      versao_num = 1
      versao_pop = "v1.0"
      titulo_default = ""
      obj_default = ""
      mat_default = ""
      passos_default = ""
      sec_default = ""
    else:
      is_novo = False
      pop_existente = next(
          p
          for p in pops_atuais
          if f"{p['codigo']} - {p['titulo']}" == sel_pop_opcao
      )
      cod_pop = pop_existente["codigo"]
      versao_num = pop_existente.get("versao", 1) + 1
      versao_pop = f"v{versao_num}.0"
      titulo_default = pop_existente["titulo"]
      obj_default = pop_existente.get("objetivo", "")
      mat_default = pop_existente.get("materiais", "")
      passos_default = pop_existente.get("passos", "")
      sec_default = pop_existente.get("seguranca", "")

    st.markdown("---")

    with st.form("form_pop_auto"):
      col_p1, col_p2, col_p3 = st.columns([1, 1, 1])
      with col_p1:
        st.text_input("Código do POP (Automático)", value=cod_pop, disabled=True)
      with col_p2:
        st.text_input(
            "Versão do POP (Automático)", value=versao_pop, disabled=True
        )
      with col_p3:
        st.text_input(
            "Elaborado por (Usuário Logado)",
            value=usuario_atual["nome"],
            disabled=True,
        )

      if is_novo:
        tit_pop = st.text_input(
            "Título do Novo POP *",
            placeholder="ex: Preparo de Solução e Tampões",
        )
      else:
        st.text_input("Título do POP", value=titulo_default, disabled=True)
        tit_pop = titulo_default

      obj_pop = st.text_area(
          "Objetivo do POP *", value=obj_default, height=80
      )
      mat_pop = st.text_area(
          "Materiais, Reagentes e Equipamentos *", value=mat_default, height=80
      )
      passos_pop = st.text_area(
          "Passo a Passo do Procedimento (Numerado) *",
          value=passos_default,
          height=150,
      )
      sec_pop = st.text_area(
          "Cuidados de Segurança e EPIs *", value=sec_default, height=80
      )

      btn_salvar_pop = st.form_submit_button(
          "💾 Salvar e Gerar Documento POP", type="primary"
      )

      if btn_salvar_pop:
        if not (tit_pop and obj_pop and mat_pop and passos_pop and sec_pop):
          st.error("Por favor, preencha todos os campos do formulário.")
        else:
          duplicado = False
          if is_novo:
            duplicado = any(
                p["titulo"].strip().lower() == tit_pop.strip().lower()
                for p in pops_atuais
            )

          if duplicado:
            st.error(
                f"❌ Erro: Já existe um POP cadastrado com o título '{tit_pop}'!"
                " Por favor, pesquise o POP existente na lista para criar uma"
                " nova versão."
            )
          else:
            if is_novo:
              novo_pop_dict = {
                  "codigo": cod_pop,
                  "titulo": tit_pop.strip(),
                  "versao": 1,
                  "objetivo": obj_pop.strip(),
                  "materiais": mat_pop.strip(),
                  "passos": passos_pop.strip(),
                  "seguranca": sec_pop.strip(),
                  "autor": usuario_atual["nome"],
              }
              pops_atuais.append(novo_pop_dict)
            else:
              pop_existente["versao"] = versao_num
              pop_existente["objetivo"] = obj_pop.strip()
              pop_existente["materiais"] = mat_pop.strip()
              pop_existente["passos"] = passos_pop.strip()
              pop_existente["seguranca"] = sec_pop.strip()
              pop_existente["autor"] = usuario_atual["nome"]

            salvar_dados(ARQUIVO_POPS, pops_atuais)
            st.success(
                f"POP '{cod_pop}' ({versao_pop}) salvo com sucesso por"
                f" {usuario_atual['nome']}!"
            )
            st.rerun()

    if tit_pop:
      conteudo_pop = f"""================================================================================
                    LABORATÓRIO LTAB - PROCEDIMENTO OPERACIONAL PADRÃO (POP)
================================================================================
CÓDIGO: {cod_pop}               VERSÃO: {versao_pop}
DATA DE EDIÇÃO: {datetime.now().strftime('%d/%m/%Y')}
TÍTULO: {tit_pop}
ELABORADO POR: {usuario_atual['nome']}
================================================================================

1. OBJETIVO:
{obj_pop}

2. MATERIAIS E EQUIPAMENTOS NECESSÁRIOS:
{mat_pop}

3. PROCEDIMENTO OPERACIONAL (PASSO A PASSO):
{passos_pop}

4. SEGURANÇA E EPIS:
{sec_pop}
================================================================================
"""
      st.markdown("---")
      st.subheader("📄 Visualização do Documento Formatado")
      st.code(conteudo_pop, language="markdown")

      col_d1, col_d2 = st.columns(2)
      with col_d1:
        st.download_button(
            label="⬇️ Baixar POP em Texto (.txt)",
            data=conteudo_pop.encode("utf-8"),
            file_name=f"{cod_pop}_{versao_pop}.txt",
            mime="text/plain",
        )
      with col_d2:
        if st.button("📤 Enviar POP para Repositório (Requer Aprovação)"):
          data_str = datetime.now().strftime("%Y%m%d_%H%M%S")
          nome_pop_file = f"{cod_pop}_{versao_pop}_{data_str}.txt"
          caminho_pop = os.path.join(PASTA_UPLOADS, nome_pop_file)

          with open(caminho_pop, "w", encoding="utf-8") as f:
            f.write(conteudo_pop)

          arqs_frescos = carregar_dados(ARQUIVO_ARQUIVOS, [])
          arqs_frescos.append({
              "id": len(arqs_frescos) + 1,
              "titulo": f"POP {cod_pop}: {tit_pop} ({versao_pop})",
              "pasta": "POPs e Protocolos",
              "descricao": (
                  f"POP {cod_pop} ({versao_pop}) elaborado por"
                  f" {usuario_atual['nome']}."
              ),
              "nome_original": nome_pop_file,
              "caminho": caminho_pop,
              "autor": usuario_atual["nome"],
              "data": datetime.now().strftime("%d/%m/%Y"),
              "status": "Pendente",
          })
          salvar_dados(ARQUIVO_ARQUIVOS, arqs_frescos)
          st.success("POP enviado para aprovação do Administrador!")

  # --- 7. CENTRAL DE APROVAÇÕES (EXCLUSIVO ADMIN) ---
  elif menu_selecionado == "🔑 Central de Aprovações" and is_admin:
    st.title("🔑 Central de Aprovações (Administrador)")

    tab_acessos, tab_perfis, tab_files, tab_folders, tab_direto = st.tabs([
        "1. Novos Acessos",
        "2. Alterações de Perfil",
        "3. Aprovar Arquivos",
        "4. Aprovar Pastas",
        "⚡ Cadastrar & Aprovar Direto",
    ])

    with tab_acessos:
      usrs_tempo_real = carregar_dados(ARQUIVO_USUARIOS, usuario_admin_padrao)
      pend_acessos = [
          u for u in usrs_tempo_real if u.get("status") == "Pendente"
      ]

      if pend_acessos:
        for idx, u in enumerate(pend_acessos):
          c_inf, c_b1, c_b2 = st.columns([3, 1, 1])
          with c_inf:
            st.write(f"👤 **{u['nome']}** (Usuário: `{u['usuario']}`)")
            st.caption(
                f"Cat: {u.get('categoria','-')} | Tel: {u.get('telefone','-')} |"
                f" Email: {u.get('email','-')}"
            )
          with c_b1:
            if st.button("✅ Aprovar", key=f"ap_usr_{idx}", type="primary"):
              usrs_atuais = carregar_dados(
                  ARQUIVO_USUARIOS, usuario_admin_padrao
              )
              for usr_item in usrs_atuais:
                if usr_item["usuario"] == u["usuario"]:
                  usr_item["status"] = "Aprovado"

              salvar_dados(ARQUIVO_USUARIOS, usrs_atuais)

              ints_atuais = carregar_dados(ARQUIVO_INTEGRANTES, [])
              for p in ints_atuais:
                if p["Nome"].lower() == u["nome"].lower():
                  p["Situação"] = "Ativo"
                  p["Categoria"] = u.get("categoria", p.get("Categoria"))
                  p["Telefone"] = u.get("telefone", p.get("Telefone", "-"))
                  p["Email"] = u.get("email", p.get("Email", "-"))

              salvar_dados(ARQUIVO_INTEGRANTES, ints_atuais)
              st.success(f"Acesso aprovado para {u['nome']}!")
              st.rerun()
          with c_b2:
            if st.button("❌ Recusar", key=f"rec_usr_{idx}"):
              usrs_atuais = carregar_dados(
                  ARQUIVO_USUARIOS, usuario_admin_padrao
              )
              for usr_item in usrs_atuais:
                if usr_item["usuario"] == u["usuario"]:
                  usr_item["status"] = "Recusado"

              salvar_dados(ARQUIVO_USUARIOS, usrs_atuais)
              st.warning(f"Solicitação de {u['nome']} recusada.")
              st.rerun()
      else:
        st.info("Nenhuma solicitação de novo acesso pendente no momento.")

    with tab_perfis:
      usrs_tempo_real = carregar_dados(ARQUIVO_USUARIOS, usuario_admin_padrao)
      pend_perfis = [u for u in usrs_tempo_real if u.get("pendente_atualizacao")]
      if pend_perfis:
        for idx, u in enumerate(pend_perfis):
          p_data = u["pendente_atualizacao"]
          c_inf, c_b1, c_b2 = st.columns([3, 1, 1])
          with c_inf:
            st.write(f"👤 **{u['nome']}** (`{u['usuario']}`)")
            st.caption(
                f"Novo Tel: {p_data.get('telefone')} | Novo Email:"
                f" {p_data.get('email')}"
            )
          with c_b1:
            if st.button(
                "✅ Aprovar Mudança", key=f"ap_prf_{idx}", type="primary"
            ):
              usrs_atuais = carregar_dados(
                  ARQUIVO_USUARIOS, usuario_admin_padrao
              )
              for usr_item in usrs_atuais:
                if usr_item["usuario"] == u["usuario"]:
                  usr_item["categoria"] = p_data.get("categoria")
                  usr_item["vinculo"] = p_data.get("vinculo")
                  usr_item["telefone"] = p_data.get("telefone")
                  usr_item["email"] = p_data.get("email")
                  if "pendente_atualizacao" in usr_item:
                    del usr_item["pendente_atualizacao"]

              salvar_dados(ARQUIVO_USUARIOS, usrs_atuais)

              ints_atuais = carregar_dados(ARQUIVO_INTEGRANTES, [])
              for p in ints_atuais:
                if p["Nome"].lower() == u["nome"].lower():
                  p["Categoria"] = p_data.get("categoria")
                  p["Vínculo"] = p_data.get("vinculo")
                  p["Telefone"] = p_data.get("telefone")
                  p["Email"] = p_data.get("email")

              salvar_dados(ARQUIVO_INTEGRANTES, ints_atuais)
              st.success(f"Perfil de {u['nome']} atualizado!")
              st.rerun()
          with c_b2:
            if st.button("❌ Recusar", key=f"rec_prf_{idx}"):
              usrs_atuais = carregar_dados(
                  ARQUIVO_USUARIOS, usuario_admin_padrao
              )
              for usr_item in usrs_atuais:
                if (
                    usr_item["usuario"] == u["usuario"]
                    and "pendente_atualizacao" in usr_item
                ):
                  del usr_item["pendente_atualizacao"]
              salvar_dados(ARQUIVO_USUARIOS, usrs_atuais)
              st.warning("Mudança recusada.")
              st.rerun()
      else:
        st.info("Nenhuma alteração de perfil pendente.")

    with tab_files:
      arqs_tempo_real = carregar_dados(ARQUIVO_ARQUIVOS, [])
      pend_arquivos = [
          a for a in arqs_tempo_real if a.get("status") == "Pendente"
      ]
      if pend_arquivos:
        for idx, doc in enumerate(pend_arquivos):
          c_inf, c_b1, c_b2 = st.columns([3, 1, 1])
          with c_inf:
            st.write(
                f"📄 **{doc['titulo']}** (Pasta: {doc.get('pasta','Geral')})"
            )
            st.caption(
                f"Enviado por: {doc['autor']} | Ficheiro:"
                f" {doc['nome_original']}"
            )
            st.caption(f"Descrição: {doc['descricao']}")

          with c_b1:
            if st.button(
                "✅ Aprovar Ficheiro", key=f"ap_file_{idx}", type="primary"
            ):
              arqs_atuais = carregar_dados(ARQUIVO_ARQUIVOS, [])
              for item in arqs_atuais:
                if item["id"] == doc["id"]:
                  item["status"] = "Aprovado"
              salvar_dados(ARQUIVO_ARQUIVOS, arqs_atuais)
              st.success(
                  f"Ficheiro '{doc['titulo']}' aprovado para publicação!"
              )
              st.rerun()
          with c_b2:
            if st.button("❌ Apagar Ficheiro", key=f"rec_file_{idx}"):
              arqs_atuais = carregar_dados(ARQUIVO_ARQUIVOS, [])
              if os.path.exists(doc.get("caminho", "")):
                try:
                  os.remove(doc["caminho"])
                except Exception:
                  pass
              arqs_filtrados = [
                  item for item in arqs_atuais if item["id"] != doc["id"]
              ]
              salvar_dados(ARQUIVO_ARQUIVOS, arqs_filtrados)
              st.warning("Ficheiro recusado e apagado.")
              st.rerun()
      else:
        st.info("Nenhum arquivo pendente de aprovação.")

    with tab_folders:
      pastas_tempo_real = carregar_dados(ARQUIVO_PASTAS, PASTAS_INICIAIS)
      pend_pastas = [
          p for p in pastas_tempo_real if p.get("status") == "Pendente"
      ]
      if pend_pastas:
        for idx, pst in enumerate(pend_pastas):
          c_inf, c_b1, c_b2 = st.columns([3, 1, 1])
          with c_inf:
            st.write(f"📁 **Pasta: {pst['nome']}**")
            st.caption(
                f"Solicitada por: {pst['criador']} | Descrição:"
                f" {pst['descricao']}"
            )

          with c_b1:
            if st.button(
                "✅ Aprovar Pasta", key=f"ap_fold_{idx}", type="primary"
            ):
              pastas_atuais = carregar_dados(ARQUIVO_PASTAS, PASTAS_INICIAIS)
              for p in pastas_atuais:
                if p["nome"] == pst["nome"]:
                  p["status"] = "Aprovado"
              salvar_dados(ARQUIVO_PASTAS, pastas_atuais)
              st.success(f"Pasta '{pst['nome']}' aprovada com sucesso!")
              st.rerun()

          with c_b2:
            if st.button("❌ Recusar Pasta", key=f"rec_fold_{idx}"):
              pastas_atuais = carregar_dados(ARQUIVO_PASTAS, PASTAS_INICIAIS)
              pastas_filtradas = [
                  p for p in pastas_atuais if p["nome"] != pst["nome"]
              ]
              salvar_dados(ARQUIVO_PASTAS, pastas_filtradas)
              st.warning(f"Solicitação da pasta '{pst['nome']}' recusada.")
              st.rerun()
      else:
        st.info("Nenhuma solicitação de nova pasta pendente.")

    with tab_direto:
      st.subheader("⚡ Atalho: Cadastrar e Aprovar Usuário Instantaneamente")
      st.caption(
          "Use esta ferramenta caso precise liberar o acesso de alguém de"
          " imediato sem depender da fila."
      )

      with st.form("form_cad_direto_admin"):
        c_dir1, c_dir2 = st.columns(2)
        with c_dir1:
          dir_nome = st.text_input("Nome Completo", "Gabriela Mendes")
          dir_user = st.text_input("Nome de Usuário", "gabriela matos")
          dir_senha = st.text_input("Senha para Acesso", "123456")
        with c_dir2:
          dir_cat = st.selectbox("Categoria", CATEGORIAS_PADRAO)
          dir_vinc = st.text_input("Vínculo", "UFRRJ - Engenharia Química")
          dir_tel = st.text_input("Telefone", "21996778065")
          dir_email = st.text_input("E-mail", "gbsmtsm@ufrrj.br")

        btn_cad_direto = st.form_submit_button(
            "⚡ Cadastrar e Liberar Acesso Agora", type="primary"
        )

        if btn_cad_direto:
          if not (dir_nome and dir_user and dir_senha):
            st.error("Preencha ao menos Nome, Usuário e Senha.")
          else:
            usrs_frescos = carregar_dados(
                ARQUIVO_USUARIOS, usuario_admin_padrao
            )
            clean_u = dir_user.strip().lower()

            usrs_frescos = [
                u
                for u in usrs_frescos
                if u["usuario"].strip().lower() != clean_u
            ]

            novo_usr_aprovado = {
                "nome": dir_nome.strip(),
                "usuario": dir_user.strip(),
                "senha": dir_senha,
                "categoria": dir_cat,
                "vinculo": dir_vinc.strip(),
                "telefone": dir_tel.strip(),
                "email": dir_email.strip(),
                "status": "Aprovado",
                "is_admin": False,
            }
            usrs_frescos.append(novo_usr_aprovado)
            salvar_dados(ARQUIVO_USUARIOS, usrs_frescos)

            ints_frescos = carregar_dados(ARQUIVO_INTEGRANTES, [])
            ints_frescos = [
                p
                for p in ints_frescos
                if p["Nome"].strip().lower() != dir_nome.strip().lower()
            ]
            ints_frescos.append({
                "Nome": dir_nome.strip(),
                "Categoria": dir_cat,
                "Vínculo": dir_vinc.strip(),
                "Telefone": dir_tel.strip(),
                "Email": dir_email.strip(),
                "Situação": "Ativo",
            })
            salvar_dados(ARQUIVO_INTEGRANTES, ints_frescos)

            st.success(
                f"✅ Usuário '{dir_user.strip()}' cadastrado e APROVADO com"
                " sucesso! O acesso já está liberado para login."
            )
            st.rerun()

  # --- 8. MEU PERFIL ---
  elif menu_selecionado == "👤 Meu Perfil":
    st.title("👤 Meu Perfil e Configurações")

    st.subheader("Meus Dados Registrados")
    c_p1, c_p2 = st.columns(2)
    with c_p1:
      st.write(f"**Nome:** {usuario_atual.get('nome')}")
      st.write(f"**Usuário:** `{usuario_atual.get('usuario')}`")
      st.write(f"**Categoria:** {usuario_atual.get('categoria', '-')}")
    with c_p2:
      st.write(f"**Vínculo:** {usuario_atual.get('vinculo', '-')}")
      st.write(f"**Telefone:** {usuario_atual.get('telefone', '-')}")
      st.write(f"**E-mail:** {usuario_atual.get('email', '-')}")

    st.markdown("---")
    st.subheader("✏️ Solicitar Alteração de Dados ao Administrador")

    with st.form("form_edit_perfil"):
      nova_cat = st.selectbox("Categoria", CATEGORIAS_PADRAO)
      novo_vinc = st.text_input(
          "Vínculo", value=usuario_atual.get("vinculo", "UFRRJ")
      )
      novo_tel = st.text_input(
          "Telefone (Obrigatório) *", value=usuario_atual.get("telefone", "")
      )
      novo_email = st.text_input(
          "E-mail (Obrigatório) *", value=usuario_atual.get("email", "")
      )

      btn_env_prof = st.form_submit_button("Enviar Alterações para Aprovação")

      if btn_env_prof:
        if not (novo_tel.strip() and novo_email.strip()):
          st.error("Preencha Telefone e E-mail.")
        else:
          dados_m = {
              "categoria": nova_cat,
              "vinculo": novo_vinc.strip(),
              "telefone": novo_tel.strip(),
              "email": novo_email.strip(),
          }

          usrs_frescos = carregar_dados(ARQUIVO_USUARIOS, usuario_admin_padrao)
          for u in usrs_frescos:
            if u["usuario"] == usuario_atual["usuario"]:
              u["pendente_atualizacao"] = dados_m
              break

          salvar_dados(ARQUIVO_USUARIOS, usrs_frescos)
          st.success("Solicitação enviada ao Administrador!")
          st.rerun()
