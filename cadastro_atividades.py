import streamlit as st
import pandas as pd
import requests
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# Configurações do Supabase (Mesmas do seu login)
SUPABASE_URL = "https://argwssuemadgslqhtzvf.supabase.co"
SUPABASE_KEY = "sb_publishable_4ccXrmTqx8XowR_B7bbhlg_EfhVHxvC"
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def carregar_dados():
    endpoint = f"{SUPABASE_URL}/rest/v1/atividades?select=*"
    response = requests.get(endpoint, headers=HEADERS)
    if response.status_code == 200:
        return pd.DataFrame(response.json())
    return pd.DataFrame()

def atualizar_supabase(id, dados):
    endpoint = f"{SUPABASE_URL}/rest/v1/atividades?id=eq.{id}"
    requests.patch(endpoint, headers=HEADERS, json=dados)

def excluir_supabase(id):
    endpoint = f"{SUPABASE_URL}/rest/v1/atividades?id=eq.{id}"
    requests.delete(endpoint, headers=HEADERS)

def pagina_atividades():
    st.title("Gestão de Atividades")
    
    df = carregar_dados()
    if df.empty:
        st.write("Nenhuma atividade encontrada.")
        return

    # Organizar colunas conforme sua solicitação
    colunas_ordem = ["data","contato","tipo_atividade","retornar","canal","status",
                     "negociacao","previsao","descricao","recepcao","clinica",
                     "usuario","data_cadastro","hora_cadastro","id"]
    df = df[[c for c in colunas_ordem if c in df.columns]]

    # Configuração do Grid
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_selection('single', use_checkbox=True)
    gb.configure_pagination(paginationAutoPageSize=True)
    # Define quais colunas são editáveis
    for col in df.columns:
        if col != "id": # Não permitir editar o ID
            gb.configure_column(col, editable=True)
    
    grid_options = gb.build()

    # Exibição
    grid_response = AgGrid(df, gridOptions=grid_options, update_mode=GridUpdateMode.MODEL_CHANGED)

    # Botões de Ação
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Salvar Alterações"):
            dados_editados = grid_response["data"]
            # Aqui você identifica o que mudou e envia apenas o registro alterado
            for _, row in dados_editados.iterrows():
                atualizar_supabase(row["id"], row.to_dict())
            st.success("Dados atualizados no banco!")
            st.rerun()

    with col2:
        if st.button("🗑️ Excluir Selecionado"):
            selected = grid_response["selected_rows"]
            if selected:
                id_excluir = selected[0]["id"]
                excluir_supabase(id_excluir)
                st.success(f"Registro {id_excluir} excluído!")
                st.rerun()
            else:
                st.warning("Selecione uma linha.")

# Chamada no seu fluxo principal
if "usuario_logado" in st.session_state:
    pagina_atividades()
else:
    login_page()
