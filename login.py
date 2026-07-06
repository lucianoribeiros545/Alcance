import streamlit as st
import requests
import os

def login_page():
    # Logo no topo
    logo_path = os.path.join("imagens", "logo.png")
    if os.path.exists(logo_path):
        st.image(logo_path, width=200)

    # Título
    st.markdown("<h1 style='text-align:center;'>Login do Sistema</h1>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([3,2,3])
    with col2:
        st.markdown("""
            <style>
            input[type="text"] {
                text-transform: uppercase;
            }
            </style>
        """, unsafe_allow_html=True)

        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")

        if st.button("Entrar"):
            usuario_upper = usuario.upper().strip()

            # 🔹 Configuração Supabase (pegue de st.secrets no Streamlit Cloud)
            #SUPABASE_URL = st.secrets["SUPABASE_URL"]
            #SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
            SUPABASE_URL = "https://argwssuemadgslqhtzvf.supabase.co"   # sem /rest/v1 aqui
            SUPABASE_KEY = "sb_publishable_4ccXrmTqx8XowR_B7bbhlg_EfhVHxvC"

            endpoint = f"{SUPABASE_URL}/rest/v1/usuarios"
            headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json"
            }

            # 🔹 Consulta ao Supabase filtrando usuário e senha
            params = {
                "usuario": f"eq.{usuario_upper}",
                "senha": f"eq.{senha}"
            }

            response = requests.get(endpoint, headers=headers, params=params)

            if response.status_code == 200:
                data = response.json()
                if data:  # encontrou usuário
                    st.session_state["usuario_logado"] = usuario_upper
                    st.success("Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error("Usuário ou senha inválidos")
            else:
                st.error(f"Erro na conexão: {response.status_code}")
