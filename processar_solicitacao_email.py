"""
Processa o pedido de envio do relatorio mensal feito pelo app web (PWA).

O botao "Solicitar Envio do Relatorio" do PWA grava em config_app a chave
email_solicitar_pwa com {"solicitado_em", "mes", "usuario"}. Este script le
esse pedido, gera o relatorio do mes (HTML + PDF anexo), envia para os
destinatarios cadastrados em email_config e grava o resultado na mesma chave
(status "enviado" ou "erro"), para o PWA mostrar e para nao reenviar.

Roda pelo GitHub Actions (.github/workflows/enviar_relatorio.yml).
Precisa da variavel de ambiente DATABASE_URL (secret do repositorio).

Teste local:  py -3.12 processar_solicitacao_email.py
Forcar envio de um mes sem pedido:  py -3.12 processar_solicitacao_email.py --mes 2026-10
"""
import os, sys, json, calendar
from datetime import date, datetime, timedelta, timezone

import pandas as pd

from database import (carregar_sf6, carregar_temps, carregar_pendencias,
                      carregar_inspecoes, carregar_equipamentos,
                      carregar_operacoes, carregar_contadores, carregar_fotos,
                      carregar_config, salvar_config)
from email_report import (gerar_html_relatorio, enviar_relatorio,
                          carregar_config_email, html_para_pdf)

CHAVE = "email_solicitar_pwa"
TZ_BR = timezone(timedelta(hours=-3))
MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho",
         "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]


def periodo_do_mes(mes_iso: str):
    """'2026-10' -> (date(2026,10,1), data_fim, 'Outubro/2026').
    data_fim = ultimo dia do mes, ou hoje se o mes ainda esta em curso."""
    ano, m = (int(x) for x in mes_iso.split("-"))
    d_ini = date(ano, m, 1)
    ult = date(ano, m, calendar.monthrange(ano, m)[1])
    hoje = datetime.now(TZ_BR).date()
    d_fim = min(ult, hoje)
    return d_ini, d_fim, f"{MESES[m - 1]}/{ano}"


def montar_dados(d_ini: date, d_fim: date, mes: str, operador: str) -> dict:
    df_sf6_r    = carregar_sf6(data_ini=d_ini, data_fim=d_fim)
    df_sf6_hist = carregar_sf6()
    df_t_r      = carregar_temps(data_ini=d_ini, data_fim=d_fim)
    df_p_r      = carregar_pendencias()
    df_i_r      = carregar_inspecoes(data_ini=d_ini, data_fim=d_fim)
    df_i_sec    = carregar_inspecoes(sistema="Seccionadora",  data_ini=d_ini, data_fim=d_fim)
    df_i_sf6vis = carregar_inspecoes(sistema="Disjuntor SF6", data_ini=d_ini, data_fim=d_fim)
    df_i_trafo  = carregar_inspecoes(sistema="Transformador", data_ini=d_ini, data_fim=d_fim)
    df_ops_r    = carregar_operacoes()
    df_secs     = carregar_equipamentos("Seccionadora")
    df_cnt_r    = carregar_contadores(data_ini=d_ini, data_fim=d_fim)

    print(f"  SF6: {len(df_sf6_r)} | Temp: {len(df_t_r)} | Insp: {len(df_i_r)} | "
          f"Secc: {len(df_i_sec)} | Contadores: {len(df_cnt_r)}")

    n_alarmes = len(df_sf6_r[df_sf6_r.status_sf6 != "NORMAL"]) if not df_sf6_r.empty else 0
    pend_ab   = len(df_p_r[df_p_r.status == "Aberta"]) if not df_p_r.empty else 0
    pend_conc = len(df_p_r[df_p_r.status == "Concluída"]) if not df_p_r.empty else 0

    sf6_tab = []
    if not df_sf6_r.empty:
        _ult = df_sf6_r.sort_values("created_at").groupby(["disjuntor", "polo"]).last().reset_index()
        sf6_tab = _ult.to_dict("records")

    sf6_visual = []
    if not df_i_sf6vis.empty:
        for _, r in df_i_sf6vis.sort_values("data").groupby("item").last().reset_index().iterrows():
            try:
                itens = json.loads(r.observacao.split(" | ")[0]) if r.observacao else {}
            except Exception:
                itens = {}
            sf6_visual.append({"disjuntor": r["item"], "status": r.status,
                               "data": r.data, "itens": itens})

    if not df_ops_r.empty:
        df_ops_p = df_ops_r[(df_ops_r.data >= str(d_ini)) & (df_ops_r.data <= str(d_fim))]
        ops_lista = df_ops_p.to_dict("records")
    else:
        ops_lista = []

    trafo_tab = (df_t_r.sort_values("data", ascending=False).head(15).to_dict("records")
                 if not df_t_r.empty else [])
    trafo_insp = {}
    if not df_i_trafo.empty:
        u = df_i_trafo.sort_values("data").iloc[-1]
        try:
            trafo_insp = json.loads(u.observacao) if u.observacao else {}
            trafo_insp["data"] = u.data
            trafo_insp["status"] = u.status
        except Exception:
            trafo_insp = {"data": u.data, "status": u.status}

    insp_complement = []
    for nome, tag in [("Para-raios 230kV", "PARA-RAIOS-230kV"),
                      ("Sala Elétrica da SE", "SALA-ELETRICA-SE"),
                      ("Cúbilo de 13.8kV", "CUBILO-13.8kV-SE")]:
        df_tag = df_i_r[df_i_r.item == tag] if not df_i_r.empty else pd.DataFrame()
        if not df_tag.empty:
            u = df_tag.sort_values("data").iloc[-1]
            try:
                dados_ic = json.loads(u.observacao) if u.observacao else {}
            except Exception:
                dados_ic = {}
            insp_complement.append({"nome": nome, "data": u.data, "status": u.status, "dados": dados_ic})
        else:
            insp_complement.append({"nome": nome, "data": "—", "status": "Sem registro", "dados": {}})

    nok_sec = df_i_sec[df_i_sec.status == "NOK"].to_dict("records") if not df_i_sec.empty else []
    todas_sec = []
    if not df_i_sec.empty:
        for _, r in df_i_sec.sort_values("data").groupby("item").last().reset_index().iterrows():
            todas_sec.append({"item": r["item"], "data": r.data, "status": r.status})

    fotos = []
    try:
        from PIL import Image, ImageOps
        import io, base64
        df_fotos = carregar_fotos(data_ini=str(d_ini), data_fim=str(d_fim))
        for _, fr in df_fotos.head(10).iterrows():
            if not fr.foto_base64:
                continue
            try:
                img = Image.open(io.BytesIO(base64.b64decode(fr.foto_base64)))
                img = ImageOps.exif_transpose(img).convert("RGB")
                buf = io.BytesIO(); img.save(buf, format="JPEG", quality=85)
                b64 = base64.b64encode(buf.getvalue()).decode()
            except Exception:
                b64 = fr.foto_base64
            fotos.append({"base64": b64, "legenda": fr.legenda or ""})
    except Exception as e:
        print(f"  Fotos nao carregadas: {e}")
    print(f"  Fotos: {len(fotos)}")

    return {
        "operador": operador,
        "nivel":    "SR",
        "mes":      mes,
        "sistemas": ["Subestação 230kV", "Sala Elétrica da SE", "Cúbilo de 13.8kV da SE"],
        "resumo": {
            "leituras_sf6":          len(df_sf6_r),
            "alarmes_sf6":           n_alarmes,
            "temp_registradas":      len(df_t_r),
            "inspecoes":             len(df_i_r),
            "pendencias_abertas":    pend_ab,
            "pendencias_concluidas": pend_conc,
        },
        "observacoes":     carregar_config("rel_obs_guardiao", ""),
        "acoes":           carregar_config("rel_acoes_destaque", ""),
        "img_sf6":         "",
        "img_temp":        "",
        "pendencias":      df_p_r[df_p_r.status != "Concluída"].to_dict("records") if not df_p_r.empty else [],
        "sf6_tabela":      sf6_tab,
        "sf6_visual":      sf6_visual,
        "operacoes":       ops_lista,
        "sec_resumo": {
            "total":         len(df_secs) if not df_secs.empty else 27,
            "inspecionadas": len(df_i_sec["item"].unique()) if not df_i_sec.empty else 0,
            "nok":           nok_sec,
            "todas":         todas_sec,
        },
        "trafo_tabela":    trafo_tab,
        "trafo_insp":      trafo_insp,
        "insp_complement": insp_complement,
        "contadores":      df_cnt_r.to_dict("records") if not df_cnt_r.empty else [],
        "fotos":           fotos,
        "sf6_historico":   df_sf6_hist.to_dict("records") if not df_sf6_hist.empty else [],
    }


def enviar_mes(mes_iso: str, operador: str) -> tuple:
    d_ini, d_fim, mes = periodo_do_mes(mes_iso)
    print(f"Relatorio {mes} ({d_ini} a {d_fim})")

    cfg = carregar_config_email()
    if not cfg.get("email_remetente") or not cfg.get("senha_app"):
        return False, "E-mail remetente ou senha de app nao configurados (aba Configurar E-mail do app Streamlit)."
    if not cfg.get("destinatarios"):
        return False, "Nenhum destinatario cadastrado em email_config."

    dados = montar_dados(d_ini, d_fim, mes, operador)
    html = gerar_html_relatorio(dados, usar_cid=bool(dados["fotos"]))

    anexos = []
    try:
        pdf = html_para_pdf(dados)
        if pdf:
            anexos.append((f"Relatorio_Guardiao_{mes.replace('/', '_')}.pdf", pdf))
            print(f"  PDF gerado ({len(pdf)//1024} kB)")
    except Exception as e:
        print(f"  PDF nao gerado: {e}")

    assunto = f"Relatorio Guardiao da Usina — {mes} | {operador}"
    ok, msg = enviar_relatorio(cfg, html, assunto,
                               fotos=dados["fotos"] or None,
                               anexos=anexos or None)
    if ok:
        salvar_config("relatorio_enviado_mes", mes)
        salvar_config("relatorio_enviado_em", str(datetime.now(TZ_BR).date()))
        if not anexos:
            msg += " (sem PDF anexo: falha ao gerar o PDF)"
    return ok, msg


def main():
    if not os.environ.get("DATABASE_URL"):
        print("ERRO: variavel DATABASE_URL nao definida.")
        sys.exit(1)

    if "--mes" in sys.argv:
        mes_iso = sys.argv[sys.argv.index("--mes") + 1]
        ok, msg = enviar_mes(mes_iso, "Jose Aparecido")
        print(("OK: " if ok else "ERRO: ") + msg)
        sys.exit(0 if ok else 1)

    bruto = carregar_config(CHAVE)
    if not bruto:
        print("Nenhum pedido de envio.")
        return
    try:
        pedido = json.loads(bruto)
    except Exception:
        print(f"Pedido invalido: {bruto!r}")
        return
    if pedido.get("status") in ("enviado", "erro"):
        print(f"Ultimo pedido ja processado ({pedido.get('status')} em {pedido.get('processado_em')}).")
        return

    mes_iso = pedido.get("mes") or datetime.now(TZ_BR).strftime("%Y-%m")
    operador = pedido.get("usuario") or "Jose Aparecido"
    print(f"Pedido de {operador} em {pedido.get('solicitado_em')} para {mes_iso}")

    try:
        ok, msg = enviar_mes(mes_iso, operador)
    except Exception as e:
        ok, msg = False, f"Erro ao gerar/enviar: {e}"

    pedido.update({
        "status": "enviado" if ok else "erro",
        "mensagem": msg,
        "processado_em": datetime.now(TZ_BR).isoformat(timespec="seconds"),
    })
    salvar_config(CHAVE, json.dumps(pedido, ensure_ascii=False))
    print(("OK: " if ok else "ERRO: ") + msg)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
