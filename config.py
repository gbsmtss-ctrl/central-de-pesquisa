import streamlit as st
from datetime import datetime

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
        "mural": "📌 **Anotações do Grupo:** Apresentação da qualificação agendada para o próximo mês. Revisar dados do lote 3 de lipases."
    }
]

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
    "orientador_status": "Aprovado"
}]

def aplicar_estilos_css():
    st.markdown(
        """
        <style>
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        [data-testid="stHeader"] {display: none;}
        [data-testid="stToolbar"] {display: none;}
        .stApp { background-color: #F8FAFC; }
        [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E2E8F0; }
        [data-testid="stSidebar"] div.stButton > button { text-align: left !important; justify-content: flex-start !important; width: 100% !important; margin-bottom: 3px !important; border-radius: 6px !important; font-size: 0.88rem !important; }
        .sidebar-section { font-size: 0.70rem; font-weight: 800; color: #94A3B8; text-transform: uppercase; margin-top: 1.2rem; margin-bottom: 0.4rem; letter-spacing: 0.08em; }
        .kpi-card { border-radius: 10px; padding: 16px 20px; border: 1px solid #E2E8F0; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 1px 3px rgba(0,0,0,0.02); }
        .kpi-card-blue { background-color: #F0F9FF; border-left: 4px solid #0284C7; }
        .kpi-card-green { background-color: #ECFDF5; border-left: 4px solid #059669; }
        .kpi-card-amber { background-color: #FFFBEB; border-left: 4px solid #D97706; }
        .kpi-card-purple { background-color: #F5F3FF; border-left: 4px solid #7C3AED; }
        .kpi-val { font-size: 1.8rem; font-weight: 800; color: #0F172A; line-height: 1; }
        .kpi-label { font-size: 0.82rem; font-weight: 600; color: #475569; margin-top: 4px; }
        .kpi-icon { font-size: 2rem; opacity: 0.85; }
        .aviso-card { background-color: #FFFFFF; border-radius: 8px; padding: 14px 16px; margin-bottom: 10px; border-left: 4px solid #0E7490; box-shadow: 0 1px 3px rgba(0,0,0,0.02); }
        .event-card { background-color: #FFFFFF; border-radius: 8px; padding: 12px 14px; margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.02); border: 1px solid #E2E8F0; }
        .pop-preview-card { background-color: #FFFFFF; border: 1px solid #CBD5E1; border-left: 4px solid #0E7490; border-radius: 8px; padding: 16px; margin-bottom: 15px; }
        .css-card { background-color: white; padding: 16px; border-radius: 8px; border: 1px solid #E2E8F0; margin-bottom: 12px; }
        </style>
        """,
        unsafe_allow_html=True,
    )
