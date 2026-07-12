import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

# O comando de configuração deve vir logo após os imports
st.set_page_config(layout="wide")

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
    # --- BARRA SUPERIOR (Apenas Botão Sair) ---
    col_vazia, col_sair = st.columns([12, 1])
    with col_sair:
        if st.button("🚪 Sair"):
            st.session_state["usuario_logado"] = None
            st.rerun()

    # --- MENSAGENS ---
    if "msg_sucesso" in st.session_state: st.success(st.session_state.pop("msg_sucesso"))
    if "msg_aviso" in st.session_state: st.warning(st.session_state.pop("msg_aviso"))

    # --- CARREGAMENTO ---
    colunas_ordem = ["data","contato","tipo_atividade","retornar","canal","status",
                     "negociacao","previsao","descricao","recepcao","clinica",
                     "usuario","data_cadastro","hora_cadastro","id"]

    if "df_grid" not in st.session_state:
        usuario_logado = st.session_state.get("usuario_logado", "USUARIO").upper()
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

    # --- BOTÕES (AGORA ACIMA DO GRID) ---
    c_btn1, c_btn2, c_btn3, c_espaco = st.columns([1, 1, 2, 6])
    btn_add = c_btn1.button("➕ Incluir", use_container_width=True)
    btn_del = c_btn2.button("❌ Excluir", use_container_width=True)
    salvar_topo = c_btn3.button("💾 Salvar Alterações", type="primary", use_container_width=True)

    # --- AG GRID ---
    gb = GridOptionsBuilder.from_dataframe(st.session_state["df_grid"])
    gb.configure_default_column(editable=True, resizable=True, sortable=True, filter=True)
    
    # ... (Configurações de colunas permanecem iguais) ...
    gb.configure_column("tipo_atividade", cellEditor="agSelectCellEditor", cellEditorParams={"values": ["","LIGAÇÃO","WHATS","LIGAÇÃO/WHATS","RECEPÇÃO","EXTERNO","REDE SOCIAL","CLINICA"]})
    gb.configure_column("retornar", cellEditor="agSelectCellEditor", cellEditorParams={"values": ["","Sim","Não"]})
    gb.configure_column("canal", cellEditor="agSelectCellEditor", cellEditorParams={"values": ["","LEAD","LEAD RENATA","HUB","PROSPECÇÃO","REFILIAÇÃO","RECEPÇÃO","EXTERNO","REDE SOCIAIS"]})
    gb.configure_column("status", cellEditor="agSelectCellEditor", cellEditorParams={"values": ["","EM NEGOCIAÇÃO","AGUARDANDO","SEM RESPOSTA","JÁ ERA CLIENTE","LEAD DESISTIU","LEAD FECHOU"]})
    gb.configure_column("negociacao", cellEditor="agSelectCellEditor", cellEditorParams={"values": ["","Sim","Não"]})
    gb.configure_column("recepcao", cellEditor="agSelectCellEditor", cellEditorParams={"values": ["","ATUALIZAÇÃO CADASTRAL","PAGAMENTO","CANCELAMENTO","VENDA","INFORMAÇÃO GERAL","CARTEIRINHA"]})
    gb.configure_column("clinica", cellEditor="agSelectCellEditor", cellEditorParams={"values": ["","APP","PAGAMENTO","CANCELAMENTO","RETENÇÃO","VENDA","INFORMAÇÃO GERAL"]})
    
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    grid_response = AgGrid(st.session_state["df_grid"], gridOptions=gb.build(), update_mode=GridUpdateMode.VALUE_CHANGED | GridUpdateMode.SELECTION_CHANGED, theme="alpine", height=400)

    # --- AÇÕES (Lógica Mantida) ---
    if btn_add:
        hoje = datetime.now().strftime("%d/%m/%Y")
        nova = pd.DataFrame([{"data": hoje, "usuario": st.session_state.get("usuario_logado", "").upper(), "id": ""}])
        st.session_state["df_grid"] = pd.concat([nova, st.session_state["df_grid"]], ignore_index=True)
        st.rerun()

    if btn_del:
        sel = grid_response.get("selected_rows")
        if sel is not None and len(sel) > 0:
            ids_sel = [str(r.get("id", "")).strip() for r in sel]
            st.session_state["df_grid"] = st.session_state["df_grid"][~st.session_state["df_grid"]["id"].isin(ids_sel)]
            st.rerun()
        else:
            st.warning("⚠️ Selecione linhas para excluir.")

    if salvar_topo:
        # ... (Lógica de salvamento permanece igual) ...
        st.session_state["msg_sucesso"] = "✅ Sincronizado!"
        st.session_state.pop("df_grid", None)
        st.rerun()
