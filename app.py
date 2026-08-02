import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime, time, timedelta
import calendar
from database import (init_db, salvar_sf6, carregar_sf6, salvar_temp, carregar_temps,
                      salvar_operacao, carregar_operacoes, salvar_inspecao, carregar_inspecoes,
                      salvar_pendencia, carregar_pendencias, atualizar_pendencia,
                      salvar_equipamento, atualizar_equipamento, desativar_equipamento,
                      carregar_equipamentos, buscar_equipamento_por_tag,
                      salvar_config, carregar_config,
                      salvar_contador, carregar_contadores,
                      salvar_foto, carregar_fotos, carregar_foto_base64, excluir_foto,
                      excluir_fotos_periodo)
from equipamentos import DISJUNTORES, TRANSFORMADORES, BATERIAS, corrigir_pressao_sf6, status_sf6
from email_report import (salvar_config_email, carregar_config_email,
                           gerar_html_relatorio, enviar_relatorio, fig_para_base64,
                           foto_para_base64)
from checklists import SISTEMAS, CHECKLISTS

st.set_page_config(page_title="Guardião da Usina", page_icon="🛡️",
                   layout="wide", initial_sidebar_state="auto")

# Cache das consultas ao banco — evita reconectar a cada interação
@st.cache_data(ttl=120, show_spinner=False)
def _carregar_equipamentos(tipo=None, sistema=None, ativo_only=True):
    return carregar_equipamentos(tipo, sistema, ativo_only)

@st.cache_data(ttl=60, show_spinner=False)
def _carregar_sf6(disjuntor=None, data_ini=None, data_fim=None):
    return carregar_sf6(disjuntor, data_ini, data_fim)

@st.cache_data(ttl=60, show_spinner=False)
def _carregar_inspecoes(sistema=None, data_ini=None, data_fim=None):
    return carregar_inspecoes(sistema, data_ini, data_fim)

@st.cache_data(ttl=60, show_spinner=False)
def _carregar_pendencias(status=None):
    return carregar_pendencias(status)

@st.cache_data(ttl=120, show_spinner=False)
def _buscar_equipamento_por_tag(tag):
    return buscar_equipamento_por_tag(tag)

@st.cache_data(ttl=60, show_spinner=False)
def _carregar_contadores(disjuntor=None, data_ini=None, data_fim=None):
    return carregar_contadores(disjuntor, data_ini, data_fim)

@st.cache_data(ttl=60, show_spinner=False)
def _carregar_temps(equipamento=None, data_ini=None, data_fim=None):
    return carregar_temps(equipamento, data_ini, data_fim)

@st.cache_data(ttl=120, show_spinner=False)
def _carregar_operacoes(disjuntor=None):
    return carregar_operacoes(disjuntor)

@st.cache_data(ttl=30, show_spinner=False)
def _carregar_fotos(data_ini=None, data_fim=None, sem_base64=False):
    return carregar_fotos(data_ini=data_ini, data_fim=data_fim, sem_base64=sem_base64)

@st.cache_data(ttl=60, show_spinner=False)
def _carregar_inspecoes_hoje(data):
    return carregar_inspecoes(data_ini=data, data_fim=data)

@st.cache_resource(show_spinner=False)
def _init_db():
    init_db()

_init_db()

# Restaurar condições ambientais salvas — persiste entre sessões
if "temp_amb_global" not in st.session_state:
    st.session_state["temp_amb_global"] = float(carregar_config("temp_amb", "28.0") or 28.0)
    st.session_state["umid_amb_global"] = float(carregar_config("umid_amb", "70.0") or 70.0)
    _t = carregar_config("turno", "Manhã (06-14h)")
    st.session_state["turno_global"] = _t if _t in ["Manhã (06-14h)","Tarde (14-22h)","Noite (22-06h)"] else "Manhã (06-14h)"

# ═══════════════════════════════════════════════════════════════ CSS ══════
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.stApp{background:#07090f;}
/* ── Streamlit Cloud: esconder Fork/GitHub mas manter botão ☰ ── */
footer{display:none !important;}
#MainMenu{display:none !important;}
[data-testid="stBottom"]{display:none !important;}
[data-testid="stStatusWidget"]{display:none !important;}
[data-testid="manage-app-button"]{display:none !important;}
.stDeployButton{display:none !important;}
div[class*="StatusWidget"]{display:none !important;}
div[class*="ViewerBadge"]{display:none !important;}
/* Manter header mas esconder apenas toolbar do Cloud */
[data-testid="stToolbar"]{visibility:hidden !important; height:0 !important;}
/* Header fica com altura mínima só para o botão ☰ aparecer */
header[data-testid="stHeader"]{
  background:transparent !important;
  border-bottom:none !important;
  min-height:2.5rem !important;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#0a0e1a,#111827);border-right:1px solid #1e3a5f;}
/* Botão ☰ grande e visível no mobile */
[data-testid="collapsedControl"]{
  display:flex !important; visibility:visible !important;
  background:#1e3a5f !important; border-radius:8px !important;
  padding:6px !important; z-index:9999 !important;
}
[data-testid="collapsedControl"] svg{
  fill:#60a5fa !important; width:24px !important; height:24px !important;
}
.card{background:linear-gradient(145deg,#0f172a,#1e293b);border:1px solid #1e3a5f;border-radius:14px;padding:20px;margin:6px 0;}
.card-green{border-left:4px solid #10b981;} .card-red{border-left:4px solid #ef4444;}
.card-yellow{border-left:4px solid #f59e0b;} .card-blue{border-left:4px solid #3b82f6;}
.card-purple{border-left:4px solid #8b5cf6;}
.kpi{background:linear-gradient(135deg,#0f1e3a,#162447);border-radius:12px;padding:18px;text-align:center;border:1px solid #1e3a5f;}
.kpi-n{font-size:2.4rem;font-weight:900;line-height:1;} .kpi-l{font-size:0.72rem;color:#64748b;margin-top:4px;text-transform:uppercase;letter-spacing:1px;}
.badge-ok{background:#052e16;color:#34d399;border:1px solid #10b981;border-radius:20px;padding:2px 12px;font-size:0.78rem;font-weight:700;}
.badge-alarm{background:#451a03;color:#fcd34d;border:1px solid #f59e0b;border-radius:20px;padding:2px 12px;font-size:0.78rem;font-weight:700;}
.badge-crit{background:#450a0a;color:#fca5a5;border:1px solid #ef4444;border-radius:20px;padding:2px 12px;font-size:0.78rem;font-weight:700;}
.badge-bloq{background:#3b0764;color:#d8b4fe;border:1px solid #8b5cf6;border-radius:20px;padding:2px 12px;font-size:0.78rem;font-weight:700;}
h1,h2,h3,h4{color:#f1f5f9!important;} p,li,label{color:#94a3b8;}
.stButton>button{background:linear-gradient(135deg,#1d4ed8,#2563eb);color:white;border:none;border-radius:8px;font-weight:700;width:100%;}
.stSelectbox>div>div,.stTextInput>div>div>input,.stTextArea>div>div>textarea,.stNumberInput>div>div>input
{background:#0f172a!important;color:#f1f5f9!important;border:1px solid #1e3a5f!important;border-radius:8px!important;}
/* Garantir cor do texto em TODOS os inputs — mobile e desktop */
input, textarea, select, [data-baseweb="input"] input,
[data-baseweb="textarea"] textarea, [data-baseweb="select"] div,
div[data-testid="stNumberInput"] input,
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea
{color:#f1f5f9 !important; -webkit-text-fill-color:#f1f5f9 !important;
 font-size:1rem !important; background:#0f172a !important;}
/* Labels dos campos */
div[data-testid="stNumberInput"] label,
div[data-testid="stTextInput"] label,
div[data-testid="stSelectbox"] label,
div[data-testid="stTextArea"] label
{color:#94a3b8 !important; font-size:0.85rem !important;}
.stSlider>div{color:#94a3b8;}
hr{border-color:#1e3a5f;}

/* ── RESPONSIVO MOBILE ─────────────────────────────────────────── */
@media (max-width: 768px) {
  .block-container{padding:0.5rem 0.8rem !important;}

  /* KPIs: grade 2x2 no mobile */
  [data-testid="stHorizontalBlock"]:has(.kpi) [data-testid="column"]{
    min-width:48% !important; width:48% !important; flex:0 0 48% !important;
  }

  .kpi{padding:8px 4px !important;}
  .kpi-n{font-size:1.3rem !important;}
  .kpi-l{font-size:0.6rem !important;}

  /* Inputs e selects — texto visível e grande */
  .stSelectbox label, .stNumberInput label,
  .stTextInput label, .stTextArea label,
  .stSelectbox>div>div, .stNumberInput>div>div>input,
  .stTextInput>div>div>input, .stTextArea>div>div>textarea,
  [data-baseweb="select"] span, [data-baseweb="input"] input
  {font-size:1rem !important; color:#f1f5f9 !important;}

  /* Botões — tamanho normal para mobile */
  .stButton>button{font-size:0.85rem !important; min-height:38px !important; padding:0.3rem 0.6rem !important;}

  /* Texto */
  label{font-size:0.9rem !important; color:#94a3b8 !important;}
  h1{font-size:1.3rem !important;}
  h2{font-size:1.1rem !important;}
  h3{font-size:0.95rem !important;}
  .card{padding:10px !important;}
}
</style>""", unsafe_allow_html=True)

# Remove barra inferior do Streamlit via JavaScript
st.markdown("""<script>
function removeStreamlitBar() {
  const selectors = [
    '[data-testid="stBottom"]',
    '[data-testid="stStatusWidget"]',
    '[data-testid="manage-app-button"]',
    '.stDeployButton',
    'iframe[src*="streamlit.io"]'
  ];
  selectors.forEach(s => {
    document.querySelectorAll(s).forEach(el => el.remove());
  });
}
setTimeout(removeStreamlitBar, 500);
setTimeout(removeStreamlitBar, 1500);
</script>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════ LOGIN ════
if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    # PINs por operador — adicione novos operadores aqui conforme necessário
    PINS = {
        "José Aparecido": "200695",
    }
    NIVEL = {"José Aparecido": "SR"}

    st.markdown("""
    <style>
    /* LOGIN — tela cheia, responsivo */
    .login-box{
        max-width:420px; margin:40px auto; padding:32px 24px;
        background:linear-gradient(145deg,#0f172a,#1e293b);
        border:1px solid #1e3a5f; border-radius:18px;
    }
    .login-logo{font-size:4rem;text-align:center;margin-bottom:8px;}
    .login-title{color:#f1f5f9;font-size:1.6rem;font-weight:900;text-align:center;margin:0 0 4px;}
    .login-sub{color:#475569;font-size:0.85rem;text-align:center;margin-bottom:24px;}
    .login-label{color:#94a3b8;font-size:1rem;font-weight:600;margin-bottom:4px;}
    /* Inputs grandes para celular */
    .stSelectbox>div>div{font-size:1.1rem !important;min-height:52px !important;}
    .stTextInput>div>div>input{font-size:1.2rem !important;min-height:52px !important;letter-spacing:4px;}
    .stButton>button{min-height:54px !important;font-size:1.1rem !important;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='login-box'>", unsafe_allow_html=True)
    st.markdown("<div class='login-logo'>🛡️</div>", unsafe_allow_html=True)
    st.markdown("<div class='login-title'>Guardião da Usina</div>", unsafe_allow_html=True)
    st.markdown("<div class='login-sub'>Norte Energia · UHE Pimental · SE 230kV</div>", unsafe_allow_html=True)

    operador = st.selectbox("👤 Seu nome", list(PINS.keys()), key="login_nome")
    pin      = st.text_input("🔑 PIN", type="password", max_chars=6,
                              placeholder="Digite seu PIN", key="login_pin")

    if st.button("🛡️  Entrar", use_container_width=True, type="primary", key="login_btn"):
        if pin == PINS.get(operador, ""):
            st.session_state.user  = operador
            st.session_state.nivel = NIVEL.get(operador, "OP")
            st.session_state.login = operador.split()[0].lower()
            st.rerun()
        else:
            st.error("PIN incorreto. Tente novamente.")

    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ═══════════════════════════════════════════════════════════════ SIDEBAR ══
with st.sidebar:
    st.markdown(f"""<div style='padding:16px 0 8px;text-align:center'>
        <div style='font-size:2.8rem'>🛡️</div>
        <div style='color:#f1f5f9;font-size:1rem;font-weight:800'>Guardião da Usina</div>
        <div style='color:#334155;font-size:0.7rem'>UHE Pimental | SE 230kV</div>
    </div>""", unsafe_allow_html=True)
    st.divider()
    st.markdown(f"**👤 {st.session_state.user}**")
    st.markdown(f"<span style='background:#0f1e3a;color:#60a5fa;border:1px solid #1d4ed8;border-radius:20px;padding:3px 12px;font-size:0.75rem;font-weight:700'>Nível {st.session_state.nivel}</span>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    pagina = st.radio("", [
        "🏠  Painel Geral",
        "🗂️  Cadastro de Equipamentos",
        "⚡  Disjuntores SF6",
        "🌡️  Temperaturas",
        "🧮  Calculadora Técnica",
        "📋  Inspeção de Campo",
        "⚠️  Pendências",
        "📊  Relatório Mensal",
        "📧  Configurar E-mail",
    ], label_visibility="collapsed", key="nav_sidebar")
    st.divider()
    st.markdown(f"<div style='color:#334155;font-size:0.7rem'>📅 {date.today().strftime('%d/%m/%Y')}</div>", unsafe_allow_html=True)
    if st.button("🚪 Sair", use_container_width=True):
        for k in ["user","nivel","login"]: st.session_state.pop(k,None)
        st.rerun()

# ── MENU MOBILE (dropdown no topo — sempre visível) ────────────────────────
PAGINAS = [
    "🏠  Painel Geral","🗂️  Cadastro de Equipamentos","⚡  Disjuntores SF6",
    "🌡️  Temperaturas","🧮  Calculadora Técnica","📋  Inspeção de Campo",
    "⚠️  Pendências","📊  Relatório Mensal","📧  Configurar E-mail",
]
st.markdown("""<style>
.nav-mobile{display:none;}
@media(max-width:768px){
  .nav-mobile{display:block !important; margin-bottom:10px;}
  section[data-testid="stSidebar"]{display:none !important;}
}
</style>""", unsafe_allow_html=True)

_nav_container = st.container()
with _nav_container:
    st.markdown("<div class='nav-mobile'>", unsafe_allow_html=True)
    _col_nav, _col_sair = st.columns([4,1])
    pagina_mobile = _col_nav.selectbox(
        "📱 Menu",
        PAGINAS,
        index=PAGINAS.index(pagina) if pagina in PAGINAS else 0,
        key="nav_mobile",
        label_visibility="collapsed"
    )
    if _col_sair.button("🚪", key="sair_mobile", help="Sair"):
        for k in ["user","nivel","login"]: st.session_state.pop(k,None)
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# No mobile, pagina vem do selectbox; no desktop, da sidebar
import re as _re
_is_mobile = False
pagina = pagina_mobile if "nav_mobile" in st.session_state else pagina

# ═══════════════════════════════════════════════════════════════ PAINEL ══
if "Painel" in pagina:
    st.markdown("""<div style='background:linear-gradient(90deg,#0c2340,#0f3460,#0c2340);border-radius:14px;padding:18px 28px;margin-bottom:12px;border:1px solid #1e3a5f'>
        <div style='color:#f1f5f9;font-size:1.4rem;font-weight:900'>🛡️ Guardião da Usina — Painel Operacional</div>
        <div style='color:#3b82f6;font-size:0.8rem;margin-top:2px'>Subestação 230kV · UHE Pimental | Workflow de Inspeção</div>
    </div>""", unsafe_allow_html=True)

    # ══ 1. TEMPERATURA AMBIENTE CENTRALIZADA ════════════════════════════════
    # Campos em linha — responsivo no mobile
    _a1, _a2, _a3, _a4 = st.columns(4)
    t_amb = _a1.number_input(
        "🌡️ Temperatura (°C)",
        value=float(st.session_state.get("temp_amb_global", 28.0)),
        min_value=-10.0, max_value=60.0, step=0.5, format="%.1f", key="amb_temp_painel"
    )
    u_amb = _a2.number_input(
        "💧 Umidade (%)",
        value=float(st.session_state.get("umid_amb_global", 70.0)),
        min_value=0.0, max_value=100.0, step=1.0, format="%.0f", key="amb_umid_painel"
    )
    turno_dia = _a3.selectbox(
        "⏰ Turno",
        ["Manhã (06-14h)", "Tarde (14-22h)", "Noite (22-06h)"],
        index=["Manhã (06-14h)","Tarde (14-22h)","Noite (22-06h)"].index(
            st.session_state.get("turno_global", "Manhã (06-14h)")),
        key="amb_turno_painel"
    )
    _data_insp = _a4.date_input(
        "📅 Data da inspeção",
        value=date.today(),
        key="data_insp_painel",
        help="Mude para continuar uma inspeção iniciada em outro dia"
    )

    if t_amb > 35:   _cc = "#ef4444"; _ct = "Muito Quente"
    elif t_amb > 30: _cc = "#f59e0b"; _ct = "Quente"
    elif t_amb > 22: _cc = "#10b981"; _ct = "Confortável"
    else:            _cc = "#3b82f6"; _ct = "Ameno"

    st.markdown(f"""<div style='background:#0a1628;border:1px solid #1e3a5f;border-radius:10px;
        padding:10px 16px;margin-top:4px;
        display:grid;grid-template-columns:repeat(auto-fit,minmax(100px,1fr));gap:12px;text-align:center'>
        <div>
            <div style='font-size:1.5rem;font-weight:900;color:{_cc}'>{t_amb:.1f}°C</div>
            <div style='font-size:0.65rem;color:#475569'>{_ct}</div>
        </div>
        <div>
            <div style='font-size:1.5rem;font-weight:900;color:#3b82f6'>{u_amb:.0f}%</div>
            <div style='font-size:0.65rem;color:#475569'>Umidade</div>
        </div>
        <div>
            <div style='font-size:1rem;font-weight:700;color:#f59e0b'>{t_amb + 65:.0f}°C</div>
            <div style='font-size:0.65rem;color:#475569'>Lim. OTI Trafo</div>
        </div>
        <div>
            <div style='font-size:0.9rem;font-weight:700;color:#10b981'>{turno_dia.split()[0]}</div>
            <div style='font-size:0.65rem;color:#475569'>Turno</div>
        </div>
    </div>""", unsafe_allow_html=True)

    st.session_state["temp_amb_global"] = t_amb
    st.session_state["umid_amb_global"] = u_amb
    st.session_state["turno_global"]    = turno_dia
    # Persistir no banco — restaura ao reabrir o app
    if t_amb    != st.session_state.get("_cfg_temp"):
        salvar_config("temp_amb", str(t_amb));   st.session_state["_cfg_temp"]  = t_amb
    if u_amb    != st.session_state.get("_cfg_umid"):
        salvar_config("umid_amb", str(u_amb));   st.session_state["_cfg_umid"]  = u_amb
    if turno_dia != st.session_state.get("_cfg_turno"):
        salvar_config("turno", turno_dia);       st.session_state["_cfg_turno"] = turno_dia

    st.markdown("<div style='border-bottom:1px solid #1e3a5f;margin:14px 0'></div>", unsafe_allow_html=True)

    # ══ DADOS COMUNS ═════════════════════════════════════════════════════════
    df_sf6_all  = _carregar_sf6()
    df_pend_all = _carregar_pendencias()
    df_djs_db   = _carregar_equipamentos("Disjuntor SF6")
    df_secs_db  = _carregar_equipamentos("Seccionadora")

    # Período do mês atual para controle de inspeções
    _mes_ini = date(_data_insp.year, _data_insp.month, 1)
    _mes_fim = _data_insp

    df_sf6_mes  = _carregar_sf6(data_ini=_mes_ini, data_fim=_mes_fim)
    df_insp_sec_mes = _carregar_inspecoes(sistema="Seccionadora", data_ini=_mes_ini, data_fim=_mes_fim)

    djs_todos          = df_djs_db["tag"].tolist() if not df_djs_db.empty else []
    djs_inspecionados  = set(df_sf6_mes["disjuntor"].unique()) if not df_sf6_mes.empty else set()
    djs_pendentes      = [t for t in djs_todos if t not in djs_inspecionados]
    if not djs_pendentes:
        djs_pendentes = list(djs_todos)

    secs_todos         = df_secs_db["tag"].tolist() if not df_secs_db.empty else []
    secs_inspecionadas = set(df_insp_sec_mes["item"].unique()) if not df_insp_sec_mes.empty else set()
    secs_pendentes     = [t for t in secs_todos if t not in secs_inspecionadas]
    if not secs_pendentes:
        secs_pendentes = list(secs_todos)

    pend_abertas = len(df_pend_all[df_pend_all.status == "Aberta"]) if not df_pend_all.empty else 0

    # Alertas preditivos (pré-calcular)
    alertas_list = []
    if not df_sf6_all.empty:
        _ult = df_sf6_all.sort_values("created_at").groupby(["disjuntor","polo"]).last().reset_index()
        for _, _r in _ult.iterrows():
            _eq = buscar_equipamento_por_tag(_r.disjuntor)
            if not _eq: continue
            _p_al  = float(_eq.get("pressao_alarme", 5.5))
            _p_bl  = float(_eq.get("pressao_bloqueio", 5.0))
            _p_nom = float(_eq.get("pressao_nominal", 6.0))
            _p_c   = float(_r.pressao_corrigida)
            if   _p_c < _p_bl:          alertas_list.append({"tag":_r.disjuntor,"polo":_r.polo,"p":_p_c,"nivel":"BLOQUEIO","cor":"#ef4444","bg":"#450a0a","margem":_p_c-_p_bl})
            elif _p_c < _p_al:          alertas_list.append({"tag":_r.disjuntor,"polo":_r.polo,"p":_p_c,"nivel":"ALARME",  "cor":"#f59e0b","bg":"#451a03","margem":_p_c-_p_al})
            elif _p_c < _p_al + 0.3:   alertas_list.append({"tag":_r.disjuntor,"polo":_r.polo,"p":_p_c,"nivel":"PRÉ-ALARME","cor":"#f97316","bg":"#431407","margem":_p_c-_p_al})
    alertas_list.sort(key=lambda x: x["margem"])

    # ══ BANNER DE ALERTA — aparece no topo se há SF6 crítico ════════════════
    if alertas_list:
        _bloqueios = [a for a in alertas_list if a["nivel"] == "BLOQUEIO"]
        _alarmes   = [a for a in alertas_list if a["nivel"] == "ALARME"]
        _pre       = [a for a in alertas_list if a["nivel"] == "PRÉ-ALARME"]

        if _bloqueios:
            _titulo_banner = "🚨 BLOQUEIO SF6 — AÇÃO IMEDIATA NECESSÁRIA"
            _cor_banner    = "#ef4444"
            _bg_banner     = "#3b0000"
            _borda_banner  = "#ef4444"
        elif _alarmes:
            _titulo_banner = "⚠️ ALARME SF6 — MONITORAR COM ATENÇÃO"
            _cor_banner    = "#f59e0b"
            _bg_banner     = "#2d1800"
            _borda_banner  = "#f59e0b"
        else:
            _titulo_banner = "🔔 PRÉ-ALARME SF6 — PRESSÃO SE APROXIMANDO DO LIMITE"
            _cor_banner    = "#f97316"
            _bg_banner     = "#1f1000"
            _borda_banner  = "#f97316"

        _linhas = ""
        for _a in alertas_list:
            _ic = "🔴" if _a["nivel"]=="BLOQUEIO" else "🟠" if _a["nivel"]=="ALARME" else "🟡"
            _linhas += (f"<div style='display:flex;justify-content:space-between;align-items:center;"
                        f"background:rgba(0,0,0,0.3);border-radius:6px;padding:6px 12px;margin:4px 0'>"
                        f"<span style='color:#f1f5f9;font-weight:700;font-size:0.9rem'>"
                        f"{_ic} {_a['tag']} · Polo {_a['polo']}</span>"
                        f"<span style='color:{_a['cor']};font-weight:900;font-size:1rem'>"
                        f"{_a['p']:.3f} bar</span>"
                        f"<span style='background:{_a['cor']};color:#000;font-size:0.7rem;"
                        f"font-weight:900;border-radius:4px;padding:2px 8px'>{_a['nivel']}</span>"
                        f"</div>")

        st.markdown(f"""
        <div style='background:{_bg_banner};border:2px solid {_borda_banner};
            border-radius:12px;padding:14px 18px;margin-bottom:16px'>
            <div style='color:{_cor_banner};font-size:1rem;font-weight:900;
                letter-spacing:0.5px;margin-bottom:10px'>{_titulo_banner}</div>
            {_linhas}
        </div>""", unsafe_allow_html=True)

    # ══ KPIs ════════════════════════════════════════════════════════════════
    # KPIs em grid HTML responsivo — funciona no mobile sem depender de st.columns
    _djs_feitos  = len(djs_inspecionados)
    _secs_feitas = len(secs_inspecionadas)
    _kpis = [
        ("⚡", f"{_djs_feitos}/{len(djs_todos)}",    "DJ Mês",     "#10b981" if _djs_feitos==len(djs_todos) else "#3b82f6"),
        ("🔌", f"{_secs_feitas}/{len(secs_todos)}",  "SEC Mês",    "#10b981" if _secs_feitas==len(secs_todos) else "#06b6d4"),
        ("🚨", len(alertas_list),                    "Alertas",    "#ef4444" if alertas_list else "#10b981"),
        ("⚠️", pend_abertas,                         "Pendências", "#8b5cf6"),
    ]
    _kpi_html = "".join([f"""
        <div style='background:linear-gradient(135deg,#0f1e3a,#162447);border:1px solid #1e3a5f;
            border-top:3px solid {c};border-radius:12px;padding:12px 6px;text-align:center;'>
            <div style='font-size:1.4rem'>{ic}</div>
            <div style='font-size:1.6rem;font-weight:900;color:{c};line-height:1.1'>{n}</div>
            <div style='font-size:0.65rem;color:#64748b;text-transform:uppercase;letter-spacing:1px;margin-top:3px'>{lb}</div>
        </div>""" for ic,n,lb,c in _kpis])
    st.markdown(f"""<div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(90px,1fr));
        gap:8px;margin-bottom:12px'>{_kpi_html}</div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ══ COLUNAS PRINCIPAIS ═══════════════════════════════════════════════════
    col_wf, col_painel = st.columns([3, 2])

    # ── COLUNA ESQUERDA: WORKFLOWS ──────────────────────────────────────────
    with col_wf:

        # ── 2. WORKFLOW SF6 ─────────────────────────────────────────────────
        st.markdown("""<div style='color:#60a5fa;font-size:0.72rem;font-weight:700;
            text-transform:uppercase;letter-spacing:1px;margin-bottom:6px'>
            ⚡ Inspeção SF6 — Disjuntores</div>""", unsafe_allow_html=True)

        _dj_tot  = len(djs_todos)
        _dj_done = _dj_tot - len(djs_pendentes)
        _dj_pct  = _dj_done / _dj_tot if _dj_tot else 0
        st.progress(_dj_pct, text=f"{_dj_done}/{_dj_tot} disjuntores inspecionados hoje")

        # Última leitura por disjuntor — verde=hoje, amarelo=≤7d, vermelho=>7d
        if not df_sf6_all.empty:
            _ult_sf6 = df_sf6_all.sort_values("data").groupby("disjuntor").last()[["data","pressao_corrigida","status_sf6"]].reset_index()
            _chips = []
            for _, _r in _ult_sf6.iterrows():
                try: _dias = (date.today() - date.fromisoformat(str(_r.data))).days
                except: _dias = 999
                _cor = "#10b981" if _dias == 0 else "#f59e0b" if _dias <= 7 else "#ef4444"
                _chips.append(f"<span style='background:#0a1628;border:1px solid {_cor};border-radius:6px;"
                               f"padding:2px 8px;font-size:0.7rem;color:{_cor};margin:2px;display:inline-block'>"
                               f"{_r.disjuntor} · {_r.data} · {_r.pressao_corrigida:.3f} bar</span>")
            if _chips:
                st.markdown("<div style='margin:4px 0 10px;line-height:2'>" + "".join(_chips) + "</div>",
                            unsafe_allow_html=True)

        _djs_todos_feitos = len(djs_inspecionados) >= len(djs_todos) and len(djs_todos) > 0
        if _djs_todos_feitos:
            st.success(f"✅ Todos os {len(djs_todos)} disjuntores inspecionados neste mês! Lista disponível para nova rodada.")
        else:
            _df_dj_pend = df_djs_db[df_djs_db["tag"].isin(djs_pendentes)]
            _opc_dj = {r.tag: f"{r.tag}  ·  {r.modelo or '—'}  ·  {(r.descricao or '')[:40]}"
                       for _, r in _df_dj_pend.iterrows()}
            _dj_sel = st.selectbox("⚡ Disjuntor pendente", list(_opc_dj.keys()),
                                   format_func=lambda t: _opc_dj[t], key="wf_dj_sel")

            _eq_dj = _buscar_equipamento_por_tag(_dj_sel)
            _p_nom_wf = float(_eq_dj.get("pressao_nominal", 6.0)) if _eq_dj else 6.0
            _p_al_wf  = float(_eq_dj.get("pressao_alarme",  5.5)) if _eq_dj else 5.5
            _p_bl_wf  = float(_eq_dj.get("pressao_bloqueio",5.0)) if _eq_dj else 5.0
            _np_wf    = int(_eq_dj.get("num_polos") or DISJUNTORES.get(_dj_sel,{}).get("num_polos",1)) if _eq_dj else 1
            _polos_wf = ["Polo A","Polo B","Polo V"] if _np_wf == 3 else ["Câmara Única"]

            _ITENS_DJ = [
                "Sem vazamentos visíveis",
                "Indicador de pressão funcionando",
                "Sem corrosão / aparência anormal",
                "Mecanismo de operação normal",
                "Sem ruídos anormais",
            ]

            with st.form(f"form_sf6_{_dj_sel}", clear_on_submit=True):
                # ── PRESSÕES ─────────────────────────────────────────────
                st.markdown("<div style='color:#3b82f6;font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px'>📊 Pressão SF6</div>", unsafe_allow_html=True)
                st.caption(f"Nominal: {_p_nom_wf} bar · Alarme: {_p_al_wf} bar · Bloqueio: {_p_bl_wf} bar · Correção a 20°C automática")
                _cols_polo = st.columns(len(_polos_wf))
                _pressoes_form = {}
                for _i, _polo in enumerate(_polos_wf):
                    with _cols_polo[_i]:
                        _pressoes_form[_polo] = st.number_input(f"{_polo} (bar)", value=_p_nom_wf,
                                                 min_value=0.0, max_value=10.0,
                                                 step=0.01, format="%.3f", key=f"wf_p_{_polo}")

                st.markdown("<div style='border-bottom:1px solid #1e3a5f;margin:10px 0 8px'></div>", unsafe_allow_html=True)

                # ── INSPEÇÃO VISUAL ──────────────────────────────────────
                st.markdown("<div style='color:#60a5fa;font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px'>🔍 Inspeção Visual</div>", unsafe_allow_html=True)
                _res_visual = {}
                for _iv in _ITENS_DJ:
                    _vv = st.radio(f"{_iv}", ["OK","NC"], index=None,
                                   horizontal=True, key=f"dj_vis_{_dj_sel}_{_iv}")
                    _res_visual[_iv] = _vv

                st.markdown("<div style='border-bottom:1px solid #1e3a5f;margin:10px 0 8px'></div>", unsafe_allow_html=True)

                # ── OPERAÇÕES ────────────────────────────────────────────
                st.markdown("<div style='color:#8b5cf6;font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px'>🔢 Operações no Turno</div>", unsafe_allow_html=True)
                _houve_op = st.radio("Houve operações neste turno?", ["Não","Sim"],
                                     index=0, horizontal=True, key=f"op_houve_{_dj_sel}")
                _oc1, _oc2 = st.columns(2)
                _op_tipo = _oc1.selectbox("Tipo de operação", [
                    "Abertura Normal","Fechamento Normal",
                    "Abertura por Falta","Fechamento Automático","Teste"
                ], key=f"op_tipo_{_dj_sel}")
                _op_qtd = _oc2.number_input("Quantidade", min_value=1, max_value=50,
                                            value=1, step=1, key=f"op_qtd_{_dj_sel}")
                st.caption("Preencha tipo e quantidade apenas se houver operações.")

                st.markdown("<div style='border-bottom:1px solid #1e3a5f;margin:10px 0 8px'></div>", unsafe_allow_html=True)

                # ── CONTADORES ───────────────────────────────────────────
                st.markdown("<div style='color:#06b6d4;font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px'>📟 Contadores de Operações</div>", unsafe_allow_html=True)
                st.caption("Informe 0 se não verificado nesta inspeção.")
                _cc1, _cc2 = st.columns(2)
                _cnt_trip = _cc1.number_input("P1LT — Tripolar", min_value=0, value=0, step=1, key=f"cnt_trip_{_dj_sel}")
                _cnt_cc   = _cc2.number_input("P2 — Curto Circuito", min_value=0, value=0, step=1, key=f"cnt_cc_{_dj_sel}")
                if _np_wf == 3:
                    _ca, _cb, _cv = st.columns(3)
                    _cnt_a = _ca.number_input("P1LA — Polo A", min_value=0, value=0, step=1, key=f"cnt_a_{_dj_sel}")
                    _cnt_b = _cb.number_input("P1LB — Polo B", min_value=0, value=0, step=1, key=f"cnt_b_{_dj_sel}")
                    _cnt_v = _cv.number_input("P1LV — Polo V", min_value=0, value=0, step=1, key=f"cnt_v_{_dj_sel}")
                else:
                    _cnt_a = _cnt_b = _cnt_v = 0

                st.markdown("<div style='border-bottom:1px solid #1e3a5f;margin:10px 0 8px'></div>", unsafe_allow_html=True)
                _obs_wf = st.text_input("Observação geral (opcional)", key="wf_dj_obs",
                                        placeholder="Condições de campo, instrumento usado...")
                _foto_dj = st.file_uploader("📷 Foto (opcional)", type=["jpg","jpeg","png"],
                                             key=f"foto_dj_{_dj_sel}")
                _leg_dj = ""
                if _foto_dj:
                    _leg_dj = st.text_input("Legenda da foto", key=f"leg_dj_{_dj_sel}",
                                             placeholder=f"Ex: Manômetro {_dj_sel}")
                _salvar_sf6 = st.form_submit_button(
                    f"💾 Salvar {_dj_sel} e Avançar ({len(djs_pendentes)-1} restante(s))",
                    type="primary", use_container_width=True)

            if _salvar_sf6:
                import json as _json
                _vis_preench = [v for v in _res_visual.values() if v is not None]
                if len(_vis_preench) < len(_ITENS_DJ):
                    st.warning(f"⚠️ Preencha todos os {len(_ITENS_DJ)} itens da inspeção visual ({len(_vis_preench)}/{len(_ITENS_DJ)} preenchidos).")
                else:
                    _vis_nc = sum(1 for v in _res_visual.values() if v == "NC")
                    _hora_wf = datetime.now().time()
                    _obs_completo = _json.dumps(_res_visual, ensure_ascii=False)
                    if _obs_wf: _obs_completo += f" | {_obs_wf}"
                    _resumo_pressoes = []
                    for _polo, _p_med in _pressoes_form.items():
                        _p_cor = corrigir_pressao_sf6(_p_med, t_amb)
                        if _p_cor < _p_bl_wf: _st_sf6 = "BLOQUEIO"
                        elif _p_cor < _p_al_wf: _st_sf6 = "ALARME"
                        else: _st_sf6 = "NORMAL"
                        salvar_sf6({"data":str(_data_insp),"hora":str(_hora_wf),
                                    "turno":turno_dia,"disjuntor":_dj_sel,"polo":_polo,
                                    "pressao_medida":_p_med,"temperatura":t_amb,
                                    "pressao_corrigida":_p_cor,"status_sf6":_st_sf6,
                                    "observacao":_obs_completo,"usuario":st.session_state.login})
                        _resumo_pressoes.append(f"{_polo}: {_p_cor:.3f} bar ({_st_sf6})")
                    _st_vis = "NC" if _vis_nc > 0 else "OK"
                    salvar_inspecao({"data":str(_data_insp),"turno":turno_dia,
                                     "sistema":"Disjuntor SF6","item":_dj_sel,
                                     "status":_st_vis,"observacao":_obs_completo,
                                     "usuario":st.session_state.login})
                    if _houve_op == "Sim" and _op_tipo:
                        salvar_operacao({"data":str(_data_insp),"disjuntor":_dj_sel,
                                         "tipo_operacao":_op_tipo,"motivo":turno_dia,
                                         "num_operacoes_total":int(_op_qtd),
                                         "usuario":st.session_state.login})
                    if any([_cnt_trip, _cnt_cc, _cnt_a, _cnt_b, _cnt_v]):
                        salvar_contador({"data":str(_data_insp),"hora":str(_hora_wf),"turno":turno_dia,
                                         "disjuntor":_dj_sel,
                                         "polo_a":int(_cnt_a),"polo_b":int(_cnt_b),"polo_v":int(_cnt_v),
                                         "tripolar":int(_cnt_trip),"curto_circuito":int(_cnt_cc),
                                         "usuario":st.session_state.login})
                        _carregar_contadores.clear()
                    if _foto_dj:
                        _foto_dj.seek(0)
                        salvar_foto({"data":str(_data_insp), "sistema":f"SF6 — {_dj_sel}",
                                     "legenda":_leg_dj or _dj_sel,
                                     "foto_base64":foto_para_base64(_foto_dj.read()),
                                     "usuario":st.session_state.login})
                    _vs2 = "🟢 BOA" if _vis_nc==0 else "🟡 ATENÇÃO" if _vis_nc<=2 else "🔴 CRÍTICA"
                    st.success(f"✅ {_dj_sel} — {' · '.join(_resumo_pressoes)} | Visual: {_vs2}")
                    _carregar_sf6.clear()
                    st.rerun()

    # ── COLUNA DIREITA: ALERTAS + EVOLUÇÃO SF6 ──────────────────────────────
    with col_painel:

        # ── 5. ALERTAS PREDITIVOS ────────────────────────────────────────────
        st.markdown("""<div style='color:#ef4444;font-size:0.72rem;font-weight:700;
            text-transform:uppercase;letter-spacing:1px;margin-bottom:6px'>
            🚨 Alertas Preditivos — SF6</div>""", unsafe_allow_html=True)

        if not alertas_list:
            st.markdown("""<div style='background:#052e16;border:1px solid #10b981;
                border-radius:10px;padding:12px 16px;text-align:center'>
                <div style='font-size:1.2rem'>🟢</div>
                <div style='color:#34d399;font-weight:700;font-size:0.85rem'>Todos os disjuntores OK</div>
                <div style='color:#065f46;font-size:0.72rem'>Pressão dentro dos limites</div>
            </div>""", unsafe_allow_html=True)
        else:
            for _a in alertas_list:
                _margem_txt = f"Δ {_a['margem']:.3f} bar até alarme" if _a["nivel"] != "BLOQUEIO" else "OPERAÇÃO IMPEDIDA"
                st.markdown(f"""<div style='background:{_a["bg"]};border:1px solid {_a["cor"]};
                    border-left:4px solid {_a["cor"]};border-radius:8px;
                    padding:10px 14px;margin-bottom:6px'>
                    <div style='display:flex;justify-content:space-between;align-items:center'>
                        <div>
                            <span style='color:#f1f5f9;font-weight:800;font-size:0.9rem'>{_a["tag"]}</span>
                            <span style='color:#475569;font-size:0.75rem'> · {_a["polo"]}</span>
                        </div>
                        <span style='color:{_a["cor"]};font-size:1rem;font-weight:900'>{_a["p"]:.3f} bar</span>
                    </div>
                    <div style='display:flex;justify-content:space-between;margin-top:4px'>
                        <span style='background:{_a["cor"]}33;color:{_a["cor"]};border-radius:8px;
                            padding:2px 10px;font-size:0.72rem;font-weight:800'>{_a["nivel"]}</span>
                        <span style='color:#475569;font-size:0.7rem'>{_margem_txt}</span>
                    </div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<div style='border-bottom:1px solid #1e3a5f;margin:12px 0'></div>", unsafe_allow_html=True)

        # ── HISTÓRICO DO DIA ─────────────────────────────────────────────────
        st.markdown("""<div style='color:#94a3b8;font-size:0.72rem;font-weight:700;
            text-transform:uppercase;letter-spacing:1px;margin-bottom:6px'>
            📋 Atividades de Hoje</div>""", unsafe_allow_html=True)

        _hist_itens = []

        # SF6 hoje — última leitura por disjuntor
        _sf6_hoje = df_sf6_all[df_sf6_all["data"] == str(_data_insp)] if not df_sf6_all.empty else pd.DataFrame()
        if not _sf6_hoje.empty:
            _sf6_ult = _sf6_hoje.sort_values("hora").groupby("disjuntor").last().reset_index()
            for _, _r in _sf6_ult.iterrows():
                _st_cor = "#10b981" if _r.status_sf6 == "NORMAL" else "#ef4444"
                _hist_itens.append(("⚡", "#1e3a5f",
                    f"<b style='color:#f1f5f9'>{_r.disjuntor}</b>"
                    f"<span style='color:{_st_cor}'> · {float(_r.pressao_corrigida):.3f} bar</span>"
                    f"<span style='color:#475569'> · {str(_r.hora)[:5]}</span>"))

        # Inspeções de campo hoje (trafo, para-raios, sala elétrica, cúbilo, seccionadoras)
        _insp_hoje = _carregar_inspecoes_hoje(_data_insp)
        if not _insp_hoje.empty:
            _ICONES_SIS = {
                "Transformador": "🌡️", "Subestação 230kV": "⚡",
                "Sala Elétrica da SE": "🏭", "Cúbilo de 13.8kV da SE": "🔲",
            }
            _sec_hoje = _insp_hoje[_insp_hoje.sistema == "Seccionadora"]
            _outros_hoje = _insp_hoje[_insp_hoje.sistema != "Seccionadora"]

            if not _sec_hoje.empty:
                _n_sec = len(_sec_hoje["item"].unique())
                _cor_sec = "#10b981" if _n_sec >= len(secs_todos) else "#06b6d4"
                _hist_itens.append(("🔌", "#0c2340",
                    f"<b style='color:{_cor_sec}'>{_n_sec}/{len(secs_todos)} seccionadoras</b>"
                    f"<span style='color:#475569'> inspecionadas</span>"))

            for _, _ri in _outros_hoje.drop_duplicates("sistema").iterrows():
                _ic_s = _ICONES_SIS.get(_ri.sistema, "🔍")
                _st_c = "#10b981" if _ri.status in ("OK","NORMAL") else "#ef4444" if _ri.status in ("NOK","CRITICO") else "#f59e0b"
                _hist_itens.append((_ic_s, "#0c2340",
                    f"<b style='color:#e2e8f0'>{_ri.sistema.replace(' TR-SE-01 (Toshiba 10/12.5 MVA)','')[:28]}</b>"
                    f"<span style='color:{_st_c}'> · {_ri.status}</span>"
                    f"<span style='color:#475569'> · {_ri.usuario}</span>"))

        # Pendências abertas hoje
        _pend_hoje = df_pend_all[df_pend_all["data_abertura"] == str(_data_insp)] if not df_pend_all.empty else pd.DataFrame()
        if not _pend_hoje.empty:
            for _, _rp in _pend_hoje.iterrows():
                _pri_c = "#ef4444" if _rp.prioridade=="Alta" else "#f59e0b" if _rp.prioridade in ("Média","Media") else "#10b981"
                _hist_itens.append(("⚠️", "#1a0a00",
                    f"<b style='color:{_pri_c}'>[{_rp.prioridade}]</b>"
                    f"<span style='color:#e2e8f0'> {str(_rp.descricao)[:35]}{'…' if len(str(_rp.descricao))>35 else ''}</span>"))

        if _hist_itens:
            _hist_html = "".join([
                f"<div style='background:{bg};border-left:3px solid #1e3a5f;"
                f"border-radius:6px;padding:6px 10px;margin:3px 0;"
                f"display:flex;align-items:center;gap:8px'>"
                f"<span style='font-size:0.85rem'>{ic}</span>"
                f"<span style='font-size:0.78rem;line-height:1.3'>{txt}</span></div>"
                for ic, bg, txt in _hist_itens
            ])
            st.markdown(f"<div style='max-height:260px;overflow-y:auto'>{_hist_html}</div>",
                        unsafe_allow_html=True)
        else:
            st.markdown("""<div style='background:#0a1628;border:1px dashed #1e3a5f;
                border-radius:8px;padding:10px 14px;text-align:center'>
                <div style='color:#334155;font-size:0.8rem'>Nenhuma atividade registrada hoje</div>
                <div style='color:#1e3a5f;font-size:0.7rem;margin-top:2px'>Primeiro turno do dia</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='border-bottom:1px solid #1e3a5f;margin:12px 0'></div>", unsafe_allow_html=True)

        # ── 4. EVOLUÇÃO SF6 ──────────────────────────────────────────────────
        st.markdown("""<div style='color:#60a5fa;font-size:0.72rem;font-weight:700;
            text-transform:uppercase;letter-spacing:1px;margin-bottom:6px'>
            📈 Evolução da Pressão SF6</div>""", unsafe_allow_html=True)

        if not df_sf6_all.empty and len(df_sf6_all) > 1:
            _df_plot = df_sf6_all.copy()
            _df_plot["data_hora"] = pd.to_datetime(_df_plot["data"] + " " + _df_plot["hora"])
            _df_plot["label"] = _df_plot["disjuntor"] + " · " + _df_plot["polo"]
            _df_plot = _df_plot.sort_values("data_hora")

            _fig = go.Figure()
            _cores = ["#3b82f6","#10b981","#f59e0b","#8b5cf6","#ef4444","#06b6d4","#f97316"]
            for _i, _lbl in enumerate(_df_plot["label"].unique()):
                _df_l = _df_plot[_df_plot["label"] == _lbl]
                _fig.add_trace(go.Scatter(
                    x=_df_l["data_hora"], y=_df_l["pressao_corrigida"],
                    mode="lines+markers", name=_lbl,
                    line=dict(color=_cores[_i % len(_cores)], width=2),
                    marker=dict(size=5)))

            # Linhas de referência (primeira config)
            _eq0 = buscar_equipamento_por_tag(djs_todos[0]) if djs_todos else None
            if _eq0:
                _fig.add_hline(y=float(_eq0.get("pressao_nominal",6.0)), line_dash="dot",
                               line_color="#475569", annotation_text="Nominal",
                               annotation_font_color="#475569", annotation_font_size=10)
                _fig.add_hline(y=float(_eq0.get("pressao_alarme",5.5)), line_dash="dash",
                               line_color="#f59e0b", annotation_text="Alarme",
                               annotation_font_color="#f59e0b", annotation_font_size=10)
                _fig.add_hline(y=float(_eq0.get("pressao_bloqueio",5.0)), line_dash="dash",
                               line_color="#ef4444", annotation_text="Bloqueio",
                               annotation_font_color="#ef4444", annotation_font_size=10)

            _fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0.2)",
                font_color="#94a3b8", height=320, margin=dict(l=0,r=0,t=10,b=0),
                xaxis_title="", yaxis_title="bar a 20°C",
                legend=dict(bgcolor="rgba(0,0,0,0)", font_size=9, orientation="h",
                            yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(_fig, use_container_width=True)
        else:
            st.info("Sem histórico SF6. Registre leituras para visualizar tendências.")

    # ── 3. WORKFLOW SECCIONADORAS — largura total ────────────────────────────
    st.markdown("<div style='border-top:1px solid #1e3a5f;margin:14px 0'></div>", unsafe_allow_html=True)
    st.markdown("""<div style='color:#06b6d4;font-size:0.72rem;font-weight:700;
        text-transform:uppercase;letter-spacing:1px;margin-bottom:6px'>
        🔌 Inspeção de Seccionadoras</div>""", unsafe_allow_html=True)

    _sec_tot  = len(secs_todos)
    _sec_done = _sec_tot - len(secs_pendentes)
    _sec_pct  = _sec_done / _sec_tot if _sec_tot else 0
    st.progress(_sec_pct, text=f"{_sec_done}/{_sec_tot} seccionadoras inspecionadas hoje")

    _ITENS_SEC = [
        "Condição geral (visual)",
        "Isoladores — trincas e sujidade",
        "Fixação e parafusos",
        "Lubrificação — articulações e mecanismo",
        "Contatos — desgaste e oxidação",
        "Sistema de travamento/bloqueio",
        "Identificação e sinalização",
    ]

    _secs_todas_feitas = len(secs_inspecionadas) >= len(secs_todos) and len(secs_todos) > 0
    if _secs_todas_feitas:
        st.success(f"✅ Todas as {len(secs_todos)} seccionadoras inspecionadas neste mês! Lista disponível para nova rodada.")
    else:
        _df_sec_pend = df_secs_db[df_secs_db["tag"].isin(secs_pendentes)]
        _opc_sec = {r.tag: f"{r.tag}  ·  {(r.descricao or '')[:55]}"
                    for _, r in _df_sec_pend.iterrows()}
        _sec_sel = st.selectbox("🔌 Seccionadora pendente", list(_opc_sec.keys()),
                                format_func=lambda t: _opc_sec[t], key="wf_sec_sel")

        # JS injeta estilo inline nos radios após render — coloca OK/NC antes da label
        st.components.v1.html("""
        <script>
        function fixRadios() {
            var radios = parent.document.querySelectorAll('[data-testid="stRadio"]');
            radios.forEach(function(r) {
                r.style.display = 'flex';
                r.style.flexDirection = 'row';
                r.style.alignItems = 'center';
                r.style.gap = '10px';
                r.style.background = '#0f172a';
                r.style.border = '1px solid #1e3a5f';
                r.style.borderRadius = '8px';
                r.style.padding = '6px 12px';
                r.style.marginBottom = '4px';
                var lbl = r.querySelector('[data-testid="stWidgetLabel"]');
                var opts = r.querySelector('div[class]');
                if (lbl) { lbl.style.order = '2'; lbl.style.fontSize = '0.85rem'; }
                if (opts) { opts.style.order = '1'; opts.style.flexShrink = '0'; }
            });
        }
        setTimeout(fixRadios, 200);
        setTimeout(fixRadios, 600);
        setTimeout(fixRadios, 1500);
        </script>
        """, height=0)

        if _sec_sel.startswith("PMCA"):
            st.markdown("<div style='background:#0c2340;border:1px solid #1e3a5f;border-radius:6px;padding:5px 12px;margin:4px 0;font-size:0.75rem;color:#60a5fa'>⚡ Chave de Aterramento — varão simples, sem isoladores de porcelana</div>", unsafe_allow_html=True)
            _ITENS_INSP = [
                "Condição geral (visual)",
                "Fixação e parafusos",
                "Lubrificação — articulações e mecanismo",
                "Contatos — desgaste e oxidação",
                "Sistema de travamento/bloqueio",
                "Identificação e sinalização",
            ]
        else:
            _ITENS_INSP = _ITENS_SEC

        with st.form(f"form_sec_{_sec_sel}", clear_on_submit=True):
            st.markdown("<div style='margin:6px 0 4px;color:#94a3b8;font-size:0.78rem;font-weight:600'>Itens de inspeção:</div>", unsafe_allow_html=True)
            _resultados = {}
            for _item in _ITENS_INSP:
                _val = st.radio(f"{_item}", ["OK","NC"], index=None,
                                horizontal=True, key=f"sec_{_sec_sel}_{_item}")
                _resultados[_item] = _val
            _obs_sec = st.text_input("Observação geral", key="wf_sec_obs",
                                     placeholder="Condições observadas, intercorrências...")
            _foto_sec = st.file_uploader("📷 Foto (opcional)", type=["jpg","jpeg","png"],
                                          key=f"foto_sec_{_sec_sel}")
            _leg_sec = ""
            if _foto_sec:
                _leg_sec = st.text_input("Legenda da foto", key=f"leg_sec_{_sec_sel}",
                                          placeholder=f"Ex: {_sec_sel} contato")
            _salvar_sec = st.form_submit_button(
                f"💾 Salvar {_sec_sel} e Avançar ({len(secs_pendentes)-1} restante(s))",
                type="primary", use_container_width=True)

        if _salvar_sec:
            import json as _json
            _preenchidos = [v for v in _resultados.values() if v is not None]
            if len(_preenchidos) < len(_ITENS_INSP):
                st.warning(f"⚠️ Preencha todos os {len(_ITENS_INSP)} itens antes de salvar ({len(_preenchidos)}/{len(_ITENS_INSP)} preenchidos).")
            else:
                _n_nc = sum(1 for v in _resultados.values() if v == "NC")
                _n_ok = len(_ITENS_INSP) - _n_nc
                _status_geral = "NC" if _n_nc > 0 else "OK"
                _obs_completo = _json.dumps(_resultados, ensure_ascii=False)
                if _obs_sec: _obs_completo += f" | {_obs_sec}"
                salvar_inspecao({"data":str(_data_insp),"turno":turno_dia,
                                 "sistema":"Seccionadora","item":_sec_sel,
                                 "status":_status_geral,"observacao":_obs_completo,
                                 "usuario":st.session_state.login})
                if _foto_sec:
                    _foto_sec.seek(0)
                    salvar_foto({"data":str(_data_insp), "sistema":f"Seccionadora — {_sec_sel}",
                                 "legenda":_leg_sec or _sec_sel,
                                 "foto_base64":foto_para_base64(_foto_sec.read()),
                                 "usuario":st.session_state.login})
                _txt = "🟢 BOA" if _n_nc==0 else "🟡 ATENÇÃO" if _n_nc<=2 else "🔴 CRÍTICA"
                st.success(f"✅ {_sec_sel} — {_txt} ({_n_ok}/{len(_ITENS_INSP)} OK)")
                _carregar_inspecoes_hoje.clear()
                _carregar_inspecoes.clear()
                st.rerun()

    # ── 4. INSPEÇÃO DO TRANSFORMADOR — largura total ─────────────────────────
    st.markdown("<div style='border-top:1px solid #1e3a5f;margin:14px 0'></div>", unsafe_allow_html=True)
    st.markdown("""<div style='color:#f59e0b;font-size:0.72rem;font-weight:700;
        text-transform:uppercase;letter-spacing:1px;margin-bottom:6px'>
        🔄 Inspeção do Transformador</div>""", unsafe_allow_html=True)

    _TRAFO_TAG  = "SE+01TRF"
    _TRAFO_NOME = "SE+01TRF — Trafo Trifásico 230/69kV 12,5 MVA"
    _t_amb_tr   = float(st.session_state.get("temp_amb_global", 28.0))
    _lim_oti    = _t_amb_tr + 65.0

    # Verifica se trafo foi inspecionado hoje
    _df_hoje_all  = _carregar_inspecoes_hoje(_data_insp)
    _df_trafo_hoje = _df_hoje_all[_df_hoje_all.sistema == "Transformador"] if not _df_hoje_all.empty else _df_hoje_all
    _trafo_insp = not _df_trafo_hoje.empty

    _tr_pct = 1.0 if _trafo_insp else 0.0
    _data_insp_str = _data_insp.strftime("%d/%m")
    st.progress(_tr_pct, text=f"1/1 transformador inspecionado em {_data_insp_str}" if _trafo_insp else f"0/1 transformador inspecionado em {_data_insp_str}")

    if _trafo_insp:
        st.success("✅ Transformador inspecionado hoje!")
    else:
        # ── Temperaturas ────────────────────────────────────────────────────
        st.markdown(f"<div style='color:#94a3b8;font-size:0.78rem;font-weight:600;margin:8px 0 4px'>🌡️ Temperaturas — TM1 Treetech (Limite: T_amb {_t_amb_tr:.0f}°C + 65°C = <b style=\"color:#ef4444\">{_lim_oti:.0f}°C</b>)</div>", unsafe_allow_html=True)
        _tr1, _tr2 = st.columns(2)
        _oti = _tr1.number_input("OTI — Temperatura do Óleo (°C)",        value=_t_amb_tr+20, min_value=0.0, max_value=200.0, step=0.5, format="%.1f", key="tr_oti")
        _wti = _tr2.number_input("WTI — Temperatura do Enrolamento (°C)",  value=_t_amb_tr+20, min_value=0.0, max_value=200.0, step=0.5, format="%.1f", key="tr_wti")

        def _tr_badge(v, lim):
            cor = "#ef4444" if v > lim else "#10b981"
            txt = "ALARME" if v > lim else "OK"
            return f"<span style='color:{cor};font-weight:700'>{v:.1f}°C {txt}</span>"

        st.markdown(f"<div style='font-size:0.8rem;margin:4px 0 8px'>{_tr_badge(_oti,_lim_oti)} &nbsp;|&nbsp; {_tr_badge(_wti,_lim_oti)}</div>", unsafe_allow_html=True)

        st.markdown("<div style='border-bottom:1px solid #1e3a5f;margin:8px 0'></div>", unsafe_allow_html=True)

        # Mapa de nomes dos campos para mensagem de erro específica
        _CAMPOS_NOMES = [
            "Nível óleo conservador (status)",
            "Nível óleo — Bucha AT",
            "Nível óleo — Bucha BT",
            "Ventiladores (resfriamento)",
            "Ruído/Vibração anormal",
            "Status AVR K60 (comutador)",
            "Vazamentos",
            "Sílica Gel",
            "Buchas AT/BT (visual)",
            "Caixa de controle",
        ]

        # ── FORMULÁRIO (sem reload a cada clique) ───────────────────────────
        with st.form("form_trafo", clear_on_submit=True):
            st.markdown("<div style='color:#94a3b8;font-size:0.78rem;font-weight:600;margin:4px 0'>💧 Nível de Óleo — Conservador do Transformador</div>", unsafe_allow_html=True)
            _no1, _no2 = st.columns([1, 2])
            _nivel_oleo  = _no1.number_input("Indicador (%)", min_value=0, max_value=100, value=60, step=1, key="tr_nivel_oleo")
            _status_oleo = _no2.radio("Status", ["Dentro da faixa","Baixo","Alto"], index=None, horizontal=True, key="tr_st_oleo")

            st.markdown("<div style='color:#94a3b8;font-size:0.78rem;font-weight:600;margin:8px 0 4px'>🔵 Nível de Óleo — Buchas (Isolamento a Óleo)</div>", unsafe_allow_html=True)
            _bch1, _bch2 = st.columns(2)
            _nivel_bucha_at = _bch1.radio("Bucha AT", ["Normal","Baixo","Crítico"], index=None, horizontal=True, key="tr_bch_at")
            _nivel_bucha_bt = _bch2.radio("Bucha BT", ["Normal","Baixo","Crítico"], index=None, horizontal=True, key="tr_bch_bt")

            st.markdown("<div style='border-bottom:1px solid #1e3a5f;margin:8px 0'></div>", unsafe_allow_html=True)
            st.markdown("<div style='color:#94a3b8;font-size:0.78rem;font-weight:600;margin:4px 0'>🌀 Sistema de Resfriamento (ONAN/ONAF)</div>", unsafe_allow_html=True)
            _rs1, _rs2 = st.columns(2)
            _ventiladores = _rs1.radio("Ventiladores", ["OK","FALHA","MANUAL"], index=None, horizontal=True, key="tr_vent")
            _vibracao     = _rs2.radio("Ruído/Vibração anormal", ["Não","Sim"], index=None, horizontal=True, key="tr_vib")

            st.markdown("<div style='border-bottom:1px solid #1e3a5f;margin:8px 0'></div>", unsafe_allow_html=True)
            st.markdown("<div style='color:#94a3b8;font-size:0.78rem;font-weight:600;margin:4px 0'>🔌 Comutador em Carga — OLTC / K60 Treetech AVR</div>", unsafe_allow_html=True)
            _ol1, _ol2 = st.columns([1, 2])
            _oltc_pos   = _ol1.text_input("Posição do tap (K60)", value="", placeholder="Ex: 9", key="tr_oltc_pos")
            _avr_status = _ol2.radio("Status AVR (K60)", ["Automático","Manual","Bloqueado"], index=None, horizontal=True, key="tr_avr_status")

            st.markdown("<div style='border-bottom:1px solid #1e3a5f;margin:8px 0'></div>", unsafe_allow_html=True)
            st.markdown("<div style='color:#94a3b8;font-size:0.78rem;font-weight:600;margin:4px 0'>🔍 Inspeção Visual</div>", unsafe_allow_html=True)
            _vi1, _vi2 = st.columns(2)
            _vazamento  = _vi1.radio("Vazamentos", ["Não","Sim"], index=None, horizontal=True, key="tr_vaz")
            _silica     = _vi2.radio("Silica Gel", ["Azul (OK)","Rosa (trocar)","Parcial"], index=None, horizontal=True, key="tr_silica")
            _vi3, _vi4 = st.columns(2)
            _buchas     = _vi3.radio("Buchas AT/BT", ["Limpas","Sujas","Rachaduras"], index=None, horizontal=True, key="tr_buchas")
            _caixa      = _vi4.radio("Caixa de controle", ["OK","Alarmes ativos"], index=None, horizontal=True, key="tr_caixa")

            st.markdown("<div style='border-bottom:1px solid #1e3a5f;margin:8px 0'></div>", unsafe_allow_html=True)
            _obs_tr = st.text_area("Observações", height=70, key="tr_obs",
                                   placeholder="Condições observadas, ocorrências, ações tomadas...")
            _salvar_tr = st.form_submit_button("💾 Salvar Inspeção do Transformador",
                                               type="primary", use_container_width=True)

        if _salvar_tr:
            import json as _json
            _tr_campos = [_status_oleo, _nivel_bucha_at, _nivel_bucha_bt,
                          _ventiladores, _vibracao, _avr_status,
                          _vazamento, _silica, _buchas, _caixa]
            _faltando = [_CAMPOS_NOMES[i] for i, v in enumerate(_tr_campos) if v is None]

            if _faltando:
                st.warning("⚠️ Preencha os campos obrigatórios antes de salvar:\n\n"
                           + "\n".join(f"• {f}" for f in _faltando))
            else:
                _hora_tr = datetime.now().time()
                _alertas_tr = []
                if _status_oleo != "Dentro da faixa":  _alertas_tr.append(f"Nível óleo: {_status_oleo}")
                if _nivel_bucha_at != "Normal":         _alertas_tr.append(f"Bucha AT: {_nivel_bucha_at}")
                if _nivel_bucha_bt != "Normal":         _alertas_tr.append(f"Bucha BT: {_nivel_bucha_bt}")
                if _ventiladores != "OK":               _alertas_tr.append(f"Ventiladores: {_ventiladores}")
                if _vibracao == "Sim":                  _alertas_tr.append("Vibração/ruído")
                if _avr_status != "Automático":         _alertas_tr.append(f"AVR K60: {_avr_status}")
                if _vazamento == "Sim":                 _alertas_tr.append("Vazamento")
                if _silica != "Azul (OK)":              _alertas_tr.append(f"Silica: {_silica}")
                if _buchas != "Limpas":                 _alertas_tr.append(f"Buchas: {_buchas}")
                if _caixa != "OK":                      _alertas_tr.append("Alarmes na caixa")
                if _oti > _lim_oti:                     _alertas_tr.append(f"OTI {_oti:.1f}°C acima limite")
                if _wti > _lim_oti:                     _alertas_tr.append(f"WTI {_wti:.1f}°C acima limite")

                if not _alertas_tr:   _tr_saude_txt = "NORMAL"
                elif len(_alertas_tr) <= 2: _tr_saude_txt = "ATENCAO"
                else:                 _tr_saude_txt = "CRITICO"

                for _ponto, _temp, _lim in [
                    ("OTI — Temperatura do Óleo",       _oti, _lim_oti),
                    ("WTI — Temperatura do Enrolamento", _wti, _lim_oti),
                ]:
                    salvar_temp({"data":str(_data_insp),"hora":str(_hora_tr),"turno":turno_dia,
                                 "equipamento":_TRAFO_NOME,"ponto":_ponto,
                                 "temperatura":_temp,"umidade":0.0,"limite_max":_lim,
                                 "status":"ALARME" if _temp > _lim else "NORMAL",
                                 "observacao":_obs_tr,"usuario":st.session_state.login})

                _insp_dados = {
                    "nivel_oleo_pct": _nivel_oleo, "status_oleo": _status_oleo,
                    "nivel_bucha_at": _nivel_bucha_at, "nivel_bucha_bt": _nivel_bucha_bt,
                    "ventiladores": _ventiladores, "vibracao": _vibracao,
                    "oltc_posicao": _oltc_pos, "avr_k60": _avr_status,
                    "vazamento": _vazamento, "silica_gel": _silica,
                    "buchas_externas": _buchas, "caixa_controle": _caixa,
                    "alertas": _alertas_tr
                }
                if _obs_tr: _insp_dados["observacao"] = _obs_tr
                salvar_inspecao({"data":str(_data_insp),"turno":turno_dia,
                                 "sistema":"Transformador","item":_TRAFO_TAG,
                                 "status":_tr_saude_txt,
                                 "observacao":_json.dumps(_insp_dados, ensure_ascii=False),
                                 "usuario":st.session_state.login})
                _emoji = "🟢" if _tr_saude_txt=="NORMAL" else "🟡" if _tr_saude_txt=="ATENCAO" else "🔴"
                st.success(f"✅ {_TRAFO_NOME} — {_emoji} {_tr_saude_txt}" +
                           (f" | ⚠️ {', '.join(_alertas_tr[:3])}" if _alertas_tr else ""))
                _carregar_inspecoes_hoje.clear()
                _carregar_temps.clear()
                st.rerun()

    # ── 5. PARA-RAIOS — largura total ────────────────────────────────────────
    st.markdown("<div style='border-top:1px solid #1e3a5f;margin:14px 0'></div>", unsafe_allow_html=True)
    st.markdown("""<div style='color:#f97316;font-size:0.72rem;font-weight:700;
        text-transform:uppercase;letter-spacing:1px;margin-bottom:6px'>
        ⚡ Inspeção de Para-raios — 230kV</div>""", unsafe_allow_html=True)

    _PR_TAG = "PARA-RAIOS-230kV"
    _df_pr_hoje = _df_hoje_all[_df_hoje_all.sistema == "Subestação 230kV"] if not _df_hoje_all.empty else _df_hoje_all
    _pr_insp = not _df_pr_hoje[_df_pr_hoje.item == _PR_TAG].empty if not _df_pr_hoje.empty else False
    st.progress(1.0 if _pr_insp else 0.0,
                text="Para-raios inspecionados" if _pr_insp else "Para-raios pendente")

    if _pr_insp:
        st.success("✅ Para-raios inspecionados!")
    else:
        with st.form("form_pr", clear_on_submit=True):
            st.markdown("<div style='color:#94a3b8;font-size:0.78rem;font-weight:600;margin:4px 0'>🔍 Inspeção Visual — Para-raios 230kV (por fase: A, B, C)</div>", unsafe_allow_html=True)
            _pr1, _pr2 = st.columns(2)
            _pr_cond   = _pr1.radio("Condição geral (sem trincas, sujidade ou marcas de descarga)",
                                    ["Normal","Anomalia"], index=None, horizontal=True, key="pr_cond")
            _pr_isol   = _pr2.radio("Isoladores — ausência de trincas e poluição",
                                    ["Normal","Anomalia"], index=None, horizontal=True, key="pr_isol")
            _pr3, _pr4 = st.columns(2)
            _pr_conex  = _pr3.radio("Conexões e aterramento firmes",
                                    ["Normal","Anomalia"], index=None, horizontal=True, key="pr_conex")
            _pr_sinal  = _pr4.radio("Identificação e sinalização",
                                    ["OK","NC"], index=None, horizontal=True, key="pr_sinal")
            _obs_pr    = st.text_input("Observações", key="obs_pr", placeholder="Condições observadas...")
            _salvar_pr = st.form_submit_button("💾 Registrar Para-raios",
                                               type="primary", use_container_width=True)

        if _salvar_pr:
            import json as _json
            _campos_pr = [_pr_cond, _pr_isol, _pr_conex, _pr_sinal]
            _falt_pr   = [n for v,n in zip(_campos_pr,["Condição geral","Isoladores","Conexões","Identificação"]) if v is None]
            if _falt_pr:
                st.warning("⚠️ Preencha: " + " · ".join(_falt_pr))
            else:
                _nc_pr = sum(1 for v in _campos_pr if v in ("Anomalia","NC"))
                _st_pr = "NC" if _nc_pr else "OK"
                _dados_pr = {"condicao":_pr_cond,"isoladores":_pr_isol,
                             "conexoes":_pr_conex,"identificacao":_pr_sinal}
                if _obs_pr: _dados_pr["observacao"] = _obs_pr
                salvar_inspecao({"data":str(_data_insp),"turno":turno_dia,
                                 "sistema":"Subestação 230kV","item":_PR_TAG,
                                 "status":_st_pr,
                                 "observacao":_json.dumps(_dados_pr, ensure_ascii=False),
                                 "usuario":st.session_state.login})
                _txt_pr = "🟢 NORMAL" if not _nc_pr else f"🔴 {_nc_pr} ANOMALIA(S)"
                st.success(f"✅ Para-raios — {_txt_pr}")
                _carregar_inspecoes_hoje.clear()
                st.rerun()

    # ── 6. SALA ELÉTRICA DA SE — largura total ───────────────────────────────
    st.markdown("<div style='border-top:1px solid #1e3a5f;margin:14px 0'></div>", unsafe_allow_html=True)
    st.markdown("""<div style='color:#8b5cf6;font-size:0.72rem;font-weight:700;
        text-transform:uppercase;letter-spacing:1px;margin-bottom:6px'>
        🏢 Inspeção — Sala Elétrica da SE</div>""", unsafe_allow_html=True)

    _SE_TAG = "SALA-ELETRICA-SE"
    _df_se_hoje = _df_hoje_all[_df_hoje_all.sistema == "Sala Elétrica da SE"] if not _df_hoje_all.empty else _df_hoje_all
    _se_insp = not _df_se_hoje[_df_se_hoje.item == _SE_TAG].empty if not _df_se_hoje.empty else False
    st.progress(1.0 if _se_insp else 0.0,
                text="Sala Elétrica inspecionada" if _se_insp else "Sala Elétrica pendente")

    if _se_insp:
        st.success("✅ Sala Elétrica inspecionada!")
    else:
        with st.form("form_se", clear_on_submit=True):
            _se_cols = st.columns(3)
            _se_temp = _se_cols[0].number_input("🌡️ Temperatura sala (°C)",
                                                min_value=0.0, max_value=60.0, value=float(t_amb),
                                                step=0.5, format="%.1f", key="se_temp")
            st.markdown("<div style='color:#94a3b8;font-size:0.78rem;font-weight:600;margin:6px 0 4px'>Verificações</div>", unsafe_allow_html=True)
            _a1, _a2 = st.columns(2)
            _se_ac    = _a1.radio("A/C e ventilação", ["OK","Falha","Desligado"],
                                  index=None, horizontal=True, key="se_ac")
            _se_alarm = _a2.radio("Ausência de alarmes nos painéis",
                                  ["Sem alarmes","Alarme ativo"], index=None, horizontal=True, key="se_alarm")
            _b1, _b2 = st.columns(2)
            _se_agua  = _b1.radio("Ausência de água / infiltração",
                                  ["Não","Sim"], index=None, horizontal=True, key="se_agua")
            _se_cond  = _b2.radio("Condição geral dos painéis e cabos",
                                  ["Normal","Anomalia"], index=None, horizontal=True, key="se_cond")
            _obs_se   = st.text_input("Observações", key="obs_se", placeholder="Temperatura, A/C, intercorrências...")
            _salvar_se = st.form_submit_button("💾 Registrar Sala Elétrica",
                                               type="primary", use_container_width=True)

        if _salvar_se:
            import json as _json
            _campos_se = [_se_ac, _se_alarm, _se_agua, _se_cond]
            _falt_se   = [n for v,n in zip(_campos_se,["A/C","Alarmes","Infiltração","Painéis"]) if v is None]
            if _falt_se:
                st.warning("⚠️ Preencha: " + " · ".join(_falt_se))
            else:
                _nc_se = sum(1 for v in [_se_alarm, _se_agua, _se_cond]
                             if v in ("Alarme ativo","Sim","Anomalia"))
                _nc_se += 1 if _se_ac in ("Falha","Desligado") else 0
                _nc_se += 1 if _se_temp > 35 else 0
                _st_se = "NC" if _nc_se else "OK"
                _dados_se = {"temperatura_sala": _se_temp, "ac_ventilacao": _se_ac,
                             "alarmes": _se_alarm, "infiltracao": _se_agua, "paineis": _se_cond}
                if _obs_se: _dados_se["observacao"] = _obs_se
                salvar_inspecao({"data":str(_data_insp),"turno":turno_dia,
                                 "sistema":"Sala Elétrica da SE","item":_SE_TAG,
                                 "status":_st_se,
                                 "observacao":_json.dumps(_dados_se, ensure_ascii=False),
                                 "usuario":st.session_state.login})
                _txt_se = "🟢 NORMAL" if not _nc_se else f"🟡 {_nc_se} ponto(s) de atenção"
                st.success(f"✅ Sala Elétrica — {_txt_se}")
                _carregar_inspecoes_hoje.clear()
                st.rerun()

    # ── 7. CÚBILO DE 13.8kV — largura total ──────────────────────────────────
    st.markdown("<div style='border-top:1px solid #1e3a5f;margin:14px 0'></div>", unsafe_allow_html=True)
    st.markdown("""<div style='color:#06b6d4;font-size:0.72rem;font-weight:700;
        text-transform:uppercase;letter-spacing:1px;margin-bottom:6px'>
        ⚡ Inspeção — Cúbilo de 13.8kV da SE</div>""", unsafe_allow_html=True)

    _CUB_TAG = "CUBILO-13.8kV-SE"
    _df_cub_hoje = _df_hoje_all[_df_hoje_all.sistema == "Cúbilo de 13.8kV da SE"] if not _df_hoje_all.empty else _df_hoje_all
    _cub_insp = not _df_cub_hoje[_df_cub_hoje.item == _CUB_TAG].empty if not _df_cub_hoje.empty else False
    st.progress(1.0 if _cub_insp else 0.0,
                text="Cúbilo inspecionado" if _cub_insp else "Cúbilo pendente")

    if _cub_insp:
        st.success("✅ Cúbilo de 13.8kV inspecionado!")
    else:
        with st.form("form_cub", clear_on_submit=True):
            st.markdown("<div style='color:#94a3b8;font-size:0.78rem;font-weight:600;margin:4px 0'>Verificações</div>", unsafe_allow_html=True)
            _c1, _c2 = st.columns(2)
            _cub_pos   = _c1.radio("Posição das chaves/disjuntores conforme esperado",
                                   ["Conforme","Divergência"], index=None, horizontal=True, key="cub_pos")
            _cub_alarm = _c2.radio("Ausência de alarmes",
                                   ["Sem alarmes","Alarme ativo"], index=None, horizontal=True, key="cub_alarm")
            _c3, _c4 = st.columns(2)
            _cub_ind   = _c3.radio("Indicadores de tensão presentes",
                                   ["Presentes","Ausentes"], index=None, horizontal=True, key="cub_ind")
            _cub_cond  = _c4.radio("Condição visual (buchas, barras, limpeza)",
                                   ["Normal","Anomalia"], index=None, horizontal=True, key="cub_cond")
            _obs_cub   = st.text_input("Observações", key="obs_cub",
                                       placeholder="Posição de chaves, alarmes, temperatura...")
            _salvar_cub = st.form_submit_button("💾 Registrar Cúbilo 13.8kV",
                                                type="primary", use_container_width=True)

        if _salvar_cub:
            import json as _json
            _campos_cub = [_cub_pos, _cub_alarm, _cub_ind, _cub_cond]
            _falt_cub   = [n for v,n in zip(_campos_cub,["Posição","Alarmes","Indicadores","Condição visual"]) if v is None]
            if _falt_cub:
                st.warning("⚠️ Preencha: " + " · ".join(_falt_cub))
            else:
                _nc_cub = sum(1 for v in _campos_cub
                              if v in ("Divergência","Alarme ativo","Ausentes","Anomalia"))
                _st_cub = "NC" if _nc_cub else "OK"
                _dados_cub = {"posicao_chaves": _cub_pos, "alarmes": _cub_alarm,
                              "indicadores_tensao": _cub_ind, "condicao_visual": _cub_cond}
                if _obs_cub: _dados_cub["observacao"] = _obs_cub
                salvar_inspecao({"data":str(_data_insp),"turno":turno_dia,
                                 "sistema":"Cúbilo de 13.8kV da SE","item":_CUB_TAG,
                                 "status":_st_cub,
                                 "observacao":_json.dumps(_dados_cub, ensure_ascii=False),
                                 "usuario":st.session_state.login})
                _txt_cub = "🟢 NORMAL" if not _nc_cub else f"🔴 {_nc_cub} ponto(s) de atenção"
                st.success(f"✅ Cúbilo 13.8kV — {_txt_cub}")
                _carregar_inspecoes_hoje.clear()
                st.rerun()

# ══════════════════════════════════════════════════════ CADASTRO EQUIPAMENTOS
elif "Cadastro" in pagina:
    st.markdown("## 🗂️ Cadastro de Equipamentos")

    TIPOS = ["Disjuntor SF6","Transformador de Potência","Transformador de Corrente (TC)",
             "Transformador de Potencial (TP)","Para-raios","Banco de Baterias",
             "Retificador / Carregador","Cubículo MT","Seccionadora","Reator","Outro"]
    SISTEMAS_EQ = ["Subestação 230kV","Sala Elétrica da SE","Cúbilo de 13.8kV da SE",
                   "Sistema de Baterias","Pátio de Manobras","Outro"]

    tab1, tab2, tab3 = st.tabs(["➕ Novo Equipamento", "📋 Lista / Editar", "📊 Resumo"])

    # ── Novo Equipamento ──────────────────────────────────────────────────
    with tab1:
        st.markdown("### Cadastrar Novo Equipamento")
        with st.form("form_equip", clear_on_submit=True):
            # Identificação
            st.markdown("#### 🏷️ Identificação")
            c1,c2,c3 = st.columns(3)
            tipo_eq  = c1.selectbox("Tipo de Equipamento", TIPOS)
            tag_eq   = c2.text_input("TAG / ID *", placeholder="Ex: DJ-01, TR-01, BAT-125-01")
            sis_eq   = c3.selectbox("Sistema", SISTEMAS_EQ)

            c4,c5 = st.columns(2)
            desc_eq = c4.text_input("Descrição", placeholder="Ex: Disjuntor Vão 01 - Barra 1")
            loc_eq  = c5.text_input("Localização", placeholder="Ex: Vão 01, Quadro QD-01")

            st.markdown("#### 🏭 Dados do Fabricante")
            c6,c7,c8,c9 = st.columns(4)
            fab_eq  = c6.text_input("Fabricante", placeholder="ABB, Siemens, WEG...")
            mod_eq  = c7.text_input("Modelo", placeholder="LTB 245E2")
            ano_eq  = c8.text_input("Ano Fabricação", placeholder="2015")
            ser_eq  = c9.text_input("Nº de Série", placeholder="SN-123456")

            st.markdown("#### ⚡ Dados Técnicos")
            c10,c11,c12 = st.columns(3)
            ten_eq  = c10.number_input("Tensão Nominal (kV)", value=0.0, step=0.1, format="%.1f")
            cor_eq  = c11.number_input("Corrente Nominal (A)", value=0.0, step=1.0, format="%.0f")
            pot_eq  = c12.number_input("Potência (MVA)", value=0.0, step=0.1, format="%.1f")

            # Campos específicos por tipo
            mostrar_sf6 = tipo_eq == "Disjuntor SF6"
            mostrar_temp = tipo_eq in ["Transformador de Potência","Banco de Baterias","Cubículo MT"]

            p_nom = p_alarm = p_bloq = 0.0
            t_max = 0.0

            if mostrar_sf6:
                st.markdown("#### 💨 Parâmetros SF6")
                cs1,cs2,cs3 = st.columns(3)
                p_nom   = cs1.number_input("Pressão Nominal (bar)", value=6.0, step=0.1, format="%.2f")
                p_alarm = cs2.number_input("Pressão de Alarme (bar)", value=5.5, step=0.1, format="%.2f")
                p_bloq  = cs3.number_input("Pressão de Bloqueio (bar)", value=5.0, step=0.1, format="%.2f")

            if mostrar_temp:
                st.markdown("#### 🌡️ Limites de Temperatura")
                t_max = st.number_input("Temperatura Máxima (°C)", value=85.0, step=1.0, format="%.0f")

            obs_eq = st.text_area("📝 Observações", height=70)

            submitted = st.form_submit_button("💾 Cadastrar Equipamento", type="primary", use_container_width=True)
            if submitted:
                if not tag_eq.strip():
                    st.error("⚠️ TAG é obrigatória!")
                else:
                    ok, msg = salvar_equipamento({
                        "tipo": tipo_eq, "tag": tag_eq.strip().upper(), "descricao": desc_eq,
                        "fabricante": fab_eq, "modelo": mod_eq, "ano_fabricacao": ano_eq,
                        "numero_serie": ser_eq, "tensao_nominal": ten_eq,
                        "corrente_nominal": cor_eq, "potencia_mva": pot_eq,
                        "pressao_nominal": p_nom, "pressao_alarme": p_alarm,
                        "pressao_bloqueio": p_bloq, "temp_max": t_max,
                        "localizacao": loc_eq, "sistema": sis_eq, "observacao": obs_eq
                    })
                    if ok:
                        st.success(f"✅ {msg}")
                    else:
                        st.error(f"❌ {msg}")

    # ── Lista / Editar ────────────────────────────────────────────────────
    with tab2:
        st.markdown("### Equipamentos Cadastrados")

        cf1,cf2,cf3 = st.columns(3)
        tipo_f = cf1.selectbox("Filtrar por Tipo", ["Todos"]+TIPOS, key="eq_tipo_f")
        sis_f  = cf2.selectbox("Filtrar por Sistema", ["Todos"]+SISTEMAS_EQ, key="eq_sis_f")
        apenas_ativos = cf3.checkbox("Apenas ativos", value=True)

        df_eq = carregar_equipamentos(tipo_f, sis_f, apenas_ativos)

        if df_eq.empty:
            st.info("Nenhum equipamento cadastrado. Use a aba **Novo Equipamento** para começar.")
        else:
            st.markdown(f"**{len(df_eq)} equipamento(s) encontrado(s)**")

            # Ícones por tipo
            icone_tipo = {
                "Disjuntor SF6": "⚡", "Transformador de Potência": "🔄",
                "Transformador de Corrente (TC)": "〰️", "Transformador de Potencial (TP)": "〰️",
                "Para-raios": "⛈️", "Banco de Baterias": "🔋",
                "Retificador / Carregador": "🔌", "Cubículo MT": "🗄️",
                "Seccionadora": "✂️", "Reator": "🌀", "Outro": "🔧"
            }

            for _, row in df_eq.iterrows():
                icone = icone_tipo.get(row.tipo, "🔧")
                ativo_badge = "<span style='background:#052e16;color:#34d399;border-radius:10px;padding:2px 10px;font-size:0.75rem;font-weight:700'>ATIVO</span>"

                with st.expander(f"{icone} **{row.tag}** — {row.descricao or row.tipo} | {row.sistema or ''} {ativo_badge}", expanded=False):
                    col_info, col_edit = st.columns([2,1])
                    with col_info:
                        st.markdown(f"""
                        <div class='card' style='padding:14px'>
                            <div style='display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:0.85rem'>
                                <div><span style='color:#475569'>Tipo:</span> <b style='color:#f1f5f9'>{row.tipo}</b></div>
                                <div><span style='color:#475569'>Sistema:</span> <b style='color:#f1f5f9'>{row.sistema or '—'}</b></div>
                                <div><span style='color:#475569'>Fabricante:</span> <b style='color:#f1f5f9'>{row.fabricante or '—'}</b></div>
                                <div><span style='color:#475569'>Modelo:</span> <b style='color:#f1f5f9'>{row.modelo or '—'}</b></div>
                                <div><span style='color:#475569'>Nº Série:</span> <b style='color:#f1f5f9'>{row.numero_serie or '—'}</b></div>
                                <div><span style='color:#475569'>Ano Fab.:</span> <b style='color:#f1f5f9'>{row.ano_fabricacao or '—'}</b></div>
                                <div><span style='color:#475569'>Tensão:</span> <b style='color:#f1f5f9'>{row.tensao_nominal or '—'} kV</b></div>
                                <div><span style='color:#475569'>Corrente:</span> <b style='color:#f1f5f9'>{row.corrente_nominal or '—'} A</b></div>
                                {f"<div><span style='color:#475569'>P. Nominal SF6:</span> <b style='color:#60a5fa'>{row.pressao_nominal} bar</b></div><div><span style='color:#475569'>P. Alarme:</span> <b style='color:#f59e0b'>{row.pressao_alarme} bar</b></div><div><span style='color:#475569'>P. Bloqueio:</span> <b style='color:#ef4444'>{row.pressao_bloqueio} bar</b></div>" if row.pressao_nominal else ""}
                                {f"<div><span style='color:#475569'>Temp. Máx.:</span> <b style='color:#f59e0b'>{row.temp_max}°C</b></div>" if row.temp_max else ""}
                                <div><span style='color:#475569'>Localização:</span> <b style='color:#f1f5f9'>{row.localizacao or '—'}</b></div>
                            </div>
                            {f"<div style='margin-top:8px;color:#64748b;font-size:0.8rem'>Obs: {row.observacao}</div>" if row.observacao else ""}
                        </div>
                        """, unsafe_allow_html=True)

                    with col_edit:
                        st.markdown("**Editar**")
                        nova_desc  = st.text_input("Descrição", value=row.descricao or "", key=f"ed_{row.id}")
                        novo_fab   = st.text_input("Fabricante", value=row.fabricante or "", key=f"ef_{row.id}")
                        novo_mod   = st.text_input("Modelo", value=row.modelo or "", key=f"em_{row.id}")
                        novo_loc   = st.text_input("Localização", value=row.localizacao or "", key=f"el_{row.id}")
                        nova_obs   = st.text_area("Obs.", value=row.observacao or "", key=f"eo_{row.id}", height=60)

                        if row.pressao_nominal:
                            nova_pn = st.number_input("P. Nominal (bar)", value=float(row.pressao_nominal or 6.0), step=0.1, format="%.2f", key=f"epn_{row.id}")
                            nova_pa = st.number_input("P. Alarme (bar)", value=float(row.pressao_alarme or 5.5), step=0.1, format="%.2f", key=f"epa_{row.id}")
                            nova_pb = st.number_input("P. Bloqueio (bar)", value=float(row.pressao_bloqueio or 5.0), step=0.1, format="%.2f", key=f"epb_{row.id}")
                        else:
                            nova_pn = nova_pa = nova_pb = 0.0

                        col_btn1, col_btn2 = st.columns(2)
                        if col_btn1.button("💾 Salvar", key=f"save_{row.id}", use_container_width=True):
                            atualizar_equipamento(row.id, {
                                "tipo": row.tipo, "tag": row.tag, "descricao": nova_desc,
                                "fabricante": novo_fab, "modelo": novo_mod,
                                "ano_fabricacao": row.ano_fabricacao, "numero_serie": row.numero_serie,
                                "tensao_nominal": row.tensao_nominal, "corrente_nominal": row.corrente_nominal,
                                "potencia_mva": row.potencia_mva,
                                "pressao_nominal": nova_pn, "pressao_alarme": nova_pa,
                                "pressao_bloqueio": nova_pb, "temp_max": row.temp_max,
                                "localizacao": novo_loc, "sistema": row.sistema, "observacao": nova_obs
                            })
                            st.success("✅ Atualizado!"); st.rerun()

                        if col_btn2.button("🗑️ Inativar", key=f"del_{row.id}", use_container_width=True):
                            desativar_equipamento(row.id)
                            st.warning("Equipamento inativado."); st.rerun()

            # Exportar
            st.divider()
            csv = df_eq.to_csv(index=False).encode("utf-8-sig")
            st.download_button("⬇️ Exportar Lista CSV", csv, "equipamentos.csv", "text/csv")

    # ── Resumo ────────────────────────────────────────────────────────────
    with tab3:
        st.markdown("### 📊 Resumo do Parque de Equipamentos")
        df_all = carregar_equipamentos(ativo_only=False)
        if df_all.empty:
            st.info("Nenhum equipamento cadastrado ainda.")
        else:
            df_ativos = df_all[df_all.ativo==1]
            c1,c2,c3 = st.columns(3)
            c1.metric("Total Cadastrados", len(df_all))
            c2.metric("Ativos", len(df_ativos))
            c3.metric("Tipos Diferentes", df_ativos["tipo"].nunique())

            col_a, col_b = st.columns(2)
            with col_a:
                g1 = df_ativos.groupby("tipo").size().reset_index(name="qtd").sort_values("qtd", ascending=True)
                fig1 = px.bar(g1, x="qtd", y="tipo", orientation="h",
                             title="Equipamentos por Tipo",
                             color="qtd", color_continuous_scale="Blues",
                             labels={"qtd":"Quantidade","tipo":"Tipo"})
                fig1.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0.1)",
                                  font_color="#94a3b8", height=350, showlegend=False)
                st.plotly_chart(fig1, use_container_width=True)

            with col_b:
                g2 = df_ativos.groupby("sistema").size().reset_index(name="qtd")
                fig2 = px.pie(g2, names="sistema", values="qtd",
                             title="Distribuição por Sistema",
                             color_discrete_sequence=px.colors.sequential.Blues_r,
                             hole=0.45)
                fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#94a3b8", height=350)
                st.plotly_chart(fig2, use_container_width=True)

# ═══════════════════════════════════════════════════════════════ SF6 ══════
elif "SF6" in pagina:
    st.markdown("## ⚡ Disjuntores SF6 — Histórico e Operações")
    st.markdown("""<div style='background:#0a1628;border:1px solid #1e3a5f;border-radius:8px;
        padding:10px 16px;margin-bottom:14px;color:#475569;font-size:0.82rem'>
        📌 Leituras SF6 são registradas no <b style='color:#60a5fa'>Painel Geral</b> durante a inspeção de campo.
        Esta página exibe o histórico e a evolução ao longo do tempo.
    </div>""", unsafe_allow_html=True)
    tab2, tab3, tab4 = st.tabs(["📈 Evolução / Histórico", "🔢 Contagem de Operações", "📟 Contadores"])

    with tab2:

        # Filtros
        df_dj_db2 = carregar_equipamentos("Disjuntor SF6")
        tags_hist = ["Todos"] + (df_dj_db2["tag"].tolist() if not df_dj_db2.empty else [])
        opcoes_hist = {"Todos": "Todos os Disjuntores"}
        if not df_dj_db2.empty:
            for _, r in df_dj_db2.iterrows():
                opcoes_hist[r.tag] = f"{r.tag}  ·  {r.modelo or '—'}  ·  {(r.descricao or '')[:40]}"

        cc1, cc2, cc3 = st.columns(3)
        dj_f  = cc1.selectbox("⚡ Disjuntor", options=tags_hist,
                              format_func=lambda t: opcoes_hist.get(t, t), key="dj_f")
        d_ini = cc2.date_input("De", value=date(2026, 6, 1), key="sf6_ini")
        d_fim = cc3.date_input("Até", value=date.today(), key="sf6_fim")

        df_ev = carregar_sf6(dj_f, d_ini, d_fim)
        if df_ev.empty:
            st.info("Sem dados no período. Registre leituras no Painel Geral.")
        else:
            df_ev["data_hora"] = pd.to_datetime(df_ev["data"] + " " + df_ev["hora"])

            # ── Gauges — status atual por polo ─────────────────────────────
            st.markdown("#### Status Atual (última leitura por polo)")
            df_last = df_ev.sort_values("data_hora").groupby(["disjuntor","polo"]).last().reset_index()
            if not df_last.empty:
                cols_g = st.columns(min(len(df_last), 6))
                for i, (_, row) in enumerate(df_last.iterrows()):
                    eq_g = buscar_equipamento_por_tag(row.disjuntor) or {}
                    p_nom_g  = float(eq_g.get("pressao_nominal",  6.0) or 6.0)
                    p_al_g   = float(eq_g.get("pressao_alarme",   5.5) or 5.5)
                    p_bloq_g = float(eq_g.get("pressao_bloqueio", 5.0) or 5.0)
                    fig_g = go.Figure(go.Indicator(
                        mode="gauge+number+delta",
                        value=row.pressao_corrigida,
                        delta={"reference": p_nom_g, "valueformat": ".3f"},
                        number={"suffix": " bar", "valueformat": ".3f"},
                        title={"text": f"{row.disjuntor}<br>{row.polo}", "font": {"size": 11, "color": "#94a3b8"}},
                        gauge={
                            "axis": {"range": [4.0, 7.0], "tickcolor": "#475569"},
                            "bar": {"color": "#3b82f6"},
                            "steps": [
                                {"range": [4.0, p_bloq_g], "color": "#450a0a"},
                                {"range": [p_bloq_g, p_al_g], "color": "#451a03"},
                                {"range": [p_al_g, p_nom_g + 0.5], "color": "#052e16"},
                            ],
                            "threshold": {"line": {"color": "#ef4444", "width": 3}, "value": p_al_g}
                        }
                    ))
                    fig_g.update_layout(height=200, paper_bgcolor="rgba(0,0,0,0)",
                                       font_color="#94a3b8", margin=dict(t=30, b=5, l=5, r=5))
                    cols_g[i % 6].plotly_chart(fig_g, use_container_width=True)

            # ── Gráfico de evolução ─────────────────────────────────────────
            st.markdown("#### 📈 Evolução da Pressão SF6 Corrigida a 20°C")
            fig_ev = go.Figure()
            _cores_ev = {"Polo A": "#3b82f6", "Polo B": "#10b981", "Polo V": "#f59e0b",
                         "Câmara Única": "#60a5fa"}
            _cores_dj = ["#3b82f6","#10b981","#f59e0b","#8b5cf6","#ef4444","#06b6d4","#f97316"]

            for _i, _dj in enumerate(df_ev["disjuntor"].unique()):
                for _polo in df_ev[df_ev.disjuntor == _dj]["polo"].unique():
                    _df_p = df_ev[(df_ev.disjuntor == _dj) & (df_ev.polo == _polo)].sort_values("data_hora")
                    if not _df_p.empty:
                        _cor = _cores_ev.get(_polo, _cores_dj[_i % len(_cores_dj)])
                        fig_ev.add_trace(go.Scatter(
                            x=_df_p.data_hora, y=_df_p.pressao_corrigida,
                            mode="lines+markers",
                            name=f"{_dj} · {_polo}",
                            line=dict(color=_cor, width=2),
                            marker=dict(size=6),
                            hovertemplate=f"<b>{_dj} · {_polo}</b><br>Data: %{{x}}<br>Pressão: %{{y:.3f}} bar<extra></extra>"
                        ))

            # Linhas de referência
            eq_ref = buscar_equipamento_por_tag(dj_f) if dj_f != "Todos" else None
            if eq_ref:
                _p_n = float(eq_ref.get("pressao_nominal", 6.0) or 6.0)
                _p_a = float(eq_ref.get("pressao_alarme",  5.5) or 5.5)
                _p_b = float(eq_ref.get("pressao_bloqueio",5.0) or 5.0)
                fig_ev.add_hline(y=_p_n, line_dash="dot",  line_color="#475569",
                                annotation_text=f"Nominal {_p_n} bar", annotation_font_size=10)
                fig_ev.add_hline(y=_p_a, line_dash="dash", line_color="#f59e0b",
                                annotation_text=f"Alarme {_p_a} bar",
                                annotation_font_color="#f59e0b", annotation_font_size=10)
                fig_ev.add_hline(y=_p_b, line_dash="dash", line_color="#ef4444",
                                annotation_text=f"Bloqueio {_p_b} bar",
                                annotation_font_color="#ef4444", annotation_font_size=10)

            fig_ev.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0.15)",
                font_color="#94a3b8", height=380,
                xaxis_title="Data / Hora", yaxis_title="Pressão (bar a 20°C)",
                legend=dict(bgcolor="rgba(0,0,0,0)", font_size=10,
                            orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1))
            st.plotly_chart(fig_ev, use_container_width=True)

            # ── Tabela histórica ────────────────────────────────────────────
            st.markdown("#### Histórico de Leituras")
            cols_show = ["data","hora","turno","disjuntor","polo",
                         "pressao_medida","temperatura","pressao_corrigida","status_sf6","observacao"]
            _df_show = df_ev[cols_show].sort_values(["data","hora"], ascending=False).reset_index(drop=True)

            def _cor_status(v):
                if v == "NORMAL":   return "color: #10b981; font-weight: bold"
                if v == "ALARME":   return "color: #f59e0b; font-weight: bold"
                return "color: #ef4444; font-weight: bold"

            st.dataframe(
                _df_show.style.map(_cor_status, subset=["status_sf6"]),
                use_container_width=True, hide_index=True
            )
            _csv = _df_show.to_csv(index=False).encode("utf-8-sig")
            st.download_button("⬇️ Exportar CSV", _csv, f"sf6_{dj_f}_{d_ini}_{d_fim}.csv", "text/csv")

    with tab3:
        st.markdown("### Registro de Operações — Disjuntores")
        with st.form("form_op", clear_on_submit=True):
            c1,c2,c3 = st.columns(3)
            data_op = c1.date_input("Data", value=date.today())
            dj_op   = c2.selectbox("Disjuntor", list(DISJUNTORES.keys()))
            tipo_op = c3.selectbox("Tipo", ["Abertura Normal","Fechamento Normal","Abertura por Falta","Fechamento Automático","Teste"])
            c4,c5   = st.columns(2)
            motivo  = c4.text_input("Motivo / Ocorrência")
            num_op  = c5.number_input("Contador total de operações", min_value=0, step=1)
            if st.form_submit_button("💾 Registrar Operação", type="primary", use_container_width=True):
                salvar_operacao({"data":str(data_op),"disjuntor":dj_op,"tipo_operacao":tipo_op,
                                "motivo":motivo,"num_operacoes_total":int(num_op),"usuario":st.session_state.login})
                _carregar_operacoes.clear()
                st.success("✅ Operação registrada!")

        df_op = _carregar_operacoes()
        if not df_op.empty:
            fig_op = px.bar(df_op.groupby("disjuntor").size().reset_index(name="total"),
                           x="disjuntor", y="total", title="Total de Operações Registradas por Disjuntor",
                           color="total", color_continuous_scale="Blues")
            fig_op.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0.15)",
                                font_color="#94a3b8", height=280)
            st.plotly_chart(fig_op, use_container_width=True)
            st.dataframe(df_op[["data","disjuntor","tipo_operacao","motivo","num_operacoes_total","usuario"]],
                        use_container_width=True, hide_index=True)

    with tab4:
        st.markdown("### 📟 Contadores de Operações — Disjuntores 3 Polos")
        st.markdown("""<div style='background:#0a1628;border:1px solid #1e3a5f;border-radius:8px;
            padding:10px 16px;margin-bottom:14px;color:#475569;font-size:0.82rem'>
            📌 Registre aqui as leituras dos contadores físicos (P1LA, P1LB, P1LV, P1LT, P2).<br>
            Os contadores também podem ser registrados durante a inspeção SF6 no <b style='color:#60a5fa'>Painel Geral</b>.
        </div>""", unsafe_allow_html=True)

        df_dj_cnt = carregar_equipamentos("Disjuntor SF6")
        _tags_3p = [r.tag for _,r in df_dj_cnt.iterrows() if int(r.get("num_polos",1) or 1)==3] if not df_dj_cnt.empty else []
        _tags_cnt_all = df_dj_cnt["tag"].tolist() if not df_dj_cnt.empty else []

        _cnt_col1, _cnt_col2 = st.columns([2,1])
        dj_cnt = _cnt_col1.selectbox("⚡ Disjuntor", _tags_cnt_all, key="dj_cnt_sel")
        d_cnt  = _cnt_col2.date_input("📅 Data", value=date.today(), key="d_cnt")

        # Última leitura
        df_cnt_hist = _carregar_contadores(dj_cnt)
        if not df_cnt_hist.empty:
            _ult = df_cnt_hist.iloc[0]
            _is3p = dj_cnt in _tags_3p
            st.markdown(f"<div style='color:#94a3b8;font-size:0.78rem;margin:4px 0'>Última leitura registrada: <b style='color:#60a5fa'>{_ult.data}</b></div>", unsafe_allow_html=True)
            _kpis_cnt = []
            if _is3p:
                _kpis_cnt += [("P1LA\nPolo A", _ult.polo_a, "#3b82f6"),
                               ("P1LB\nPolo B", _ult.polo_b, "#10b981"),
                               ("P1LV\nPolo V", _ult.polo_v, "#f59e0b")]
            _kpis_cnt += [("P1LT\nTripolar", _ult.tripolar, "#8b5cf6"),
                           ("P2\nCurto Circ.", _ult.curto_circuito, "#ef4444")]
            _cnt_kpi_html = "".join([f"""<div style='background:#0f1e3a;border:1px solid #1e3a5f;
                border-top:3px solid {c};border-radius:10px;padding:10px;text-align:center'>
                <div style='font-size:1.5rem;font-weight:900;color:{c}'>{v}</div>
                <div style='font-size:0.65rem;color:#64748b;white-space:pre-line'>{l}</div></div>"""
                for l,v,c in _kpis_cnt])
            st.markdown(f"<div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(90px,1fr));gap:8px;margin:8px 0'>{_cnt_kpi_html}</div>", unsafe_allow_html=True)

        # Formulário de registro
        st.markdown("#### Registrar Leitura dos Contadores")
        _is3p_form = dj_cnt in _tags_3p
        with st.form("form_contadores", clear_on_submit=True):
            _fc1, _fc2 = st.columns(2)
            _f_trip = _fc1.number_input("P1LT — Tripolar",      min_value=0, value=0, step=1, key="f_trip")
            _f_cc   = _fc2.number_input("P2 — Curto Circuito",  min_value=0, value=0, step=1, key="f_cc")
            if _is3p_form:
                _fa, _fb, _fv = st.columns(3)
                _f_a = _fa.number_input("P1LA — Polo A", min_value=0, value=0, step=1, key="f_a")
                _f_b = _fb.number_input("P1LB — Polo B", min_value=0, value=0, step=1, key="f_b")
                _f_v = _fv.number_input("P1LV — Polo V", min_value=0, value=0, step=1, key="f_v")
            else:
                _f_a = _f_b = _f_v = 0
            turno_cnt = st.selectbox("Turno", ["Manhã (06-14h)","Tarde (14-22h)","Noite (22-06h)"],
                                     index=["Manhã (06-14h)","Tarde (14-22h)","Noite (22-06h)"].index(
                                         st.session_state.get("turno_global","Manhã (06-14h)")), key="tc")
            _salvar_cnt = st.form_submit_button("💾 Registrar Contadores", type="primary", use_container_width=True)

        if _salvar_cnt:
            salvar_contador({"data":str(d_cnt),"hora":str(datetime.now().time()),"turno":turno_cnt,
                             "disjuntor":dj_cnt,
                             "polo_a":int(_f_a),"polo_b":int(_f_b),"polo_v":int(_f_v),
                             "tripolar":int(_f_trip),"curto_circuito":int(_f_cc),
                             "usuario":st.session_state.login})
            _carregar_contadores.clear()
            st.success(f"✅ Contadores de {dj_cnt} registrados em {d_cnt.strftime('%d/%m/%Y')}")
            st.rerun()

        # Histórico
        if not df_cnt_hist.empty:
            st.markdown("#### Histórico de Contadores")
            _cols_cnt = ["data","turno","disjuntor","polo_a","polo_b","polo_v","tripolar","curto_circuito","usuario"]
            _df_cnt_show = df_cnt_hist[_cols_cnt].rename(columns={
                "polo_a":"P1LA","polo_b":"P1LB","polo_v":"P1LV","tripolar":"P1LT","curto_circuito":"P2"
            })
            st.dataframe(_df_cnt_show, use_container_width=True, hide_index=True)
            _csv_cnt = _df_cnt_show.to_csv(index=False).encode("utf-8-sig")
            st.download_button("⬇️ Exportar CSV", _csv_cnt,
                               f"contadores_{dj_cnt}.csv", "text/csv")

# ═══════════════════════════════════════════════════════════════ TEMP ═════
elif "Temperatura" in pagina:
    st.markdown("## 🌡️ Transformador — Temperatura OTI / WTI")
    st.markdown("""<div style='background:#0a1628;border:1px solid #1e3a5f;border-radius:8px;
        padding:10px 16px;margin-bottom:14px;color:#475569;font-size:0.82rem'>
        📌 Registre aqui as leituras de <b style='color:#60a5fa'>OTI (óleo)</b> e
        <b style='color:#60a5fa'>WTI (enrolamentos)</b> do transformador.<br>
        A temperatura ambiente é herdada do <b style='color:#60a5fa'>Painel Geral</b> —
        limite OTI = T_amb + 65°C conforme placa.
    </div>""", unsafe_allow_html=True)

    _t_amb_tr = float(st.session_state.get("temp_amb_global", 28.0))
    _limite_oti = _t_amb_tr + 65.0
    _limite_wti = _t_amb_tr + 65.0

    tab1, tab2 = st.tabs(["📥 Registrar Leitura", "📈 Histórico / Tendência"])

    PONTOS_TR = [
        {"ponto": "OTI — Temperatura do Óleo",        "limite": _limite_oti},
        {"ponto": "WTI — Temperatura do Enrolamento",  "limite": _limite_wti},
    ]
    EQUIP_TR = "SE+01TRF — Trafo Trifásico 230/69kV 12,5 MVA"

    with tab1:
        # Mostrar T ambiente herdada
        st.markdown(f"""<div style='background:#0f172a;border:1px solid #1e3a5f;border-radius:8px;
            padding:10px 16px;margin-bottom:12px;display:flex;gap:32px;align-items:center'>
            <div style='text-align:center'>
                <div style='font-size:1.4rem;font-weight:900;color:#f59e0b'>{_t_amb_tr:.1f}°C</div>
                <div style='font-size:0.65rem;color:#475569'>T. Ambiente (Painel Geral)</div>
            </div>
            <div style='text-align:center'>
                <div style='font-size:1.4rem;font-weight:900;color:#ef4444'>{_limite_oti:.0f}°C</div>
                <div style='font-size:0.65rem;color:#475569'>Limite OTI/WTI (T_amb + 65°C)</div>
            </div>
            <div style='color:#334155;font-size:0.78rem'>
                Atualize a temperatura ambiente no Painel Geral<br>para recalcular os limites automaticamente.
            </div>
        </div>""", unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        data_t  = c1.date_input("📅 Data", value=date.today(), key="data_tr")
        hora_t  = c2.time_input("🕐 Hora", value=datetime.now().time(), key="hora_tr")
        turno_t = c3.selectbox("Turno", ["Manhã (06-14h)","Tarde (14-22h)","Noite (22-06h)"],
                               index=["Manhã (06-14h)","Tarde (14-22h)","Noite (22-06h)"].index(
                                   st.session_state.get("turno_global","Manhã (06-14h)")),
                               key="turno_tr")

        st.markdown("<div style='border-bottom:1px solid #1e3a5f;margin:10px 0'></div>", unsafe_allow_html=True)

        _leituras_tr = {}
        hc1, hc2, hc3 = st.columns([3, 1.5, 2])
        hc1.markdown("<div style='color:#475569;font-size:0.72rem;font-weight:700;text-transform:uppercase'>Ponto de Medição</div>", unsafe_allow_html=True)
        hc2.markdown("<div style='color:#475569;font-size:0.72rem;font-weight:700;text-transform:uppercase'>Leitura (°C)</div>", unsafe_allow_html=True)
        hc3.markdown("<div style='color:#475569;font-size:0.72rem;font-weight:700;text-transform:uppercase'>Status</div>", unsafe_allow_html=True)

        for _p in PONTOS_TR:
            _c1, _c2, _c3 = st.columns([3, 1.5, 2])
            _c1.markdown(f"<div style='padding:8px 0;color:#94a3b8'>🌡️ {_p['ponto']}</div>", unsafe_allow_html=True)
            _tv = _c2.number_input("°C", key=f"tr_{_p['ponto']}", value=float(_t_amb_tr + 20),
                                   min_value=0.0, max_value=200.0, step=0.5, format="%.1f",
                                   label_visibility="collapsed")
            _st = "ALARME" if _tv > _p["limite"] else "NORMAL"
            _cor = "#ef4444" if _st == "ALARME" else "#10b981"
            _c3.markdown(f"""<div style='padding:8px 0'>
                <span style='color:{_cor};font-weight:700'>{_st}</span>
                <span style='color:#334155;font-size:0.75rem'> (lim: {_p['limite']:.0f}°C)</span>
            </div>""", unsafe_allow_html=True)
            _leituras_tr[_p["ponto"]] = {"val": _tv, "limite": _p["limite"], "status": _st}

        _obs_tr = st.text_area("Observação", height=60, key="obs_tr",
                               placeholder="Condições observadas, nível de óleo, alarmes ativos...")

        if st.button("💾 Salvar Leituras do Transformador", type="primary", use_container_width=True, key="save_tr"):
            for _ponto, _d in _leituras_tr.items():
                salvar_temp({"data": str(data_t), "hora": str(hora_t), "turno": turno_t,
                             "equipamento": EQUIP_TR, "ponto": _ponto,
                             "temperatura": _d["val"], "umidade": 0.0,
                             "limite_max": _d["limite"], "status": _d["status"],
                             "observacao": _obs_tr, "usuario": st.session_state.login})
            _carregar_temps.clear()
            st.success("✅ OTI e WTI salvos!")

    with tab2:
        _c1, _c2 = st.columns(2)
        _di = _c1.date_input("De", value=date(2026, 6, 1), key="tr_ini")
        _df2 = _c2.date_input("Até", value=date.today(), key="tr_fim")
        _df_t = _carregar_temps(EQUIP_TR, _di, _df2)
        if _df_t.empty:
            st.info("Sem registros. Use a aba Registrar Leitura para começar.")
        else:
            _df_t["data_hora"] = pd.to_datetime(_df_t["data"] + " " + _df_t["hora"])
            _fig_t = px.line(_df_t, x="data_hora", y="temperatura", color="ponto",
                            title="Evolução OTI / WTI — SE+01TRF 230/69kV",
                            labels={"temperatura": "Temp (°C)", "data_hora": "Data/Hora", "ponto": "Ponto"})
            _fig_t.add_hline(y=_limite_oti, line_dash="dash", line_color="#ef4444",
                            annotation_text=f"Limite {_limite_oti:.0f}°C",
                            annotation_font_color="#ef4444", annotation_font_size=10)
            _fig_t.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0.15)",
                                font_color="#94a3b8", height=380,
                                legend=dict(bgcolor="rgba(0,0,0,0)", font_size=10))
            st.plotly_chart(_fig_t, use_container_width=True)

            def _cor_st(v):
                return "color:#ef4444;font-weight:bold" if v == "ALARME" else "color:#10b981;font-weight:bold"
            _df_t_show = _df_t[["data","hora","turno","ponto","temperatura","limite_max","status"]
                               ].sort_values(["data","hora"], ascending=False).reset_index(drop=True)
            st.dataframe(
                _df_t_show.style.map(_cor_st, subset=["status"]),
                use_container_width=True, hide_index=True
            )
            _csv_t = _df_t_show.to_csv(index=False).encode("utf-8-sig")
            st.download_button("⬇️ Exportar CSV", _csv_t,
                               f"temperaturas_{_di}_{_df2}.csv", "text/csv")

# ══════════════════════════════════════════════════════════ CALCULADORA ════
elif "Calculadora" in pagina:
    st.markdown("## 🧮 Calculadora Técnica — INTEC")
    tab1, tab2, tab3, tab4 = st.tabs(["⚡ SF6 — Correção Temp.", "📐 Índice de Polarização", "🔧 Correção Resist. Enrolamento", "🌡️ Correção Temp. Transformador"])

    with tab1:
        st.markdown("### Correção de Pressão SF6 para 20°C")
        st.markdown("""<div class='card card-blue'>
            <b style='color:#60a5fa'>Fórmula (Lei dos Gases — INTEC):</b><br>
            <code style='color:#a5f3fc;font-size:1rem'>P₂₀ = P_med × (293,15 / (T_med + 273,15))</code><br>
            <small style='color:#334155'>Onde: P₂₀ = pressão corrigida a 20°C | P_med = pressão medida em campo | T_med = temperatura ambiente (°C)</small>
        </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        c1,c2 = st.columns(2)
        p_input = c1.number_input("📊 Pressão medida em campo (bar)", value=5.80, step=0.01, format="%.3f")
        t_input = c2.number_input("🌡️ Temperatura ambiente (°C)", value=32.0, step=0.5, format="%.1f")

        p_corr = corrigir_pressao_sf6(p_input, t_input)
        delta  = p_corr - 6.0

        st.markdown("<br>", unsafe_allow_html=True)
        r1,r2,r3 = st.columns(3)
        r1.metric("Pressão Medida", f"{p_input:.3f} bar")
        r2.metric("Temperatura", f"{t_input:.1f} °C")
        r3.metric("✅ Pressão a 20°C", f"{p_corr:.3f} bar", delta=f"{delta:+.3f} bar")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### Verificar contra disjuntor específico")
        dj_calc = st.selectbox("Selecione o disjuntor", list(DISJUNTORES.keys()))
        info_c  = DISJUNTORES[dj_calc]
        s_c     = status_sf6(p_corr, dj_calc)
        badge_c = {"NORMAL":"badge-ok","ALARME":"badge-alarm","BLOQUEIO":"badge-bloq"}.get(s_c["status"],"badge-crit")

        st.markdown(f"""<div class='card {"card-green" if s_c["status"]=="NORMAL" else "card-red" if s_c["status"]=="BLOQUEIO" else "card-yellow"}'>
            <div style='font-size:1.1rem;font-weight:700;color:#f1f5f9'>{s_c["icone"]} Resultado: <span class='{badge_c}'>{s_c["status"]}</span></div>
            <br>
            <div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;color:#94a3b8;font-size:0.85rem'>
                <div>P. Nominal: <b style='color:#f1f5f9'>{info_c["pressao_nominal"]} bar</b></div>
                <div>P. Alarme: <b style='color:#f59e0b'>{info_c["pressao_alarme"]} bar</b></div>
                <div>P. Bloqueio: <b style='color:#ef4444'>{info_c["pressao_bloqueio"]} bar</b></div>
            </div>
        </div>""", unsafe_allow_html=True)

        # Tabela de conversão
        st.markdown("#### 📋 Tabela de Correção SF6 (múltiplas temperaturas)")
        temps_ref = list(range(0, 55, 5))
        rows = [{"Temp (°C)": t, "P medida (bar)": p_input, "P corrigida a 20°C (bar)": round(corrigir_pressao_sf6(p_input, t), 3)} for t in temps_ref]
        df_tab = pd.DataFrame(rows)
        st.dataframe(df_tab, use_container_width=True, hide_index=True)

    with tab2:
        st.markdown("### Índice de Polarização (IP) — Resistência de Isolamento")
        st.markdown("""<div class='card card-blue'>
            <b style='color:#60a5fa'>Fórmula (INTEC / NBR 5356):</b><br>
            <code style='color:#a5f3fc;font-size:1rem'>IP = R₁₀ / R₁</code><br>
            <small style='color:#334155'>R₁₀ = Resistência de isolamento aos 10 minutos | R₁ = Resistência de isolamento ao 1 minuto</small>
        </div>""", unsafe_allow_html=True)

        c1,c2 = st.columns(2)
        r1_ip  = c1.number_input("R₁ — Resistência a 1 min (MΩ)", value=1000.0, step=10.0)
        r10_ip = c2.number_input("R₁₀ — Resistência a 10 min (MΩ)", value=1800.0, step=10.0)

        ip = r10_ip / r1_ip if r1_ip > 0 else 0

        if ip >= 2.0:   status_ip = ("EXCELENTE","#10b981"); avaliacao = "Isolamento em ótimas condições"
        elif ip >= 1.5: status_ip = ("BOM","#22c55e");       avaliacao = "Isolamento em boas condições"
        elif ip >= 1.3: status_ip = ("ACEITÁVEL","#f59e0b"); avaliacao = "Isolamento aceitável — Monitorar"
        elif ip >= 1.1: status_ip = ("QUESTIONÁVEL","#f97316"); avaliacao = "Investigar — possível contaminação"
        else:           status_ip = ("RUIM","#ef4444");       avaliacao = "AÇÃO IMEDIATA — Isolamento comprometido"

        st.markdown("<br>", unsafe_allow_html=True)
        st.metric("Índice de Polarização (IP)", f"{ip:.2f}", delta=status_ip[0])
        st.markdown(f"""<div class='card' style='border-left:4px solid {status_ip[1]}'>
            <span style='color:{status_ip[1]};font-size:1.1rem;font-weight:700'>{status_ip[0]}</span><br>
            <span style='color:#94a3b8'>{avaliacao}</span>
        </div>""", unsafe_allow_html=True)

        st.markdown("""
        | IP | Classificação INTEC |
        |---|---|
        | < 1.1 | 🔴 Ruim — Ação imediata |
        | 1.1 – 1.3 | 🟠 Questionável |
        | 1.3 – 1.5 | 🟡 Aceitável |
        | 1.5 – 2.0 | 🟢 Bom |
        | > 2.0 | 🟦 Excelente |
        """)

    with tab3:
        st.markdown("### Correção de Resistência de Enrolamento por Temperatura")
        st.markdown("""<div class='card card-blue'>
            <b style='color:#60a5fa'>Fórmula (INTEC / IEC 60076):</b><br>
            <code style='color:#a5f3fc;font-size:1rem'>R₇₅ = R_med × (235 + 75) / (235 + T_med)</code><br>
            <small style='color:#334155'>Para condutores de cobre. Corrige a resistência medida para 75°C de referência.</small>
        </div>""", unsafe_allow_html=True)

        c1,c2,c3 = st.columns(3)
        r_med  = c1.number_input("Resistência medida (mΩ)", value=150.0, step=0.1, format="%.3f")
        t_med2 = c2.number_input("Temperatura de medição (°C)", value=28.0, step=0.5, format="%.1f")
        mat    = c3.selectbox("Material do condutor", ["Cobre (k=235)","Alumínio (k=225)"])
        k = 235 if "Cobre" in mat else 225
        r_75 = r_med * (k + 75) / (k + t_med2)

        st.markdown("<br>", unsafe_allow_html=True)
        c1,c2,c3 = st.columns(3)
        c1.metric("R medida", f"{r_med:.3f} mΩ")
        c2.metric("Temperatura", f"{t_med2:.1f} °C")
        c3.metric("✅ R corrigida a 75°C", f"{r_75:.3f} mΩ")

    with tab4:
        st.markdown("### 🌡️ Correção de Temperatura — SE+01TRF 230/69kV 12,5 MVA")

        # ── Bloco 1: Limite de alarme real pela temperatura ambiente ──────
        st.markdown("""<div class='card card-blue'>
            <b style='color:#60a5fa'>Limite Real de Alarme = Temperatura Ambiente + Elevação de Temperatura (placa)</b><br>
            <code style='color:#a5f3fc'>T_alarme = T_amb + ΔT_placa</code><br>
            <small style='color:#334155'>SE+01TRF 230/69kV 12,5 MVA · Patrimônio 10004079 · ΔT Óleo = 65°C | ΔT Enrolamento = 65°C (NBR 5356/2007)</small>
        </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        t_amb_tr = st.number_input("🌡️ Temperatura Ambiente atual (°C)",
                                    value=st.session_state.get("temp_amb_global", 30.0),
                                    min_value=0.0, max_value=50.0, step=0.5, format="%.1f",
                                    key="t_amb_tr4")
        delta_oleo  = 65.0   # conforme placa
        delta_enrol = 65.0   # conforme placa

        t_max_oleo  = t_amb_tr + delta_oleo
        t_max_enrol = t_amb_tr + delta_enrol
        t_alarm_oleo  = t_amb_tr + delta_oleo - 5    # alarme 5°C abaixo do máx
        t_alarm_enrol = t_amb_tr + delta_enrol - 5

        c1,c2,c3,c4 = st.columns(4)
        c1.metric("T. Ambiente",   f"{t_amb_tr:.1f} °C")
        c2.metric("Máx. Óleo (OTI)",      f"{t_max_oleo:.1f} °C",    delta=f"Alarme: {t_alarm_oleo:.0f}°C")
        c3.metric("Máx. Enrol. AT (WTI)", f"{t_max_enrol:.1f} °C",   delta=f"Alarme: {t_alarm_enrol:.0f}°C")
        c4.metric("Limite Absoluto (NBR)", "105 °C",                   delta="Amb. 40°C + 65°C")

        st.markdown(f"""<div class='card {"card-yellow" if t_amb_tr>35 else "card-green"}' style='margin-top:12px'>
            <b style='color:#f1f5f9'>Resumo para T. Ambiente = {t_amb_tr:.1f}°C</b><br>
            <div style='display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:10px;font-size:0.88rem'>
                <div>🛢️ <b style='color:#f1f5f9'>Óleo (OTI)</b><br>
                    Alarme: <b style='color:#f59e0b'>{t_alarm_oleo:.0f}°C</b> |
                    Trip: <b style='color:#ef4444'>{t_max_oleo:.0f}°C</b>
                </div>
                <div>⚡ <b style='color:#f1f5f9'>Enrolamento AT/BT (WTI)</b><br>
                    Alarme: <b style='color:#f59e0b'>{t_alarm_enrol:.0f}°C</b> |
                    Trip: <b style='color:#ef4444'>{t_max_enrol:.0f}°C</b>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

        st.divider()

        # ── Bloco 2: Verificação de uma leitura OTI/WTI ──────────────────
        st.markdown("#### Verificar Leitura Atual OTI / WTI")
        cv1,cv2,cv3 = st.columns(3)
        tipo_med = cv1.selectbox("Medição", ["OTI — Temperatura do Óleo","WTI — Enrolamento AT","WTI — Enrolamento BT"])
        t_lida   = cv2.number_input("Temperatura lida (°C)", value=55.0, step=0.5, format="%.1f", key="t_lida_tr")
        elevacao_lida = t_lida - t_amb_tr

        limite_rel = t_max_oleo if "OTI" in tipo_med else t_max_enrol
        alarm_rel  = limite_rel - 5
        margem     = limite_rel - t_lida

        if t_lida >= limite_rel:    s_tr = ("TRIP / CRÍTICO","#ef4444")
        elif t_lida >= alarm_rel:   s_tr = ("ALARME","#f59e0b")
        elif t_lida >= alarm_rel-10: s_tr = ("ATENÇÃO","#f97316")
        else:                        s_tr = ("NORMAL","#10b981")

        cv3.markdown(f"""<div style='background:#0a1628;border:2px solid {s_tr[1]};border-radius:10px;
            padding:10px;text-align:center;margin-top:2px'>
            <div style='font-size:1.5rem;font-weight:900;color:{s_tr[1]}'>{t_lida:.1f}°C</div>
            <div style='font-size:0.72rem;color:#475569'>{s_tr[0]}</div>
        </div>""", unsafe_allow_html=True)

        st.markdown(f"""<div style='background:#0a1628;border:1px solid #1e3a5f;border-radius:10px;
            padding:14px 20px;margin-top:10px;display:flex;gap:32px;font-size:0.88rem'>
            <div>Elevação medida: <b style='color:#f1f5f9'>{elevacao_lida:.1f}°C</b>
            <span style='color:#475569'> (máx. placa: 65°C)</span></div>
            <div>Margem até alarme: <b style='color:{"#ef4444" if margem<5 else "#f59e0b" if margem<15 else "#10b981"}'>{margem:.1f}°C</b></div>
            <div>Status: <b style='color:{s_tr[1]}'>{s_tr[0]}</b></div>
        </div>""", unsafe_allow_html=True)

        st.divider()

        # ── Bloco 3: Correção de Resistência de Isolamento por Temperatura ─
        st.markdown("#### Correção de Resistência de Isolamento para 20°C (ABNT/IEC 60076)")
        st.markdown("""<div class='card card-blue'>
            <b style='color:#60a5fa'>Fórmula INTEC:</b>
            <code style='color:#a5f3fc;margin-left:8px'>R₂₀ = Rₜ × Kₜ</code>
            &nbsp;onde&nbsp;
            <code style='color:#a5f3fc'>Kₜ = 2^((T - 20) / 10)</code><br>
            <small style='color:#334155'>A resistência de isolamento dobra a cada 10°C de redução de temperatura.</small>
        </div>""", unsafe_allow_html=True)

        cr1,cr2 = st.columns(2)
        r_med_iso = cr1.number_input("Resistência medida (MΩ)", value=5000.0, step=10.0, format="%.1f", key="r_iso_tr")
        t_med_iso = cr2.number_input("Temperatura na medição (°C)", value=t_amb_tr, step=0.5, format="%.1f", key="t_iso_tr")

        kt    = 2 ** ((t_med_iso - 20) / 10)
        r_20  = r_med_iso * kt

        ci1,ci2,ci3 = st.columns(3)
        ci1.metric("R medida", f"{r_med_iso:,.0f} MΩ", delta=f"a {t_med_iso:.1f}°C")
        ci2.metric("Fator Kₜ", f"{kt:.3f}", delta=f"T_med={t_med_iso:.1f}°C")
        ci3.metric("✅ R corrigida a 20°C", f"{r_20:,.0f} MΩ")

        # Tabela de Kₜ por temperatura
        st.markdown("#### Tabela de Fatores de Correção Kₜ")
        tbl_kt = [{"T (°C)": t, "Kₜ": round(2**((t-20)/10), 4),
                   "R corrigida (MΩ)": round(r_med_iso * 2**((t-20)/10), 1)}
                  for t in range(10, 55, 5)]
        st.dataframe(pd.DataFrame(tbl_kt), use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════ INSPEÇÃO ═
elif "Inspeção" in pagina:
    st.markdown("## 📋 Inspeções — Programação e Registro")

    # Mapeamento: cada sistema inclui inspeções do Painel Geral
    _SIS_MAP = {
        "Subestação 230kV":     ["Subestação 230kV", "Disjuntor SF6", "Seccionadora", "PARA-RAIOS-230kV"],
        "Sala Elétrica da SE":  ["Sala Elétrica da SE", "SALA-ELETRICA-SE"],
        "Cúbilo de 13.8kV da SE": ["Cúbilo de 13.8kV da SE", "CUBILO-13.8kV-SE"],
        "Transformador TR-SE-01 (Toshiba 10/12.5 MVA)": ["Transformador TR-SE-01 (Toshiba 10/12.5 MVA)", "Transformador"],
    }

    # Frequência configurável (salva no banco)
    import json as _jf
    _freq_cfg_raw = carregar_config("freq_inspecoes", None)
    _freq_cfg = _jf.loads(_freq_cfg_raw) if _freq_cfg_raw else {}
    _FREQ_PADRAO = {"SF6 Gás": 7}
    for s in SISTEMAS:
        _FREQ_PADRAO[s] = 30

    with st.expander("⚙️ Configurar frequência das inspeções (dias)"):
        _fc = st.columns(len(SISTEMAS) + 1)
        _freq_sf6 = _fc[0].number_input("SF6 Gás", min_value=1, max_value=365,
                                         value=_freq_cfg.get("SF6 Gás", 7), key="freq_sf6")
        _freq_new = {"SF6 Gás": _freq_sf6}
        for i, s in enumerate(SISTEMAS):
            _freq_new[s] = _fc[i+1].number_input(s[:18], min_value=1, max_value=365,
                                                  value=_freq_cfg.get(s, 30), key=f"freq_{i}")
        if st.button("💾 Salvar frequências", use_container_width=True):
            salvar_config("freq_inspecoes", _jf.dumps(_freq_new))
            st.success("✅ Frequências salvas!")
            st.rerun()

    FREQ = {s: _freq_new.get(s, 30) for s in SISTEMAS}
    FREQ_SF6_DIAS = _freq_new.get("SF6 Gás", 7)

    # Calcular status de vencimento
    df_insp_all = _carregar_inspecoes()
    st.markdown("### 📅 Status das Inspeções")
    cw = st.columns(len(SISTEMAS) + 1)

    # SF6
    df_sf6_v = _carregar_sf6()
    ultima_sf6 = pd.to_datetime(df_sf6_v["data"].max()) if not df_sf6_v.empty else None
    dias_sf6   = (date.today() - ultima_sf6.date()).days if ultima_sf6 else 999
    cor_sf6    = "#10b981" if dias_sf6<=FREQ_SF6_DIAS else "#f59e0b" if dias_sf6<=FREQ_SF6_DIAS+3 else "#ef4444"
    prox_sf6   = f"Vence em {FREQ_SF6_DIAS-dias_sf6}d" if dias_sf6<FREQ_SF6_DIAS else f"ATRASADO {dias_sf6-FREQ_SF6_DIAS}d" if dias_sf6>FREQ_SF6_DIAS else "Hoje"
    cw[0].markdown(f"""<div class='kpi' style='border-top:3px solid {cor_sf6}'>
        <div style='font-size:1.1rem'>⚡</div>
        <div style='color:#f1f5f9;font-weight:700;font-size:0.85rem'>SF6 Gás</div>
        <div style='color:#475569;font-size:0.72rem'>A cada {FREQ_SF6_DIAS}d</div>
        <div style='color:{cor_sf6};font-weight:900;font-size:0.9rem;margin-top:4px'>{prox_sf6}</div>
        <div style='color:#334155;font-size:0.7rem'>Última: {ultima_sf6.strftime("%d/%m") if ultima_sf6 else "—"}</div>
    </div>""", unsafe_allow_html=True)

    for i, sis in enumerate(SISTEMAS):
        # Buscar última inspeção considerando TODOS os sistemas mapeados
        _sistemas_rel = _SIS_MAP.get(sis, [sis])
        if not df_insp_all.empty:
            df_s = df_insp_all[df_insp_all.sistema.isin(_sistemas_rel)]
        else:
            df_s = pd.DataFrame()
        ultima = pd.to_datetime(df_s["data"].max()) if not df_s.empty else None
        dias   = (date.today() - ultima.date()).days if ultima else 999
        lim    = FREQ[sis]
        cor    = "#10b981" if dias<=lim else "#f59e0b" if dias<=lim+7 else "#ef4444"
        prox   = f"Vence em {lim-dias}d" if dias<lim else f"ATRASADO {dias-lim}d" if dias>lim else "Hoje"
        cw[i+1].markdown(f"""<div class='kpi' style='border-top:3px solid {cor}'>
            <div style='font-size:1.1rem'>📋</div>
            <div style='color:#f1f5f9;font-weight:700;font-size:0.82rem'>{sis[:20]}</div>
            <div style='color:#475569;font-size:0.72rem'>A cada {lim}d</div>
            <div style='color:{cor};font-weight:900;font-size:0.9rem;margin-top:4px'>{prox}</div>
            <div style='color:#334155;font-size:0.7rem'>Última: {ultima.strftime("%d/%m") if ultima else "—"}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["➕ Nova Inspeção","📜 Histórico"])
    with tab1:
        # ── Condições ambientais herdadas do Painel (editáveis aqui também) ──
        t_amb_i = st.session_state.get("temp_amb_global", 28.0)
        u_amb_i = st.session_state.get("umid_amb_global", 70.0)
        turno_g = st.session_state.get("turno_global", "Manhã (06-14h)")

        st.markdown(f"""<div style='background:#0a1628;border:1px solid #1e5a96;
            border-radius:10px;padding:12px 20px;margin-bottom:14px;
            display:flex;align-items:center;gap:20px'>
            <div style='color:#60a5fa;font-weight:700;font-size:0.85rem'>🌡️ Condições do Dia:</div>
            <div style='color:#f1f5f9;font-size:0.9rem;font-weight:700'>{t_amb_i:.1f}°C</div>
            <div style='color:#475569;font-size:0.8rem'>Temperatura</div>
            <div style='color:#3b82f6;font-size:0.9rem;font-weight:700'>{u_amb_i:.0f}%</div>
            <div style='color:#475569;font-size:0.8rem'>Umidade</div>
            <div style='color:#10b981;font-size:0.9rem;font-weight:700'>{turno_g.split(" ")[0]}</div>
            <div style='color:#475569;font-size:0.8rem'>Turno</div>
            <div style='color:#334155;font-size:0.75rem;margin-left:8px'>
            ✏️ Para alterar, volte ao <b style='color:#60a5fa'>Painel Geral</b></div>
        </div>""", unsafe_allow_html=True)

        c1,c2,c3 = st.columns(3)
        data_i  = c1.date_input("📅 Data", value=date.today())
        turno_i = c2.selectbox("🕐 Turno", ["Manhã (06-14h)","Tarde (14-22h)","Noite (22-06h)"],
                               index=["Manhã (06-14h)","Tarde (14-22h)","Noite (22-06h)"].index(
                                   turno_g if turno_g in ["Manhã (06-14h)","Tarde (14-22h)","Noite (22-06h)"]
                                   else "Manhã (06-14h)"))
        sis_i   = c3.selectbox("⚡ Sistema", SISTEMAS)
        st.divider()
        itens = CHECKLISTS[sis_i]; res = {}
        for i,item in enumerate(itens):
            cc1,cc2,cc3 = st.columns([3.5,1.2,2.5])
            cc1.markdown(f"<div style='color:#94a3b8;padding:8px 0;font-size:0.88rem'>{i+1}. {item}</div>", unsafe_allow_html=True)
            st_ = cc2.selectbox("",["✅ OK","❌ NOK","⚠️ Atenção","➖ N/A"], key=f"i_{i}", label_visibility="collapsed")
            # Pré-preencher temperatura e umidade nas observações quando relevante
            obs_default = ""
            if "temperatura" in item.lower() or "OTI" in item or "WTI" in item:
                obs_default = f"T={t_amb_i:.1f}°C | UR={u_amb_i:.0f}%"
            obs = cc3.text_input("", key=f"o_{i}", label_visibility="collapsed",
                                 placeholder="Obs...", value=obs_default)
            res[item] = {"status":st_,"obs":obs}
        if st.button("💾 Salvar Inspeção", type="primary", use_container_width=True):
            nok = []
            for item,r in res.items():
                salvar_inspecao({"data":str(data_i),"turno":turno_i,"sistema":sis_i,"item":item,"status":r["status"],"observacao":r["obs"],"usuario":st.session_state.login})
                if r["status"]=="❌ NOK": nok.append(item)
            st.success(f"✅ {len(res)} itens salvos!")
            if nok: st.error(f"⚠️ NOK: {', '.join(nok[:3])}{'...' if len(nok)>3 else ''}")
    with tab2:
        c1,c2,c3 = st.columns(3)
        fs = c1.selectbox("Sistema",["Todos"]+SISTEMAS,key="fsh")
        fi = c2.date_input("De",value=date(2026,6,1),key="fih")
        ff = c3.date_input("Até",value=date.today(),key="ffh")
        df_i = carregar_inspecoes(fs,fi,ff)
        if df_i.empty: st.info("Sem registros.")
        else:
            def cs(v): return "color:#10b981;font-weight:bold" if v=="✅ OK" else "color:#ef4444;font-weight:bold" if v=="❌ NOK" else "color:#f59e0b;font-weight:bold" if "Atenção" in str(v) else ""
            _cols_disp = [c for c in ["data","turno","sistema","item","status","observacao","usuario"] if c in df_i.columns]
            _styler = df_i[_cols_disp].style.map(cs, subset=["status"]) if "status" in _cols_disp else df_i[_cols_disp].style
            st.dataframe(_styler, use_container_width=True, hide_index=True)
            _csv_i = df_i[_cols_disp].to_csv(index=False).encode("utf-8-sig")
            _nome_sis = fs.replace(" ", "_").replace("/", "-")
            st.download_button("⬇️ Exportar CSV", _csv_i,
                               f"inspecoes_{_nome_sis}_{fi}_{ff}.csv", "text/csv")

# ═══════════════════════════════════════════════════════════════ PENDÊNCIAS
elif "Pendências" in pagina:
    st.markdown("## ⚠️ Gestão de Pendências")
    tab1,tab2 = st.tabs(["➕ Nova","📋 Acompanhamento"])
    with tab1:
        with st.form("fp",clear_on_submit=True):
            c1,c2 = st.columns(2)
            da = c1.date_input("Data Abertura",value=date.today()); sis = c2.selectbox("Sistema",SISTEMAS)
            desc = st.text_area("Descrição",height=80)
            c3,c4,c5 = st.columns(3)
            sap = c3.text_input("Nota SAP"); prio = c4.selectbox("Prioridade",["Alta","Média","Baixa"]); st_p = c5.selectbox("Status",["Aberta","Em andamento"])
            obs = st.text_area("Obs.",height=50)
            if st.form_submit_button("💾 Registrar",type="primary",use_container_width=True):
                salvar_pendencia({"data_abertura":str(da),"sistema":sis,"descricao":desc,"nota_sap":sap,"prioridade":prio,"status":st_p,"observacao":obs,"usuario":st.session_state.login})
                st.success("✅ Pendência registrada!")
    with tab2:
        df_p = carregar_pendencias()
        if df_p.empty: st.info("Sem pendências.")
        else:
            _ab   = len(df_p[df_p.status == "Aberta"])
            _and  = len(df_p[df_p.status == "Em andamento"])
            _conc = len(df_p[df_p.status.isin(["Concluída","Cancelada"])])
            st.markdown(f"<div style='font-size:0.82rem;margin:4px 0 8px'>"
                        f"🔴 <b>{_ab}</b> abertas &nbsp;·&nbsp; "
                        f"🟡 <b>{_and}</b> em andamento &nbsp;·&nbsp; "
                        f"✅ <b>{_conc}</b> concluídas/canceladas</div>", unsafe_allow_html=True)
            _show_conc = st.toggle("Mostrar concluídas e canceladas", value=False, key="pend_show_all")
            _df_pend = df_p if _show_conc else df_p[df_p.status.isin(["Aberta","Em andamento"])]
            for _,row in _df_pend.iterrows():
                ico = {"Alta":"🔴","Média":"🟡","Baixa":"🟢"}.get(row.prioridade,"⚪")
                _badge = " ✅" if row.status=="Concluída" else " ❌" if row.status=="Cancelada" else ""
                with st.expander(f"{ico}{_badge} [{row.prioridade}] {row.sistema} — {str(row.descricao)[:60]}"):
                    c1,c2,c3 = st.columns(3)
                    c1.write(f"**Abertura:** {row.data_abertura}"); c2.write(f"**SAP:** {row.nota_sap or '—'}"); c3.write(f"**Status:** {row.status}")
                    st.write(f"**Descrição:** {row.descricao}")
                    ns = st.selectbox("Novo status",["Em andamento","Concluída","Cancelada"],key=f"ns{row.id}")
                    dc = st.date_input("Data conclusão",value=date.today(),key=f"dc{row.id}")
                    no = st.text_input("Obs.",key=f"no{row.id}")
                    if st.button("Atualizar",key=f"up{row.id}"): atualizar_pendencia(row.id,ns,str(dc),no); st.rerun()

# ═══════════════════════════════════════════════════════════════ RELATÓRIO
elif "Relatório" in pagina:
    st.markdown("## 📊 Relatório Mensal — Guardião da Usina")
    st.markdown("""<div class='card card-blue' style='padding:12px 18px'>
        <b style='color:#f1f5f9'>📋 Programa Guardiões — UHE Pimental</b>
        <span style='color:#334155;font-size:0.82rem'> · Envio mensal ao gestor</span>
    </div>""", unsafe_allow_html=True)

    # Período — meses gerados dinamicamente (6 atrás + atual + 3 à frente)
    _MESES_PT = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho",
                 "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
    _hoje_r = date.today()
    _meses_dict = {}
    for _d in range(-6, 4):
        _m = (_hoje_r.month + _d - 1) % 12 + 1
        _a = _hoje_r.year + (_hoje_r.month + _d - 1) // 12
        _meses_dict[f"{_MESES_PT[_m-1]}/{_a}"] = (_a, _m)
    # Padrão = mês anterior (relatório fechado ao virar o mês)
    _prev_m = _hoje_r.month - 1 if _hoje_r.month > 1 else 12
    _prev_a = _hoje_r.year if _hoje_r.month > 1 else _hoje_r.year - 1
    _mes_padrao = f"{_MESES_PT[_prev_m-1]}/{_prev_a}"
    _idx_mes = list(_meses_dict.keys()).index(_mes_padrao) if _mes_padrao in _meses_dict else 5

    _r1, _r2, _r3 = st.columns(3)
    mes = _r1.selectbox("📅 Mês", list(_meses_dict.keys()), index=_idx_mes, key="rel_mes")
    _ano_r, _mes_r = _meses_dict[mes]
    _ultimo_r = calendar.monthrange(_ano_r, _mes_r)[1]
    d_ini = _r2.date_input("De",  value=date(_ano_r, _mes_r, 1),         key="rel_ini")
    d_fim = _r3.date_input("Até", value=date(_ano_r, _mes_r, _ultimo_r),  key="rel_fim")

    # Carregar dados (versões com cache — evita reconexão ao banco a cada render)
    df_sf6_r    = _carregar_sf6(data_ini=d_ini, data_fim=d_fim)
    df_sf6_hist = _carregar_sf6()  # histórico completo para gráfico de evolução
    df_t_r      = _carregar_temps(data_ini=d_ini, data_fim=d_fim)
    df_p_r      = _carregar_pendencias()
    df_i_r      = _carregar_inspecoes(data_ini=d_ini, data_fim=d_fim)
    df_i_sec    = _carregar_inspecoes(sistema="Seccionadora",  data_ini=d_ini, data_fim=d_fim)
    df_i_sf6vis = _carregar_inspecoes(sistema="Disjuntor SF6", data_ini=d_ini, data_fim=d_fim)
    df_i_trafo  = _carregar_inspecoes(sistema="Transformador", data_ini=d_ini, data_fim=d_fim)
    df_ops_r    = _carregar_operacoes()
    df_secs     = _carregar_equipamentos("Seccionadora")
    df_cnt_r    = _carregar_contadores(data_ini=d_ini, data_fim=d_fim)

    n_alarmes_sf6   = len(df_sf6_r[df_sf6_r.status_sf6 != "NORMAL"]) if not df_sf6_r.empty else 0
    pend_abertas    = len(df_p_r[df_p_r.status == "Aberta"])          if not df_p_r.empty else 0
    pend_concluidas = len(df_p_r[df_p_r.status == "Concluída"])       if not df_p_r.empty else 0
    nok_sec_lista   = df_i_sec[df_i_sec.status == "NOK"].to_dict("records") if not df_i_sec.empty else []
    # Lista de todas as seccionadoras inspecionadas (última por item)
    todas_sec_lista = []
    if not df_i_sec.empty:
        for _, _rs in df_i_sec.sort_values("data").groupby("item").last().reset_index().iterrows():
            todas_sec_lista.append({"item": _rs["item"], "data": _rs.data, "status": _rs.status})
    insp_sec_count  = len(df_i_sec["item"].unique()) if not df_i_sec.empty else 0
    total_sec_count = len(df_secs) if not df_secs.empty else 27
    df_ops_periodo  = df_ops_r[(df_ops_r.data >= str(d_ini)) & (df_ops_r.data <= str(d_fim))] if not df_ops_r.empty else pd.DataFrame()

    # KPIs resumo
    _kpis_r = [
        (len(df_sf6_r),      "Leituras SF6",     "#3b82f6"),
        (n_alarmes_sf6,      "Alarmes SF6",       "#ef4444"),
        (len(df_t_r),        "Reg. Temperatura",  "#f59e0b"),
        (len(df_i_r),        "Inspeções",         "#10b981"),
        (pend_abertas,       "Pend. Abertas",     "#8b5cf6"),
        (pend_concluidas,    "Pend. Concluídas",  "#06b6d4"),
    ]
    st.markdown("<div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(100px,1fr));gap:8px;margin:12px 0'>" +
        "".join([f"<div style='background:#0f1e3a;border:1px solid #1e3a5f;border-top:3px solid {c};"
                 f"border-radius:10px;padding:10px;text-align:center'>"
                 f"<div style='font-size:1.5rem;font-weight:900;color:{c}'>{n}</div>"
                 f"<div style='font-size:0.65rem;color:#64748b;text-transform:uppercase'>{l}</div></div>"
                 for n,l,c in _kpis_r]) + "</div>", unsafe_allow_html=True)

    st.divider()

    # Gráficos
    _gc1, _gc2 = st.columns(2)
    with _gc1:
        st.markdown("#### ⚡ Evolução SF6 por Disjuntor")
        if not df_sf6_r.empty and len(df_sf6_r) > 1:
            fig_sf6_r = go.Figure()
            _cores_base = ["#3b82f6","#10b981","#f59e0b","#8b5cf6","#ef4444","#06b6d4","#f97316"]
            _combos = df_sf6_r.groupby(["disjuntor","polo"]).size().reset_index()[["disjuntor","polo"]]
            for _i, (_,row) in enumerate(_combos.iterrows()):
                _d = df_sf6_r[(df_sf6_r.disjuntor==row.disjuntor) & (df_sf6_r.polo==row.polo)].sort_values("data")
                _label = f"{row.disjuntor} · {row.polo}"
                _cor   = _cores_base[_i % len(_cores_base)]
                fig_sf6_r.add_trace(go.Scatter(
                    x=_d.data, y=_d.pressao_corrigida,
                    mode="lines+markers", name=_label,
                    line=dict(color=_cor, width=2), marker=dict(size=6),
                    hovertemplate=f"<b>{_label}</b><br>Data: %{{x}}<br>Pressão: %{{y:.3f}} bar<extra></extra>"
                ))
            fig_sf6_r.add_hline(y=5.2, line_dash="dash", line_color="#f59e0b",
                                annotation_text="Alarme 5,2 bar", annotation_font_color="#f59e0b", annotation_font_size=10)
            fig_sf6_r.add_hline(y=5.0, line_dash="dash", line_color="#ef4444",
                                annotation_text="Bloqueio 5,0 bar", annotation_font_color="#ef4444", annotation_font_size=10)
            fig_sf6_r.add_hline(y=6.0, line_dash="dot", line_color="#475569",
                                annotation_text="Nominal 6,0 bar", annotation_font_color="#475569", annotation_font_size=10)
            fig_sf6_r.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0.15)",
                font_color="#94a3b8", height=300,
                yaxis_title="Pressão (bar)", xaxis_title="Data",
                legend=dict(bgcolor="rgba(0,0,0,0)", font_size=10,
                            orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1))
            st.plotly_chart(fig_sf6_r, use_container_width=True)
        else:
            st.info("Sem dados SF6 no período.")
            fig_sf6_r = None

    with _gc2:
        st.markdown("#### 🌡️ Temperatura Trafo")
        if not df_t_r.empty and len(df_t_r) > 1:
            fig_temp_r = px.line(df_t_r.sort_values("data"), x="data", y="temperatura",
                                color="ponto", labels={"temperatura":"°C","data":"Data"})
            fig_temp_r.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0.15)",
                                     font_color="#94a3b8", height=280)
            st.plotly_chart(fig_temp_r, use_container_width=True)
        else:
            st.info("Sem dados de temperatura no período.")
            fig_temp_r = None

    st.divider()

    # Texto do guardião — carrega do banco na primeira abertura da sessão
    if "rel_obs_guardiao" not in st.session_state:
        _obs_db = carregar_config("rel_obs_guardiao", "")
        if _obs_db:
            st.session_state["rel_obs_guardiao"] = _obs_db
    if "rel_acoes_destaque" not in st.session_state:
        _acoes_db = carregar_config("rel_acoes_destaque", "")
        if _acoes_db:
            st.session_state["rel_acoes_destaque"] = _acoes_db

    obs_r   = st.text_area("📝 Observações do Guardião", height=100,
                            placeholder="Descreva as principais atividades, ocorrências e condições dos sistemas...",
                            key="rel_obs_guardiao")
    acoes_r = st.text_area("🏆 Ações de Destaque", height=80,
                            placeholder="1. Identificou desvio em...\n2. Abriu nota SAP...",
                            key="rel_acoes_destaque")

    st.divider()

    # ── Fotos persistentes — salvas no banco ─────────────────────────────
    st.markdown("#### 📷 Registro Fotográfico do Período")
    st.markdown("""<div style='background:#0a1628;border:1px solid #1e3a5f;border-radius:8px;
        padding:10px 16px;margin-bottom:10px;color:#475569;font-size:0.82rem'>
        📌 Carregue até <b style='color:#60a5fa'>10 fotos</b> (JPG/PNG) de inspeções, anomalias ou
        registros do período. As fotos ficam <b style='color:#10b981'>salvas no banco</b> e
        serão incluídas automaticamente no relatório mensal.
    </div>""", unsafe_allow_html=True)

    # Fotos já salvas no banco para o período (cache 30s — máx 6 fotos)
    df_fotos_salvas = _carregar_fotos(data_ini=str(d_ini), data_fim=str(d_fim), sem_base64=False)
    _n_salvas = len(df_fotos_salvas)
    _max_fotos = 10
    _vagas = max(0, _max_fotos - _n_salvas)

    # Exibir fotos salvas com imagem real em 2 colunas
    if _n_salvas > 0:
        import base64 as _b64
        st.markdown(f"<div style='color:#10b981;font-size:0.8rem;margin:4px 0 8px'>"
                    f"📷 {_n_salvas} foto(s) salva(s) no período</div>", unsafe_allow_html=True)
        _cols_fs = st.columns(2)
        for i, (_, _fr) in enumerate(df_fotos_salvas.iterrows()):
            with _cols_fs[i % 2]:
                try:
                    _img_bytes = _b64.b64decode(_fr.foto_base64)
                    st.image(_img_bytes, use_container_width=True)
                except Exception:
                    st.markdown("📷", unsafe_allow_html=False)
                st.markdown(f"<div style='font-size:0.78rem;color:#e2e8f0;margin:2px 0'>"
                            f"<b>{_fr.legenda or '—'}</b></div>"
                            f"<div style='font-size:0.68rem;color:#64748b;margin-bottom:6px'>"
                            f"📅 {_fr.data} · {_fr.sistema or ''}</div>",
                            unsafe_allow_html=True)
                if st.button("🗑️ Remover", key=f"rm_foto_{_fr.id}", use_container_width=True):
                    excluir_foto(_fr.id)
                    _carregar_fotos.clear()
                    st.rerun()

    # Upload de novas fotos (se houver vagas)
    if _vagas > 0:
        _fk = st.session_state.get("foto_counter", 0)
        fotos_upload = st.file_uploader(
            f"Adicionar fotos ({_vagas} vaga(s) restante(s))",
            type=["jpg","jpeg","png","webp"],
            accept_multiple_files=True, key=f"rel_fotos_{_fk}")
        if fotos_upload:
            _cols_fn = st.columns(3)
            for i, arq in enumerate(fotos_upload[:_vagas]):
                img_bytes = arq.read()
                with _cols_fn[i % 3]:
                    st.image(img_bytes, use_container_width=True)
                    leg = st.text_input("Legenda", key=f"leg_new_{i}",
                                        placeholder=f"Descreva a foto...",
                                        label_visibility="collapsed")
            if st.button("💾 Salvar fotos no banco", type="primary", use_container_width=True):
                _saved = 0
                for i, arq in enumerate(fotos_upload[:_vagas]):
                    arq.seek(0)
                    img_bytes = arq.read()
                    leg = st.session_state.get(f"leg_new_{i}", "")
                    b64 = foto_para_base64(img_bytes)
                    salvar_foto({
                        "data": str(d_fim),
                        "sistema": "Relatório Mensal",
                        "legenda": leg,
                        "foto_base64": b64,
                        "usuario": st.session_state.user
                    })
                    _saved += 1
                st.success(f"✅ {_saved} foto(s) salva(s) com sucesso!")
                _carregar_fotos.clear()
                st.session_state["foto_counter"] = _fk + 1
                st.rerun()
    elif _n_salvas >= _max_fotos:
        st.info(f"📷 Limite de {_max_fotos} fotos atingido. Remova uma para adicionar outra.")

    # Botão para limpar todas as fotos do período (após envio do relatório)
    if _n_salvas > 0:
        if st.button(f"🗑️ Excluir todas as {_n_salvas} fotos do período", use_container_width=True):
            st.session_state["_confirmar_limpar_fotos"] = True
        if st.session_state.get("_confirmar_limpar_fotos"):
            st.warning(f"⚠️ Tem certeza? Isso vai excluir **{_n_salvas} foto(s)** de {d_ini} a {d_fim}.")
            _cf1, _cf2 = st.columns(2)
            if _cf1.button("✅ Sim, excluir todas", type="primary", use_container_width=True):
                n = excluir_fotos_periodo(d_ini, d_fim)
                _carregar_fotos.clear()
                st.session_state["_confirmar_limpar_fotos"] = False
                st.success(f"✅ {n} foto(s) excluída(s)!")
                st.rerun()
            if _cf2.button("❌ Cancelar", use_container_width=True):
                st.session_state["_confirmar_limpar_fotos"] = False
                st.rerun()

    # fotos_dados montado dentro de montar_dados_relatorio() para não carregar base64 a cada render

    st.divider()

    cfg_email = carregar_config_email()
    dest_str  = ", ".join(cfg_email.get("destinatarios", []))

    col_b1, col_b2, col_b3 = st.columns(3)

    def _montar_fotos_dados():
        _df_f = carregar_fotos(data_ini=str(d_ini), data_fim=str(d_fim))
        _fotos = []
        for _, _fr in _df_f.head(10).iterrows():
            if _fr.foto_base64:
                _fotos.append({"base64": _fr.foto_base64, "legenda": _fr.legenda or ""})
        return _fotos

    def montar_dados_relatorio():
        import json as _j
        # SF6 — última pressão por disjuntor/polo
        sf6_tab = []
        if not df_sf6_r.empty:
            _ult = df_sf6_r.sort_values("created_at").groupby(["disjuntor","polo"]).last().reset_index()
            sf6_tab = _ult.to_dict("records")

        # SF6 — inspeção visual (última por disjuntor)
        sf6_visual = []
        if not df_i_sf6vis.empty:
            for _, _r in df_i_sf6vis.sort_values("data").groupby("item").last().reset_index().iterrows():
                try:
                    _itens = _j.loads(_r.observacao.split(" | ")[0]) if _r.observacao else {}
                except Exception:
                    _itens = {}
                sf6_visual.append({"disjuntor": _r["item"], "status": _r.status,
                                   "data": _r.data, "itens": _itens})

        # Operações no período
        ops_lista = df_ops_periodo.to_dict("records") if not df_ops_periodo.empty else []

        # Trafo — temperaturas
        trafo_tab = df_t_r.sort_values("data", ascending=False).head(15).to_dict("records") if not df_t_r.empty else []

        # Trafo — última inspeção completa
        trafo_insp = {}
        if not df_i_trafo.empty:
            _ult_tr = df_i_trafo.sort_values("data").iloc[-1]
            try:
                trafo_insp = _j.loads(_ult_tr.observacao) if _ult_tr.observacao else {}
                trafo_insp["data"]   = _ult_tr.data
                trafo_insp["status"] = _ult_tr.status
            except Exception:
                trafo_insp = {"data": _ult_tr.data, "status": _ult_tr.status}

        # Inspeções complementares — Para-raios, Sala Elétrica, Cúbilo
        _IC_MAP = [
            ("Para-raios 230kV",    "PARA-RAIOS-230kV"),
            ("Sala Elétrica da SE", "SALA-ELETRICA-SE"),
            ("Cúbilo de 13.8kV",   "CUBILO-13.8kV-SE"),
        ]
        insp_complement = []
        for _nome, _tag in _IC_MAP:
            _df_tag = df_i_r[df_i_r.item == _tag] if not df_i_r.empty else pd.DataFrame()
            if not _df_tag.empty:
                _ult_ic = _df_tag.sort_values("data").iloc[-1]
                try:
                    _dados_ic = _j.loads(_ult_ic.observacao) if _ult_ic.observacao else {}
                except Exception:
                    _dados_ic = {}
                insp_complement.append({"nome": _nome, "data": _ult_ic.data,
                                         "status": _ult_ic.status, "dados": _dados_ic})
            else:
                insp_complement.append({"nome": _nome, "data": "—",
                                         "status": "Sem registro", "dados": {}})

        cnt_lista = df_cnt_r.to_dict("records") if not df_cnt_r.empty else []

        return {
            "operador": st.session_state.user,
            "nivel":    st.session_state.nivel,
            "mes":      mes,
            "sistemas": ["Subestação 230kV","Sala Elétrica da SE","Cúbilo de 13.8kV da SE"],
            "resumo": {
                "leituras_sf6":          len(df_sf6_r),
                "alarmes_sf6":           n_alarmes_sf6,
                "temp_registradas":      len(df_t_r),
                "inspecoes":             len(df_i_r),
                "pendencias_abertas":    pend_abertas,
                "pendencias_concluidas": pend_concluidas,
            },
            "observacoes":   obs_r,
            "acoes":         acoes_r,
            "img_sf6":       fig_para_base64(fig_sf6_r)  if fig_sf6_r  else "",
            "img_temp":      fig_para_base64(fig_temp_r) if fig_temp_r else "",
            "pendencias":    df_p_r[df_p_r.status!="Concluída"].to_dict("records") if not df_p_r.empty else [],
            "sf6_tabela":    sf6_tab,
            "sf6_visual":    sf6_visual,
            "operacoes":     ops_lista,
            "sec_resumo": {
                "total":         total_sec_count,
                "inspecionadas": insp_sec_count,
                "nok":           nok_sec_lista,
                "todas":         todas_sec_lista,
            },
            "trafo_tabela":    trafo_tab,
            "trafo_insp":      trafo_insp,
            "insp_complement": insp_complement,
            "contadores":      cnt_lista,
            "fotos":           _montar_fotos_dados(),
            "sf6_historico":   df_sf6_hist.to_dict("records") if not df_sf6_hist.empty else [],
        }

    col_b1, col_b2, col_b3, col_b4 = st.columns(4)

    if col_b1.button("👁️ Visualizar", use_container_width=True):
        with st.spinner("Gerando pré-visualização..."):
            html_r = gerar_html_relatorio(montar_dados_relatorio())
        with st.expander("📄 Pré-visualização", expanded=True):
            st.components.v1.html(html_r, height=700, scrolling=True)

    if col_b2.button("⬇️ Baixar HTML", use_container_width=True):
        html_r = gerar_html_relatorio(montar_dados_relatorio())
        st.download_button("⬇️ Salvar .html", html_r,
                          f"Relatorio_{mes.replace('/','_')}.html",
                          "text/html", use_container_width=True)

    if col_b3.button("📄 Baixar PDF", use_container_width=True):
        try:
            from xhtml2pdf import pisa
            with st.spinner("Gerando PDF..."):
                from email_report import html_para_pdf
                _dados_pdf = montar_dados_relatorio()
                pdf_bytes = html_para_pdf(_dados_pdf)
            st.download_button("📄 Salvar .pdf", pdf_bytes,
                              f"Relatorio_{mes.replace('/','_')}.pdf",
                              "application/pdf", use_container_width=True)
        except ImportError:
            html_r = gerar_html_relatorio(montar_dados_relatorio())
            st.download_button("⬇️ Baixar HTML (abra no Chrome e imprima como PDF)",
                              html_r, f"Relatorio_{mes.replace('/','_')}.html",
                              "text/html", use_container_width=True)
            st.info("💡 Para gerar PDF: abra o arquivo no Chrome → Ctrl+P → 'Salvar como PDF'")

    if col_b4.button("📧 Enviar E-mail", type="primary", use_container_width=True):
        if not cfg_email.get("email_remetente") or not cfg_email.get("senha_app"):
            st.error("⚠️ Configure o e-mail primeiro na aba **📧 Configurar E-mail**")
        elif not cfg_email.get("destinatarios"):
            st.error("⚠️ Adicione pelo menos um destinatário nas configurações de e-mail")
        else:
            with st.spinner("Gerando relatório e enviando..."):
                # Persistir observações no banco para próximas sessões
                if obs_r:
                    salvar_config("rel_obs_guardiao", obs_r)
                if acoes_r:
                    salvar_config("rel_acoes_destaque", acoes_r)
                dados_r  = montar_dados_relatorio()
                _fotos_e = dados_r.get("fotos", [])
                # Para e-mail: HTML com CID (Gmail/Outlook renderizam as fotos)
                html_r   = gerar_html_relatorio(dados_r, usar_cid=bool(_fotos_e))
                assunto  = f"🛡️ Relatório Guardião da Usina — {mes} | {st.session_state.user}"
                # Gerar PDF para anexar
                _anexos = []
                try:
                    from email_report import html_para_pdf
                    pdf_bytes = html_para_pdf(dados_r)
                    if pdf_bytes:
                        _anexos.append((f"Relatorio_Guardiao_{mes.replace('/','_')}.pdf", pdf_bytes))
                except Exception:
                    pass
                ok, msg  = enviar_relatorio(cfg_email, html_r, assunto,
                                            fotos=_fotos_e if _fotos_e else None,
                                            anexos=_anexos if _anexos else None)
            if ok:
                st.success(msg)
                excluir_fotos_periodo(d_ini, d_fim)
                st.session_state["foto_counter"] = st.session_state.get("foto_counter", 0) + 1
                st.rerun()
            else:
                st.error(msg)

    if dest_str:
        st.markdown(f"<div style='color:#334155;font-size:0.78rem;margin-top:8px'>📧 Destinatários configurados: <b style='color:#60a5fa'>{dest_str}</b></div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='color:#ef4444;font-size:0.78rem;margin-top:8px'>⚠️ Nenhum destinatário configurado. Vá em <b>📧 Configurar E-mail</b></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════ CONFIG EMAIL
elif "E-mail" in pagina:
    st.markdown("## 📧 Configuração de E-mail")

    cfg = carregar_config_email()

    st.markdown("""<div class='card card-blue' style='padding:14px 18px;margin-bottom:16px'>
        <b style='color:#60a5fa'>Como configurar o Gmail:</b><br>
        <div style='color:#94a3b8;font-size:0.82rem;margin-top:6px'>
        1. Acesse <b>myaccount.google.com</b> → Segurança → Verificação em duas etapas (ative)<br>
        2. Em Segurança → <b>Senhas de app</b> → Selecione "Outro" → Digite "Guardião" → Gere<br>
        3. Copie a senha de 16 caracteres gerada e cole no campo abaixo<br>
        <span style='color:#f59e0b'>⚠️ Use a senha de APP, não a senha normal da conta!</span>
        </div>
    </div>""", unsafe_allow_html=True)

    with st.form("form_email_cfg"):
        st.markdown("#### Servidor SMTP")
        c1,c2 = st.columns(2)
        smtp_srv  = c1.selectbox("Servidor", ["smtp.gmail.com","smtp.office365.com","smtp.mail.yahoo.com"],
                                 index=["smtp.gmail.com","smtp.office365.com","smtp.mail.yahoo.com"].index(cfg.get("smtp_server","smtp.gmail.com")))
        smtp_port = c2.number_input("Porta", value=int(cfg.get("smtp_port",587)), step=1)

        st.markdown("#### Credenciais")
        c3,c4 = st.columns(2)
        email_rem = c3.text_input("📧 E-mail remetente", value=cfg.get("email_remetente",""),
                                   placeholder="seu@gmail.com")
        senha_app = c4.text_input("🔑 Senha de App", value=cfg.get("senha_app",""),
                                   type="password", placeholder="xxxx xxxx xxxx xxxx")

        st.markdown("#### Destinatários")
        dest_atual = "\n".join(cfg.get("destinatarios",[]))
        dest_input = st.text_area("📬 Destinatários (um por linha)",
                                   value=dest_atual, height=100,
                                   placeholder="gestor@norteenergia.com.br\nengenharia@empresa.com.br")

        assunto_pad = st.text_input("📝 Assunto padrão",
                                    value=cfg.get("assunto_padrao","Relatório Mensal — Guardião da Usina | UHE Pimental"))

        col_s1, col_s2 = st.columns(2)
        salvo = col_s1.form_submit_button("💾 Salvar Configuração", type="primary", use_container_width=True)
        testar = col_s2.form_submit_button("🧪 Testar Envio", use_container_width=True)

        if salvo or testar:
            destinatarios = [d.strip() for d in dest_input.split("\n") if d.strip()]
            nova_cfg = {
                "smtp_server":      smtp_srv,
                "smtp_port":        smtp_port,
                "email_remetente":  email_rem,
                "senha_app":        senha_app,
                "destinatarios":    destinatarios,
                "assunto_padrao":   assunto_pad,
            }
            salvar_config_email(nova_cfg)
            st.success("✅ Configuração salva!")

            if testar:
                html_teste = f"""<h2>🛡️ Teste — Guardião da Usina</h2>
                <p>E-mail de teste enviado com sucesso pelo sistema <b>Guardião da Usina</b>.</p>
                <p>Sistema: Norte Energia — UHE Pimental</p>
                <p>Usuário: {st.session_state.user}</p>"""
                with st.spinner("Enviando e-mail de teste..."):
                    ok, msg = enviar_relatorio(nova_cfg, html_teste, "🧪 Teste — Guardião da Usina")
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

    # Status atual
    st.divider()
    st.markdown("#### Status da Configuração Atual")
    cfg_atual = carregar_config_email()
    c1,c2,c3 = st.columns(3)
    c1.markdown(f"**Servidor:** `{cfg_atual.get('smtp_server','—')}:{cfg_atual.get('smtp_port','—')}`")
    c2.markdown(f"**Remetente:** `{cfg_atual.get('email_remetente','Não configurado')}`")
    c3.markdown(f"**Destinatários:** {len(cfg_atual.get('destinatarios',[]))}")
    if cfg_atual.get("destinatarios"):
        for d in cfg_atual["destinatarios"]:
            st.markdown(f"  → `{d}`")
