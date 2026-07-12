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
    if pd.isna(valor) or not valor: return None
    try: return datetime.strptime(str(valor).strip(), "%d/%m/%Y").strftime("%Y-%m-%d")
    except:
        try: return pd.to_datetime(valor).strftime("%Y-%m-%d")
        except: return str(valor).strip()

def cadastro_atividades_page():
    st.markdown("<style>html { scroll-behavior: auto !important; }</style>", unsafe_allow_html=True)
    if "usuario_logado" not in st.session_state or not st.session_state["usuario_logado"]:
        st.error("⚠️ Nenhum usuário logado.")
        st.stop()
    usuario_logado = st.session_state["usuario_logado"].upper()

    # --- FILTROS ---
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

    colunas_ordem = ["data","contato","tipo_atividade","retornar","canal","status",
                     "negociacao","previsao","descricao","recepcao","clinica",
                     "usuario","data_cadastro","hora_cadastro","id"]

    if "df_grid" not in st.session_state:
        response = requests.get(endpoint, headers=headers)
        df = pd.DataFrame(response.json()) if response.status_code == 200 else pd.DataFrame(columns=colunas_ordem)
        st.session_state["df_grid"] = df
        st.session_state["df_original_dict"] = df[df["id"] != ""].set_index("id").to_dict(orient="index") if not df.empty else {}# --- EXIBIÇÃO DO GRID ---
    st.subheader("📋 Painel de Atividades")
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
    grid_options = gb.build()
    
    grid_response = AgGrid(
        st.session_state["df_grid"], 
        gridOptions=grid_options, 
        height=400, 
        theme="alpine",
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        update_mode=GridUpdateMode.SELECTION_CHANGED
    )# --- PAINEL DE BOTÕES E AÇÕES ---
    st.markdown("<div id='painel-edicao'></div>", unsafe_allow_html=True)
    st.subheader("📋 Painel de Edição")
    c_qtd, c_btn1, c_btn2, c_btn3 = st.columns([1, 2, 2, 3])
    with c_qtd: qtd = st.number_input("Qtd", min_value=1, value=1)
    with c_btn1: btn_add = st.button("➕ Incluir")
    with c_btn2: btn_del = st.button("❌ Excluir")
    with c_btn3: salvar = st.button("💾 Salvar")

    # Lógica de exclusão e salvamento simplificada para o fluxo
    if btn_del:
        raw_data = grid_response.get("selected_rows", [])
        ids_excluir = [str(r.get("id", "")).strip() for r in raw_data if r.get("id")]
        for id_del in ids_excluir:
            requests.delete(f"{endpoint}?id=eq.{id_del}", headers=headers)
        st.session_state.pop("df_grid", None)
        st.rerun()

    if salvar:
        # Aqui entra sua lógica de POST/PATCH original
        st.session_state.pop("df_grid", None)
        st.rerun()

# --- FECHAMENTO DO ARQUIVO ---
if "scroll_to" in st.session_state:
    st.components.v1.html(f"""
        <script>
            window.parent.location.hash = 'painel-edicao';
            setTimeout(function() {{
                window.parent.history.replaceState(null, null, ' ');
            }}, 500);
        </script>
    """, height=0)
    del st.session_state["scroll_to"]
