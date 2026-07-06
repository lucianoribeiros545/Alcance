import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# 🔹 Configuração Supabase
SUPABASE_URL = "https://argwssuemadgslqhtzvf.supabase.co"
SUPABASE_KEY = "sb_publishable_4ccXrmTqx8XowR_B7bbhlg_EfhVHxvC"

endpoint = f"{SUPABASE_URL}/rest/v1/usuarios"
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def configuracoes_page():
    # CSS para ícones maiores e coloridos
    st.markdown("""
        <style>
        h1 {
            color: #1976D2;
            text-align: center;
            font-family: 'sans-serif';
            font-size: 38px;
            margin-top: 20px;
            margin-bottom: 40px;
        }
        div[data-testid="stDataEditor"] svg {
            width: 48px !important;
            height: 48px !important;
        }
        div[data-testid="stDataEditorRowAdd"] svg { fill: #28a745 !important; }
        div[data-testid="stDataEditorRowDelete"] svg { fill: #dc3545 !important; }
        div[data-testid="stDataEditorRowView"] svg { fill: #0078D7 !important; }
        div[data-testid="stDataEditorRowDownload"] svg { fill: #ff9800 !important; }
        div[data-testid="stDataEditorRowSearch"] svg { fill: #6f42c1 !important; }
        </style>
    """, unsafe_allow_html=True)

    # 🔹 Carregar usuários do Supabase
    response = requests.get(endpoint, headers=headers)
    df = pd.DataFrame(response.json()) if response.status_code == 200 else pd.DataFrame()

    if df.empty:
        df = pd.DataFrame(columns=["id", "usuario", "senha"])

    # Título
    st.markdown("<h1>Configurações de Usuários</h1>", unsafe_allow_html=True)

    # Grid editável
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        height=400,
        key="usuarios_grid",
        column_config={
            "usuario": st.column_config.TextColumn("Usuário"),
            "senha": st.column_config.TextColumn("Senha"),
            "id": st.column_config.TextColumn("ID", disabled=True)
        },
        hide_index=True
    )

    # Botão de salvar
    if st.button("💾 Salvar alterações"):
        inseridos, atualizados, excluidos = 0, 0, 0
        ids_atuais = set()

        for _, row in edited_df.iterrows():
            usuario = str(row["usuario"]).strip() if pd.notna(row["usuario"]) else ""
            senha = str(row["senha"]).strip() if pd.notna(row["senha"]) else ""

            if usuario and senha:
                if pd.notna(row["id"]):
                    update_endpoint = f"{endpoint}?id=eq.{row['id']}"
                    response = requests.patch(update_endpoint, headers=headers, json={"usuario": usuario, "senha": senha})
                    if response.status_code in [200, 204]:
                        atualizados += 1
                        ids_atuais.add(row["id"])
                    else:
                        st.error(f"❌ Falha ao atualizar {row['id']}: {response.text}")
                else:
                    response = requests.post(endpoint, headers=headers, json={"usuario": usuario, "senha": senha})
                    if response.status_code == 201:
                        inseridos += 1
                    else:
                        st.error(f"❌ Falha ao inserir: {response.text}")

        # Excluir registros removidos
        ids_originais = set(df["id"].tolist()) if "id" in df.columns else set()
        ids_para_excluir = ids_originais - ids_atuais
        for id_del in ids_para_excluir:
            delete_endpoint = f"{endpoint}?id=eq.{id_del}"
            response = requests.delete(delete_endpoint, headers=headers)
            if response.status_code in [200, 204]:
                excluidos += 1
            else:
                st.error(f"❌ Falha ao excluir {id_del}: {response.text}")

        st.success(f"✅ Alterações salvas! ({inseridos} inseridos, {atualizados} atualizados, {excluidos} excluídos)")
