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
        background-color: #F4F8FB;
    }
    [data-testid="stSidebar"] {
        background-color: #EBF3FA;
        border-right: 1px solid #D6E4F0;
    }
    h1, h2, h3 {
        color: #0D47A1 !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .sidebar-section {
        font-size: 0.75rem;
        font-weight: 700;
        color: #5C768D;
        text-transform: uppercase;
        margin-top: 1.2rem;
        margin-bottom: 0.3rem;
        letter-spacing: 0.05em;
    }
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
    .css-card {
        background-color: white;
        padding: 18px;
        border-radius: 10px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        margin-bottom: 15px;
    }
    .drive-folder-card {
        background-color: white;
        border: 1px solid #CBD5E1;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 10px;
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


def gerar_pdf_etiquetas(qr_img_pil, quantidade, mm_size):
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

# --- INICIALIZAÇÃO DE SESSÃO PERSISTENTE NO SESSION_STATE ---
if "usuarios" not in st.session_state:
  st.session_state.usuarios = carregar_dados(
      ARQUIVO_USUARIOS, usuario_admin_padrao
  )
if "integrantes" not in st.session_state:
  st.session_state.integrantes = carregar_dados(
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

if "usr" in st.query_params:
  usr_param = st.query_params["usr"]
  usr_encontrado = next(
      (
          u
          for u in st.session_state.usuarios
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
        usr_clean = user_input.strip().lower()
        usuario_encontrado = None

        for u in st.session_state.usuarios:
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
          ja_aprovado = any(
              u["usuario"].strip().lower() == usr_clean
              and u.get("status") == "Aprovado"
              for u in st.session_state.usuarios
          )

          if ja_aprovado:
            st.error(
                "Este nome de usuário já pertence a uma conta APROVADA. Tente"
                " fazer o login na aba 'Entrar no Sistema'."
            )
          else:
            st.session_state.usuarios = [
                u
                for u in st.session_state.usuarios
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
            st.session_state.usuarios.append(novo_user_dict)
            salvar_dados(ARQUIVO_USUARIOS, st.session_state.usuarios)

            st.session_state.integrantes = [
                p
                for p in st.session_state.integrantes
                if p["Nome"].strip().lower() != novo_nome.strip().lower()
            ]
            st.session_state.integrantes.append({
                "Nome": novo_nome.strip(),
                "Categoria": nova_categoria,
                "Vínculo": novo_vinculo.strip(),
                "Telefone": novo_telefone.strip(),
                "Email": novo_email.strip(),
                "Situação": "Pendente",
            })
            salvar_dados(ARQUIVO_INTEGRANTES, st.session_state.integrantes)

            st.success(
                f"Solicitação enviada com sucesso! O nome '{novo_nome.strip()}'"
                " foi registrado. Aguarde a aprovação do Administrador."
            )

# --- ÁREA LOGADA ---
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

    col_m1, col_m2, col_m3 = st.columns(3)
    ativos_cnt = sum(
        1
        for p in st.session_state.integrantes
        if p.get("Situação") == "Ativo"
    )
    alunos_cnt = sum(
        1
        for p in st.session_state.integrantes
        if p.get("Categoria") != "Orientador" and p.get("Situação") == "Ativo"
    )
    agenda_cnt = len(st.session_state.agenda)

    col_m1.metric("Integrantes Ativos", ativos_cnt)
    col_m2.metric("Pesquisadores / Alunos", alunos_cnt)
    col_m3.metric("Agendamentos Ativos", agenda_cnt)

    st.markdown("---")

    col_esq, col_dir = st.columns([1.2, 1])

    with col_esq:
      st.subheader("📋 Tabela de Integrantes do Laboratório")
      if st.session_state.integrantes:
        df_int = pd.DataFrame(st.session_state.integrantes)
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
      if st.session_state.agenda:
        df_ag = pd.DataFrame(st.session_state.agenda)
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

        lista_resp = [
            p["Nome"]
            for p in st.session_state.integrantes
            if p.get("Nome")
        ]
        responsavel = (
            st.selectbox("Pesquisador Responsável", lista_resp)
            if lista_resp
            else st.text_input("Pesquisador Responsável")
        )

        obs = st.text_input("Observações / Detalhes", "Análise de amostras")
        btn_agendar = st.form_submit_button("Confirmar Agendamento")

        if btn_agendar and titulo:
          novo_evento = {
              "ID": len(st.session_state.agenda) + 1,
              "Título": titulo,
              "Data": data_evento.strftime("%Y-%m-%d"),
              "Início": hora_inicio.strftime("%H:%M"),
              "Término": hora_fim.strftime("%H:%M"),
              "Equipamento": equipamento,
              "Responsável": responsavel,
              "criador": usuario_atual["usuario"],
              "Observações": obs,
          }
          st.session_state.agenda.append(novo_evento)
          salvar_dados(ARQUIVO_AGENDA, st.session_state.agenda)
          st.success("Evento agendado com sucesso!")
          st.rerun()

    with col_dir:
      st.subheader("🗓️ Consultar Compromissos por Data")
      data_consulta = st.date_input(
          "Selecione o dia:", datetime.now().date(), key="dt_cons"
      )
      data_str = data_consulta.strftime("%Y-%m-%d")

      eventos_dia = [
          e for e in st.session_state.agenda if e["Data"] == data_str
      ]

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

    if st.session_state.agenda:
      df_ag_full = pd.DataFrame(st.session_state.agenda)
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
        meus_eventos = st.session_state.agenda
      else:
        meus_eventos = [
            e
            for e in st.session_state.agenda
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
          st.session_state.agenda = [
              e for e in st.session_state.agenda if e["ID"] != id_del
          ]
          salvar_dados(ARQUIVO_AGENDA, st.session_state.agenda)
          st.success("Agendamento cancelado com sucesso!")
          st.rerun()

  # --- 3. GESTÃO DE INTEGRANTES ---
  elif menu_selecionado in [
      "👥 Gestão de Integrantes",
      "👥 Equipe do Laboratório",
  ]:
    st.title("👥 Integrantes do Laboratório")

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
                  for p in st.session_state.integrantes
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
            st.session_state.integrantes.append({
                "Nome": nome.strip(),
                "Categoria": categoria,
                "Vínculo": vinculo,
                "Telefone": telefone,
                "Email": email,
                "Situação": situacao,
            })

          salvar_dados(ARQUIVO_INTEGRANTES, st.session_state.integrantes)
          st.success(f"Integrante {nome} salvo com sucesso!")
          st.rerun()

    df_eq = pd.DataFrame(st.session_state.integrantes)
    st.dataframe(df_eq, use_container_width=True)

  # --- 4. GERAR QR CODE ---
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

      lista_cadastrados = [
          p["Nome"] for p in st.session_state.integrantes if p.get("Nome")
      ]
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
            (
                p
                for p in st.session_state.integrantes
                if p["Nome"] == sel_resp
            ),
            None,
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
            label="🖼️ Baixar QR Code (PNG)",
            data=img_bytes,
            file_name=f"QR_{id_amostra}.png",
            mime="image/png",
        )

        pdf_etiquetas = gerar_pdf_etiquetas(img, qtd_etiquetas, tamanho_mm)

        st.download_button(
            label=f"📄 Baixar PDF ({qtd_etiquetas}x Etiquetas)",
            data=pdf_etiquetas,
            file_name=f"Etiquetas_{id_amostra}_{tamanho_mm}mm.pdf",
            mime="application/pdf",
            type="primary",
        )

  # --- 5. REPOSITÓRIO DE ARQUIVOS (NAVEGAÇÃO TIPO GOOGLE DRIVE) ---
  elif menu_selecionado == "📁 Repositório de Arquivos":
    st.title("📁 Central de Arquivos & Documentos")

    aba_docs, aba_upload, aba_nova_pasta = st.tabs([
        "📂 Drive de Arquivos",
        "📥 Enviar / Atualizar Arquivo",
        "📁 Criar / Solicitar Pasta",
    ])

    pastas_aprovadas = [
        p
        for p in st.session_state.pastas_db
        if p.get("status") == "Aprovado"
    ]
    if not pastas_aprovadas:
      pastas_aprovadas = [
          {"nome": "Geral", "descricao": "Arquivos gerais do laboratório"}
      ]

    # --- ABA DRIVE DE ARQUIVOS ---
    with aba_docs:
      # Caso nenhuma pasta esteja aberta, exibe o Grid de Pastas (Google Drive)
      if st.session_state.pasta_aberta_drive is None:
        st.subheader("📂 Suas Pastas do Laboratório")
        st.caption("Clique em uma pasta para visualizar e baixar os arquivos contidos nela.")

        cols_pastas = st.columns(3)
        for idx, pst in enumerate(pastas_aprovadas):
          nome_p = pst["nome"]
          desc_p = pst.get("descricao", "Sem descrição")

          # Conta quantos arquivos aprovados pertencem a esta pasta
          qtd_files = sum(
              1
              for a in st.session_state.arquivos_db
              if a.get("pasta") == nome_p and a.get("status") == "Aprovado"
          )

          with cols_pastas[idx % 3]:
            st.markdown(
                f"""
                <div class="drive-folder-card">
                    <h3 style="margin:0; font-size: 1.3rem;">📁 {nome_p}</h3>
                    <p style="margin: 5px 0; color: #64748B; font-size: 0.85rem;">{desc_p}</p>
                    <span style="background-color: #E2E8F0; padding: 2px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: bold; color: #334155;">
                        📄 {qtd_files} arquivo(s)
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(f"📂 Abrir {nome_p}", key=f"btn_open_folder_{idx}"):
              st.session_state.pasta_aberta_drive = nome_p
              st.rerun()

      # Caso uma pasta esteja aberta, exibe o conteúdo da pasta
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
            a
            for a in st.session_state.arquivos_db
            if a.get("pasta") == nome_pasta_atual
            and a.get("status") == "Aprovado"
        ]

        if arqs_da_pasta:
          for doc in arqs_da_pasta:
            with st.container():
              st.markdown(
                  f"""
                  <div class="css-card">
                      <h4 style="margin:0; color:#0D47A1;">📄 {doc['titulo']}</h4>
                      <p style="margin:4px 0; color:#555;"><b>Enviado por:</b> {doc['autor']} em {doc['data']}</p>
                      <p style="margin:4px 0; color:#666;"><i>{doc['descricao']}</i></p>
                  </div>
                  """,
                  unsafe_allow_html=True,
              )

              if "conteudo_b64" in doc:
                bytes_f = base64.b64decode(doc["conteudo_b64"])
                st.download_button(
                    label=f"⬇️ Baixar {doc['nome_original']}",
                    data=bytes_f,
                    file_name=doc["nome_original"],
                    key=f"dl_{doc['id']}",
                )
              else:
                st.caption("Ficheiro indisponível.")
              st.markdown("---")
        else:
          st.info(f"Nenhum arquivo encontrado na pasta '{nome_pasta_atual}'.")

    # SISTEMA DE UPLOAD DE ARQUIVOS
    with aba_upload:
      st.subheader("Enviar ou Atualizar Documento")
      st.caption("Envie seus arquivos para ficarem salvos no Drive do laboratório.")

      lista_nomes_pastas = [p["nome"] for p in pastas_aprovadas]

      tit_doc = st.text_input("Título do Documento *", key="up_tit")
      pasta_doc = st.selectbox("Selecione a Pasta *", lista_nomes_pastas, key="up_pasta")
      desc_doc = st.text_area("Descrição / Detalhes do Arquivo *", height=80, key="up_desc")
      arq_up = st.file_uploader(
          "Selecione o Ficheiro (PDF, DOCX, XLSX, PNG, JPG, CSV, TXT) *",
          type=["pdf", "docx", "xlsx", "png", "jpg", "csv", "txt"],
          key="up_file_widget",
      )

      if st.button("📤 Confirmar Envio do Documento", type="primary"):
        if not tit_doc.strip():
          st.error("Preencha o Título do Documento.")
        elif not desc_doc.strip():
          st.error("Preencha a Descrição do Documento.")
        elif arq_up is None:
          st.error("Selecione um ficheiro antes de clicar em confirmar.")
        else:
          bytes_conteudo = arq_up.getvalue()
          b64_str = base64.b64encode(bytes_conteudo).decode("utf-8")

          status_doc = "Aprovado" if is_admin else "Pendente"

          doc_existente = next(
              (
                  a
                  for a in st.session_state.arquivos_db
                  if a.get("titulo", "").strip().lower()
                  == tit_doc.strip().lower()
              ),
              None,
          )

          if doc_existente:
            doc_existente["pasta"] = pasta_doc
            doc_existente["descricao"] = desc_doc.strip()
            doc_existente["nome_original"] = arq_up.name
            doc_existente["conteudo_b64"] = b64_str
            doc_existente["autor"] = usuario_atual["nome"]
            doc_existente["data"] = datetime.now().strftime("%d/%m/%Y")
            doc_existente["status"] = status_doc
            salvar_dados(ARQUIVO_ARQUIVOS, st.session_state.arquivos_db)
            st.success(f"✅ Documento '{tit_doc.strip()}' atualizado!")
          else:
            novo_doc = {
                "id": len(st.session_state.arquivos_db) + 1,
                "titulo": tit_doc.strip(),
                "pasta": pasta_doc,
                "descricao": desc_doc.strip(),
                "nome_original": arq_up.name,
                "conteudo_b64": b64_str,
                "autor": usuario_atual["nome"],
                "data": datetime.now().strftime("%d/%m/%Y"),
                "status": status_doc,
            }
            st.session_state.arquivos_db.append(novo_doc)
            salvar_dados(ARQUIVO_ARQUIVOS, st.session_state.arquivos_db)
            st.success("✅ Documento enviado com sucesso!")

    with aba_nova_pasta:
      st.subheader("Solicitar ou Criar Nova Pasta")
      with st.form("form_nova_pasta"):
        nome_pasta = st.text_input("Nome da Nova Pasta *")
        desc_pasta = st.text_input("Descrição / Finalidade *")
        btn_pasta = st.form_submit_button("Criar / Solicitar Pasta")

        if btn_pasta:
          if not (nome_pasta and desc_pasta):
            st.error("Preencha todos os campos.")
          else:
            p_clean = nome_pasta.strip()
            ja_existe = any(
                p["nome"].lower() == p_clean.lower()
                for p in st.session_state.pastas_db
            )

            if ja_existe:
              st.error("Esta pasta já existe.")
            else:
              status_pasta = "Aprovado" if is_admin else "Pendente"
              st.session_state.pastas_db.append({
                  "nome": p_clean,
                  "descricao": desc_pasta.strip(),
                  "criador": usuario_atual["nome"],
                  "status": status_pasta,
              })
              salvar_dados(ARQUIVO_PASTAS, st.session_state.pastas_db)
              if is_admin:
                st.success(f"Pasta '{p_clean}' criada com sucesso!")
              else:
                st.success(f"Solicitação para criar a pasta '{p_clean}' enviada ao Administrador!")

  # --- 6. CRIADOR DE POP ---
  elif menu_selecionado == "📝 Criador de POP Padrão":
    st.title("📝 Criador e Atualizador de POP Padrão")

    busca_pop = st.text_input("🔎 Buscar POP por título ou código:", "")
    pops_filtrados = st.session_state.pops_db

    if busca_pop.strip():
      pops_filtrados = [
          p
          for p in st.session_state.pops_db
          if busca_pop.lower() in p["codigo"].lower()
          or busca_pop.lower() in p["titulo"].lower()
      ]

    opcoes_pops = [
        f"{p['codigo']} - {p['titulo']}" for p in pops_filtrados
    ] + ["➕ Cadastrar Novo POP..."]

    sel_pop_opcao = st.selectbox("Selecione uma opção:", opcoes_pops)

    if sel_pop_opcao == "➕ Cadastrar Novo POP...":
      is_novo = True
      num_pop = len(st.session_state.pops_db) + 1
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
          for p in st.session_state.pops_db
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
        st.text_input("Código do POP", value=cod_pop, disabled=True)
      with col_p2:
        st.text_input("Versão", value=versao_pop, disabled=True)
      with col_p3:
        st.text_input("Elaborado por", value=usuario_atual["nome"], disabled=True)

      if is_novo:
        tit_pop = st.text_input("Título do Novo POP *")
      else:
        st.text_input("Título do POP", value=titulo_default, disabled=True)
        tit_pop = titulo_default

      obj_pop = st.text_area("Objetivo *", value=obj_default, height=80)
      mat_pop = st.text_area("Materiais *", value=mat_default, height=80)
      passos_pop = st.text_area(
          "Passo a Passo *", value=passos_default, height=150
      )
      sec_pop = st.text_area("Segurança *", value=sec_default, height=80)

      btn_salvar_pop = st.form_submit_button(
          "💾 Salvar e Gerar Documento POP", type="primary"
      )

      if btn_salvar_pop:
        if not (tit_pop and obj_pop and mat_pop and passos_pop and sec_pop):
          st.error("Preencha todos os campos do formulário.")
        else:
          if is_novo:
            st.session_state.pops_db.append({
                "codigo": cod_pop,
                "titulo": tit_pop.strip(),
                "versao": 1,
                "objetivo": obj_pop.strip(),
                "materiais": mat_pop.strip(),
                "passos": passos_pop.strip(),
                "seguranca": sec_pop.strip(),
                "autor": usuario_atual["nome"],
            })
          else:
            pop_existente["versao"] = versao_num
            pop_existente["objetivo"] = obj_pop.strip()
            pop_existente["materiais"] = mat_pop.strip()
            pop_existente["passos"] = passos_pop.strip()
            pop_existente["seguranca"] = sec_pop.strip()
            pop_existente["autor"] = usuario_atual["nome"]

          salvar_dados(ARQUIVO_POPS, st.session_state.pops_db)
          st.success(f"POP '{cod_pop}' salvo com sucesso!")
          st.rerun()

  # --- 7. CENTRAL DE APROVAÇÕES (ADMIN) ---
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
      pend_acessos = [
          u for u in st.session_state.usuarios if u.get("status") == "Pendente"
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
              u["status"] = "Aprovado"
              salvar_dados(ARQUIVO_USUARIOS, st.session_state.usuarios)

              p_encontrado = next(
                  (
                      p
                      for p in st.session_state.integrantes
                      if p["Nome"].strip().lower() == u["nome"].strip().lower()
                  ),
                  None,
              )
              if p_encontrado:
                p_encontrado["Situação"] = "Ativo"
                p_encontrado["Categoria"] = u.get("categoria", p_encontrado.get("Categoria"))
                p_encontrado["Telefone"] = u.get("telefone", p_encontrado.get("Telefone", "-"))
                p_encontrado["Email"] = u.get("email", p_encontrado.get("Email", "-"))
              else:
                st.session_state.integrantes.append({
                    "Nome": u["nome"].strip(),
                    "Categoria": u.get("categoria", "-"),
                    "Vínculo": u.get("vinculo", "UFRRJ"),
                    "Telefone": u.get("telefone", "-"),
                    "Email": u.get("email", "-"),
                    "Situação": "Ativo",
                })

              salvar_dados(ARQUIVO_INTEGRANTES, st.session_state.integrantes)
              st.success(f"Acesso aprovado para {u['nome']}!")
              st.rerun()
          with c_b2:
            if st.button("❌ Recusar", key=f"rec_usr_{idx}"):
              u["status"] = "Recusado"
              salvar_dados(ARQUIVO_USUARIOS, st.session_state.usuarios)
              st.warning(f"Solicitação de {u['nome']} recusada.")
              st.rerun()
      else:
        st.info("Nenhuma solicitação de novo acesso pendente no momento.")

    with tab_perfis:
      pend_perfis = [
          u for u in st.session_state.usuarios if u.get("pendente_atualizacao")
      ]
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
              u["categoria"] = p_data.get("categoria")
              u["vinculo"] = p_data.get("vinculo")
              u["telefone"] = p_data.get("telefone")
              u["email"] = p_data.get("email")
              del u["pendente_atualizacao"]

              salvar_dados(ARQUIVO_USUARIOS, st.session_state.usuarios)

              for p in st.session_state.integrantes:
                if p["Nome"].strip().lower() == u["nome"].strip().lower():
                  p["Categoria"] = p_data.get("categoria")
                  p["Vínculo"] = p_data.get("vinculo")
                  p["Telefone"] = p_data.get("telefone")
                  p["Email"] = p_data.get("email")

              salvar_dados(ARQUIVO_INTEGRANTES, st.session_state.integrantes)
              st.success(f"Perfil de {u['nome']} atualizado!")
              st.rerun()
          with c_b2:
            if st.button("❌ Recusar", key=f"rec_prf_{idx}"):
              del u["pendente_atualizacao"]
              salvar_dados(ARQUIVO_USUARIOS, st.session_state.usuarios)
              st.warning("Mudança recusada.")
              st.rerun()
      else:
        st.info("Nenhuma alteração de perfil pendente.")

    with tab_files:
      pend_arquivos = [
          a
          for a in st.session_state.arquivos_db
          if a.get("status") == "Pendente"
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
              doc["status"] = "Aprovado"
              salvar_dados(ARQUIVO_ARQUIVOS, st.session_state.arquivos_db)
              st.success(
                  f"Ficheiro '{doc['titulo']}' aprovado para publicação!"
              )
              st.rerun()
          with c_b2:
            if st.button("❌ Apagar Ficheiro", key=f"rec_file_{idx}"):
              st.session_state.arquivos_db = [
                  item
                  for item in st.session_state.arquivos_db
                  if item["id"] != doc["id"]
              ]
              salvar_dados(ARQUIVO_ARQUIVOS, st.session_state.arquivos_db)
              st.warning("Ficheiro recusado e apagado.")
              st.rerun()
      else:
        st.info("Nenhum arquivo pendente de aprovação.")

    with tab_folders:
      pend_pastas = [
          p for p in st.session_state.pastas_db if p.get("status") == "Pendente"
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
              pst["status"] = "Aprovado"
              salvar_dados(ARQUIVO_PASTAS, st.session_state.pastas_db)
              st.success(f"Pasta '{pst['nome']}' aprovada com sucesso!")
              st.rerun()

          with c_b2:
            if st.button("❌ Recusar Pasta", key=f"rec_fold_{idx}"):
              st.session_state.pastas_db = [
                  p
                  for p in st.session_state.pastas_db
                  if p["nome"] != pst["nome"]
              ]
              salvar_dados(ARQUIVO_PASTAS, st.session_state.pastas_db)
              st.warning(f"Solicitação da pasta '{pst['nome']}' recusada.")
              st.rerun()
      else:
        st.info("Nenhuma solicitação de nova pasta pendente.")

    with tab_direto:
      st.subheader("⚡ Atalho: Cadastrar e Aprovar Usuário Instantaneamente")

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
            clean_u = dir_user.strip().lower()

            st.session_state.usuarios = [
                u
                for u in st.session_state.usuarios
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
            st.session_state.usuarios.append(novo_usr_aprovado)
            salvar_dados(ARQUIVO_USUARIOS, st.session_state.usuarios)

            st.session_state.integrantes = [
                p
                for p in st.session_state.integrantes
                if p["Nome"].strip().lower() != dir_nome.strip().lower()
            ]
            st.session_state.integrantes.append({
                "Nome": dir_nome.strip(),
                "Categoria": dir_cat,
                "Vínculo": dir_vinc.strip(),
                "Telefone": dir_tel.strip(),
                "Email": dir_email.strip(),
                "Situação": "Ativo",
            })
            salvar_dados(ARQUIVO_INTEGRANTES, st.session_state.integrantes)

            st.success(
                f"✅ Usuário '{dir_user.strip()}' cadastrado e APROVADO com"
                " sucesso!"
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

          usuario_atual["pendente_atualizacao"] = dados_m
          for u in st.session_state.usuarios:
            if u["usuario"] == usuario_atual["usuario"]:
              u["pendente_atualizacao"] = dados_m
              break

          salvar_dados(ARQUIVO_USUARIOS, st.session_state.usuarios)
          st.success("Solicitação enviada ao Administrador!")
          st.rerun()
