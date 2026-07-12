import streamlit as st
import os
from cadastro_atividades import cadastro_atividades_page
from configuracoes import configuracoes_page
from login import login_page
from dashboard import dashboard_page
from dashboard_view import dashboard_view
from streamlit_option_menu import option_menu

# Configuração da página
st.set_page_config(page_title="FAST TD", layout="wide")

# Estilização CSS para um visual moderno e compacto
st.markdown("""
    <style>
    /* Remove o espaço superior padrão do Streamlit */
    .block-container { padding-top: 2rem; }
    /* Ajusta o estilo das subheaders */
    h2 { margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# 🔹 Controle de login
if "usuario_logado" not in st.session_state:
    login_page()
else:
    # Cabeçalho com logo e nome do usuário
    col1, col2 = st.columns([1, 5])
    with col1:
        if os.path.exists("logo.png"):
            st.image("logo.png", width=120)
    with col2:
        st.markdown(f"<p style='text-align:right; margin-top: 20px;'>👋 Olá, <b>{st.session_state['usuario_logado']}</b>!</p>", unsafe_allow_html=True)

    # 🔹 Definição do menu conforme perfil
    if st.session_state["usuario_logado"].lower() == "admin":
        menu_opcoes = ["📈 Dashboard", "📋 Atividades", "⚙️ Configurações", "📈 Dashboard View++", "🚪 Sair"]
        menu_icones = ["bar-chart", "list-task", "gear", "person-lines-fill", "door-closed"]
    elif st.session_state["usuario_logado"].lower() == "gestor":
        menu_opcoes = ["📈 Dashboard", "📋 Atividades", "📈 Dashboard View++", "🚪 Sair"]
        menu_icones = ["bar-chart", "list-task", "person-lines-fill", "door-closed"]
    else:
        menu_opcoes = ["📋 Atividades", "🚪 Sair"]
        menu_icones = ["list-task", "door-closed"]

    # 🔹 Menu Moderno (Linha única no topo)
    selected = option_menu(
        menu_title=None,
        options=menu_opcoes,
        icons=menu_icones,
        orientation="horizontal",
        styles={
            "container": {
                "padding": "0px", 
                "background-color": "#f8f9fa",
                "border-bottom": "1px solid #e0e0e0"
            },
            "icon": {"color": "#1e3c72", "font-size": "18px"},
            "nav-link": {
                "font-size": "14px",
                "text-align": "center",
                "margin": "0px 5px",
                "padding": "10px 15px",
                "color": "#444",
                "font-weight": "600",
                "transition": "all 0.3s"
            },
            "nav-link-selected": {
                "background-color": "#e0e7ff",
                "color": "#1e3c72",
                "border-bottom": "3px solid #1e3c72",
                "border-radius": "0px"
            },
        }
    )

    st.write("") # Pequeno espaçamento

    # 🔹 Conteúdo das abas
    if selected == "📈 Dashboard":
        st.subheader("📈 Módulo de Dashboard")
        dashboard_page()

    elif selected == "📋 Atividades":
        st.subheader("📋 Minhas Atividades")
        cadastro_atividades_page()

    elif selected == "⚙️ Configurações":
        st.subheader("⚙️ Módulo de Configurações")
        configuracoes_page()

    elif selected == "📈 Dashboard View++":
        st.subheader("📈 Módulo Gestão")
        dashboard_view()

    elif selected == "🚪 Sair":
        st.subheader("🚪 Encerrar Sessão")
        if st.button("Confirmar saída"):
            st.session_state.clear()
            st.rerun()
