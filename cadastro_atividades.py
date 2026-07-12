import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import traceback
import time

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
            st.session_state.pop("df_original_dict", None)

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

        # --- EXIBIÇÃO DE MENSAGENS TEMPORÁRIAS ---
        placeholder_mensagem = st.empty()

        # 🚀 Tratamento especial para o Sucesso pós-salvamento (Usa o timer para sumir)
        if "msg_sucesso" in st.session_state:
            with placeholder_mensagem.container():
                st.success(st.session_state.pop("msg_sucesso"))
            time.sleep(3)
            placeholder_mensagem.empty()

        # 🚀 Avisos simples (como remoção visual da linha) usam st.warning padrão sem sleep para não congelar o rerun
        if "msg_aviso" in st.session_state:
            st.warning(st.session_state.pop("msg_aviso"))

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

        # Ação do botão Incluir
        if btn_add:
            novas_linhas_lista = []
            hoje_br = datetime.now().strftime("%d/%m/%Y")
            hora_atual = datetime.now().strftime("%H:%M:%S")
            
            for _ in range(qtd_linhas):
                novas_linhas_lista.append({
                    "data": hoje_br, "contato": "", "tipo_atividade": "", 
                    "retornar": "", "canal": "", "status": "", "negociacao": "", "previsao": "", 
                    "descricao": "", "recepcao": "", "clinica": "", "usuario": usuario_logado, 
                    "data_cadastro": hoje_br, "hora_cadastro": hora_atual, "id": ""
                })
            novas_linhas_df = pd.DataFrame(novas_linhas_lista)
            novas_linhas_df = novas_linhas_df[colunas_ordem]
            
            st.session_state["df_grid"] = pd.concat([novas_linhas_df, st.session_state["df_grid"]], ignore_index=True)
            st.rerun()

        # --- CONFIGURAÇÃO DO AG GRID ---
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
        
        gb.configure_grid_options(
            enterMovesDownAfterEdit=True,
            enableClipboard=True,
            clipboardDelimitedByChars="\t",
            suppressClipboardPaste=False
        )
        grid_options = gb.build()

        grid_response = AgGrid(
            st.session_state["df_grid"],
            gridOptions=grid_options,
            key="aggrid_atividades",  # <--- ESSENCIAL para rastrear mudanças
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            update_mode=GridUpdateMode.VALUE_CHANGED | GridUpdateMode.SELECTION_CHANGED, 
            fit_columns_on_grid_load=True, 
            reload_data=False,        # <--- Garante que os dados locais sejam respeitados
            theme="alpine",
            height=400
        )

        edited_df = pd.DataFrame(grid_response["data"])
        if not edited_df.empty and "id" in edited_df.columns:
            edited_df["id"] = edited_df["id"].fillna("").astype(str).str.strip()
     
        
        if btn_del:
            # 1. Captura a seleção
            sel_rows = grid_response.get("selected_rows")
            
            # 2. Verifica se o objeto existe e não está vazio
            # Se for um DataFrame, checamos .empty. Se for lista, checamos se tem itens.
            tem_selecao = False
            if isinstance(sel_rows, pd.DataFrame):
                tem_selecao = not sel_rows.empty
            elif isinstance(sel_rows, list):
                tem_selecao = len(sel_rows) > 0
            
            if tem_selecao:
                # Se sel_rows for um DataFrame, usamos ele direto. Se for lista, convertemos.
                df_selecionado = sel_rows if isinstance(sel_rows, pd.DataFrame) else pd.DataFrame(sel_rows)
                
                df_atual = st.session_state["df_grid"].copy()
                
                # O índice do AgGrid geralmente coincide com o do DataFrame original
                indices_a_remover = df_selecionado.index
                
                df_atual = df_atual.drop(indices_a_remover)
                
                st.session_state["df_grid"] = df_atual.reset_index(drop=True)
                
                if "df_original_dict" in st.session_state:
                    st.session_state.pop("df_original_dict")
                
                st.session_state["msg_aviso"] = f"❌ {len(df_selecionado)} linha(s) removida(s). Clique em 'Salvar' para aplicar ao banco."
                st.rerun()

            else:
                st.warning("⚠️ Marque as caixas de seleção na lateral esquerda para excluir.")
                # Não usamos o rerun aqui para não ficar em loop infinito de aviso

        st.markdown(f"**Total de registros exibidos: {len(edited_df)}**")

        # --- OPERAÇÃO DE SUBMIT NO SUPABASE ---
        if salvar_topo:
            if edited_df.empty:
                # Se limpou tudo da tela e salvou, as pendentes de ID original serão deletadas abaixo
                pass

            inseridos = atualizados = excluidos = 0
            df_original_dict = st.session_state.get("df_original_dict", {})
            ids_originais = set(df_original_dict.keys())
            
            ids_na_tela = set(edited_df["id"].tolist()) if not edited_df.empty and "id" in edited_df.columns else set()
            if "" in ids_na_tela:
                ids_na_tela.remove("")

            # 1. Deleções Efetivas no Supabase
            ids_para_deletar = ids_originais - ids_na_tela
            for id_excluir in ids_para_deletar:
                if id_excluir:
                    delete_endpoint = f"{endpoint}?id=eq.{id_excluir}"
                    response = requests.delete(delete_endpoint, headers=headers)
                    if response.status_code in [200, 204]:
                        excluidos += 1

            # 2. Inclusões (POST) e Updates (PATCH)
            if not edited_df.empty:
                for _, row in edited_df.iterrows():
                    id_atual = str(row.get("id", "")).strip()
                    contato = str(row.get("contato", "")).strip()
                    data_br = row.get("data", "")
                    
                    if not data_br or pd.isna(data_br):
                        data_br = datetime.now().strftime("%d/%m/%Y")
                    
                    data_iso = formatar_data_iso(data_br)

                    if id_atual == "":
                        novo_registro = {
                            "data": data_iso, 
                            "contato": contato, 
                            "canal": str(row.get("canal", "")).strip(),
                            "tipo_atividade": str(row.get("tipo_atividade", "")).strip(), 
                            "status": str(row.get("status", "")).strip(),
                            "negociacao": str(row.get("negociacao", "")).strip(), 
                            "previsao": formatar_data_iso(row.get("previsao", "")),
                            "retornar": str(row.get("retornar", "")).strip(), 
                            "descricao": str(row.get("descricao", "")).strip(),
                            "recepcao": str(row.get("recepcao", "")).strip(), 
                            "clinica": str(row.get("clinica", "")).strip(),
                            "usuario": usuario_logado, 
                            "data_cadastro": datetime.now().strftime("%Y-%m-%d"), 
                            "hora_cadastro": datetime.now().strftime("%H:%M:%S")
                        }
                        response = requests.post(endpoint, headers=headers, json=novo_registro)
                        if response.status_code in [200, 201]:
                            inseridos += 1

                    elif id_atual in df_original_dict:
                        original_row = df_original_dict[id_atual]
                        changes = {}
                        campos_verificar = ["data", "contato", "canal", "tipo_atividade", "status", "negociacao", "previsao", "retornar", "descricao", "recepcao", "clinica"]
                        
                        for campo in campos_verificar:
                            valor_atual = str(row.get(campo, "")).strip() if pd.notna(row.get(campo)) else ""
                            valor_original = str(original_row.get(campo, "")).strip() if pd.notna(original_row.get(campo)) else ""
                            
                            if valor_atual != valor_original:
                                changes[campo] = formatar_data_iso(valor_atual) if campo in ["data", "previsao"] else valor_atual

                        if changes:
                            update_endpoint = f"{endpoint}?id=eq.{id_atual}"
                            response = requests.patch(update_endpoint, headers=headers, json=changes)
                            if response.status_code in [200, 204]:
                                atualizados += 1

            # Define o sucesso e força recarga limpa puxando do Supabase
            st.session_state["msg_sucesso"] = f"✅ Alterações sincronizadas! Inseridos: {inseridos} | 🔄 Atualizados: {atualizados} | ❌ Excluídos: {excluidos}"
            st.session_state.pop("df_grid", None)
            st.session_state.pop("df_original_dict", None)
            st.rerun()

    except Exception as e:
        st.error("❌ Erro crítico no motor do AG Grid.")
        st.text(traceback.format_exc())
