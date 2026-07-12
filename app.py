import streamlit as st
from cadastro_atividades import cadastro_atividades_page
from configuracoes import configuracoes_page
from login import login_page
from dashboard import dashboard_page
from dashboard_view import dashboard_view
from streamlit_option_menu import option_menu

# Configuração da página
st.set_page_config(page_title="FAST TD", layout="wide")

# CSS para reduzir espaços e manter o menu minimalista
st.markdown("""
    <style>
    .block-container { padding-top: 2rem; }
    div.stButton > button { width: 200px; }
    </style>
""", unsafe_allow_html=True)

# 🔹 Controle de login
if "usuario_logado" not in st.session_state:
    login_page()
else:
    # Cabeçalho simples com nome do usuário
    st.markdown(f"<p style='text-align:right;'>👤 <b>{st.session_state['usuario_logado']}</b></p>", unsafe_allow_html=True)

    # 🔹 Definição do menu
    if st.session_state["usuario_logado"].lower() == "admin":
        menu_opcoes = ["Dashboard", "Atividades", "Configurações", "Gestão", "Sair"]
        menu_icones = ["bar-chart", "list-task", "gear", "person-badge", "door-closed"]
    elif st.session_state["usuario_logado"].lower() == "gestor":
        menu_opcoes = ["Dashboard", "Atividades", "Gestão", "Sair"]
        menu_icones = ["bar-chart", "list-task", "person-badge", "door-closed"]
    else:
        menu_opcoes = ["Atividades", "Sair"]
        menu_icones = ["list-task", "door-closed"]

    # 🔹 Menu Minimalista
    selected = option_menu(
        menu_title=None,
        options=menu_opcoes,
        icons=menu_icones,
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#666", "font-size": "16px"},
            "nav-link": {
                "font-size": "15px",
                "text-align": "center",
                "padding": "8px",
                "color": "#666",
                "background-color": "transparent",
            },
            "nav-link-selected": {
                "color": "#0078D7",
                "font-weight": "bold",
                "background-color": "transparent",
                "border-bottom": "2px solid #0078D7",
                "border-radius": "0"
            },
        }
    )

    st.write("---")

    # 🔹 Conteúdo das abas
    if selected == "Dashboard":
        dashboard_page()
    elif selected == "Atividades":
        cadastro_atividades_page()
    elif selected == "Configurações":
        configuracoes_page()
    elif selected == "Gestão":
        dashboard_view()
    elif selected == "Sair":
        if st.button("Confirmar saída"):
            st.session_state.clear()
            st.rerun()
