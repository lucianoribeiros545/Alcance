import streamlit as st
from cadastro_atividades import cadastro_atividades_page
from configuracoes import configuracoes_page
from login import login_page
from dashboard import dashboard_page
from dashboard_view import dashboard_view
from streamlit_option_menu import option_menu

# Layout Wide obrigatório para não cortar a tela
st.set_page_config(layout="wide")

# CSS para forçar a visibilidade e largura total
st.markdown("""
    <style>
    /* Força o container principal a ocupar a largura total */
    .block-container {
        padding-top: 1rem !important;
        max-width: 98% !important;
    }
    /* Garante que o menu tenha altura e não seja ocultado */
    div[data-testid="stVerticalBlock"] {
        width: 100% !important;
    }
    </style>
""", unsafe_allow_html=True)

if "usuario_logado" not in st.session_state:
    login_page()
else:
    # Definição do menu
    if st.session_state["usuario_logado"].lower() == "admin":
        menu_opcoes = ["Dashboard", "Atividades", "Configurações", "Gestão", "Sair"]
        menu_icones = ["bar-chart-line", "clipboard-data", "gear", "shield-lock", "box-arrow-right"]
    elif st.session_state["usuario_logado"].lower() == "gestor":
        menu_opcoes = ["Dashboard", "Atividades", "Gestão", "Sair"]
        menu_icones = ["bar-chart-line", "clipboard-data", "shield-lock", "box-arrow-right"]
    else:
        menu_opcoes = ["Atividades", "Sair"]
        menu_icones = ["clipboard-data", "box-arrow-right"]

    # Renderiza o menu dentro de um container específico para garantir o layout
    with st.container():
        selected = option_menu(
            menu_title=None,
            options=menu_opcoes,
            icons=menu_icones,
            orientation="horizontal",
            styles={
                "container": {"padding": "5px", "background-color": "#f0f2f6", "border-radius": "10px"},
                "nav-link": {"font-size": "16px", "text-align": "center", "margin": "0px 5px", "color": "black"},
                "nav-link-selected": {"background-color": "#0078D7", "color": "white"},
            }
        )

    # Conteúdo principal
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
