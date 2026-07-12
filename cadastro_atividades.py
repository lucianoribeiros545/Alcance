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
    if pd.isna(valor) or not valor:
        return None
    try:
        return datetime.strptime(str(valor).strip(), "%d/%m/%Y").strftime("%Y-%m-%d")
    except Exception:
        try:
            return pd.to_datetime(valor).strftime("%Y-%m-%d")
        except Exception:
            return str(valor).strip()

def cadastro_atividades_page():
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
    
    try:
        if "usuario_logado" not in st.session_state or not st.session_state["usuario_logado"]:
            st.error("⚠️ Nenhum usuário logado. Faça login para acessar esta página.")
            st.stop()

        usuario_logado = st.session_state["usuario_logado"].upper()
        st.markdown(f"<h1 style='text-align:center;'>Inclusão de Atividades ({usuario_logado})</h1>", unsafe_allow_html=True)

        # --- CONTADOR DE INCLUSÕES ---
        col1, col2 = st.columns([4, 2])
        with col2:
            if st.button("📊 Consultar Inclusões do Dia"):
                hoje = datetime.now().strftime("%Y-%m-%d")
                params = {"data_cadastro": f"eq.{hoje}"}
                if usuario_logado not in ["ADMIN", "GESTOR"]:
                    params["usuario"] = f"eq.{usuario_logado}"
                response = requests.get(endpoint, headers=headers, params=params)
                st.session_state["inclusoes_hoje"] = len(response.json()) if response.status_code == 200 else 0

            st.markdown(
                f"""
                <div style="background-color:#0073e6; padding:15px; border-radius:10px; text-align:center; font-weight:bold; font-size:18px; color:#ffffff;">
                    📌 Inclusões do dia<br>
                    <span style="font-size:24px; color:#ffffff;">{st.session_state.get('inclusoes_hoje', 0)}</span>
                </div>
                """,
                unsafe_allow_html=True
            )

        # --- FORMULÁRIO DE FILTROS ---
        with st.form(key="filtro_form_unico"):
            st.subheader("🔎 Filtros de Pesquisa")
            col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns(9)
            with col1: data_inicial = st.date_input("Data inicial", value=None, format="DD/MM/YYYY")
            with col2: data_final = st.date_input("Data final", value=None, format="DD/MM/YYYY")
            with col3: contato_filtro = st.text_input("Contato", autocomplete="off")
            with col4: numero_valido_filtro = st.selectbox("Número Válido", options=["", "Sim", "Não"])
            with col5: negociacao_filtro = st.selectbox("Negociação", options=["", "Sim", "Não"])
            with col6: status_filtro = st.selectbox("Status", options=["","EM NEGOCIAÇÃO","AGUARDANDO","SEM RESPOSTA","JÁ ERA CLIENTE","LEAD DESISTIU","LEAD FECHOU"])
            with col7: tipo_atividade_filtro = st.selectbox("Tipo de Atividade", options=["","LIGAÇÃO","WHATS","LIGAÇÃO/WHATS","RECEPÇÃO","EXTERNO","REDE SOCIAL","CLINICA"])
            with col8: vendedor_filtro = st.text_input("Vendedor") if usuario_logado in ["ADMIN","GESTOR"] else ""
            with col9: canal_filtro = st.selectbox("Canal", options=["","LEAD","LEAD RENATA","HUB","PROSPECÇÃO","REFILIAÇÃO","RECEPÇÃO","EXTERNO","REDE SOCIAIS"])
            aplicar_filtro = st.form_submit_button("Pesquisar")
        
        if aplicar_filtro:
            st.session_state.pop("df_grid", None)
            st.session_state.pop("df_original", None)

        # --- CARREGAMENTO DO BANCO DE DADOS ---
        colunas_ordem = ["data","contato","tipo_atividade","retornar","canal","status",
                         "negociacao","previsao","descricao","recepcao","clinica",
                         "usuario","data_cadastro","hora_cadastro","id"]

        if "df_grid" not in st.session_state:
            response = requests.get(endpoint, headers=headers)
            df = pd.DataFrame(response.json()) if response.status_code == 200 else pd.DataFrame(columns=colunas_ordem)
            
            if not df.empty:
                for col in ["data", "previsao", "data_cadastro"]:
                    if col in df.columns: df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%d/%m/%Y").fillna("")
                df["id"] = df["id"].fillna("").astype(str).str.strip()
            
            df = df.reindex(columns=colunas_ordem).fillna("")
            st.session_state["df_grid"] = df.reset_index(drop=True)
            st.session_state["df_original"] = df.copy()

        # --- PAINEL DE BOTÕES ---
        st.subheader("📋 Painel de Edição de Atividades")
        c_qtd, c_btn1, c_btn2, c_btn3 = st.columns([1, 2, 2, 3])
        with c_qtd: qtd_linhas = st.number_input("Qtd", 1, 100, 1)
        with c_btn1: btn_add = st.button("➕ Incluir Linha(s)", use_container_width=True)
        with c_btn2: btn_del = st.button("❌ Excluir Selecionadas", use_container_width=True)
        with c_btn3: salvar_topo = st.button("💾 Salvar Alterações", key="salvar_topo", type="primary", use_container_width=True)

        if btn_add:
            hoje_br = datetime.now().strftime("%d/%m/%Y")
            nova_linha = pd.DataFrame([{"data": hoje_br, "usuario": usuario_logado, "id": ""}])
            st.session_state["df_grid"] = pd.concat([nova_linha, st.session_state["df_grid"]], ignore_index=True)
            st.rerun()

        # --- AG GRID COM SUPORTE A EXCEL ---
        gb = GridOptionsBuilder.from_dataframe(st.session_state["df_grid"])
        gb.configure_default_column(editable=True)
        gb.configure_column("id", editable=False)
        gb.configure_selection(selection_mode="multiple", use_checkbox=True)
        gb.configure_grid_options(enableClipboard=True, clipboardDelimitedByChars="\t", suppressClipboardPaste=False)
        
        grid_response = AgGrid(
            st.session_state["df_grid"], 
            gridOptions=gb.build(), 
            update_mode=GridUpdateMode.VALUE_CHANGED, 
            height=400
        )
        
        st.session_state["df_grid"] = pd.DataFrame(grid_response["data"])

        if btn_del:
            sel = grid_response.get("selected_rows")
            if sel is not None and not sel.empty:
                ids_sel = sel["id"].astype(str).tolist()
                st.session_state["df_grid"] = st.session_state["df_grid"][~st.session_state["df_grid"]["id"].astype(str).isin(ids_sel)]
                st.rerun()
            else:
                st.warning("⚠️ Marque as linhas na lateral esquerda para excluir.")

        # --- OPERAÇÃO DE SALVAMENTO INTELIGENTE ---
        if salvar_topo:
            df_atual = st.session_state["df_grid"].fillna("")
            df_orig = st.session_state["df_original"].set_index("id", drop=False).fillna("")
            
            # 1. DELEÇÃO
            ids_orig = set(df_orig.index.astype(str)) - {""}
            ids_atuais = set(df_atual[df_atual["id"] != ""]["id"].astype(str))
            for id_del in (ids_orig - ids_atuais):
                requests.delete(f"{endpoint}?id=eq.{id_del}", headers=headers)
            
            # 2. INSERÇÃO E ATUALIZAÇÃO
            for _, row in df_atual.iterrows():
                id_val = str(row.get("id", "")).strip()
                payload = {k: v for k, v in row.to_dict().items() if k != "id"}
                payload["data"] = formatar_data_iso(payload.get("data"))

                if not id_val:
                    # POST se for novo
                    requests.post(endpoint, headers=headers, json=payload)
                else:
                    # PATCH apenas se houve mudança real
                    if id_val in df_orig.index:
                        if row.to_dict() != df_orig.loc[id_val].to_dict():
                            requests.patch(f"{endpoint}?id=eq.{id_val}", headers=headers, json=payload)
            
            st.session_state.pop("df_grid", None)
            st.session_state.pop("df_original", None)
            st.success("✅ Alterações sincronizadas com sucesso!")
            st.rerun()
            
    except Exception as e:
        st.error("❌ Erro crítico no motor do grid.")
        st.text(traceback.format_exc())
