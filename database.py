import sqlite3, hashlib, os
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "guardiao.db")

def conn():
    return sqlite3.connect(DB, check_same_thread=False)

def init_db():
    c = conn(); cur = c.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT, usuario TEXT UNIQUE, senha_hash TEXT, nivel TEXT);

    CREATE TABLE IF NOT EXISTS equipamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT NOT NULL,
        tag TEXT UNIQUE NOT NULL,
        descricao TEXT,
        fabricante TEXT,
        modelo TEXT,
        ano_fabricacao TEXT,
        numero_serie TEXT,
        tensao_nominal REAL,
        corrente_nominal REAL,
        potencia_mva REAL,
        pressao_nominal REAL,
        pressao_alarme REAL,
        pressao_bloqueio REAL,
        temp_max REAL,
        localizacao TEXT,
        sistema TEXT,
        ativo INTEGER DEFAULT 1,
        num_polos INTEGER DEFAULT 1,
        observacao TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

    CREATE TABLE IF NOT EXISTS sf6_leituras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT, hora TEXT, turno TEXT,
        disjuntor TEXT, polo TEXT,
        pressao_medida REAL, temperatura REAL, pressao_corrigida REAL,
        status_sf6 TEXT, observacao TEXT,
        usuario TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

    CREATE TABLE IF NOT EXISTS temperaturas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT, hora TEXT, turno TEXT,
        equipamento TEXT, ponto TEXT,
        temperatura REAL, umidade REAL, limite_max REAL,
        status TEXT, observacao TEXT,
        usuario TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

    CREATE TABLE IF NOT EXISTS operacoes_dj (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT, disjuntor TEXT, tipo_operacao TEXT,
        motivo TEXT, num_operacoes_total INTEGER,
        usuario TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

    CREATE TABLE IF NOT EXISTS inspecoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT, turno TEXT, sistema TEXT,
        item TEXT, status TEXT, observacao TEXT,
        usuario TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

    CREATE TABLE IF NOT EXISTS pendencias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_abertura TEXT, sistema TEXT, descricao TEXT,
        nota_sap TEXT, prioridade TEXT, status TEXT,
        data_conclusao TEXT, observacao TEXT,
        usuario TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

    CREATE TABLE IF NOT EXISTS troca_turno (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT, turno_saida TEXT, turno_entrada TEXT,
        sistema TEXT, ocorrencia TEXT, acao_tomada TEXT,
        pendente INTEGER DEFAULT 0, usuario TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

    CREATE TABLE IF NOT EXISTS melhorias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT, sistema TEXT, descricao TEXT,
        status TEXT DEFAULT 'Aberto',
        usuario TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
    """)
    c.commit()
    # Migração: adiciona num_polos se ainda não existir
    try:
        c.execute("ALTER TABLE equipamentos ADD COLUMN num_polos INTEGER DEFAULT 1")
        c.commit()
    except Exception:
        pass
    c.close()

# ── Equipamentos ─────────────────────────────────────────────────
def salvar_equipamento(d):
    import sqlite3 as _sq
    c = conn()
    try:
        c.execute("""INSERT INTO equipamentos
            (tipo,tag,descricao,fabricante,modelo,ano_fabricacao,numero_serie,
             tensao_nominal,corrente_nominal,potencia_mva,pressao_nominal,pressao_alarme,
             pressao_bloqueio,temp_max,localizacao,sistema,num_polos,observacao)
            VALUES(:tipo,:tag,:descricao,:fabricante,:modelo,:ano_fabricacao,:numero_serie,
                   :tensao_nominal,:corrente_nominal,:potencia_mva,:pressao_nominal,:pressao_alarme,
                   :pressao_bloqueio,:temp_max,:localizacao,:sistema,:num_polos,:observacao)""", d)
        c.commit(); return True, "Equipamento cadastrado com sucesso!"
    except _sq.IntegrityError:
        return False, f"TAG '{d['tag']}' já existe no sistema."
    finally:
        c.close()

def atualizar_equipamento(id_, d):
    c = conn()
    c.execute("""UPDATE equipamentos SET
        tipo=:tipo, tag=:tag, descricao=:descricao, fabricante=:fabricante,
        modelo=:modelo, ano_fabricacao=:ano_fabricacao, numero_serie=:numero_serie,
        tensao_nominal=:tensao_nominal, corrente_nominal=:corrente_nominal,
        potencia_mva=:potencia_mva, pressao_nominal=:pressao_nominal,
        pressao_alarme=:pressao_alarme, pressao_bloqueio=:pressao_bloqueio,
        temp_max=:temp_max, localizacao=:localizacao, sistema=:sistema,
        observacao=:observacao WHERE id=?""", {**d, "id": id_})
    c.commit(); c.close()

def desativar_equipamento(id_):
    c = conn(); c.execute("UPDATE equipamentos SET ativo=0 WHERE id=?", (id_,)); c.commit(); c.close()

def carregar_equipamentos(tipo=None, sistema=None, ativo_only=True):
    import pandas as pd
    c = conn(); q = "SELECT * FROM equipamentos WHERE 1=1"; p = []
    if ativo_only: q += " AND ativo=1"
    if tipo and tipo != "Todos": q += " AND tipo=?"; p.append(tipo)
    if sistema and sistema != "Todos": q += " AND sistema=?"; p.append(sistema)
    q += " ORDER BY tipo, tag"
    df = pd.read_sql_query(q, c, params=p); c.close(); return df

def buscar_equipamento_por_tag(tag):
    c = conn()
    cur = c.execute("SELECT * FROM equipamentos WHERE tag=? AND ativo=1", (tag,))
    row = cur.fetchone()
    cols = [d[0] for d in cur.description] if row else []
    c.close()
    return dict(zip(cols, row)) if row else None

# ── SF6 ──────────────────────────────────────────────────────────
def salvar_sf6(d):
    c = conn()
    c.execute("""INSERT INTO sf6_leituras
        (data,hora,turno,disjuntor,polo,pressao_medida,temperatura,pressao_corrigida,status_sf6,observacao,usuario)
        VALUES(:data,:hora,:turno,:disjuntor,:polo,:pressao_medida,:temperatura,:pressao_corrigida,:status_sf6,:observacao,:usuario)""", d)
    c.commit(); c.close()

def carregar_sf6(disjuntor=None, data_ini=None, data_fim=None):
    import pandas as pd
    c = conn(); q = "SELECT * FROM sf6_leituras WHERE 1=1"; p = []
    if disjuntor and disjuntor != "Todos": q += " AND disjuntor=?"; p.append(disjuntor)
    if data_ini: q += " AND data>=?"; p.append(str(data_ini))
    if data_fim: q += " AND data<=?"; p.append(str(data_fim))
    q += " ORDER BY data DESC, hora DESC"
    df = pd.read_sql_query(q, c, params=p); c.close(); return df

# ── Temperaturas ──────────────────────────────────────────────────
def salvar_temp(d):
    c = conn()
    c.execute("""INSERT INTO temperaturas
        (data,hora,turno,equipamento,ponto,temperatura,umidade,limite_max,status,observacao,usuario)
        VALUES(:data,:hora,:turno,:equipamento,:ponto,:temperatura,:umidade,:limite_max,:status,:observacao,:usuario)""", d)
    c.commit(); c.close()

def carregar_temps(equipamento=None, data_ini=None, data_fim=None):
    import pandas as pd
    c = conn(); q = "SELECT * FROM temperaturas WHERE 1=1"; p = []
    if equipamento and equipamento != "Todos": q += " AND equipamento=?"; p.append(equipamento)
    if data_ini: q += " AND data>=?"; p.append(str(data_ini))
    if data_fim: q += " AND data<=?"; p.append(str(data_fim))
    q += " ORDER BY data DESC, hora DESC"
    df = pd.read_sql_query(q, c, params=p); c.close(); return df

# ── Operações DJ ──────────────────────────────────────────────────
def salvar_operacao(d):
    c = conn()
    c.execute("INSERT INTO operacoes_dj (data,disjuntor,tipo_operacao,motivo,num_operacoes_total,usuario) VALUES(:data,:disjuntor,:tipo_operacao,:motivo,:num_operacoes_total,:usuario)", d)
    c.commit(); c.close()

def carregar_operacoes(disjuntor=None):
    import pandas as pd
    c = conn(); q = "SELECT * FROM operacoes_dj WHERE 1=1"; p = []
    if disjuntor and disjuntor != "Todos": q += " AND disjuntor=?"; p.append(disjuntor)
    q += " ORDER BY data DESC"
    df = pd.read_sql_query(q, c, params=p); c.close(); return df

# ── Inspeções ──────────────────────────────────────────────────────
def salvar_inspecao(d):
    c = conn(); c.execute("INSERT INTO inspecoes (data,turno,sistema,item,status,observacao,usuario) VALUES(:data,:turno,:sistema,:item,:status,:observacao,:usuario)", d); c.commit(); c.close()

def carregar_inspecoes(sistema=None, data_ini=None, data_fim=None):
    import pandas as pd
    c = conn(); q = "SELECT * FROM inspecoes WHERE 1=1"; p = []
    if sistema and sistema != "Todos": q += " AND sistema=?"; p.append(sistema)
    if data_ini: q += " AND data>=?"; p.append(str(data_ini))
    if data_fim: q += " AND data<=?"; p.append(str(data_fim))
    q += " ORDER BY created_at DESC"
    df = pd.read_sql_query(q, c, params=p); c.close(); return df

# ── Pendências ────────────────────────────────────────────────────
def salvar_pendencia(d):
    c = conn(); c.execute("INSERT INTO pendencias (data_abertura,sistema,descricao,nota_sap,prioridade,status,observacao,usuario) VALUES(:data_abertura,:sistema,:descricao,:nota_sap,:prioridade,:status,:observacao,:usuario)", d); c.commit(); c.close()

def carregar_pendencias(status=None):
    import pandas as pd
    c = conn(); q = "SELECT * FROM pendencias WHERE 1=1"; p = []
    if status and status != "Todos": q += " AND status=?"; p.append(status)
    q += " ORDER BY created_at DESC"
    df = pd.read_sql_query(q, c, params=p); c.close(); return df

def atualizar_pendencia(id_, status, data_conclusao, obs):
    c = conn(); c.execute("UPDATE pendencias SET status=?,data_conclusao=?,observacao=? WHERE id=?", (status, data_conclusao, obs, id_)); c.commit(); c.close()

# ── Troca Turno ───────────────────────────────────────────────────
def salvar_troca(d):
    c = conn(); c.execute("INSERT INTO troca_turno (data,turno_saida,turno_entrada,sistema,ocorrencia,acao_tomada,pendente,usuario) VALUES(:data,:turno_saida,:turno_entrada,:sistema,:ocorrencia,:acao_tomada,:pendente,:usuario)", d); c.commit(); c.close()

def carregar_trocas(limit=20):
    import pandas as pd
    c = conn(); df = pd.read_sql_query(f"SELECT * FROM troca_turno ORDER BY created_at DESC LIMIT {limit}", c); c.close(); return df

# ── Melhorias ─────────────────────────────────────────────────────
def salvar_melhoria(d):
    c = conn(); c.execute("INSERT INTO melhorias (data,sistema,descricao,usuario) VALUES(:data,:sistema,:descricao,:usuario)", d); c.commit(); c.close()

def carregar_melhorias():
    import pandas as pd
    c = conn(); df = pd.read_sql_query("SELECT * FROM melhorias ORDER BY created_at DESC", c); c.close(); return df
