#!/usr/bin/env bash
# verificacao rapida antes de selar e travar o app_relatorio.py
APP=app_relatorio.py; falha=0
echo "== 1) compila";            python -m py_compile "$APP" && echo OK || falha=1
echo "== 2) pyflakes";           if python -m pyflakes --version >/dev/null 2>&1; then python -m pyflakes "$APP" | grep -v "never used"; echo "(fim)"; else echo "pyflakes nao instalado (pip install pyflakes)"; fi
echo "== 3) bandit (medio+)";    if python -m bandit --version >/dev/null 2>&1; then python -m bandit -q -ll "$APP" && echo "sem achados medio ou pior" || falha=1; else echo "bandit nao instalado (pip install bandit)"; fi
echo "== 4) selo"
ATUAL=$(sha256sum "$APP" | cut -d' ' -f1)
SELO=$(grep -E '^hash_codigo' .streamlit/secrets.toml 2>/dev/null | head -1 | sed -E 's/.*"([0-9a-fA-F]+)".*/\1/')
if [ "$ATUAL" = "$SELO" ]; then echo "OK: selo confere"; else echo "ATENCAO: selo diferente. Para regravar:"; echo "  NOVO=\$(sha256sum $APP | cut -d' ' -f1); sed -i \"s/^hash_codigo *=.*/hash_codigo = \\\"\$NOVO\\\"/\" .streamlit/secrets.toml"; falha=1; fi
echo "== 5) testes ponta a ponta"; python tests/gircp_testes.py comparar || falha=1
[ "$falha" = 0 ] && echo ">>> TUDO OK" || echo ">>> HA PENDENCIAS (veja acima)"
exit $falha
