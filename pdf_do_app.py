"""
Gera o PDF do relatorio mensal usando o proprio app web (docs/index.html),
do mesmo jeito que o botao "Imprimir / Salvar PDF" do celular.
Assim o PDF do e-mail fica igual ao do app.

Uso pelo processar_solicitacao_email.py:
    from pdf_do_app import gerar_pdf_app
    pdf_bytes = gerar_pdf_app("2026-10", operador="Jose Aparecido", obs="...", acoes="...")

Teste local:  python pdf_do_app.py 2026-10   (gera Relatorio_teste.pdf)
Precisa de: pip install playwright  e  python -m playwright install --with-deps chromium
"""
import calendar, functools, http.server, json, os, socketserver, sys, threading
from datetime import date, datetime, timedelta, timezone

DOCS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")
TZ_BR = timezone(timedelta(hours=-3))


def _servidor_local():
    """Serve a pasta docs/ numa porta livre e devolve (servidor, url)."""
    class Silencioso(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    handler = functools.partial(Silencioso, directory=DOCS)
    srv = socketserver.TCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}/index.html"


def _momento_do_relatorio(mes_iso: str) -> datetime:
    """Mes atual: agora. Mes que ja passou: ultimo dia desse mes, 18h.
    O app busca os dados pela data do relogio, por isso o relogio e ajustado."""
    ano, m = (int(x) for x in mes_iso.split("-"))
    agora = datetime.now(TZ_BR)
    if (ano, m) == (agora.year, agora.month):
        return agora
    return datetime(ano, m, calendar.monthrange(ano, m)[1], 18, 0, tzinfo=TZ_BR)


def gerar_pdf_app(mes_iso: str, operador: str = "Jose Aparecido",
                  obs: str = "", acoes: str = "", turno: str = "Manha") -> bytes:
    from playwright.sync_api import sync_playwright

    momento = _momento_do_relatorio(mes_iso)
    data_ref = momento.strftime("%Y-%m-%d")
    gerado_em = datetime.now(TZ_BR).strftime("%d/%m/%Y, %H:%M")
    hoje_br = datetime.now(TZ_BR).strftime("%d/%m/%Y")

    srv, url = _servidor_local()
    try:
        with sync_playwright() as p:
            nav = p.chromium.launch()
            ctx = nav.new_context(viewport={"width": 1280, "height": 900},
                                  service_workers="block", locale="pt-BR",
                                  timezone_id="America/Sao_Paulo")
            erros = []
            pag = ctx.new_page()
            pag.on("pageerror", lambda e: erros.append(str(e)))
            pag.on("console", lambda m: erros.append(m.text) if m.type in ("error", "warning") else None)
            pag.on("requestfailed", lambda r: erros.append(f"falha {r.url[:80]}: {r.failure}"))
            pag.clock.set_fixed_time(momento)

            # Entra como se o operador tivesse feito login no app
            sessao = {"usuario": operador, "turno": turno, "data": data_ref}
            pag.add_init_script(
                "sessionStorage.setItem('gd_user', %s);"
                "localStorage.setItem('gd_sessao', %s);"
                "localStorage.removeItem('gd_cache');"
                % (json.dumps(operador), json.dumps(json.dumps(sessao))))

            pag.goto(url, wait_until="networkidle")
            pag.wait_for_function("typeof pullData==='function' && typeof Chart!=='undefined'", timeout=30000)

            # Busca os dados no banco, monta o relatorio e espera os graficos
            # Busca os dados direto (sem depender do aviso de online do navegador)
            diag = pag.evaluate("""async () => {
                try {
                    const r = await supaGet('config_app', {select: 'chave', limit: '1'});
                    return 'ok';
                } catch (e) { return 'teste do banco falhou: ' + e.message; }
            }""")
            if diag != "ok":
                raise RuntimeError(diag + " | " + "; ".join(erros[:5]))
            pag.evaluate("async () => { await pullData(); }")
            if not pag.evaluate("!!getCache().lastSync"):
                raise RuntimeError("dados do mes nao carregaram | " + "; ".join(erros[:5]))
            pag.evaluate("showPage('rel')")
            pag.wait_for_timeout(1500)

            # Observacoes vindas do banco; textarea vira texto (nao corta na folha)
            pag.evaluate("""([obs, acoes, gerado, hojeBr]) => {
                [['relObs', obs], ['relAcoes', acoes]].forEach(([id, txt]) => {
                    const ta = document.getElementById(id);
                    if (!ta) return;
                    const div = document.createElement('div');
                    div.textContent = txt || 'Sem registros.';
                    div.style.cssText = 'white-space:pre-wrap;border:1px solid #ccc;padding:6px;min-height:40px;font-size:0.82rem;color:#000;margin-bottom:6px';
                    ta.replaceWith(div);
                });
                const g = document.getElementById('capaDataGer'); if (g) g.textContent = gerado;
                const a = document.getElementById('assinaturaData'); if (a) a.textContent = hojeBr;
                _prepararGraficosPrint();
            }""", [obs or "", acoes or "", gerado_em, hoje_br])
            pag.wait_for_timeout(500)

            pag.emulate_media(media="print")
            pdf = pag.pdf(format="A4", print_background=True, prefer_css_page_size=True)
            nav.close()
            if erros:
                print("  Avisos do app:", "; ".join(erros[:3]))
            return pdf
    finally:
        srv.shutdown()


if __name__ == "__main__":
    mes = sys.argv[1] if len(sys.argv) > 1 else datetime.now(TZ_BR).strftime("%Y-%m")
    with open("Relatorio_teste.pdf", "wb") as f:
        f.write(gerar_pdf_app(mes))
    print("Relatorio_teste.pdf gerado")
