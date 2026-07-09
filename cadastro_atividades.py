import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

# --- CONFIGURAÇÕES ---
SUPABASE_URL = "https://argwssuemadgslqhtzvf.supabase.co"
SUPABASE_KEY = "sb_publishable_4ccXrmTqx8XowR_B7bbhlg_EfhVHxvC"
endpoint = f"{SUPABASE_URL}/rest/v1/atividades"
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def formatar_data_iso(valor):
    if pd.isna(valor) or not valor: return None
    try: return datetime.strptime(str(valor).strip(), "%d/%m/%Y").strftime("%Y-%m-%d")
    except: return str(valor).strip()

def cadastro_atividades_page():
    if "usuario_logado" not in st.session_state:
        st.error("⚠️ Faça login primeiro.")
        return

    usuario_logado = st.session_state["usuario_logado"].upper()
    st.markdown(f"<h1 style='text-align:center;'>Inclusão de Atividades ({usuario_logado})</h1>", unsafe_allow_html=True)

    # --- INICIALIZAÇÃO DE ESTADO ---
    if "ids_para_excluir" not in st.session_state:
        st.session_state["ids_para_excluir"] = set()

    # --- CARREGAMENTO INICIAL ---
    if "df_grid" not in st.session_state:
        response = requests.get(endpoint, headers=headers)
        df = pd.DataFrame(response.json()) if response.status_code == 200 else pd.DataFrame()
        st.session_state["df_grid"] = df

    # --- PAINEL DE BOTÕES ---
    col_qtd, col1, col2, col3 = st.columns([1, 2, 2, 3])
    with col_qtd: qtd = st.number_input("Qtd", 1, 100, 1)
    with col1: btn_add = st.button("➕ Incluir Linha(s)")
    with col2: btn_del = st.button("❌ Excluir Selecionadas")
    with col3: btn_save = st.button("💾 Salvar Alterações")

    # --- CONFIGURAÇÃO DO GRID ---
    gb = GridOptionsBuilder.from_dataframe(st.session_state["df_grid"])
    gb.configure_default_column(editable=True, resizable=True, filter=True)
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    
    # Definindo colunas explicitamente para garantir visibilidade
    cols = ["data", "contato", "tipo_atividade", "retornar", "canal", "status", "negociacao", "previsao", "descricao", "recepcao", "clinica"]
    for c in cols: gb.configure_column(c, minWidth=120)
    
    grid_response = AgGrid(
        st.session_state["df_grid"],
        gridOptions=gb.build(),
        update_mode=GridUpdateMode.VALUE_CHANGED,
        fit_columns_on_grid_load=True,
        theme="alpine",
        height=400
    )

    # --- LÓGICA DE EXCLUSÃO (SEM RERUN) ---
    if btn_del:
        sel = grid_response.get("selected_rows")
        if sel is not None and (not isinstance(sel, list) or len(sel) > 0):
            df_sel = pd.DataFrame(sel)
            for _, row in df_sel.iterrows():
                s_id = str(row.get("id", "")).strip()
                if s_id: st.session_state["ids_para_excluir"].add(s_id)
            st.info("📋 Linhas marcadas. Clique em 'Salvar Alterações' para excluir do banco.")
        else:
            st.warning("⚠️ Selecione linhas na lateral.")

    # --- LÓGICA DE SALVAR ---
    if btn_save:
        edited_df = pd.DataFrame(grid_response["data"])
        
        # 1. Deletar
        for id_ex in list(st.session_state["ids_para_excluir"]):
            requests.delete(f"{endpoint}?id=eq.{id_ex}", headers=headers)
        
        # 2. Inserir/Atualizar (lógica simplificada)
        # ... (seu código de integração com Supabase continua aqui)
        
        st.success("✅ Alterações salvas com sucesso!")
        st.session_state.pop("df_grid", None)
        st.session_state.pop("ids_para_excluir", None)
        st.rerun()

cadastro_atividades_page()
