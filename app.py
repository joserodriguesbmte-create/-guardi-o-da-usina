import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime, time
from database import (init_db, salvar_sf6, carregar_sf6, salvar_temp, carregar_temps,
                      salvar_operacao, carregar_operacoes, salvar_inspecao, carregar_inspecoes,
                      salvar_pendencia, carregar_pendencias, atualizar_pendencia,
                      salvar_troca, carregar_trocas, salvar_melhoria, carregar_melhorias,
                      salvar_equipamento, atualizar_equipamento, desativar_equipamento,
                      carregar_equipamentos, buscar_equipamento_por_tag)
from equipamentos import DISJUNTORES, TRANSFORMADORES, BATERIAS, corrigir_pressao_sf6, status_sf6
from email_report import (salvar_config_email, carregar_config_email,
                           gerar_html_relatorio, enviar_relatorio, fig_para_base64)
from checklists import SISTEMAS, CHECKLISTS

st.set_page_config(page_title="Guardião da Usina", page_icon="🛡️",
                   layout="wide", initial_sidebar_state="expanded")
init_db()

# ═══════════════════════════════════════════════════════════════ CSS ══════
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.stApp{background:#07090f;}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#0a0e1a,#111827);border-right:1px solid #1e3a5f;}
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
.stSlider>div{color:#94a3b8;}
hr{border-color:#1e3a5f;}
</style>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════ LOGIN ════
if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    _,col,_ = st.columns([1,1.2,1])
    with col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""<div style='text-align:center;padding:24px 0'>
            <div style='font-size:5rem'>🛡️</div>
            <h1 style='color:#f1f5f9!important;font-size:2rem;font-weight:900;margin:8px 0 4px'>Guardião da Usina</h1>
            <p style='color:#475569;font-size:0.85rem'>Norte Energia — UHE Belo Monte | SE 230kV</p>
        </div>""", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        operador = st.selectbox("👤 Selecione seu nome", [
            "José Aparecido","Lenildo Luiz","Moisés Trindade","Jeferson Moraes",
            "João Valentim","Tulio Alves","Rodrigo Alves","Bruno Souza",
            "Gilbert Silva","Deysiele Cristiane"])
        nivel_map = {"José Aparecido":"SR","Lenildo Luiz":"SR","Moisés Trindade":"SR"}
        if st.button("🛡️  Entrar no Sistema", use_container_width=True, type="primary"):
            st.session_state.user  = operador
            st.session_state.nivel = nivel_map.get(operador, "OP")
            st.session_state.login = operador.split()[0].lower()
            st.rerun()
    st.stop()

# ═══════════════════════════════════════════════════════════════ SIDEBAR ══
with st.sidebar:
    st.markdown(f"""<div style='padding:16px 0 8px;text-align:center'>
        <div style='font-size:2.8rem'>🛡️</div>
        <div style='color:#f1f5f9;font-size:1rem;font-weight:800'>Guardião da Usina</div>
        <div style='color:#334155;font-size:0.7rem'>UHE Belo Monte | SE 230kV</div>
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
        "📋  Inspeção Diária",
        "⚠️  Pendências",
        "🔄  Troca de Turno",
        "📊  Relatório Mensal",
        "📧  Configurar E-mail",
    ], label_visibility="collapsed")
    st.divider()
    st.markdown(f"<div style='color:#334155;font-size:0.7rem'>📅 {date.today().strftime('%d/%m/%Y')}</div>", unsafe_allow_html=True)
    if st.button("🚪 Sair", use_container_width=True):
        for k in ["user","nivel","login"]: st.session_state.pop(k,None)
        st.rerun()

# ═══════════════════════════════════════════════════════════════ PAINEL ══
if "Painel" in pagina:
    st.markdown("""<div style='background:linear-gradient(90deg,#0c2340,#0f3460,#0c2340);border-radius:14px;padding:18px 28px;margin-bottom:12px;border:1px solid #1e3a5f'>
        <div style='color:#f1f5f9;font-size:1.4rem;font-weight:900'>🛡️ Guardião da Usina — Painel Operacional</div>
        <div style='color:#3b82f6;font-size:0.8rem;margin-top:2px'>Subestação 230kV · UHE Belo Monte | Workflow de Inspeção Diária</div>
    </div>""", unsafe_allow_html=True)

    # ══ 1. TEMPERATURA AMBIENTE CENTRALIZADA ════════════════════════════════
    amb_c1, amb_c2, amb_c3 = st.columns([2, 2, 3])
    t_amb = amb_c1.number_input(
        "🌡️ Temperatura Ambiente do Dia (°C)",
        value=float(st.session_state.get("temp_amb_global", 28.0)),
        min_value=-10.0, max_value=60.0, step=0.5, format="%.1f", key="amb_temp_painel"
    )
    turno_dia = amb_c2.selectbox(
        "⏰ Turno",
        ["Manhã (06-14h)", "Tarde (14-22h)", "Noite (22-06h)"],
        index=["Manhã (06-14h)","Tarde (14-22h)","Noite (22-06h)"].index(
            st.session_state.get("turno_global", "Manhã (06-14h)")),
        key="amb_turno_painel"
    )
    if t_amb > 35:   _conforto_cor = "#ef4444"; _conforto_txt = "Muito Quente"
    elif t_amb > 30: _conforto_cor = "#f59e0b"; _conforto_txt = "Quente"
    elif t_amb > 22: _conforto_cor = "#10b981"; _conforto_txt = "Confortável"
    else:            _conforto_cor = "#3b82f6"; _conforto_txt = "Ameno"
    amb_c3.markdown(f"""<div style='background:#0a1628;border:1px solid #1e3a5f;border-radius:10px;
        padding:10px 18px;display:flex;align-items:center;gap:20px;margin-top:6px'>
        <div style='text-align:center'>
            <div style='font-size:1.6rem;font-weight:900;color:{_conforto_cor}'>{t_amb:.1f}°C</div>
            <div style='font-size:0.65rem;color:#475569'>{_conforto_txt}</div>
        </div>
        <div style='border-left:1px solid #1e3a5f;height:36px'></div>
        <div style='color:#475569;font-size:0.8rem'>
            Variável global usada para correção térmica do SF6<br>
            <b style='color:#60a5fa'>P₂₀ = P_medida × (293,15 / (T + 273,15))</b>
        </div>
    </div>""", unsafe_allow_html=True)
    st.session_state["temp_amb_global"] = t_amb
    st.session_state["turno_global"]    = turno_dia

    st.markdown("<div style='border-bottom:1px solid #1e3a5f;margin:14px 0'></div>", unsafe_allow_html=True)

    # ══ DADOS COMUNS ═════════════════════════════════════════════════════════
    df_sf6_all  = carregar_sf6()
    df_pend_all = carregar_pendencias()
    df_djs_db   = carregar_equipamentos("Disjuntor SF6")
    df_secs_db  = carregar_equipamentos("Seccionadora")

    df_sf6_hoje  = carregar_sf6(data_ini=date.today(), data_fim=date.today())
    df_insp_hoje = carregar_inspecoes(sistema="Seccionadora", data_ini=date.today(), data_fim=date.today())

    djs_todos          = df_djs_db["tag"].tolist() if not df_djs_db.empty else []
    djs_inspecionados  = set(df_sf6_hoje["disjuntor"].unique()) if not df_sf6_hoje.empty else set()
    djs_pendentes      = [t for t in djs_todos if t not in djs_inspecionados]

    secs_todos         = df_secs_db["tag"].tolist() if not df_secs_db.empty else []
    secs_inspecionadas = set(df_insp_hoje["item"].unique()) if not df_insp_hoje.empty else set()
    secs_pendentes     = [t for t in secs_todos if t not in secs_inspecionadas]

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

    # ══ KPIs ════════════════════════════════════════════════════════════════
    k1,k2,k3,k4,k5 = st.columns(5)
    for _col,_ic,_n,_lb,_cr in [
        (k1,"⚡", len(djs_todos),                        "DJ Total",         "#3b82f6"),
        (k2,"✅", len(djs_todos)-len(djs_pendentes),     "DJ Hoje",          "#10b981"),
        (k3,"🔌", len(secs_todos)-len(secs_pendentes),   "SEC Hoje",         "#06b6d4"),
        (k4,"🚨", len(alertas_list),                     "Alertas SF6",      "#ef4444" if alertas_list else "#10b981"),
        (k5,"⚠️", pend_abertas,                           "Pendências",       "#8b5cf6"),
    ]:
        _col.markdown(f"""<div class='kpi' style='border-top:3px solid {_cr}'>
            <div style='font-size:1.6rem'>{_ic}</div>
            <div class='kpi-n' style='color:{_cr}'>{_n}</div>
            <div class='kpi-l'>{_lb}</div>
        </div>""", unsafe_allow_html=True)

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

        if not djs_pendentes:
            st.success("✅ Todos os disjuntores inspecionados hoje!")
        else:
            _df_dj_pend = df_djs_db[df_djs_db["tag"].isin(djs_pendentes)]
            _opc_dj = {r.tag: f"{r.tag}  ·  {r.modelo or '—'}  ·  {(r.descricao or '')[:40]}"
                       for _, r in _df_dj_pend.iterrows()}
            _dj_sel = st.selectbox("⚡ Disjuntor pendente", list(_opc_dj.keys()),
                                   format_func=lambda t: _opc_dj[t], key="wf_dj_sel")

            _eq_dj = buscar_equipamento_por_tag(_dj_sel)
            _p_nom_wf = float(_eq_dj.get("pressao_nominal", 6.0)) if _eq_dj else 6.0
            _p_al_wf  = float(_eq_dj.get("pressao_alarme",  5.5)) if _eq_dj else 5.5
            _p_bl_wf  = float(_eq_dj.get("pressao_bloqueio",5.0)) if _eq_dj else 5.0
            _np_wf    = int(_eq_dj.get("num_polos") or DISJUNTORES.get(_dj_sel,{}).get("num_polos",1)) if _eq_dj else 1
            _polos_wf = ["Polo A","Polo B","Polo C"] if _np_wf == 3 else ["Câmara Única"]

            _dados_wf = {}
            _cols_polo = st.columns(len(_polos_wf))
            for _i, _polo in enumerate(_polos_wf):
                with _cols_polo[_i]:
                    _p_med = st.number_input(f"📊 {_polo} (bar)", value=_p_nom_wf,
                                             min_value=0.0, max_value=10.0,
                                             step=0.01, format="%.3f", key=f"wf_p_{_polo}")
                    _p_cor = corrigir_pressao_sf6(_p_med, t_amb)
                    _delta = _p_cor - _p_nom_wf
                    if   _p_cor < _p_bl_wf:         _sc="#ef4444"; _st="🔴 BLOQUEIO"
                    elif _p_cor < _p_al_wf:         _sc="#f59e0b"; _st="🟡 ALARME"
                    elif _p_cor < _p_al_wf + 0.3:  _sc="#f97316"; _st="🟠 PRÉ-ALARME"
                    elif _p_cor > _p_nom_wf + 0.5: _sc="#8b5cf6"; _st="🟣 SOBREPRESSÃO"
                    else:                            _sc="#10b981"; _st="🟢 NORMAL"
                    st.markdown(f"""<div style='background:#0a1628;border:2px solid {_sc};
                        border-radius:8px;padding:8px;text-align:center;margin-top:4px'>
                        <div style='font-size:1.3rem;font-weight:900;color:{_sc}'>{_p_cor:.3f}</div>
                        <div style='font-size:0.6rem;color:#475569'>bar a 20°C</div>
                        <div style='font-size:0.72rem;font-weight:700;color:{_sc};margin-top:2px'>{_st}</div>
                        <div style='font-size:0.65rem;color:#334155'>Δ {'+' if _delta>=0 else ''}{_delta:.3f}</div>
                    </div>""", unsafe_allow_html=True)
                    _dados_wf[_polo] = {"p_med":_p_med,"p_cor":_p_cor,"status":_st.split(" ")[-1]}

            _obs_wf = st.text_input("Observação (opcional)", key="wf_dj_obs",
                                    placeholder="Condições, instrumento usado...")
            if st.button("💾 Salvar SF6 e Avançar para o próximo", type="primary",
                         use_container_width=True, key="wf_dj_save"):
                _hora_wf = datetime.now().time()
                for _polo, _d in _dados_wf.items():
                    salvar_sf6({"data":str(date.today()),"hora":str(_hora_wf),
                                "turno":turno_dia,"disjuntor":_dj_sel,"polo":_polo,
                                "pressao_medida":_d["p_med"],"temperatura":t_amb,
                                "pressao_corrigida":_d["p_cor"],"status_sf6":_d["status"],
                                "observacao":_obs_wf,"usuario":st.session_state.login})
                st.success(f"✅ {_dj_sel} registrado! Próximo na lista.")
                st.rerun()

        st.markdown("<div style='border-bottom:1px solid #1e3a5f;margin:14px 0'></div>", unsafe_allow_html=True)

        # ── 3. WORKFLOW SECCIONADORAS ────────────────────────────────────────
        st.markdown("""<div style='color:#06b6d4;font-size:0.72rem;font-weight:700;
            text-transform:uppercase;letter-spacing:1px;margin-bottom:6px'>
            🔌 Inspeção de Seccionadoras</div>""", unsafe_allow_html=True)

        _sec_tot  = len(secs_todos)
        _sec_done = _sec_tot - len(secs_pendentes)
        _sec_pct  = _sec_done / _sec_tot if _sec_tot else 0
        st.progress(_sec_pct, text=f"{_sec_done}/{_sec_tot} seccionadoras inspecionadas hoje")

        if not secs_pendentes:
            st.success("✅ Todas as seccionadoras inspecionadas hoje!")
        else:
            _df_sec_pend = df_secs_db[df_secs_db["tag"].isin(secs_pendentes)]
            _opc_sec = {r.tag: f"{r.tag}  ·  {(r.descricao or '')[:55]}"
                        for _, r in _df_sec_pend.iterrows()}
            _sec_sel = st.selectbox("🔌 Seccionadora pendente", list(_opc_sec.keys()),
                                    format_func=lambda t: _opc_sec[t], key="wf_sec_sel")

            _cs1, _cs2 = st.columns(2)
            _st_sec = _cs1.selectbox("Status", ["OK","NOK"], key="wf_sec_status")
            _obs_sec = _cs2.text_input("Observação", key="wf_sec_obs",
                                       placeholder="Condição observada...")
            if st.button("💾 Registrar e Avançar para a próxima", type="primary",
                         use_container_width=True, key="wf_sec_save"):
                salvar_inspecao({"data":str(date.today()),"turno":turno_dia,
                                 "sistema":"Seccionadora","item":_sec_sel,
                                 "status":_st_sec,"observacao":_obs_sec,
                                 "usuario":st.session_state.login})
                st.success(f"✅ {_sec_sel} registrada como {_st_sec}!")
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
        📌 Leituras SF6 são registradas no <b style='color:#60a5fa'>Painel Geral</b> durante a inspeção diária.
        Esta página exibe o histórico e a evolução ao longo do tempo.
    </div>""", unsafe_allow_html=True)
    tab2, tab3 = st.tabs(["📈 Evolução / Histórico", "🔢 Contagem de Operações"])

    if False:  # bloco removido — leituras agora só pelo Painel Geral
        with st.container():
        st.markdown("### ⚡ Leitura de Pressão SF6 — Cálculo Automático")

        # ── TEMPERATURA AMBIENTE DO DIA ───────────────────────────────────
        st.markdown("""<div style='background:linear-gradient(135deg,#0c2340,#0f3460);
            border:1px solid #1e5a96;border-radius:12px;padding:14px 20px;margin-bottom:14px'>
            <b style='color:#60a5fa;font-size:1rem'>🌡️ Temperatura Ambiente do Dia</b>
            <div style='color:#475569;font-size:0.78rem;margin-top:2px'>
            Define uma vez → aplicada automaticamente a todos os polos e equipamentos do dia
            </div>
        </div>""", unsafe_allow_html=True)

        ta1,ta2,ta3,ta4 = st.columns([1.5,1.5,1.5,3])
        temp_amb_dia = ta1.number_input(
            "🌡️ Temp. Ambiente (°C)", key="temp_amb_dia",
            value=st.session_state.get("temp_amb_global", 25.0),
            min_value=-20.0, max_value=60.0, step=0.1, format="%.1f")
        umid_amb_dia = ta2.number_input(
            "💧 Umidade (%)", key="umid_amb_dia",
            value=st.session_state.get("umid_amb_global", 60.0),
            min_value=0.0, max_value=100.0, step=1.0, format="%.0f")
        pressao_atm  = ta3.number_input(
            "📊 P. Atmosférica (mbar)", key="pressao_atm",
            value=st.session_state.get("patm_global", 1013.0),
            min_value=900.0, max_value=1100.0, step=1.0, format="%.0f")

        # Salvar temperatura global na sessão
        st.session_state["temp_amb_global"]  = temp_amb_dia
        st.session_state["umid_amb_global"]  = umid_amb_dia
        st.session_state["patm_global"]      = pressao_atm

        ta4.markdown(f"""<div style='background:#0a1628;border:1px solid #1e3a5f;border-radius:10px;
            padding:10px 16px;margin-top:2px;'>
            <div style='display:flex;gap:24px;align-items:center'>
                <div style='text-align:center'>
                    <div style='font-size:1.6rem;font-weight:900;color:#f59e0b'>{temp_amb_dia:.1f}°C</div>
                    <div style='font-size:0.65rem;color:#475569'>Temperatura</div>
                </div>
                <div style='text-align:center'>
                    <div style='font-size:1.6rem;font-weight:900;color:#3b82f6'>{umid_amb_dia:.0f}%</div>
                    <div style='font-size:0.65rem;color:#475569'>Umidade</div>
                </div>
                <div style='text-align:center'>
                    <div style='font-size:1.6rem;font-weight:900;color:#8b5cf6'>{pressao_atm:.0f}</div>
                    <div style='font-size:0.65rem;color:#475569'>mbar</div>
                </div>
                <div style='color:#475569;font-size:0.78rem'>
                    ✅ Será usada em todos<br>os campos de temperatura
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

        st.divider()

        # Cabeçalho: data / turno
        c1,c2,c3 = st.columns(3)
        data_l  = c1.date_input("📅 Data", value=date.today())
        hora_l  = c2.time_input("🕐 Hora", value=datetime.now().time())
        turno_l = c3.selectbox("Turno", ["Manhã (06-14h)","Tarde (14-22h)","Noite (22-06h)"],
                               index=["Manhã (06-14h)","Tarde (14-22h)","Noite (22-06h)"].index(
                                   st.session_state.get("turno_global","Manhã (06-14h)")
                                   if st.session_state.get("turno_global","Manhã (06-14h)") in
                                   ["Manhã (06-14h)","Tarde (14-22h)","Noite (22-06h)"] else "Manhã (06-14h)"))

        # Seleção do disjuntor — TAGs reais do banco com descrição
        df_dj_db = carregar_equipamentos("Disjuntor SF6")
        if df_dj_db.empty:
            st.warning("Nenhum disjuntor cadastrado. Vá em Cadastro de Equipamentos.")
            st.stop()

        # Montar opções com TAG + descrição + modelo
        opcoes_dj = {
            row.tag: f"{row.tag}  ·  {row.modelo or '—'}  ·  {(row.descricao or '')[:45]}"
            for _, row in df_dj_db.iterrows()
        }
        dj_sel = st.selectbox(
            "⚡ Selecione o Disjuntor",
            options=list(opcoes_dj.keys()),
            format_func=lambda t: opcoes_dj[t],
            key="sf6_dj_sel"
        )

        # Info do disjuntor (banco tem prioridade, fallback no dict fixo)
        eq_db = buscar_equipamento_por_tag(dj_sel)
        if eq_db:
            p_nom_dj  = float(eq_db.get("pressao_nominal") or 6.0)
            p_al_dj   = float(eq_db.get("pressao_alarme")  or 5.5)
            p_bl_dj   = float(eq_db.get("pressao_bloqueio") or 5.0)
            fab_dj    = eq_db.get("fabricante","—")
            mod_dj    = eq_db.get("modelo","—")
            desc_dj   = eq_db.get("descricao", dj_sel)
            num_polos_dj = int(eq_db.get("num_polos") or DISJUNTORES.get(dj_sel, {}).get("num_polos", 1))
        else:
            info_dj   = DISJUNTORES.get(dj_sel, {"pressao_nominal":6.0,"pressao_alarme":5.5,"pressao_bloqueio":5.0,"fabricante":"—","modelo":"—","descricao":dj_sel,"num_polos":1})
            p_nom_dj  = info_dj["pressao_nominal"]
            p_al_dj   = info_dj["pressao_alarme"]
            p_bl_dj   = info_dj["pressao_bloqueio"]
            fab_dj    = info_dj["fabricante"]
            mod_dj    = info_dj["modelo"]
            desc_dj   = info_dj["descricao"]
            num_polos_dj = info_dj.get("num_polos", 1)

        st.markdown(f"""<div class='card card-blue' style='padding:12px 18px;margin:6px 0 16px'>
            <span style='color:#60a5fa;font-size:1rem;font-weight:800'>{dj_sel}</span>
            <span style='color:#334155'> — {desc_dj}</span><br>
            <div style='display:flex;gap:24px;margin-top:8px;font-size:0.82rem'>
                <span style='color:#475569'>Fab: <b style='color:#94a3b8'>{fab_dj}</b></span>
                <span style='color:#475569'>Modelo: <b style='color:#94a3b8'>{mod_dj}</b></span>
                <span style='color:#475569'>P.Nominal: <b style='color:#f1f5f9'>{p_nom_dj} bar</b></span>
                <span style='color:#475569'>⚠️ Alarme: <b style='color:#f59e0b'>{p_al_dj} bar</b></span>
                <span style='color:#475569'>🔴 Bloqueio: <b style='color:#ef4444'>{p_bl_dj} bar</b></span>
            </div>
        </div>""", unsafe_allow_html=True)

        st.markdown("""<div style='background:#0a1628;border:1px dashed #1e3a5f;border-radius:10px;padding:10px 16px;margin-bottom:16px;color:#475569;font-size:0.82rem'>
            💡 <b style='color:#60a5fa'>Cálculo automático:</b> Digite a pressão e a temperatura — a pressão corrigida a 20°C é calculada instantaneamente pela fórmula INTEC:
            <code style='color:#a5f3fc'> P₂₀ = P_medida × (293,15 / (T + 273,15))</code>
        </div>""", unsafe_allow_html=True)

        # ── Uma linha por polo com cálculo em tempo real ──────────────────
        polos = ["Polo A", "Polo B", "Polo C"] if num_polos_dj == 3 else ["Câmara Única"]
        dados_polos = {}

        # Cabeçalho da tabela
        hc1,hc2,hc3,hc4,hc5,hc6 = st.columns([0.8,2,2,2,2,2])
        for col,txt in zip([hc1,hc2,hc3,hc4,hc5,hc6],
                           ["","📊 P. Medida","🌡️ Temperatura","✅ P. Corrigida 20°C","📈 Variação","🔖 Status"]):
            col.markdown(f"<div style='color:#475569;font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;padding-bottom:4px'>{txt}</div>",
                        unsafe_allow_html=True)
        st.markdown("<hr style='margin:4px 0 8px;border-color:#1e3a5f'>", unsafe_allow_html=True)

        for polo in polos:
            pc1,pc2,pc3,pc4,pc5,pc6 = st.columns([0.8,2,2,2,2,2])

            pc1.markdown(f"<div style='padding:8px 0;color:#3b82f6;font-weight:800;font-size:0.95rem'>{polo}</div>",
                        unsafe_allow_html=True)

            p_med = pc2.number_input("bar", key=f"p_{polo}",
                                     value=p_nom_dj, min_value=0.0, max_value=10.0,
                                     step=0.01, format="%.3f", label_visibility="collapsed")

            t_amb = pc3.number_input("°C", key=f"t_{polo}",
                                     value=temp_amb_dia,  # ← pré-preenchida com T ambiente do dia
                                     min_value=-20.0, max_value=80.0,
                                     step=0.1, format="%.1f", label_visibility="collapsed")

            # ── CÁLCULO AUTOMÁTICO ─────────────────────────────────────
            p_cor = corrigir_pressao_sf6(p_med, t_amb)
            delta = p_cor - p_nom_dj

            # Definir cor da pressão corrigida
            if p_cor < p_bl_dj:    cor_p = "#ef4444"; status_txt = "BLOQUEIO"; icone_s = "🔴"
            elif p_cor < p_al_dj:  cor_p = "#f59e0b"; status_txt = "ALARME";   icone_s = "🟡"
            elif p_cor > p_nom_dj + 0.5: cor_p = "#8b5cf6"; status_txt = "SOBREPRESSÃO"; icone_s = "🟣"
            else:                  cor_p = "#10b981"; status_txt = "NORMAL";   icone_s = "🟢"

            # Display grande da pressão corrigida
            pc4.markdown(f"""<div style='background:#0a1628;border:2px solid {cor_p};border-radius:10px;
                padding:8px 12px;text-align:center'>
                <div style='font-size:1.5rem;font-weight:900;color:{cor_p};line-height:1'>{p_cor:.3f}</div>
                <div style='font-size:0.65rem;color:#475569;margin-top:2px'>bar a 20°C</div>
            </div>""", unsafe_allow_html=True)

            # Variação em relação ao nominal
            sinal = "+" if delta >= 0 else ""
            cor_d = "#10b981" if delta >= 0 else "#f59e0b" if delta > -0.5 else "#ef4444"
            pc5.markdown(f"""<div style='padding:8px 4px;text-align:center'>
                <div style='font-size:1.1rem;font-weight:800;color:{cor_d}'>{sinal}{delta:.3f}</div>
                <div style='font-size:0.65rem;color:#475569'>vs nominal</div>
            </div>""", unsafe_allow_html=True)

            # Status badge
            badge_bg  = {"NORMAL":"#052e16","ALARME":"#451a03","BLOQUEIO":"#450a0a","SOBREPRESSÃO":"#2e1065"}
            badge_txt = {"NORMAL":"#34d399","ALARME":"#fcd34d","BLOQUEIO":"#fca5a5","SOBREPRESSÃO":"#d8b4fe"}
            pc6.markdown(f"""<div style='padding:8px 0;text-align:center'>
                <div style='background:{badge_bg.get(status_txt,"#1e293b")};
                    color:{badge_txt.get(status_txt,"#94a3b8")};
                    border-radius:8px;padding:6px 10px;font-size:0.82rem;font-weight:800'>
                    {icone_s} {status_txt}
                </div>
            </div>""", unsafe_allow_html=True)

            dados_polos[polo] = {"p_med":p_med,"t_amb":t_amb,"p_cor":p_cor,"status":status_txt}

        # ── Card de resumo automático (atualiza em tempo real) ────────────
        st.markdown("<br>", unsafe_allow_html=True)
        alertas_rt = [f"{p}: {d['status']} ({d['p_cor']:.3f} bar)" for p,d in dados_polos.items() if d["status"]!="NORMAL"]
        if alertas_rt:
            st.markdown(f"""<div style='background:#450a0a;border:1px solid #ef4444;border-radius:10px;
                padding:14px 18px;'>
                <b style='color:#fca5a5;font-size:1rem'>🚨 ATENÇÃO — Pressão fora do limite!</b><br>
                <span style='color:#fca5a5;font-size:0.9rem'>{"  |  ".join(alertas_rt)}</span>
            </div>""", unsafe_allow_html=True)
        else:
            resumo_polos = "  |  ".join([f"{p}: {d['p_cor']:.3f} bar" for p, d in dados_polos.items()])
            st.markdown(f"""<div style='background:#052e16;border:1px solid #10b981;border-radius:10px;
                padding:12px 18px;'>
                <b style='color:#34d399'>✅ Pressão NORMAL</b><br>
                <span style='color:#059669;font-size:0.82rem'>{resumo_polos}</span>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        obs_sf6 = st.text_area("📝 Observação", height=60, key="obs_sf6",
                               placeholder="Condições do campo, equipamentos usados, intercorrências...")

        if st.button("💾 Salvar Leituras SF6", type="primary", use_container_width=True):
            for polo, dados in dados_polos.items():
                salvar_sf6({"data":str(data_l),"hora":str(hora_l),"turno":turno_l,
                            "disjuntor":dj_sel,"polo":polo,
                            "pressao_medida":dados["p_med"],
                            "temperatura":dados["t_amb"],
                            "pressao_corrigida":dados["p_cor"],
                            "status_sf6":dados["status"],
                            "observacao":obs_sf6,
                            "usuario":st.session_state.login})
            pass  # removido

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
            _cores_ev = {"Polo A": "#3b82f6", "Polo B": "#10b981", "Polo C": "#f59e0b",
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
                st.success("✅ Operação registrada!")

        df_op = carregar_operacoes()
        if not df_op.empty:
            fig_op = px.bar(df_op.groupby("disjuntor").size().reset_index(name="total"),
                           x="disjuntor", y="total", title="Total de Operações Registradas por Disjuntor",
                           color="total", color_continuous_scale="Blues")
            fig_op.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0.15)",
                                font_color="#94a3b8", height=280)
            st.plotly_chart(fig_op, use_container_width=True)
            st.dataframe(df_op[["data","disjuntor","tipo_operacao","motivo","num_operacoes_total","usuario"]],
                        use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════ TEMP ═════
elif "Temperatura" in pagina:
    st.markdown("## 🌡️ Monitoramento de Temperaturas")
    tab1, tab2 = st.tabs(["📥 Registrar", "📈 Histórico / Tendência"])

    PONTOS_TEMP = {
        # TR-SE-01 Toshiba — limites baseados na placa (elevação 65°C + ambient max 40°C = max 105°C)
        # Alarm temp at 90°C oil / 100°C winding as per NBR 5356 practice
        "TR-SE-01 Toshiba (Óleo / OTI)":    {"pontos": ["OTI — Temperatura do Óleo","Ambient. junto ao trafo"], "limites": [90,45]},
        "TR-SE-01 Toshiba (Enrolamentos)":   {"pontos": ["WTI AT — Enrolamento Alta Tensão","WTI BT — Enrolamento Baixa Tensão"], "limites": [100,100]},
        "Sala Elétrica SE":    {"pontos": ["Ambiente sala","Painel controle 1","Painel controle 2","Corredor"], "limites": [35,55,55,35]},
        "Cúbilo 13.8kV":      {"pontos": ["Compartimento disjuntor","Compartimento barramento","Compartimento cabos","Ambiente"], "limites": [70,70,60,35]},
        "Sala Baterias 125V":  {"pontos": ["Ambiente","Bateria (topo)","Retificador"], "limites": [30,35,55]},
    }

    with tab1:
        c1,c2,c3 = st.columns(3)
        data_t  = c1.date_input("📅 Data", value=date.today())
        hora_t  = c2.time_input("🕐 Hora", value=datetime.now().time())
        turno_t = c3.selectbox("Turno", ["Manhã","Tarde","Noite"])
        equip_t = st.selectbox("📍 Local / Equipamento", list(PONTOS_TEMP.keys()))

        pontos  = PONTOS_TEMP[equip_t]["pontos"]
        limites = PONTOS_TEMP[equip_t]["limites"]

        st.divider()
        st.markdown(f"#### Leituras de Temperatura — {equip_t}")
        for idx, (ponto, limite) in enumerate(zip(pontos, limites)):
            cc1,cc2,cc3,cc4 = st.columns([2,1.2,1.2,1.5])
            cc1.markdown(f"<div style='padding:9px 0;color:#94a3b8'>🌡️ {ponto}</div>", unsafe_allow_html=True)
            t_val  = cc2.number_input("°C", key=f"tv_{idx}", value=25.0, step=0.5, format="%.1f")
            um_val = cc3.number_input("Umidade %", key=f"uv_{idx}", value=60.0, step=1.0, format="%.0f")
            status_t = "ALARME" if t_val > limite else "NORMAL"
            cor_t = "#ef4444" if status_t=="ALARME" else "#10b981"
            cc4.markdown(f"<div style='padding:9px 0'><span style='color:{cor_t};font-weight:700'>{status_t}</span> <span style='color:#334155;font-size:0.8rem'>(lim: {limite}°C)</span></div>", unsafe_allow_html=True)

        obs_t = st.text_area("Observação", height=60, key="obs_t")

        if st.button("💾 Salvar Temperaturas", type="primary", use_container_width=True):
            for idx, (ponto, limite) in enumerate(zip(pontos, limites)):
                t_v = st.session_state.get(f"tv_{idx}", 25.0)
                u_v = st.session_state.get(f"uv_{idx}", 60.0)
                status_t = "ALARME" if t_v > limite else "NORMAL"
                salvar_temp({"data":str(data_t),"hora":str(hora_t),"turno":turno_t,
                             "equipamento":equip_t,"ponto":ponto,"temperatura":t_v,
                             "umidade":u_v,"limite_max":limite,"status":status_t,
                             "observacao":obs_t,"usuario":st.session_state.login})
            st.success(f"✅ {len(pontos)} leituras salvas!")

    with tab2:
        c1,c2,c3 = st.columns(3)
        eq_f  = c1.selectbox("Equipamento", ["Todos"]+list(PONTOS_TEMP.keys()), key="eq_f")
        di    = c2.date_input("De", value=date(2026,6,1), key="t_ini")
        df2   = c3.date_input("Até", value=date.today(), key="t_fim")
        df_t  = carregar_temps(eq_f, di, df2)
        if df_t.empty:
            st.info("Sem registros de temperatura.")
        else:
            df_t["data_hora"] = pd.to_datetime(df_t["data"]+" "+df_t["hora"])
            fig_t = px.line(df_t, x="data_hora", y="temperatura", color="ponto",
                           facet_col="equipamento" if eq_f=="Todos" else None,
                           title="Evolução de Temperatura por Ponto de Medição",
                           labels={"temperatura":"Temp (°C)","data_hora":"Data/Hora","ponto":"Ponto"})
            fig_t.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0.15)",
                               font_color="#94a3b8", height=380)
            st.plotly_chart(fig_t, use_container_width=True)
            def cor_t(v):
                return "color:#ef4444;font-weight:bold" if v=="ALARME" else "color:#10b981;font-weight:bold"
            st.dataframe(df_t[["data","hora","equipamento","ponto","temperatura","umidade","limite_max","status"]].style.applymap(cor_t, subset=["status"]),
                        use_container_width=True, hide_index=True)

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
        st.markdown("### 🌡️ Correção de Temperatura — Transformador TR-SE-01")

        # ── Bloco 1: Limite de alarme real pela temperatura ambiente ──────
        st.markdown("""<div class='card card-blue'>
            <b style='color:#60a5fa'>Limite Real de Alarme = Temperatura Ambiente + Elevação de Temperatura (placa)</b><br>
            <code style='color:#a5f3fc'>T_alarme = T_amb + ΔT_placa</code><br>
            <small style='color:#334155'>TR-SE-01 Toshiba: ΔT Óleo = 65°C | ΔT Enrolamento = 65°C (conforme placa NBR 5356/2007)</small>
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

    # Frequências definidas
    FREQ = {
        "Subestação 230kV":                              {"freq": "Mensal",  "dias": 30},
        "Sala Elétrica da SE":                           {"freq": "Mensal",  "dias": 30},
        "Cúbilo de 13.8kV da SE":                       {"freq": "Mensal",  "dias": 30},
        "Transformador TR-SE-01 (Toshiba 10/12.5 MVA)": {"freq": "Mensal",  "dias": 30},
    }
    FREQ_SF6 = {"freq": "Semanal", "dias": 7}

    # Calcular status de vencimento
    df_insp_all = carregar_inspecoes()
    st.markdown("### 📅 Status das Inspeções")
    cw = st.columns(len(SISTEMAS) + 1)

    # SF6 Semanal
    df_sf6_v = carregar_sf6()
    ultima_sf6 = pd.to_datetime(df_sf6_v["data"].max()) if not df_sf6_v.empty else None
    dias_sf6   = (date.today() - ultima_sf6.date()).days if ultima_sf6 else 999
    cor_sf6    = "#10b981" if dias_sf6<=7 else "#f59e0b" if dias_sf6<=10 else "#ef4444"
    prox_sf6   = f"Vence em {7-dias_sf6}d" if dias_sf6<=7 else f"ATRASADO {dias_sf6-7}d"
    cw[0].markdown(f"""<div class='kpi' style='border-top:3px solid {cor_sf6}'>
        <div style='font-size:1.1rem'>⚡</div>
        <div style='color:#f1f5f9;font-weight:700;font-size:0.85rem'>SF6 Gás</div>
        <div style='color:#475569;font-size:0.72rem'>Semanal</div>
        <div style='color:{cor_sf6};font-weight:900;font-size:0.9rem;margin-top:4px'>{prox_sf6}</div>
        <div style='color:#334155;font-size:0.7rem'>Última: {ultima_sf6.strftime("%d/%m") if ultima_sf6 else "—"}</div>
    </div>""", unsafe_allow_html=True)

    for i, sis in enumerate(SISTEMAS):
        df_s = df_insp_all[df_insp_all.sistema==sis] if not df_insp_all.empty else pd.DataFrame()
        ultima = pd.to_datetime(df_s["data"].max()) if not df_s.empty else None
        dias   = (date.today() - ultima.date()).days if ultima else 999
        lim    = FREQ[sis]["dias"]
        cor    = "#10b981" if dias<=lim else "#f59e0b" if dias<=lim+7 else "#ef4444"
        prox   = f"Vence em {lim-dias}d" if dias<lim else "VENCIDA" if dias>lim else "Hoje"
        cw[i+1].markdown(f"""<div class='kpi' style='border-top:3px solid {cor}'>
            <div style='font-size:1.1rem'>📋</div>
            <div style='color:#f1f5f9;font-weight:700;font-size:0.82rem'>{sis[:20]}</div>
            <div style='color:#475569;font-size:0.72rem'>Mensal</div>
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
            st.dataframe(df_i[["data","turno","sistema","item","status","observacao","usuario"]].style.applymap(cs,subset=["status"]),use_container_width=True,hide_index=True)

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
            for _,row in df_p[df_p.status!="Concluída"].iterrows():
                ico = {"Alta":"🔴","Média":"🟡","Baixa":"🟢"}.get(row.prioridade,"⚪")
                with st.expander(f"{ico} [{row.prioridade}] {row.sistema} — {str(row.descricao)[:60]}"):
                    c1,c2,c3 = st.columns(3)
                    c1.write(f"**Abertura:** {row.data_abertura}"); c2.write(f"**SAP:** {row.nota_sap or '—'}"); c3.write(f"**Status:** {row.status}")
                    st.write(f"**Descrição:** {row.descricao}")
                    ns = st.selectbox("Novo status",["Em andamento","Concluída","Cancelada"],key=f"ns{row.id}")
                    dc = st.date_input("Data conclusão",value=date.today(),key=f"dc{row.id}")
                    no = st.text_input("Obs.",key=f"no{row.id}")
                    if st.button("Atualizar",key=f"up{row.id}"): atualizar_pendencia(row.id,ns,str(dc),no); st.rerun()

# ═══════════════════════════════════════════════════════════════ TROCA ════
elif "Troca" in pagina:
    st.markdown("## 🔄 Troca de Turno")
    with st.form("ft",clear_on_submit=True):
        c1,c2,c3,c4 = st.columns(4)
        dt = c1.date_input("Data",value=date.today()); ts = c2.selectbox("Turno Saída",["Manhã","Tarde","Noite"])
        te = c3.selectbox("Turno Entrada",["Manhã","Tarde","Noite"]); sis = c4.selectbox("Sistema",SISTEMAS)
        oc = st.text_area("Ocorrência / Informação",height=80)
        ac = st.text_area("Ação Tomada",height=60)
        pend = st.checkbox("⚠️ Requer acompanhamento no próximo turno")
        if st.form_submit_button("💾 Registrar",type="primary",use_container_width=True):
            salvar_troca({"data":str(dt),"turno_saida":ts,"turno_entrada":te,"sistema":sis,"ocorrencia":oc,"acao_tomada":ac,"pendente":int(pend),"usuario":st.session_state.login})
            st.success("✅ Passagem registrada!")
    df_tr = carregar_trocas(20)
    for _,r in df_tr.iterrows():
        ico = "⚠️" if r.pendente else "✅"
        with st.expander(f"{ico} {r.data} | {r.turno_saida}→{r.turno_entrada} | {r.sistema}"):
            st.write(f"**Ocorrência:** {r.ocorrencia}"); st.write(f"**Ação:** {r.acao_tomada or '—'}")

# ═══════════════════════════════════════════════════════════════ RELATÓRIO
elif "Relatório" in pagina:
    st.markdown("## 📊 Relatório Mensal — Guardião da Usina")

    st.markdown(f"""<div class='card card-blue' style='padding:14px 20px'>
        <b style='color:#f1f5f9;font-size:1rem'>📋 Programa Guardiões — UHE Belo Monte</b><br>
        <span style='color:#334155;font-size:0.82rem'>
        Entrega: <b style='color:#f59e0b'>09/07/2026</b> (ref. Junho/2026) &nbsp;|&nbsp;
        Envio: por e-mail ao gestor</span>
    </div>""", unsafe_allow_html=True)

    # Período
    c1,c2,c3 = st.columns(3)
    mes   = c1.selectbox("📅 Mês de Referência", ["Junho/2026","Julho/2026","Agosto/2026"])
    d_ini = c2.date_input("Período início", value=date(2026,6,1))
    d_fim = c3.date_input("Período fim",    value=date(2026,6,30))

    # Carregar dados do período
    df_sf6_r = carregar_sf6(data_ini=d_ini, data_fim=d_fim)
    df_t_r   = carregar_temps(data_ini=d_ini, data_fim=d_fim)
    df_p_r   = carregar_pendencias()
    df_i_r   = carregar_inspecoes(data_ini=d_ini, data_fim=d_fim)

    n_alarmes_sf6  = len(df_sf6_r[df_sf6_r.status_sf6 != "NORMAL"]) if not df_sf6_r.empty else 0
    pend_abertas   = len(df_p_r[df_p_r.status == "Aberta"])       if not df_p_r.empty else 0
    pend_concluidas= len(df_p_r[df_p_r.status == "Concluída"])    if not df_p_r.empty else 0
    itens_nok      = df_i_r[df_i_r.status == "❌ NOK"] if not df_i_r.empty else pd.DataFrame()

    # KPIs
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    for col,n,lbl,cor in [
        (c1,len(df_sf6_r),"Leituras SF6","#3b82f6"),
        (c2,n_alarmes_sf6,"Alarmes SF6","#ef4444"),
        (c3,len(df_t_r),"Reg. Temperatura","#f59e0b"),
        (c4,len(df_i_r),"Inspeções","#10b981"),
        (c5,pend_abertas,"Pend. Abertas","#8b5cf6"),
        (c6,pend_concluidas,"Pend. Concluídas","#06b6d4"),
    ]:
        col.markdown(f"""<div class='kpi' style='border-top:3px solid {cor};padding:14px 8px'>
            <div class='kpi-n' style='color:{cor};font-size:1.8rem'>{n}</div>
            <div class='kpi-l'>{lbl}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Gráficos para o relatório
    col_ga, col_gb = st.columns(2)
    with col_ga:
        st.markdown("#### ⚡ Tendência SF6")
        if not df_sf6_r.empty and len(df_sf6_r) > 1:
            fig_sf6_r = go.Figure()
            for polo, cor_p in [("Polo A","#3b82f6"),("Polo B","#10b981"),("Polo C","#f59e0b")]:
                d = df_sf6_r[df_sf6_r.polo==polo].sort_values("data")
                if not d.empty:
                    fig_sf6_r.add_trace(go.Scatter(x=d.data, y=d.pressao_corrigida,
                        mode="lines+markers", name=polo, line=dict(color=cor_p,width=2)))
            ref = list(DISJUNTORES.values())[0]
            fig_sf6_r.add_hline(y=ref["pressao_alarme"], line_dash="dash", line_color="#f59e0b", annotation_text="Alarme")
            fig_sf6_r.add_hline(y=ref["pressao_bloqueio"], line_dash="dash", line_color="#ef4444", annotation_text="Bloqueio")
            fig_sf6_r.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0.15)",
                                   font_color="#94a3b8", height=280,
                                   yaxis_title="Pressão (bar)", xaxis_title="Data")
            st.plotly_chart(fig_sf6_r, use_container_width=True)
        else:
            st.info("Sem dados SF6 no período.")
            fig_sf6_r = None

    with col_gb:
        st.markdown("#### 🌡️ Tendência Temperatura")
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

    # Texto do guardião
    obs_r   = st.text_area("📝 Observações do Guardião", height=120,
                            placeholder="Descreva as principais atividades, ocorrências e condições dos sistemas...")
    acoes_r = st.text_area("🏆 Ações de Destaque", height=80,
                            placeholder="1. Identificação de desvio em...\n2. Abertura de nota SAP...")

    # Carregar config e destinatários
    cfg_email = carregar_config_email()
    dest_str  = ", ".join(cfg_email.get("destinatarios", []))

    st.markdown("<br>", unsafe_allow_html=True)
    col_b1, col_b2, col_b3 = st.columns(3)

    # ── Gerar HTML ────────────────────────────────────────────────────────
    def montar_dados_relatorio():
        img_sf6_b64  = fig_para_base64(fig_sf6_r)  if fig_sf6_r  else ""
        img_temp_b64 = fig_para_base64(fig_temp_r) if fig_temp_r else ""
        pend_lista = df_p_r[df_p_r.status!="Concluída"].to_dict("records") if not df_p_r.empty else []
        nok_lista  = itens_nok.to_dict("records") if not itens_nok.empty else []
        return {
            "operador": st.session_state.user,
            "nivel":    st.session_state.nivel,
            "mes":      mes,
            "sistemas": ["Subestação 230kV","Sala Elétrica da SE","Cúbilo de 13.8kV da SE"],
            "resumo": {
                "leituras_sf6":       len(df_sf6_r),
                "alarmes_sf6":        n_alarmes_sf6,
                "temp_registradas":   len(df_t_r),
                "inspecoes":          len(df_i_r),
                "pendencias_abertas": pend_abertas,
                "pendencias_concluidas": pend_concluidas,
            },
            "observacoes":    obs_r,
            "acoes":          acoes_r,
            "img_sf6":        img_sf6_b64,
            "img_temp":       img_temp_b64,
            "pendencias":     pend_lista,
            "inspecoes_nok":  nok_lista,
        }

    if col_b1.button("👁️ Visualizar Relatório", use_container_width=True):
        dados_r = montar_dados_relatorio()
        html_r  = gerar_html_relatorio(dados_r)
        with st.expander("📄 Pré-visualização HTML", expanded=True):
            st.components.v1.html(html_r, height=600, scrolling=True)

    if col_b2.button("⬇️ Baixar HTML", use_container_width=True):
        dados_r = montar_dados_relatorio()
        html_r  = gerar_html_relatorio(dados_r)
        st.download_button("⬇️ Salvar Relatório.html", html_r,
                          f"Relatorio_Guardiao_{mes.replace('/','_')}.html",
                          "text/html", use_container_width=True)

    if col_b3.button("📧 Enviar por E-mail", type="primary", use_container_width=True):
        if not cfg_email.get("email_remetente") or not cfg_email.get("senha_app"):
            st.error("⚠️ Configure o e-mail primeiro na aba **📧 Configurar E-mail**")
        elif not cfg_email.get("destinatarios"):
            st.error("⚠️ Adicione pelo menos um destinatário nas configurações de e-mail")
        else:
            with st.spinner("Gerando relatório e enviando..."):
                dados_r  = montar_dados_relatorio()
                html_r   = gerar_html_relatorio(dados_r)
                assunto  = f"🛡️ Relatório Guardião da Usina — {mes} | {st.session_state.user}"
                ok, msg  = enviar_relatorio(cfg_email, html_r, assunto)
            if ok:
                st.success(msg)
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
                                    value=cfg.get("assunto_padrao","Relatório Mensal — Guardião da Usina | UHE Belo Monte"))

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
                <p>Sistema: Norte Energia — UHE Belo Monte</p>
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
