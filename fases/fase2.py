import re
from pathlib import Path

p = Path("app_relatorio.py")
s = p.read_text(encoding="utf-8")

def sub(old, new):
    global s
    assert s.count(old) == 1, "trecho nao encontrado (ou repetido): " + old[:70]
    s = s.replace(old, new)

def sub_re(padrao, novo, esperado, flags=0):
    global s
    s, n = re.subn(padrao, novo, s, flags=flags)
    assert n == esperado, f"{padrao[:50]}: {n} ocorrencias (esperado {esperado})"

# 1) dados pessoais saem do codigo: padroes vem de st.secrets['padroes'] (vazio se ausente)
sub("    return html_mod.escape(str(texto or '').strip())\n",
'''    return html_mod.escape(str(texto or '').strip())

def _padrao(chave, fallback=""):
    """Valor padrão do cadastro vindo de st.secrets['padroes'] (evita dados pessoais fixos no código)."""
    try:
        return str(st.secrets["padroes"].get(chave, fallback))
    except Exception:
        return fallback
''')
sub_re(r'value="[^"]*", key="novo_contato"', 'value=_padrao("contato"), key="novo_contato"', 1)
sub_re(r'value="[^"]*", key="novo_telefone"', 'value=_padrao("telefone"), key="novo_telefone"', 1)
sub_re(r'value="[^"]*", key="novo_email"', 'value=_padrao("email"), key="novo_email"', 1)
sub_re(r'value="[^"]*", key="novo_tecnico"', 'value=_padrao("tecnico", _padrao("contato")), key="novo_tecnico"', 1)
sub_re(r'value="[^"]*", key="novo_art_rrt"', 'value=_padrao("art_rrt"), key="novo_art_rrt"', 1)

# 2) login: falhas na auditoria e bloqueio que sobrevive a recarregar a pagina
sub("def check_password():\n", '''def _detalhe_falha_login(usuario):
    return f"Tentativa inválida (usuário: {str(usuario or 'senha geral')[:60]})"

def _falhas_recentes(usuario, minutos=5):
    """Falhas de login do mesmo usuário nos últimos minutos, contadas na auditoria (sobrevive a recarregar a página)."""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM audit_log WHERE acao = 'login_falha' AND detalhe = ? "
                "AND criado_em >= datetime('now', 'localtime', ?)",
                (_detalhe_falha_login(usuario), f"-{int(minutos)} minutes")).fetchone()[0]
    except sqlite3.Error:
        return 0

def _auditar_login(acao, detalhe):
    """Auditoria de login que nunca derruba o acesso (o banco pode não existir ainda no primeiro login)."""
    try:
        init_db()
        registrar_auditoria(acao, detalhe=detalhe)
    except Exception:
        pass

def check_password():
''')
sub('        usuario = st.session_state.get("usuario_input", "").strip().lower()\n        cfg = {}\n',
'''        usuario = st.session_state.get("usuario_input", "").strip().lower()
        if _falhas_recentes(usuario) >= 5:
            st.session_state["bloqueado_ate"] = datetime.now() + timedelta(minutes=5)
            st.session_state["password_correct"] = False
            return
        cfg = {}
''')
sub("            registrar_auditoria(\"login_sucesso\", detalhe=f\"Autenticação válida (usuário: {usuario or 'senha geral'})\")",
    "            _auditar_login(\"login_sucesso\", f\"Autenticação válida (usuário: {usuario or 'senha geral'})\")")
sub('''            st.session_state["tentativas"] += 1
            if st.session_state["tentativas"] >= 5:
                st.session_state["bloqueado_ate"] = datetime.now() + timedelta(minutes=5)
                registrar_auditoria("bloqueio_bruteforce", detalhe="Múltiplas falhas de login")''',
'''            st.session_state["tentativas"] += 1
            _auditar_login("login_falha", _detalhe_falha_login(usuario))
            if st.session_state["tentativas"] >= 5:
                st.session_state["bloqueado_ate"] = datetime.now() + timedelta(minutes=5)
                _auditar_login("bloqueio_bruteforce", "Múltiplas falhas de login")''')

# 3) hash de chave de widget: SHA-256 no lugar de MD5
sub("hashlib.md5(filename.encode()).hexdigest()[:8]", "hashlib.sha256(filename.encode()).hexdigest()[:8]")

# 4) excecoes: sem except nu
sub("except: pass", "except OSError: pass")
sub_re(r"^(\s*)except:\s*$", r"\1except Exception:", 2, re.M)

# 5) busca LIKE: % e _ digitados pelo usuario passam a ser literais
sub('''            rows = conn.execute("SELECT * FROM relatorios WHERE site_id LIKE ? OR titulo LIKE ? ORDER BY id DESC LIMIT ?", (f'%{termo}%', f'%{termo}%', limite)).fetchall()''',
r'''            _t_like = termo.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            rows = conn.execute("SELECT * FROM relatorios WHERE site_id LIKE ? ESCAPE '\\' OR titulo LIKE ? ESCAPE '\\' ORDER BY id DESC LIMIT ?", (f'%{_t_like}%', f'%{_t_like}%', limite)).fetchall()''')

# 6) geocodificacao: cache em memoria (so acertos) e intervalo minimo de 1 s entre consultas ao Nominatim
sub('''def geocodificar_endereco(endereco):
    """Converte endereço em (lat, lon) via Nominatim/OpenStreetMap (somente Brasil). Retorna None se falhar."""
    try:
''', '''_GEO_CACHE = {}
_GEO_ULTIMA = [0.0]

def geocodificar_endereco(endereco):
    """Converte endereço em (lat, lon) via Nominatim/OpenStreetMap (somente Brasil). Retorna None se falhar."""
    import time
    chave = " ".join(str(endereco).lower().split())
    if chave in _GEO_CACHE:
        return _GEO_CACHE[chave]
    espera = 1.1 - (time.time() - _GEO_ULTIMA[0])
    if espera > 0:
        time.sleep(espera)
    _GEO_ULTIMA[0] = time.time()
    try:
''')
sub('''        if isinstance(dados, list) and dados:
            return float(dados[0]["lat"]), float(dados[0]["lon"])''', '''        if isinstance(dados, list) and dados:
            if len(_GEO_CACHE) >= 200:
                _GEO_CACHE.clear()
            _GEO_CACHE[chave] = (float(dados[0]["lat"]), float(dados[0]["lon"]))
            return _GEO_CACHE[chave]''')

p.write_text(s, encoding="utf-8")
print("OK: Fase 2 aplicada em", p)
