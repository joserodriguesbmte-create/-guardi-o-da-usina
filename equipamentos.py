# Equipamentos reais da Subestação 230kV - UHE Belo Monte / Norte Energia
# num_polos: 1 = câmara única (1 medida SF6), 3 = polos separados (3 medidas SF6)

DISJUNTORES = {
    "PMDJ6-01": {"descricao": "Disjuntor Bay 01PUL", "fabricante": "ABB", "modelo": "LTB 245E2", "tensao_nominal": 230, "pressao_nominal": 6.0, "pressao_alarme": 5.5, "pressao_bloqueio": 5.0, "tipo_gas": "SF6", "num_polos": 1},
    "PMDJ6-02": {"descricao": "Disjuntor Vão Linha (3 polos separados)", "fabricante": "ABB", "modelo": "LTB 245E2", "tensao_nominal": 230, "pressao_nominal": 6.0, "pressao_alarme": 5.5, "pressao_bloqueio": 5.0, "tipo_gas": "SF6", "num_polos": 3},
    "PMDJ6-03": {"descricao": "Disjuntor Bay 02PVL", "fabricante": "ABB", "modelo": "LTB 245E2", "tensao_nominal": 230, "pressao_nominal": 6.0, "pressao_alarme": 5.5, "pressao_bloqueio": 5.0, "tipo_gas": "SF6", "num_polos": 1},
    "PMDJ6-04": {"descricao": "Disjuntor Vão Trafo", "fabricante": "ABB", "modelo": "LTB 245E2", "tensao_nominal": 230, "pressao_nominal": 6.0, "pressao_alarme": 5.5, "pressao_bloqueio": 5.0, "tipo_gas": "SF6", "num_polos": 1},
    "PMDJ6-05": {"descricao": "Disjuntor Bay 03PVL", "fabricante": "ABB", "modelo": "LTB 245E2", "tensao_nominal": 230, "pressao_nominal": 6.0, "pressao_alarme": 5.5, "pressao_bloqueio": 5.0, "tipo_gas": "SF6", "num_polos": 1},
}

TRANSFORMADORES = {
    "TR-01": {"descricao": "Transformador Principal AT/MT T1", "fabricante": "WEG", "potencia_mva": 150, "tensao_at": 230, "tensao_bt": 13.8, "temp_oleo_max": 85, "temp_enrolamento_max": 95, "nivel_oleo_min": 40, "nivel_oleo_max": 80},
    "TR-02": {"descricao": "Transformador Principal AT/MT T2", "fabricante": "WEG", "potencia_mva": 150, "tensao_at": 230, "tensao_bt": 13.8, "temp_oleo_max": 85, "temp_enrolamento_max": 95, "nivel_oleo_min": 40, "nivel_oleo_max": 80},
}

BATERIAS = {
    "BAT-125V-01": {"descricao": "Banco de Baterias 125Vcc - Sala Elétrica SE", "fabricante": "Fiamm", "tensao_nominal": 125, "num_celulas": 60, "tensao_celula_nominal": 2.1, "tensao_flutuacao_min": 120, "tensao_flutuacao_max": 130, "densidade_min": 1.24, "densidade_max": 1.28},
    "BAT-48V-01":  {"descricao": "Banco de Baterias 48Vcc - Sala Elétrica SE", "fabricante": "Fiamm", "tensao_nominal": 48, "num_celulas": 24, "tensao_celula_nominal": 2.0, "tensao_flutuacao_min": 46, "tensao_flutuacao_max": 52, "densidade_min": 1.24, "densidade_max": 1.28},
}

PAINEL_CUBICULOS = {
    "CUB-13.8-01": {"descricao": "Cubículo 01 - Alimentador Principal", "fabricante": "Schneider", "tensao_nominal": 13.8, "corrente_nominal": 1200},
    "CUB-13.8-02": {"descricao": "Cubículo 02 - Alimentador Auxiliar", "fabricante": "Schneider", "tensao_nominal": 13.8, "corrente_nominal": 630},
    "CUB-13.8-03": {"descricao": "Cubículo 03 - Medição", "fabricante": "Schneider", "tensao_nominal": 13.8, "corrente_nominal": 200},
}

# Fórmula INTEC para correção de pressão SF6 para 20°C
# Baseada na Lei dos Gases: P1/T1 = P2/T2
def corrigir_pressao_sf6(p_medida: float, t_medida: float) -> float:
    """Corrige pressão SF6 medida em campo para 20°C de referência."""
    T_ref = 293.15  # 20°C em Kelvin
    T_med = t_medida + 273.15
    return round(p_medida * (T_ref / T_med), 3)

def status_sf6(p_corrigida: float, tag: str) -> dict:
    dj = DISJUNTORES.get(tag, {})
    p_nom  = dj.get("pressao_nominal", 6.0)
    p_al   = dj.get("pressao_alarme", 5.5)
    p_bloq = dj.get("pressao_bloqueio", 5.0)
    if p_corrigida < p_bloq:
        return {"status": "BLOQUEIO", "cor": "#ef4444", "icone": "🔴"}
    elif p_corrigida < p_al:
        return {"status": "ALARME", "cor": "#f59e0b", "icone": "🟡"}
    elif p_corrigida > p_nom + 0.5:
        return {"status": "SOBREPRESSÃO", "cor": "#8b5cf6", "icone": "🟣"}
    else:
        return {"status": "NORMAL", "cor": "#10b981", "icone": "🟢"}
