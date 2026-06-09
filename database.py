import os
import psycopg2
import psycopg2.extras
import pandas as pd

def _params():
    try:
        import streamlit as st
        url = st.secrets["DATABASE_URL"]
    except Exception:
        url = os.environ.get("DATABASE_URL", "")
    # Parâmetros separados evitam problemas com caracteres especiais na senha
    try:
        from urllib.parse import urlparse, unquote
        p = urlparse(url)
        return dict(
            host=p.hostname, port=p.port or 5432,
            dbname=(p.path or "/postgres").lstrip("/"),
            user=p.username,
            password=unquote(p.password or ""),
            sslmode="require"
        )
    except Exception:
        return {"dsn": url, "sslmode": "require"}

def conn():
    return psycopg2.connect(**_params())

def init_db():
    c = conn(); cur = c.cursor()
    stmts = [
        """CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            nome TEXT, usuario TEXT UNIQUE, senha_hash TEXT, nivel TEXT)""",

        """CREATE TABLE IF NOT EXISTS equipamentos (
            id SERIAL PRIMARY KEY,
            tipo TEXT NOT NULL,
            tag TEXT UNIQUE NOT NULL,
            descricao TEXT, fabricante TEXT, modelo TEXT,
            ano_fabricacao TEXT, numero_serie TEXT,
            tensao_nominal REAL, corrente_nominal REAL, potencia_mva REAL,
            pressao_nominal REAL, pressao_alarme REAL, pressao_bloqueio REAL,
            temp_max REAL, localizacao TEXT, sistema TEXT,
            ativo INTEGER DEFAULT 1,
            num_polos INTEGER DEFAULT 1,
            observacao TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",

        """CREATE TABLE IF NOT EXISTS sf6_leituras (
            id SERIAL PRIMARY KEY,
            data TEXT, hora TEXT, turno TEXT,
            disjuntor TEXT, polo TEXT,
            pressao_medida REAL, temperatura REAL, pressao_corrigida REAL,
            status_sf6 TEXT, observacao TEXT,
            usuario TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",

        """CREATE TABLE IF NOT EXISTS temperaturas (
            id SERIAL PRIMARY KEY,
            data TEXT, hora TEXT, turno TEXT,
            equipamento TEXT, ponto TEXT,
            temperatura REAL, umidade REAL, limite_max REAL,
            status TEXT, observacao TEXT,
            usuario TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",

        """CREATE TABLE IF NOT EXISTS operacoes_dj (
            id SERIAL PRIMARY KEY,
            data TEXT, disjuntor TEXT, tipo_operacao TEXT,
            motivo TEXT, num_operacoes_total INTEGER,
            usuario TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",

        """CREATE TABLE IF NOT EXISTS inspecoes (
            id SERIAL PRIMARY KEY,
            data TEXT, turno TEXT, sistema TEXT,
            item TEXT, status TEXT, observacao TEXT,
            usuario TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",

        """CREATE TABLE IF NOT EXISTS pendencias (
            id SERIAL PRIMARY KEY,
            data_abertura TEXT, sistema TEXT, descricao TEXT,
            nota_sap TEXT, prioridade TEXT, status TEXT,
            data_conclusao TEXT, observacao TEXT,
            usuario TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",

        """CREATE TABLE IF NOT EXISTS troca_turno (
            id SERIAL PRIMARY KEY,
            data TEXT, turno_saida TEXT, turno_entrada TEXT,
            sistema TEXT, ocorrencia TEXT, acao_tomada TEXT,
            pendente INTEGER DEFAULT 0, usuario TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",

        """CREATE TABLE IF NOT EXISTS melhorias (
            id SERIAL PRIMARY KEY,
            data TEXT, sistema TEXT, descricao TEXT,
            status TEXT DEFAULT 'Aberto',
            usuario TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",

        """CREATE TABLE IF NOT EXISTS config_app (
            chave TEXT PRIMARY KEY,
            valor TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",

        """CREATE TABLE IF NOT EXISTS contadores_dj (
            id SERIAL PRIMARY KEY,
            data TEXT, hora TEXT, turno TEXT,
            disjuntor TEXT,
            polo_a INTEGER DEFAULT 0,
            polo_b INTEGER DEFAULT 0,
            polo_v INTEGER DEFAULT 0,
            tripolar INTEGER DEFAULT 0,
            curto_circuito INTEGER DEFAULT 0,
            usuario TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
    ]
    for s in stmts:
        cur.execute(s)
    c.commit()  # commit tabelas antes do migration
    # Migração segura: adiciona num_polos se não existir
    try:
        cur.execute("ALTER TABLE equipamentos ADD COLUMN num_polos INTEGER DEFAULT 1")
        c.commit()
    except Exception:
        c.rollback()
    cur.close(); c.close()

# ── Equipamentos ──────────────────────────────────────────────────────────
def salvar_equipamento(d):
    c = conn(); cur = c.cursor()
    try:
        cur.execute("""INSERT INTO equipamentos
            (tipo,tag,descricao,fabricante,modelo,ano_fabricacao,numero_serie,
             tensao_nominal,corrente_nominal,potencia_mva,pressao_nominal,pressao_alarme,
             pressao_bloqueio,temp_max,localizacao,sistema,num_polos,observacao)
            VALUES(%(tipo)s,%(tag)s,%(descricao)s,%(fabricante)s,%(modelo)s,%(ano_fabricacao)s,
                   %(numero_serie)s,%(tensao_nominal)s,%(corrente_nominal)s,%(potencia_mva)s,
                   %(pressao_nominal)s,%(pressao_alarme)s,%(pressao_bloqueio)s,%(temp_max)s,
                   %(localizacao)s,%(sistema)s,%(num_polos)s,%(observacao)s)""", d)
        c.commit(); return True, "Equipamento cadastrado com sucesso!"
    except psycopg2.errors.UniqueViolation:
        c.rollback(); return False, f"TAG '{d['tag']}' já existe no sistema."
    finally:
        cur.close(); c.close()

def atualizar_equipamento(id_, d):
    c = conn(); cur = c.cursor()
    cur.execute("""UPDATE equipamentos SET
        tipo=%(tipo)s, tag=%(tag)s, descricao=%(descricao)s, fabricante=%(fabricante)s,
        modelo=%(modelo)s, ano_fabricacao=%(ano_fabricacao)s, numero_serie=%(numero_serie)s,
        tensao_nominal=%(tensao_nominal)s, corrente_nominal=%(corrente_nominal)s,
        potencia_mva=%(potencia_mva)s, pressao_nominal=%(pressao_nominal)s,
        pressao_alarme=%(pressao_alarme)s, pressao_bloqueio=%(pressao_bloqueio)s,
        temp_max=%(temp_max)s, localizacao=%(localizacao)s, sistema=%(sistema)s,
        observacao=%(observacao)s WHERE id=%(id)s""", {**d, "id": id_})
    c.commit(); cur.close(); c.close()

def desativar_equipamento(id_):
    c = conn(); cur = c.cursor()
    cur.execute("UPDATE equipamentos SET ativo=0 WHERE id=%s", (id_,))
    c.commit(); cur.close(); c.close()

def carregar_equipamentos(tipo=None, sistema=None, ativo_only=True):
    c = conn(); q = "SELECT * FROM equipamentos WHERE 1=1"; p = []
    if ativo_only: q += " AND ativo=1"
    if tipo and tipo != "Todos": q += " AND tipo=%s"; p.append(tipo)
    if sistema and sistema != "Todos": q += " AND sistema=%s"; p.append(sistema)
    q += " ORDER BY tipo, tag"
    df = pd.read_sql_query(q, c, params=p); c.close(); return df

def buscar_equipamento_por_tag(tag):
    c = conn(); cur = c.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM equipamentos WHERE tag=%s AND ativo=1", (tag,))
    row = cur.fetchone(); cur.close(); c.close()
    return dict(row) if row else None

# ── SF6 ───────────────────────────────────────────────────────────────────
def salvar_sf6(d):
    c = conn(); cur = c.cursor()
    cur.execute("""INSERT INTO sf6_leituras
        (data,hora,turno,disjuntor,polo,pressao_medida,temperatura,pressao_corrigida,status_sf6,observacao,usuario)
        VALUES(%(data)s,%(hora)s,%(turno)s,%(disjuntor)s,%(polo)s,%(pressao_medida)s,%(temperatura)s,
               %(pressao_corrigida)s,%(status_sf6)s,%(observacao)s,%(usuario)s)""", d)
    c.commit(); cur.close(); c.close()

def carregar_sf6(disjuntor=None, data_ini=None, data_fim=None):
    c = conn(); q = "SELECT * FROM sf6_leituras WHERE 1=1"; p = []
    if disjuntor and disjuntor != "Todos": q += " AND disjuntor=%s"; p.append(disjuntor)
    if data_ini: q += " AND data>=%s"; p.append(str(data_ini))
    if data_fim: q += " AND data<=%s"; p.append(str(data_fim))
    q += " ORDER BY data DESC, hora DESC"
    df = pd.read_sql_query(q, c, params=p); c.close(); return df

# ── Temperaturas ──────────────────────────────────────────────────────────
def salvar_temp(d):
    c = conn(); cur = c.cursor()
    cur.execute("""INSERT INTO temperaturas
        (data,hora,turno,equipamento,ponto,temperatura,umidade,limite_max,status,observacao,usuario)
        VALUES(%(data)s,%(hora)s,%(turno)s,%(equipamento)s,%(ponto)s,%(temperatura)s,%(umidade)s,
               %(limite_max)s,%(status)s,%(observacao)s,%(usuario)s)""", d)
    c.commit(); cur.close(); c.close()

def carregar_temps(equipamento=None, data_ini=None, data_fim=None):
    c = conn(); q = "SELECT * FROM temperaturas WHERE 1=1"; p = []
    if equipamento and equipamento != "Todos": q += " AND equipamento=%s"; p.append(equipamento)
    if data_ini: q += " AND data>=%s"; p.append(str(data_ini))
    if data_fim: q += " AND data<=%s"; p.append(str(data_fim))
    q += " ORDER BY data DESC, hora DESC"
    df = pd.read_sql_query(q, c, params=p); c.close(); return df

# ── Operações DJ ──────────────────────────────────────────────────────────
def salvar_operacao(d):
    c = conn(); cur = c.cursor()
    cur.execute("""INSERT INTO operacoes_dj
        (data,disjuntor,tipo_operacao,motivo,num_operacoes_total,usuario)
        VALUES(%(data)s,%(disjuntor)s,%(tipo_operacao)s,%(motivo)s,%(num_operacoes_total)s,%(usuario)s)""", d)
    c.commit(); cur.close(); c.close()

def carregar_operacoes(disjuntor=None):
    c = conn(); q = "SELECT * FROM operacoes_dj WHERE 1=1"; p = []
    if disjuntor and disjuntor != "Todos": q += " AND disjuntor=%s"; p.append(disjuntor)
    q += " ORDER BY data DESC"
    df = pd.read_sql_query(q, c, params=p); c.close(); return df

# ── Inspeções ─────────────────────────────────────────────────────────────
def salvar_inspecao(d):
    c = conn(); cur = c.cursor()
    cur.execute("""INSERT INTO inspecoes
        (data,turno,sistema,item,status,observacao,usuario)
        VALUES(%(data)s,%(turno)s,%(sistema)s,%(item)s,%(status)s,%(observacao)s,%(usuario)s)""", d)
    c.commit(); cur.close(); c.close()

def carregar_inspecoes(sistema=None, data_ini=None, data_fim=None):
    c = conn(); q = "SELECT * FROM inspecoes WHERE 1=1"; p = []
    if sistema and sistema != "Todos": q += " AND sistema=%s"; p.append(sistema)
    if data_ini: q += " AND data>=%s"; p.append(str(data_ini))
    if data_fim: q += " AND data<=%s"; p.append(str(data_fim))
    q += " ORDER BY created_at DESC"
    df = pd.read_sql_query(q, c, params=p); c.close(); return df

# ── Pendências ────────────────────────────────────────────────────────────
def salvar_pendencia(d):
    c = conn(); cur = c.cursor()
    cur.execute("""INSERT INTO pendencias
        (data_abertura,sistema,descricao,nota_sap,prioridade,status,observacao,usuario)
        VALUES(%(data_abertura)s,%(sistema)s,%(descricao)s,%(nota_sap)s,%(prioridade)s,
               %(status)s,%(observacao)s,%(usuario)s)""", d)
    c.commit(); cur.close(); c.close()

def carregar_pendencias(status=None):
    c = conn(); q = "SELECT * FROM pendencias WHERE 1=1"; p = []
    if status and status != "Todos": q += " AND status=%s"; p.append(status)
    q += " ORDER BY created_at DESC"
    df = pd.read_sql_query(q, c, params=p); c.close(); return df

def atualizar_pendencia(id_, status, data_conclusao, obs):
    c = conn(); cur = c.cursor()
    cur.execute("UPDATE pendencias SET status=%s, data_conclusao=%s, observacao=%s WHERE id=%s",
                (status, data_conclusao, obs, id_))
    c.commit(); cur.close(); c.close()

# ── Troca de Turno ────────────────────────────────────────────────────────
def salvar_troca(d):
    c = conn(); cur = c.cursor()
    cur.execute("""INSERT INTO troca_turno
        (data,turno_saida,turno_entrada,sistema,ocorrencia,acao_tomada,pendente,usuario)
        VALUES(%(data)s,%(turno_saida)s,%(turno_entrada)s,%(sistema)s,%(ocorrencia)s,
               %(acao_tomada)s,%(pendente)s,%(usuario)s)""", d)
    c.commit(); cur.close(); c.close()

def carregar_trocas(limit=20):
    c = conn()
    df = pd.read_sql_query(f"SELECT * FROM troca_turno ORDER BY created_at DESC LIMIT {limit}", c)
    c.close(); return df

# ── Melhorias ─────────────────────────────────────────────────────────────
def salvar_melhoria(d):
    c = conn(); cur = c.cursor()
    cur.execute("""INSERT INTO melhorias (data,sistema,descricao,usuario)
        VALUES(%(data)s,%(sistema)s,%(descricao)s,%(usuario)s)""", d)
    c.commit(); cur.close(); c.close()

def carregar_melhorias():
    c = conn()
    df = pd.read_sql_query("SELECT * FROM melhorias ORDER BY created_at DESC", c)
    c.close(); return df

# ── Contadores de operações dos disjuntores ───────────────────────────────
def salvar_contador(d):
    c = conn(); cur = c.cursor()
    cur.execute("""INSERT INTO contadores_dj
        (data,hora,turno,disjuntor,polo_a,polo_b,polo_v,tripolar,curto_circuito,usuario)
        VALUES(%(data)s,%(hora)s,%(turno)s,%(disjuntor)s,%(polo_a)s,%(polo_b)s,%(polo_v)s,
               %(tripolar)s,%(curto_circuito)s,%(usuario)s)""", d)
    c.commit(); cur.close(); c.close()

def carregar_contadores(disjuntor=None, data_ini=None, data_fim=None):
    c = conn(); q = "SELECT * FROM contadores_dj WHERE 1=1"; p = []
    if disjuntor and disjuntor != "Todos": q += " AND disjuntor=%s"; p.append(disjuntor)
    if data_ini: q += " AND data>=%s"; p.append(str(data_ini))
    if data_fim: q += " AND data<=%s"; p.append(str(data_fim))
    q += " ORDER BY data DESC, hora DESC"
    df = pd.read_sql_query(q, c, params=p); c.close(); return df

# ── Configuração persistente do app ───────────────────────────────────────
def salvar_config(chave: str, valor: str):
    c = conn(); cur = c.cursor()
    cur.execute("""INSERT INTO config_app (chave, valor, updated_at)
        VALUES (%s, %s, NOW())
        ON CONFLICT (chave) DO UPDATE SET valor = EXCLUDED.valor, updated_at = NOW()""",
        (chave, valor))
    c.commit(); cur.close(); c.close()

def carregar_config(chave: str, padrao: str = None) -> str:
    try:
        c = conn(); cur = c.cursor()
        cur.execute("SELECT valor FROM config_app WHERE chave = %s", (chave,))
        row = cur.fetchone(); cur.close(); c.close()
        return row[0] if row else padrao
    except Exception:
        return padrao
