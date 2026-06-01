# Valores de referência por equipamento e parâmetro

REFERENCIAS = {
    "Disjuntor": {
        "Resistência de Contato (µΩ)":      {"min": None, "max": 50,    "unidade": "µΩ"},
        "Tempo de Abertura (ms)":            {"min": 40,   "max": 80,   "unidade": "ms"},
        "Tempo de Fechamento (ms)":          {"min": 40,   "max": 100,  "unidade": "ms"},
        "Resistência de Isolamento (MΩ)":    {"min": 1000, "max": None, "unidade": "MΩ"},
        "Pressão SF6 (bar)":                 {"min": 5.5,  "max": 6.5,  "unidade": "bar"},
        "Tensão de Disparo Mínima (V)":      {"min": 70,   "max": None, "unidade": "V"},
    },
    "Transformador": {
        "Resistência de Isolamento (MΩ)":    {"min": 500,  "max": None, "unidade": "MΩ"},
        "Índice de Polarização (IP)":        {"min": 1.3,  "max": None, "unidade": ""},
        "Rigidez Dielétrica Óleo (kV)":      {"min": 30,   "max": None, "unidade": "kV"},
        "Fator de Potência Isolamento (%)":  {"min": None, "max": 1.0,  "unidade": "%"},
        "Relação de Transformação (%)":      {"min": -0.5, "max": 0.5,  "unidade": "%"},
        "Resistência Enrolamento (mΩ)":      {"min": None, "max": None, "unidade": "mΩ"},
        "Temperatura Óleo (°C)":             {"min": None, "max": 85,   "unidade": "°C"},
    },
    "Bateria": {
        "Tensão Total (Vcc)":                {"min": 120,  "max": 130,  "unidade": "Vcc"},
        "Tensão por Célula (V)":             {"min": 2.15, "max": 2.35, "unidade": "V"},
        "Densidade Eletrólito (g/cm³)":      {"min": 1.24, "max": 1.28, "unidade": "g/cm³"},
        "Corrente de Float (A)":             {"min": None, "max": 2.0,  "unidade": "A"},
        "Resistência Interna (mΩ)":          {"min": None, "max": 5.0,  "unidade": "mΩ"},
        "Temperatura Ambiente (°C)":         {"min": 15,   "max": 30,   "unidade": "°C"},
    },
    "SF6": {
        "Pressão a 20°C (bar)":              {"min": 5.5,  "max": 6.5,  "unidade": "bar"},
        "Ponto de Orvalho (°C)":             {"min": None, "max": -10,  "unidade": "°C"},
        "Pureza SF6 (%)":                    {"min": 97,   "max": None, "unidade": "%"},
        "Umidade (ppm)":                     {"min": None, "max": 150,  "unidade": "ppm"},
        "Concentração SO2 (ppm)":            {"min": None, "max": 1.0,  "unidade": "ppm"},
    },
}

def calcular_resultado(equipamento, parametro, valor):
    ref = REFERENCIAS.get(equipamento, {}).get(parametro)
    if not ref:
        return "Sem referência"
    vmin, vmax = ref["min"], ref["max"]
    if vmin is not None and valor < vmin:
        return "REPROVADO"
    if vmax is not None and valor > vmax:
        return "REPROVADO"
    return "APROVADO"
