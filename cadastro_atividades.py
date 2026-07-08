import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import traceback
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
    """Converte datas do formato brasileiro (DD/MM/YYYY) para o formato do banco (YYYY-MM-DD)"""
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
        # --- VERIFICAÇÃO DE LOGIN ---
        if "usuario_logado" not in st.session_state or not st.session_state["usuario_logado"]:
            st.error("⚠️ Nenhum usuário logado. Faça login para acessar esta página.")
            st.stop()

        usuario_logado = st.session_state["usuario_logado"].upper()
        st.markdown(f"<h1 style='text-align:center;'>Inclusão de Atividades ({usuario_logado})</h1>", unsafe_allow_html=True)

        # --- PAINEL LATERAL / CONTADOR DE INCLUSÕES ---
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
        
        # Se clicar em pesquisar, limpa o cache para carregar a nova consulta
        if aplicar_filtro:
            st.session_state.pop("df_grid", None)
            st.session_state.pop("df_original_dict", None)

        # --- MONTAGEM DOS PARÂMETROS DA API ---
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

        # --- CARREGAMENTO DE DADOS (CACHE DOS ESTADOS) ---
        if "df_grid" not in st.session_state:
            response = requests.get(endpoint, headers=headers, params=params)
            df = pd.DataFrame(response.json()) if response.status_code == 200 else pd.DataFrame()
            
            if df.empty:
                df = pd.DataFrame(columns=[
                    "data","contato","tipo_atividade","retornar","canal","status",
                    "negociacao","previsao","descricao","recepcao","clinica",
                    "usuario","data_cadastro","hora_cadastro","id"
                ])

            # Converte datas vindas do banco para o padrão brasileiro
            for col in ["data", "previsao", "data_cadastro"]:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%d/%m/%Y").fillna("")

            # MANUTENÇÃO RIGOROSA DA ORDEM DAS COLUNAS ORIGINAIS
            colunas_ordem = ["data","contato","tipo_atividade","retornar","canal","status",
                             "negociacao","previsao","descricao","recepcao","clinica",
                             "usuario","data_cadastro","hora_cadastro","id"]
            df = df[[c for c in colunas_ordem if c in df.columns]]
            df = df.reset_index(drop=True)
            
            st.session_state["df_grid"] = df.copy()
            
            # FOTO DO ESTADO INICIAL (Mapeia apenas quem possui ID populado e real do banco)
            df_com_id = df.dropna(subset=["id"])
            df_com_id = df_com_id[df_com_id["id"].astype(str).str.strip() != ""]
            st.session_state["df_original_dict"] = df_com_id.set_index(df_com_id["id"].astype(str)).to_dict(orient="index")

        salvar_topo = st.button("💾 Salvar alterações (Topo)", key="salvar_topo")

        # --- ⚙️ CONFIGURAÇÃO DE RENDERIZAÇÃO DO AG GRID ---
        gb = GridOptionsBuilder.from_dataframe(st.session_state["df_grid"])
        gb.configure_default_column(editable=True, resizable=True, sortable=True, filter=True)
        
        # Mapeamento de Cabeçalhos e Caixas de Seleção (Dropdowns)
        gb.configure_column("data", header_name="Data")
        gb.configure_column("contato", header_name="Contato")
        gb.configure_column("tipo_atividade", header_name="Tipo de Atividade", cellEditor="agSelectCellEditor", cellEditorParams={"values": ["","LIGAÇÃO","WHATS","LIGAÇÃO/WHATS","RECEPÇÃO","EXTERNO","REDE SOCIAL","CLINICA"]})
        gb.configure_column("retornar", header_name="Número Válido", cellEditor="agSelectCellEditor", cellEditorParams={"values": ["","Sim","Não"]})
        gb.configure_column("canal", header_name="Canal", cellEditor="agSelectCellEditor", cellEditorParams={"values": ["","LEAD","LEAD RENATA","HUB","PROSPECÇÃO","REFILIAÇÃO","RECEPÇÃO","EXTERNO","REDE SOCIAIS"]})
        gb.configure_column("status", header_name="Status", cellEditor="agSelectCellEditor", cellEditorParams={"values": ["","EM NEGOCIAÇÃO","AGUARDANDO","SEM RESPOSTA","JÁ ERA CLIENTE","LEAD DESISTIU","LEAD FECHOU"]})
        gb.configure_column("negociacao", header_name="Negociação", cellEditor="agSelectCellEditor", cellEditorParams={"values": ["","Sim","Não"]})
        gb.configure_column("previsao", header_name="Previsão")
        gb.configure_column("descricao", header_name="Descrição")
        gb.configure_column("recepcao", header_name="Recepção", cellEditor="agSelectCellEditor", cellEditorParams={"values": ["","ATUALIZAÇÃO CADASTRAL","PAGAMENTO","CANCELAMENTO","VENDA","INFORMAÇÃO GERAL","CARTEIRINHA"]})
        gb.configure_column("clinica", header_name="Clínica", cellEditor="agSelectCellEditor", cellEditorParams={"values": ["","APP","PAGAMENTO","CANCELAMENTO","RETENÇÃO","VENDA","INFORMAÇÃO GERAL"]})
        
        # Travas de segurança: Colunas que não podem ser editadas de forma alguma
        gb.configure_column("usuario", header_name="Vendedor", editable=False)
        gb.configure_column("data_cadastro", header_name="Data Cadastro", editable=False)
        gb.configure_column("hora_cadastro", header_name="Hora Cadastro", editable=False)
        gb.configure_column("id", header_name="ID", editable=False)
        
        gb.configure_grid_options(rowSelection="single", enterMovesDownAfterEdit=True)
        grid_options = gb.build()

        # Invocação estável do componente AG Grid
        grid_response = AgGrid(
            st.session_state["df_grid"],
            gridOptions=grid_options,
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            update_mode=GridUpdateMode.MANUAL, # TRAVA MANUAL: Evita re-renderizar e dar loop enquanto digita
            fit_columns_on_grid_load=True,
            theme="alpine",
            height=400
        )

        edited_df = pd.DataFrame(grid_response["data"])
        st.markdown(f"**Total de registros exibidos: {len(edited_df)}**")
        salvar_base = st.button("💾 Salvar alterações (Base)", key="salvar_base")

        # --- LÓGICA DE PROCESSAMENTO SALVAR (SUBMIT) ---
        if salvar_topo or salvar_base:
            if edited_df.empty:
                st.warning("⚠️ Nenhum dado encontrado na tabela para salvar.")
                st.stop()

            inseridos = atualizados = excluidos = 0
            df_original_dict = st.session_state.get("df_original_dict", {})
            ids_originais = set(df_original_dict.keys())
            
            # Coleta apenas IDs válidos e populados que restaram na tela
            ids_na_tela = set()
            if "id" in edited_df.columns:
                ids_na_tela = set(str(x).strip() for x in edited_df["id"].dropna().tolist() if str(x).strip() != "")

            # --- 1. PROCESSO ISOLADO DE DELEÇÃO (Apenas se já existia no banco e sumiu da tela) ---
            ids_para_deletar = ids_originais - ids_na_tela
            for id_excluir in ids_para_deletar:
                if id_excluir:
                    delete_endpoint = f"{endpoint}?id=eq.{id_excluir}"
                    response = requests.delete(delete_endpoint, headers=headers)
                    if response.status_code in [200, 204]:
                        excluidos += 1
                    else:
                        st.error(f"❌ Falha ao excluir ID {id_excluir}: {response.text}")

            # --- 2. PROCESSO DE INCLUSÃO E UPDATE ---
            for _, row in edited_df.iterrows():
                contato = str(row.get("contato", "")).strip()
                data_br = row.get("data", "")
                data_iso = formatar_data_iso(data_br)

                # Ignora linhas fantasmas ou em branco criadas no grid
                if not contato or not data_iso:
                    continue

                id_atual = str(row.get("id", "")).strip() if pd.notna(row.get("id")) else ""

                # CASO A: Registro inteiramente novo (Sem ID) -> Executa POST
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
                    else:
                        st.error(f"❌ Erro ao inserir registro de {contato}: {response.text}")

                # CASO B: Registro já existente -> Compara células e executa PATCH apenas se mudou algo
                elif id_atual in df_original_dict:
                    original_row = df_original_dict[id_atual]
                    changes = {}
                    campos_verificar = ["data", "contato", "canal", "tipo_atividade", "status", "negociacao", "previsao", "retornar", "descricao", "recepcao", "clinica"]
                    
                    for campo in campos_verificar:
                        valor_atual = str(row.get(campo, "")).strip() if pd.notna(row.get(campo)) else ""
                        valor_original = str(original_row.get(campo, "")).strip() if pd.notna(original_row.get(campo)) else ""
                        
                        if valor_atual != valor_original:
                            if campo in ["data", "previsao"]:
                                changes[campo] = formatar_data_iso(valor_atual)
                            else:
                                changes[campo] = valor_atual

                    if changes: # Só gasta requisição se houver alteração real
                        update_endpoint = f"{endpoint}?id=eq.{id_atual}"
                        response = requests.patch(update_endpoint, headers=headers, json=changes)
                        if response.status_code in [200, 204]:
                            atualizados += 1
                        else:
                            st.error(f"❌ Erro ao atualizar ID {id_atual}: {response.text}")

            st.success(f"✅ Alterações sincronizadas! Inseridos: {inseridos} | 🔄 Atualizados: {atualizados} | ❌ Excluídos: {excluidos}")
            
            # Limpeza cirúrgica de estados para forçar recarregamento limpo pós-save
            st.session_state.pop("df_grid", None)
            st.session_state.pop("df_original_dict", None)
            st.rerun()

    except Exception as e:
        st.error("❌ Erro crítico no motor do AG Grid.")
        st.text(traceback.format_exc())
