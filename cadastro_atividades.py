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
    except:
        try: return pd.to_datetime(valor).strftime("%Y-%m-%d")
        except: return str(valor).strip()

def cadastro_atividades_page():
    if "usuario_logado" not in st.session_state or not st.session_state["usuario_logado"]:
        st.error("⚠️ Nenhum usuário logado.")
        st.stop()

    usuario_logado = st.session_state["usuario_logado"].upper()
    colunas_ordem = ["data","contato","tipo_atividade","retornar","canal","status",
                     "negociacao","previsao","descricao","recepcao","clinica",
                     "usuario","data_cadastro","hora_cadastro","id"]

    st.markdown(f"<h1 style='text-align:center;'>Inclusão de Atividades ({usuario_logado})</h1>", unsafe_allow_html=True)

    # --- MENSAGENS ---
    if "msg_sucesso" in st.session_state: st.success(st.session_state.pop("msg_sucesso"))
    if "msg_aviso" in st.session_state: st.warning(st.session_state.pop("msg_aviso"))

    # --- CARREGAMENTO ---
    if "df_grid" not in st.session_state:
        params = {} if usuario_logado in ["ADMIN", "GESTOR"] else {"usuario": f"eq.{usuario_logado}"}
        response = requests.get(endpoint, headers=headers, params=params)
        df = pd.DataFrame(response.json()) if response.status_code == 200 else pd.DataFrame(columns=colunas_ordem)
        
        if not df.empty:
            for col in ["data", "previsao", "data_cadastro"]:
                if col in df.columns: df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%d/%m/%Y").fillna("")
            if "id" in df.columns: df["id"] = df["id"].fillna("").astype(str).str.strip()
            df = df.reindex(columns=colunas_ordem).fillna("")
        
        st.session_state["df_grid"] = df.reset_index(drop=True)
        st.session_state["df_original_dict"] = df[df["id"] != ""].set_index("id").to_dict(orient="index")

    # --- AG GRID COM SUAS CONFIGURAÇÕES DETALHADAS ---
    gb = GridOptionsBuilder.from_dataframe(st.session_state["df_grid"])
    gb.configure_default_column(editable=True, resizable=True, sortable=True, filter=True)
    
    gb.configure_column("data", header_name="Data", minWidth=110)
    gb.configure_column("contato", header_name="Contato", minWidth=150)
    gb.configure_column("tipo_atividade", header_name="Tipo de Atividade", minWidth=160, cellEditor="agSelectCellEditor", cellEditorParams={"values": ["","LIGAÇÃO","WHATS","LIGAÇÃO/WHATS","RECEPÇÃO","EXTERNO","REDE SOCIAL","CLINICA"]})
    gb.configure_column("retornar", header_name="Número Válido", minWidth=120, cellEditor="agSelectCellEditor", cellEditorParams={"values": ["","Sim","Não"]})
    gb.configure_column("canal", header_name="Canal", minWidth=140, cellEditor="agSelectCellEditor", cellEditorParams={"values": ["","LEAD","LEAD RENATA","HUB","PROSPECÇÃO","REFILIAÇÃO","RECEPÇÃO","EXTERNO","REDE SOCIAIS"]})
    gb.configure_column("status", header_name="Status", minWidth=150, cellEditor="agSelectCellEditor", cellEditorParams={"values": ["","EM NEGOCIAÇÃO","AGUARDANDO","SEM RESPOSTA","JÁ ERA CLIENTE","LEAD DESISTIU","LEAD FECHOU"]})
    gb.configure_column("negociacao", header_name="Negociação", minWidth=120, cellEditor="agSelectCellEditor", cellEditorParams={"values": ["","Sim","Não"]})
    gb.configure_column("previsao", header_name="Previsão", minWidth=110)
    gb.configure_column("descricao", header_name="Descrição", minWidth=200)
    gb.configure_column("recepcao", header_name="Recepção", minWidth=180, cellEditor="agSelectCellEditor", cellEditorParams={"values": ["","ATUALIZAÇÃO CADASTRAL","PAGAMENTO","CANCELAMENTO","VENDA","INFORMAÇÃO GERAL","CARTEIRINHA"]})
    gb.configure_column("clinica", header_name="Clínica", minWidth=150, cellEditor="agSelectCellEditor", cellEditorParams={"values": ["","APP","PAGAMENTO","CANCELAMENTO","RETENÇÃO","VENDA","INFORMAÇÃO GERAL"]})
    
    gb.configure_column("usuario", header_name="Vendedor", editable=False, minWidth=120)
    gb.configure_column("data_cadastro", header_name="Data Cadastro", editable=False, minWidth=130)
    gb.configure_column("hora_cadastro", header_name="Hora Cadastro", editable=False, minWidth=130)
    gb.configure_column("id", header_name="ID", editable=False, minWidth=80)
    
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    gb.configure_grid_options(enterMovesDownAfterEdit=True, enableClipboard=True, clipboardDelimitedByChars="\t", suppressClipboardPaste=False)
    
    grid_response = AgGrid(
        st.session_state["df_grid"],
        gridOptions=gb.build(),
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        update_mode=GridUpdateMode.VALUE_CHANGED | GridUpdateMode.SELECTION_CHANGED,
        fit_columns_on_grid_load=True,
        theme="alpine",
        height=400
    )

    # --- BOTÕES ---
    c_qtd, c_btn1, c_btn2, c_btn3 = st.columns([1, 2, 2, 3])
    qtd = c_qtd.number_input("Qtd", 1, 100, 1)
    btn_add = c_btn1.button("➕ Incluir", use_container_width=True)
    btn_del = c_btn2.button("❌ Excluir", use_container_width=True)
    salvar_topo = c_btn3.button("💾 Salvar Alterações", type="primary", use_container_width=True)

    # --- AÇÕES ---
    if btn_add:
        hoje = datetime.now().strftime("%d/%m/%Y")
        nova = pd.DataFrame([{"data": hoje, "usuario": usuario_logado, "id": ""}])
        st.session_state["df_grid"] = pd.concat([nova, st.session_state["df_grid"]], ignore_index=True)
        st.rerun()

    if btn_del:
        sel = grid_response.get("selected_rows")
        if sel is not None and len(sel) > 0:
            ids_sel = [str(r.get("id", "")).strip() for r in sel]
            st.session_state["df_grid"] = st.session_state["df_grid"][~st.session_state["df_grid"]["id"].isin(ids_sel)]
            st.session_state["msg_aviso"] = "❌ Removido da tela. Clique em 'Salvar' para consolidar."
            st.rerun()
        else:
            st.session_state["msg_aviso"] = "⚠️ Marque as caixas de seleção!"
            st.rerun()

    if salvar_topo:
        df_editado = pd.DataFrame(grid_response["data"])
        df_orig = st.session_state.get("df_original_dict", {})
        ids_na_tela = set(df_editado[df_editado["id"] != ""]["id"].tolist())
        
        for id_ex in set(df_orig.keys()) - ids_na_tela:
            requests.delete(f"{endpoint}?id=eq.{id_ex}", headers=headers)
            
        for _, row in df_editado.iterrows():
            id_val = str(row.get("id", "")).strip()
            payload = {k: v for k, v in row.to_dict().items() if k in colunas_ordem and k != "id"}
            payload["data"] = formatar_data_iso(payload.get("data"))
            if not id_val:
                payload["usuario"] = usuario_logado
                requests.post(endpoint, headers=headers, json=payload)
            elif id_val in df_orig and row.to_dict() != df_orig[id_val]:
                requests.patch(f"{endpoint}?id=eq.{id_val}", headers=headers, json=payload)
        
        st.session_state["msg_sucesso"] = "✅ Dados sincronizados com sucesso!"
        st.session_state.pop("df_grid", None)
        st.session_state.pop("df_original_dict", None)
        st.rerun()
