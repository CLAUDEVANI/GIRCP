"""Rede de protecao do GIRCP. Roda o app inteiro (AppTest) sobre um banco SINTETICO e em pasta temporaria
(nao toca no seu .db, nas fotos nem no secrets.toml).

uso (na pasta do projeto):
  python tests/gircp_testes.py salvar      grava a linha de base (rode ANTES de refatorar)
  python tests/gircp_testes.py comparar    compara todas as telas com a linha de base
  python tests/gircp_testes.py corrompido  laudo com JSON quebrado nao pode derrubar nenhuma tela
  python tests/gircp_testes.py seguranca   login, busca, padroes e geocodificacao (apos a Fase 2)
"""
import ast, json, os, re, shutil, sqlite3, sys, tempfile, time, types
from streamlit.testing.v1 import AppTest

APP = "app_relatorio.py"
BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "baseline.json")
MENUS = {"novo": "📝 NOVO RELATÓRIO", "pesquisa": "🔍 PESQUISAR E EXPORTAR", "dashboard": "📊 DASHBOARD",
         "rota": "🗺️ ROTEIRIZAÇÃO TÁTICA", "sla": "📺 PAINEL SLA"}

def _copia_isolada(app_path):
    pasta = tempfile.mkdtemp(prefix="gircp_teste_")
    src = open(app_path, encoding="utf-8").read()
    src = re.sub(r'^DB_NAME = ".*"$', f'DB_NAME = r"{pasta}/t.db"', src, flags=re.M)
    src = re.sub(r'^FOTOS_DIR = ".*"$', f'FOTOS_DIR = r"{pasta}/fotos"', src, flags=re.M)
    destino = os.path.join(pasta, "app.py")
    open(destino, "w", encoding="utf-8").write(src)
    return pasta, destino

def _ev(titulo, sev, prazo, cat="Geral", mats=None, desc=""):
    return {"titulo": titulo, "severidade": sev, "prazo_correcao": prazo, "categoria": cat,
            "comentarios": desc, "materiais": mats or [], "arquivo": "x.jpg"}

def semear(db):
    IM, UR, PL, MO = "Imediato (0–24h)", "Urgente (até 7 dias)", "Planejado (até 30 dias)", "Monitorar"
    mat = lambda d, q, c: {"descricao": d, "unidade": "un", "quantidade": q, "custo_unit": c}
    L = [
      ("SMGRSA7", "Tecnico A CRT: 111.111.xxx.xx", None, "05/09/2026 10:00", -23.50, -46.81, "✅ Aprovado",
       [_ev("Evidência 1", "Normal", PL, "Antes", [mat("cabo", 10, 5.0), mat("borne", 2, 0)], "N/A")]),
      ("SMMAU12", "Tecnico A Sobrenome CRT: 111.222.xxx.xx", None, "08/09/2026 13:53", -23.51, -46.82, "⚠️ Aprovado com Ressalvas",
       [_ev("VISOR", "Normal", MO, "Antes"), _ev("POSTE", "Crítico", IM, "Depois", [mat("poste", 1, 1500.0)], "risco de queda"),
        _ev("QM", "Observação", UR, "Geral", [mat("disjuntor", 3, 40.0)], "sem proteção")]),
      ("SMIPI28", None, "João da Silva", "10/09/2026 09:00", 0.0, 0.0, None, [_ev("Cabo exposto", "Observação", UR, "Antes")]),
      ("SMVMR31", "TESTE2026", None, "11/09/2026 09:00", -23.4, -46.7, "🔄 Em Acompanhamento", [_ev("Teste", "Crítico", IM, "Geral")]),
      ("SMPB09", "Tecnico A", None, "12/09/2026 09:00", None, None, "❌ Reprovado", []),
      ("SMXXX", "Fulano", None, "data invalida", -23.3, -46.6, None, [_ev("Prazo estranho", "Normal", "Outro", "Geral")]),
    ]
    con = sqlite3.connect(db)
    for i, (site, tec, contato, dh, lat, lon, st_, fotos) in enumerate(L, 1):
        con.execute("INSERT INTO relatorios (titulo, contato, empresa, telefone, email, site_id, endereco, data_hora, fotos_json, extras_json, tecnico, latitude, longitude, status_laudo) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (f"T{i}", contato, "EMP", "000", "a@b.c", site, "Rua X", dh, json.dumps(fotos), json.dumps([{"nome": "a.pdf"}] if i == 2 else []), tec, lat, lon, st_))
    if os.environ.get("GIRCP_TESTE_CORROMPIDO") == "1":
        con.execute("INSERT INTO relatorios (titulo, site_id, data_hora, fotos_json, extras_json, tecnico) VALUES ('X','SMBAD','13/09/2026 09:00','JSON_QUEBRADO','nao_json','Fulano')")
    con.commit(); con.close()

def _normaliza(txt):
    txt = re.sub(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}(?!:)", "<DATAHORA>", str(txt))
    return re.sub(r"\s+", " ", txt).strip()

def retrato(at):
    r = {"excecoes": [str(e.value)[:200] for e in at.exception], "erros": [e.value for e in at.error]}
    r["markdown"] = [_normaliza(m.value) for m in at.markdown]
    r["caption"] = [_normaliza(c.value) for c in at.caption]
    r["info"] = [i.value for i in at.info] + [s.value for s in at.success] + [w.value for w in at.warning]
    r["dataframes"] = [json.loads(d.value.to_json(orient="records", date_format="iso", default_handler=str)) for d in at.dataframe]
    r["metricas"] = [(m.label, m.value) for m in at.metric]
    r["botoes"] = [b.label for b in at.button]
    r["checkbox"] = [(c.label, c.value) for c in at.checkbox]
    r["radio"] = [(w.label, w.value) for w in at.radio]
    r["multiselect"] = [(w.label, list(w.options)) for w in at.multiselect]
    r["expanders"] = [e.label for e in at.expander]
    r["abas"] = [t.label for t in at.tabs]
    r["graficos"] = len(at.get("plotly_chart")) + len(at.get("deck_gl_json_chart"))
    return r

def _nova(app, secrets=None):
    at = AppTest.from_file(app, default_timeout=90)
    if secrets is None:
        at.session_state["password_correct"] = True
    else:
        for k, v in secrets.items():
            at.secrets[k] = v
    return at

def executar(app_path=APP):
    pasta, app = _copia_isolada(app_path)
    cwd = os.getcwd()
    os.chdir(pasta)            # isola do .streamlit/secrets.toml real (selo de integridade, senhas)
    try:
        _nova(app).run()       # inicializa o banco
        semear(f"{pasta}/t.db")
        saida = {}
        for t in ("dashboard", "sla", "pesquisa", "rota", "novo"):
            at = _nova(app).run()
            at.sidebar.radio[0].set_value(MENUS[t]).run()
            saida[t] = retrato(at)
        at = _nova(app)
        at.secrets["padroes"] = {"rota_partida": "-23.5051209,-46.8109935"}
        at = at.run()
        at.sidebar.radio[0].set_value(MENUS["rota"]).run()
        sites = list(at.multiselect[0].options)
        if sites:
            at.multiselect[0].set_value(sites[:3]).run()
            for b in at.button:
                if "Otimizar" in b.label:
                    b.click().run()
                    break
        saida["rota_otimizada"] = retrato(at)
        return saida
    finally:
        os.chdir(cwd)
        shutil.rmtree(pasta, ignore_errors=True)

def diferencas(a, b):
    n = 0
    for tela in sorted(set(a) | set(b)):
        for k in sorted(set(a.get(tela, {})) | set(b.get(tela, {}))):
            x, y = a.get(tela, {}).get(k), b.get(tela, {}).get(k)
            if x != y:
                n += 1
                print(f"  DIFERENTE  {tela}.{k}")
                if isinstance(x, list) and isinstance(y, list):
                    for i in range(max(len(x), len(y))):
                        p = x[i] if i < len(x) else "<ausente>"
                        q = y[i] if i < len(y) else "<ausente>"
                        if p != q:
                            print("     antes :", str(p)[:200]); print("     depois:", str(q)[:200]); break
    return n

def modo_corrompido():
    os.environ["GIRCP_TESTE_CORROMPIDO"] = "1"
    r = executar()
    ruins = {t: v["excecoes"][0] for t, v in r.items() if v["excecoes"]}
    for t in r:
        print(("FALHOU  " if t in ruins else "PASSOU  ") + f"tela '{t}' com laudo corrompido" + (f"  [{ruins[t][:80]}]" if t in ruins else ""))
    return not ruins

def modo_seguranca():
    ok = [True]
    def check(nome, cond, extra=""):
        ok[0] &= bool(cond)
        print(("PASSOU  " if cond else "FALHOU  ") + nome + (f"  [{extra}]" if extra else ""))
    cwd = os.getcwd()
    pasta, app = _copia_isolada(APP)
    os.chdir(pasta)
    SEG = {"usuarios": {"ana": {"senha": "certa123", "perfil": "tecnico", "nome": "Ana"}}, "senha_acesso": "geral"}
    def tentar(at, usuario, senha):
        at.text_input(key="usuario_input").set_value(usuario)
        at.text_input(key="password_input").set_value(senha).run()
        return at
    try:
        at = _nova(app, SEG).run()
        for i in range(5):
            at = tentar(at, "ana", f"errada{i}")
        msg = " ".join(e.value for e in at.error)
        check("5 falhas -> bloqueio", "bloqueado" in msg.lower(), msg[:60])
        con = sqlite3.connect(f"{pasta}/t.db")
        nf = con.execute("SELECT COUNT(*) FROM audit_log WHERE acao='login_falha'").fetchone()[0]
        con.close()
        check("falhas de login gravadas na auditoria", nf == 5, f"{nf}")
        at2 = tentar(_nova(app, SEG).run(), "ana", "certa123")
        check("recarregar a pagina NAO zera o bloqueio (senha certa recusada)", not at2.session_state["password_correct"])
        at3 = tentar(_nova(app, SEG).run(), "outro", "x")
        check("bloqueio e por usuario", "bloqueado" not in " ".join(e.value for e in at3.error).lower())
    finally:
        os.chdir(cwd); shutil.rmtree(pasta, ignore_errors=True)

    pasta, app = _copia_isolada(APP)
    os.chdir(pasta)
    try:
        at = tentar(_nova(app, SEG).run(), "ana", "certa123")
        con = sqlite3.connect(f"{pasta}/t.db"); suc = con.execute("SELECT COUNT(*) FROM audit_log WHERE acao='login_sucesso'").fetchone()[0]; con.close()
        check("primeiro login (banco ainda inexistente) funciona e audita", at.session_state["password_correct"] is True and suc == 1)
    finally:
        os.chdir(cwd); shutil.rmtree(pasta, ignore_errors=True)

    pasta, app = _copia_isolada(APP)
    os.chdir(pasta)
    try:
        _nova(app).run(); semear(f"{pasta}/t.db")
        def achados(termo):
            a = _nova(app).run(); a.sidebar.radio[0].set_value(MENUS["pesquisa"]).run(); a.text_input[0].set_value(termo).run()
            for m in a.markdown:
                r = re.search(r'eng-metric-val">(\d+)</div><div class="eng-metric-label">RESULTADOS', m.value)
                if r: return int(r.group(1))
            return 0
        check("busca 'SMMAU' acha 1", achados("SMMAU") == 1)
        check("busca '_' e '%' sao literais (nao casam tudo)", achados("_") == 0 and achados("%") == 0)
        def campos(com):
            a = _nova(app)
            if com: a.secrets["padroes"] = {"contato": "Fulano de Tal", "telefone": "1100000000"}
            a.session_state["password_correct"] = True; a.run()
            return {t.key: t.value for t in a.text_input if t.key and t.key.startswith("novo_")}
        sem, com = campos(False), campos(True)
        check("sem [padroes] o cadastro nao traz dado pessoal", all(sem.get(k, "") == "" for k in ("novo_contato", "novo_telefone", "novo_email", "novo_art_rrt")))
        check("com [padroes] os padroes sao aplicados", com.get("novo_contato") == "Fulano de Tal" and com.get("novo_tecnico") == "Fulano de Tal")
    finally:
        os.chdir(cwd); shutil.rmtree(pasta, ignore_errors=True)

    src = open(APP, encoding="utf-8").read()
    partes = [ast.get_source_segment(src, n) for n in ast.parse(src).body
              if (isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") in ("_GEO_CACHE", "_GEO_ULTIMA"))
              or (isinstance(n, ast.FunctionDef) and n.name == "geocodificar_endereco")]
    cham = {"n": 0, "resp": "ok"}
    class R:
        def raise_for_status(self): pass
        def json(self): return [{"lat": "-23.5", "lon": "-46.8"}] if cham["resp"] == "ok" else []
    fake = types.SimpleNamespace(get=lambda *a, **k: (cham.__setitem__("n", cham["n"] + 1), R())[1])
    ns = {"requests": fake}; exec("\n".join(partes), ns)
    g = ns["geocodificar_endereco"]
    a1, a2 = g("Rua A, 1"), g("  rua a,   1 ")
    check("geocodificacao: repetida sai do cache", a1 == a2 and cham["n"] == 1, f"chamadas={cham['n']}")
    cham["resp"] = "vazio"; r1 = g("Rua B, 2"); cham["resp"] = "ok"; r2 = g("Rua B, 2")
    check("geocodificacao: falha nao fica em cache", r1 is None and r2 == (-23.5, -46.8))
    t0 = time.time(); g("Rua C, 3"); g("Rua D, 4")
    check("geocodificacao: intervalo minimo de ~1 s", time.time() - t0 >= 1.0)
    return ok[0]

def main():
    modo = sys.argv[1] if len(sys.argv) > 1 else "comparar"
    if modo == "salvar":
        json.dump(executar(), open(BASE, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
        print("linha de base gravada em", BASE); return 0
    if modo == "comparar":
        if not os.path.exists(BASE):
            print("ERRO: rode antes  python tests/gircp_testes.py salvar"); return 2
        n = diferencas(json.load(open(BASE, encoding="utf-8")), json.loads(json.dumps(executar(), default=str)))
        print("IDENTICO a linha de base em todas as telas" if n == 0 else f"{n} diferenca(s) em relacao a linha de base")
        return 0 if n == 0 else 1
    if modo == "corrompido":
        return 0 if modo_corrompido() else 1
    if modo == "seguranca":
        return 0 if modo_seguranca() else 1
    print(__doc__); return 2

if __name__ == "__main__":
    sys.exit(main())
