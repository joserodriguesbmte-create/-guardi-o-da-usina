"""
Importa pendências da planilha SAP para o Guardião da Usina.
Execute: py -3.12 importar_pendencias.py
"""
import pandas as pd
import psycopg2
from datetime import date

DB_URL = "postgresql://postgres.stgibmuefxrnistysckt:Guardiao2026.@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"

ARQUIVO = r"C:\Users\joser\Downloads\planilha 01.xlsx"

# Lê sem se preocupar com encoding das colunas — usamos índice
df = pd.read_excel(ARQUIVO)

# Índices das colunas necessárias (baseado na estrutura real do arquivo)
# 0=Data da nota, 5=Nota SAP, 7=Descrição, 9=Loc.instalação,
# 10=Denominação (tipo equip), 12=Denominação.1 (nome equip),
# 15=Data encermto, 24=Concl.desejada, 25=Status sistema,
# 26=Status usuário, 27=Prioridade
IDX = {
    "data_nota":   0,
    "nota_sap":    5,
    "descricao":   7,
    "loc":         9,
    "denom":      10,
    "denom1":     12,
    "data_enc":   15,
    "concl":      24,
    "status_sis": 25,
    "status_usr": 26,
    "prioridade": 27,
}

def _val(row, idx):
    v = row.iloc[idx]
    return "" if pd.isna(v) else str(v).strip()

def map_prioridade(raw):
    r = str(raw)
    if any(x in r for x in ["1.", "Muito", "Elevad"]):
        return "Alta"
    if "2." in r:
        return "Alta"
    if "3." in r or "édia" in r or "edia" in r:
        return "Média"
    return "Baixa"

def map_status(row):
    usr = _val(row, IDX["status_usr"])
    sis = _val(row, IDX["status_sis"])
    if "CONC" in usr:
        return "Concluída"
    if "MSEN" in sis:
        return "Em andamento"
    return "Aberta"

def map_sistema(row):
    denom  = _val(row, IDX["denom"]).upper()
    denom1 = _val(row, IDX["denom1"]).upper()
    if "TRAFO" in denom1 or "TRANSF" in denom1 or "TRF" in denom1:
        return "Transformador TR-SE-01 (Toshiba 10/12.5 MVA)"
    if "SECCION" in denom or ("DISJUNTOR" in denom and "230" in denom):
        return "Subestação 230kV"
    if "DISJUNTOR" in denom or "SECCION" in denom:
        return "Subestação 230kV"
    if "PAINEL" in denom or "CAIXA" in denom or "ARMARIO" in denom:
        return "Sala Elétrica da SE"
    if "VENTIL" in denom or "EXAUST" in denom:
        return "Sala Elétrica da SE"
    return "Subestação 230kV"

def fmt_data(raw):
    try:
        v = str(raw).replace("-", "")[:8]
        if len(v) == 8 and v.isdigit():
            return f"{v[:4]}-{v[4:6]}-{v[6:8]}"
    except Exception:
        pass
    return str(date.today())

c = psycopg2.connect(DB_URL, sslmode="require")
c.set_client_encoding("UTF8")
cur = c.cursor()

def limpar(s):
    """Remove caracteres de substituição e espaços extras."""
    return s.replace("�", "?").strip() if isinstance(s, str) else s
ok = 0; skip = 0

for _, row in df.iterrows():
    nota_sap = _val(row, IDX["nota_sap"])
    descricao = _val(row, IDX["descricao"])
    if not descricao:
        skip += 1; continue

    data_abertura = fmt_data(_val(row, IDX["data_nota"]))
    prioridade    = map_prioridade(_val(row, IDX["prioridade"]))
    status        = map_status(row)
    sistema       = map_sistema(row)
    descricao     = limpar(descricao)
    nome_equip    = limpar(_val(row, IDX["denom1"]))
    concl         = _val(row, IDX["concl"])

    obs = f"Equipamento: {nome_equip}" if nome_equip else ""
    if concl and concl not in ("nan", "NaT"):
        obs += f" | Conclusão prevista: {concl[:10]}"

    try:
        cur.execute("""
            INSERT INTO pendencias
              (data_abertura, sistema, descricao, nota_sap, prioridade,
               status, observacao, usuario)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (data_abertura, sistema, descricao, nota_sap, prioridade,
              status, obs.strip(" |"), "importado_sap"))
        print(f"OK  {nota_sap} - {descricao[:55]}  [{prioridade}] [{status}]")
        ok += 1
    except Exception as e:
        print(f"ERRO {nota_sap}: {e}")
        c.rollback()

c.commit(); cur.close(); c.close()
print(f"\n{ok} pendência(s) importada(s). {skip} linha(s) ignorada(s).")
