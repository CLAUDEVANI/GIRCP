from pathlib import Path

p = Path("app_relatorio.py")
s = p.read_text(encoding="utf-8")

def sub(old, new):
    global s
    assert s.count(old) == 1, "trecho nao encontrado (ou repetido): " + old[:70]
    s = s.replace(old, new)

BLOCO = '''# ══════════════════════════════════════════════════════════════════════════
# ESTATÍSTICAS GERAIS (fonte única: uma linha por evidência)
# ══════════════════════════════════════════════════════════════════════════
_PRAZOS_ORD = ["Imediato (0–24h)", "Urgente (até 7 dias)", "Planejado (até 30 dias)", "Monitorar"]
_ORDEM_PRAZO = {p: i for i, p in enumerate(_PRAZOS_ORD)}

def _txt_ou(v, padrao):
    return padrao if (v is None or pd.isna(v) or not str(v).strip()) else str(v).strip()

def _card_kpi(valor, rotulo, cor=None):
    estilo = f' style="color:{cor};"' if cor else ""
    return f'<div class="eng-metric"><div class="eng-metric-val"{estilo}>{valor}</div><div class="eng-metric-label">{rotulo}</div></div>'

def _montar_evidencias(df):
    """Uma linha por evidência fotográfica. Todas as estatísticas partem daqui (evita contagens divergentes)."""
    cols = ["laudo_id", "site_id", "tecnico", "data", "status_laudo", "titulo", "severidade",
            "categoria", "prazo", "n_materiais", "mat_sem_custo", "custo"]
    linhas = []
    for _, r in df.iterrows():
        try:
            fotos = json.loads(r.get("fotos_json") or "[]")
        except (ValueError, TypeError):
            fotos = []
        for f in fotos:
            n_mat, sem_custo, custo = 0, 0, 0.0
            for m in (f.get("materiais") or []):
                if not str(m.get("descricao", "")).strip():
                    continue
                try:
                    q = float(m.get("quantidade", 1))
                    cu = float(m.get("custo_unit", 0.0))
                except (ValueError, TypeError):
                    q, cu = 1.0, 0.0
                n_mat += 1
                custo += q * cu
                if cu == 0:
                    sem_custo += 1
            linhas.append({
                "laudo_id": r.get("id"),
                "site_id": _txt_ou(r.get("site_id"), "—"),
                "tecnico": _txt_ou(r.get("tecnico"), _txt_ou(r.get("contato"), "—")),
                "data": r.get("data_formatada"),
                "status_laudo": _txt_ou(r.get("status_laudo"), "Não informado"),
                "titulo": f.get("titulo", "—"),
                "severidade": normalizar_sev(f.get("severidade", "Normal")),
                "categoria": f.get("categoria", "Geral"),
                "prazo": f.get("prazo_correcao", "Monitorar"),
                "n_materiais": n_mat,
                "mat_sem_custo": sem_custo,
                "custo": custo,
            })
    return pd.DataFrame(linhas, columns=cols)

def _render_estatisticas(df_f):
    df_ev = _montar_evidencias(df_f)
    n_laudos = len(df_f)
    n_ev = len(df_ev)
    n_crit = int((df_ev["severidade"] == "Critico").sum())
    taxa_crit = (n_crit / n_ev * 100) if n_ev else 0.0
    media_ev = (n_ev / n_laudos) if n_laudos else 0.0
    n_urg = int(df_ev["prazo"].isin(_PRAZOS_ORD[:2]).sum())
    custo_total = float(df_ev["custo"].sum())
    n_sem_ev = int((df_f["qtd_fotos"] == 0).sum()) if "qtd_fotos" in df_f.columns else 0

    secao("📐", "ESTATÍSTICAS GERAIS")
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.markdown(_card_kpi(f"{taxa_crit:.1f}%", "TAXA DE CRITICIDADE", COR_VERMELHO if n_crit else None), unsafe_allow_html=True)
    k2.markdown(_card_kpi(f"{media_ev:.1f}", "MÉDIA EVID. / LAUDO"), unsafe_allow_html=True)
    k3.markdown(_card_kpi(n_urg, "SLA IMEDIATO + URGENTE", "#ea580c" if n_urg else None), unsafe_allow_html=True)
    k4.markdown(_card_kpi(f"R$ {custo_total:,.2f}", "CUSTO ESTIMADO", COR_AZUL), unsafe_allow_html=True)
    k5.markdown(_card_kpi(n_sem_ev, "LAUDOS SEM EVIDÊNCIA", COR_AMARELO if n_sem_ev else None), unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    t_tec, t_site, t_cat, t_status, t_qual = st.tabs(
        ["👷 Por técnico", "📍 Por site (risco)", "🖼️ Antes / Depois", "📋 Status dos laudos", "🧹 Qualidade dos dados"])

    with t_tec:
        if df_ev.empty:
            st.info("Sem evidências para o filtro atual.")
        else:
            laudos_tec = df_f.apply(lambda r: _txt_ou(r.get("tecnico"), _txt_ou(r.get("contato"), "—")), axis=1).value_counts().rename("Laudos").rename_axis("tecnico")
            evid = df_ev.groupby("tecnico").agg(
                Evidencias=("titulo", "size"),
                Criticas=("severidade", lambda x: int((x == "Critico").sum())),
                Custo=("custo", "sum"))
            tab = laudos_tec.to_frame().join(evid, how="left").fillna(0).reset_index()
            tab["Evidencias"] = tab["Evidencias"].astype(int)
            tab["Criticas"] = tab["Criticas"].astype(int)
            tab["pct"] = (tab["Criticas"] / tab["Evidencias"].where(tab["Evidencias"] > 0) * 100).fillna(0).round(1)
            tab["media"] = (tab["Evidencias"] / tab["Laudos"].where(tab["Laudos"] > 0)).fillna(0).round(1)
            tab = tab.rename(columns={"tecnico": "Técnico", "Evidencias": "Evidências", "Criticas": "Críticas",
                                      "pct": "% Críticas", "media": "Média evid./laudo", "Custo": "Custo est. (R$)"})
            st.dataframe(tab, use_container_width=True, hide_index=True)
            df_sev = df_ev.groupby(["tecnico", "severidade"]).size().reset_index(name="Quantidade")
            fig = px.bar(df_sev, x="tecnico", y="Quantidade", color="severidade", barmode="stack",
                         color_discrete_map={"Critico": COR_VERMELHO, "Observacao": COR_AMARELO, "Normal": COR_VERDE},
                         labels={"tecnico": "Técnico", "severidade": "Severidade"})
            fig.update_layout(margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig, use_container_width=True)

    with t_site:
        if df_ev.empty:
            st.info("Sem evidências para o filtro atual.")
        else:
            agg = df_ev.groupby("site_id").agg(
                Evidencias=("titulo", "size"),
                Criticas=("severidade", lambda x: int((x == "Critico").sum())),
                Observacoes=("severidade", lambda x: int((x == "Observacao").sum())),
                Imediato=("prazo", lambda x: int((x == _PRAZOS_ORD[0]).sum())),
                Custo=("custo", "sum"))
            laudos_site = df_f["site_id"].map(lambda v: _txt_ou(v, "—")).value_counts().rename("Laudos").rename_axis("site_id")
            tab = laudos_site.to_frame().join(agg, how="left").fillna(0).reset_index()
            for c in ["Evidencias", "Criticas", "Observacoes", "Imediato"]:
                tab[c] = tab[c].astype(int)
            tab = tab.sort_values(["Criticas", "Imediato", "Evidencias"], ascending=False).head(15)
            tab = tab.rename(columns={"site_id": "Site", "Evidencias": "Evidências", "Criticas": "Críticas",
                                      "Observacoes": "Observações", "Imediato": "SLA imediato", "Custo": "Custo est. (R$)"})
            st.caption("Top 15 sites por nº de evidências críticas, depois SLA imediato.")
            st.dataframe(tab, use_container_width=True, hide_index=True)

    with t_cat:
        if df_ev.empty:
            st.info("Sem evidências para o filtro atual.")
        else:
            cat = df_ev["categoria"].value_counts().rename_axis("Categoria").reset_index(name="Evidências")
            st.dataframe(cat, use_container_width=True, hide_index=True)
            s_antes = set(df_ev.loc[df_ev["categoria"] == "Antes", "site_id"])
            s_depois = set(df_ev.loc[df_ev["categoria"] == "Depois", "site_id"])
            pend = sorted(s_antes - s_depois, key=str)
            a1, a2, a3 = st.columns(3)
            a1.markdown(_card_kpi(len(s_antes), 'SITES COM "ANTES"'), unsafe_allow_html=True)
            a2.markdown(_card_kpi(len(s_depois), 'SITES COM "DEPOIS"'), unsafe_allow_html=True)
            a3.markdown(_card_kpi(len(pend), '"ANTES" SEM "DEPOIS"', COR_AMARELO if pend else None), unsafe_allow_html=True)
            st.caption("Indicador aproximado de correções sem comprovação fotográfica: o app ainda não registra o fechamento de cada pendência.")
            if pend:
                st.caption("Sites: " + ", ".join(str(x) for x in pend[:30]))

    with t_status:
        st_ser = df_f["status_laudo"].map(lambda v: _txt_ou(v, "Não informado")) if "status_laudo" in df_f.columns else None
        if st_ser is None or st_ser.empty:
            st.info("Sem dados de status.")
        else:
            tab = st_ser.value_counts().rename_axis("Status").reset_index(name="Laudos")
            tab["%"] = (tab["Laudos"] / tab["Laudos"].sum() * 100).round(1)
            st.dataframe(tab, use_container_width=True, hide_index=True)
'''  # <- O FECHO DA STRING ESTAVA EM FALTA AQUI

# ══════════════════════════════════════════════════════════════════════════
# EXECUÇÃO DA SUBSTITUIÇÃO (Exemplo)
# Para o script funcionar, precisa de invocar a função 'sub' indicando o
# código antigo que quer substituir, e depois gravar o ficheiro.
# ══════════════════════════════════════════════════════════════════════════

# TRECHO_ANTIGO = '''Cole aqui exatamente a parte de código do app_relatorio.py que deseja substituir'''
# sub(TRECHO_ANTIGO, BLOCO)
#
# Gravar as alterações de volta no ficheiro
# p.write_text(s, encoding="utf-8")
# print("Substituição concluída com sucesso!")

