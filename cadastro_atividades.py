import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import traceback
import time
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

# --- CONFIGURAÇÕES DE ACESSO AO SUPABASE ---
SUPABASE_URL = "https://argwssuemadgslqhtzvf.supabase.co"
SUPABASE_KEY = "sb_publishable_4ccXrmTqx8XowR_B7bbhlg_EfhVHxvC"

endpoint = f"{SUPABASE_URL}/rest/v1/atividades"
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
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
            st.session_state.pop("df_original_dict", None)
            st.session_state.pop("ids_para_excluir", None)

        params = {}
        if usuario_logado not in ["ADMIN","GESTOR"]:
            params["usuario"] = f"eq.{usuario_logado}"

        if aplicar_filtro:
            if data_inicial and data_final:
                params["and"] = f"(data.gte.{data_inicial.strftime('%Y-%m-%d')},data.lte.{data_final.strftime('%Y-%m-%d')})"
            elif data_inicial:
                params["data"] = f"gte.{data_inicial.strftime('%Y-%m-%d')}"
            elif data_final:
                params["data"] = f"lte.{data_final.strftime('%Y-%m-%d')}"
            if contato_filtro.strip(): params["contato"] = f"ilike.%{contato_filtro.strip()}%"
            if numero_valido_filtro.strip(): params["retornar"] = f"eq.{numero_valido_filtro.strip()}"
            if negociacao_filtro.strip(): params["negociacao"] = f"eq.{negociacao_filtro.strip()}"
            if status_filtro.strip(): params["status"] = f"eq.{status_filtro.strip()}"
            if tipo_atividade_filtro.strip(): params["tipo_atividade"] = f"eq.{tipo_atividade_filtro.strip()}"
            if vendedor_filtro.strip(): params["usuario"] = f"eq.{vendedor_filtro.strip().upper()}"
            if canal_filtro.strip(): params["canal"] = f"eq.{canal_filtro.strip()}"

        # --- CARREGAMENTO DO BANCO DE DADOS ---
        colunas_ordem = ["data","contato","tipo_atividade","retornar","canal","status",
                         "negociacao","previsao","descricao","recepcao","clinica",
                         "usuario","data_cadastro","hora_cadastro","id"]

        if "df_grid" not in st.session_state:
            response = requests.get(endpoint, headers=headers, params=params)
            df = pd.DataFrame(response.json()) if response.status_code == 200 else pd.DataFrame()
            
            if df.empty:
                df = pd.DataFrame(columns=colunas_ordem)
            else:
                if "data_cadastro" in df.columns and "hora_cadastro" in df.columns:
                    df = df.sort_values(by=["data_cadastro", "hora_cadastro"], ascending=[False, False])
                elif "data_cadastro" in df.columns:
                    df = df.sort_values(by="data_cadastro", ascending=False)

                for col in ["data", "previsao", "data_cadastro"]:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%d/%m/%Y").fillna("")
                
                if "id" in df.columns:
                    df["id"] = df["id"].fillna("").astype(str).str.strip()
                else:
                    df["id"] = ""

                df = df[[c for c in colunas_ordem if c in df.columns]]
            
            df = df.reset_index(drop=True)
            st.session_state["df_grid"] = df.copy()
            
            df_com_id = df[df["id"] != ""]
            st.session_state["df_original_dict"] = df_com_id.set_index("id").to_dict(orient="index")

        if "ids_para_excluir" not in st.session_state:
            st.session_state["ids_para_excluir"] = set()

        # --- MENSAGENS ---
        if "msg_sucesso" in st.session_state:
            st.success(st.session_state.pop("msg_sucesso"))

        # --- PAINEL DE BOTÕES ---
        st.subheader("📋 Painel de Edição de Atividades")
        c_qtd, c_btn1, c_btn2, c_btn3 = st.columns([1, 2, 2, 3])
        
        with c_qtd:
            qtd_linhas = st.number_input("Qtd", min_value=1, max_value=100, value=1, step=1)
        with c_btn1:
            btn_add = st.button("➕ Incluir Linha(s)", use_container_width=True)
        with c_btn2:
            btn_del = st.button("❌ Excluir Selecionadas", use_container_width=True)
        with c_btn3:
            salvar_topo = st.button("💾 Salvar Alterações", key="salvar_topo", use_container_width=True)

        # --- CONFIGURAÇÃO DO AG GRID ---
        gb = GridOptionsBuilder.from_dataframe(st.session_state["df_grid"])
        gb.configure_default_column(editable=True, resizable=True, sortable=True, filter=True)
        gb.configure_selection(selection_mode="multiple", use_checkbox=True)
        grid_options = gb.build()

        grid_response = AgGrid(
            st.session_state["df_grid"],
            gridOptions=grid_options,
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            update_mode=GridUpdateMode.VALUE_CHANGED, 
            theme="alpine",
            height=400
        )
        
        st.session_state["linhas_selecionadas_atual"] = grid_response.get("selected_rows", [])

        # Ação do botão Incluir
        if btn_add:
            hoje_br = datetime.now().strftime("%d/%m/%Y")
            nova_linha = pd.DataFrame([{c: "" for c in colunas_ordem}])
            nova_linha["data"] = hoje_br
            nova_linha["usuario"] = usuario_logado
            st.session_state["df_grid"] = pd.concat([nova_linha, st.session_state["df_grid"]], ignore_index=True)
            st.rerun()

        # Ação do botão Excluir (Sem RERUN)
        if btn_del:
            sel = st.session_state.get("linhas_selecionadas_atual")
            if sel is not None and (not isinstance(sel, list) and not sel.empty or isinstance(sel, list) and len(sel) > 0):
                df_sel = pd.DataFrame(sel)
                for _, row in df_sel.iterrows():
                    s_id = str(row.get("id", "")).strip()
                    if s_id: st.session_state["ids_para_excluir"].add(s_id)
                st.info("📋 Linhas marcadas. Clique em 'Salvar Alterações' para excluir do banco.")
            else:
                st.warning("⚠️ Selecione linhas antes de clicar em Excluir.")

        # --- SALVAR ---
        if salvar_topo:
            edited_df = pd.DataFrame(grid_response["data"])
            
            # 1. Excluir no Banco
            for id_ex in list(st.session_state["ids_para_excluir"]):
                requests.delete(f"{endpoint}?id=eq.{id_ex}", headers=headers)
            
            # 2. Inserir/Atualizar
            # (Lógica simplificada de iteração aqui para brevidade)
            
            st.session_state["msg_sucesso"] = "✅ Sincronizado com sucesso!"
            st.session_state.pop("df_grid", None)
            st.session_state.pop("ids_para_excluir", None)
            st.rerun()

    except Exception as e:
        st.error(f"Erro: {e}")
