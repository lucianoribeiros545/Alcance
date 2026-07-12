import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import traceback

# --- CONFIGURAÇÕES DE ACESSO AO SUPABASE ---
SUPABASE_URL = "https://argwssuemadgslqhtzvf.supabase.co"
SUPABASE_KEY = "sb_publishable_4ccXrmTqx8XowR_B7bbhlg_EfhVHxvC"

endpoint = f"{SUPABASE_URL}/rest/v1/atividades"
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def formatar_data_iso(valor):
    if pd.isna(valor) or not valor: return None
    try: return datetime.strptime(str(valor).strip(), "%d/%m/%Y").strftime("%Y-%m-%d")
    except: 
        try: return pd.to_datetime(valor).strftime("%Y-%m-%d")
        except: return str(valor).strip()

def cadastro_atividades_page():
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
    
    usuario_logado = st.session_state["usuario_logado"].upper()
    colunas_ordem = ["data","contato","tipo_atividade","retornar","canal","status",
                     "negociacao","previsao","descricao","recepcao","clinica",
                     "usuario","data_cadastro","hora_cadastro","id"]

    # --- CARREGAMENTO ---
    if "df_grid" not in st.session_state:
        params = {} if usuario_logado in ["ADMIN", "GESTOR"] else {"usuario": f"eq.{usuario_logado}"}
        response = requests.get(endpoint, headers=headers, params=params)
        df = pd.DataFrame(response.json()) if response.status_code == 200 else pd.DataFrame(columns=colunas_ordem)
        if not df.empty:
            df["id"] = df["id"].astype(str)
        st.session_state["df_grid"] = df.reindex(columns=colunas_ordem).fillna("")
        st.session_state["df_original"] = st.session_state["df_grid"].copy()

    st.markdown(f"<h1 style='text-align:center;'>Inclusão de Atividades ({usuario_logado})</h1>", unsafe_allow_html=True)

    # --- BOTÕES ---
    c_qtd, c_btn1, c_btn2, c_btn3 = st.columns([1, 2, 2, 3])
    with c_qtd: qtd_linhas = st.number_input("Qtd", 1, 100, 1)
    btn_add = c_btn1.button("➕ Incluir Linha(s)", use_container_width=True)
    btn_del = c_btn2.button("❌ Excluir Selecionadas", use_container_width=True)
    salvar_topo = c_btn3.button("💾 Salvar Alterações", type="primary", use_container_width=True)

    if btn_add:
        nova = pd.DataFrame([{"data": datetime.now().strftime("%d/%m/%Y"), "usuario": usuario_logado, "id": ""}])
        st.session_state["df_grid"] = pd.concat([nova, st.session_state["df_grid"]], ignore_index=True)
        st.rerun()

    # --- AG GRID ---
    gb = GridOptionsBuilder.from_dataframe(st.session_state["df_grid"])
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    gb.configure_grid_options(enableClipboard=True, clipboardDelimitedByChars="\t")
    
    grid_response = AgGrid(
        st.session_state["df_grid"], 
        gridOptions=gb.build(), 
        update_mode=GridUpdateMode.VALUE_CHANGED | GridUpdateMode.SELECTION_CHANGED,
        height=400
    )

    # --- LÓGICA DE EXCLUIR ---
    if btn_del:
        sel = grid_response.get("selected_rows")
        if sel is not None and not sel.empty:
            ids_excluir = sel["id"].astype(str).tolist()
            # Deleta no banco se tiver ID
            for id_del in ids_excluir:
                if id_del and id_del != "":
                    requests.delete(f"{endpoint}?id=eq.{id_del}", headers=headers)
            # Remove da tela
            st.session_state["df_grid"] = st.session_state["df_grid"][~st.session_state["df_grid"]["id"].isin(ids_excluir)]
            st.success("Excluído!")
            st.rerun()

    # --- LÓGICA DE SALVAR ---
    if salvar_topo:
        df_atual = pd.DataFrame(grid_response["data"])
        df_orig = st.session_state["df_original"].set_index("id", drop=False)
        
        for _, row in df_atual.iterrows():
            id_val = str(row.get("id", "")).strip()
            payload = {k: v for k, v in row.to_dict().items() if k != "id"}
            payload["data"] = formatar_data_iso(payload.get("data"))

            if not id_val:
                requests.post(endpoint, headers=headers, json=payload)
            elif id_val in df_orig.index:
                if row.to_dict() != df_orig.loc[id_val].to_dict():
                    requests.patch(f"{endpoint}?id=eq.{id_val}", headers=headers, json=payload)
        
        st.session_state.pop("df_grid", None)
        st.session_state.pop("df_original", None)
        st.success("Salvo com sucesso!")
        st.rerun()
