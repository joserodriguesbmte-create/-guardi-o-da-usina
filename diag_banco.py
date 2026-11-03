"""Diagnostico rapido do banco para o vigia (so imprime, nao altera dados do app)."""
import json, re, urllib.request, os
from database import carregar_config, conn

html = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "index.html"), encoding="utf-8").read()
URL = re.search(r'const SUPA_URL = "([^"]+)"', html).group(1)
KEY = re.search(r'const SUPA_KEY = "([^"]+)"', html).group(1)

def chamar(metodo, caminho, corpo=None, extra=None):
    h = {"apikey": KEY, "Authorization": "Bearer " + KEY, "Content-Type": "application/json"}
    h.update(extra or {})
    req = urllib.request.Request(URL + caminho, data=json.dumps(corpo).encode() if corpo is not None else None,
                                 headers=h, method=metodo)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, r.read().decode()[:200]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]

print("== Banco direto (senha do banco) ==")
try:
    c = conn(); cur = c.cursor(); cur.execute("SELECT chave, LEFT(valor,150), updated_at FROM config_app WHERE chave LIKE 'email%' OR chave LIKE 'diag%'")
    for r in cur.fetchall(): print("  ", r)
    cur.close(); c.close()
except Exception as e:
    print("  ERRO banco direto:", e)

print("== Como o app (chave publica) ==")
print("  ler pedido:", chamar("GET", "/config_app?chave=eq.email_solicitar_pwa&select=valor"))
print("  gravar (upsert) teste:", chamar("POST", "/config_app?on_conflict=chave",
      {"chave": "diag_upsert", "valor": "teste"},
      {"Prefer": "resolution=merge-duplicates,return=minimal"}))
print("  gravar (insert) teste:", chamar("POST", "/config_app", {"chave": "diag_insert", "valor": "teste"},
      {"Prefer": "return=minimal"}))
print("  atualizar (patch) pedido:", chamar("PATCH", "/config_app?chave=eq.diag_upsert", {"valor": "teste2"},
      {"Prefer": "return=representation"}))

