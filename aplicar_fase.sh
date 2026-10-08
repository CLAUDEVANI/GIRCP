#!/usr/bin/env bash
# uso: ./aplicar_fase.sh 1|2|3|4|5   (rode na pasta do projeto, com a linha de base ja salva)
set -u
APP=app_relatorio.py
N="${1:-}"
case "$N" in 1|2|3|4|5|6|7) ;; *) echo "uso: ./aplicar_fase.sh 1|2|3|4|5|6|7"; exit 1;; esac
[ -w "$APP" ] || { echo "ERRO: $APP esta travado. Rode: sudo chattr -i $APP && chmod u+w $APP"; exit 1; }
[ -f tests/baseline.json ] || { echo "ERRO: salve antes a linha de base: python tests/gircp_testes.py salvar"; exit 1; }
[ -f "fases/fase$N.py" ] || [ -f "fases/fase${N}_docs.py" ] || { echo "ERRO: script da fase $N nao encontrado"; exit 1; }
SCRIPT="fases/fase$N.py"; [ "$N" = "5" ] && SCRIPT="fases/fase5_docs.py"
BAK=".bak_antes_fase$N"
cp "$APP" "$BAK.py"; [ -f README.md ] && cp README.md "$BAK.README.md"
restaurar() {
  cp "$BAK.py" "$APP"; [ -f "$BAK.README.md" ] && cp "$BAK.README.md" README.md
  echo ">>> REVERTIDO: $APP (e README.md) voltaram ao estado anterior a fase $N"; exit 1
}
if [ "$N" = "2" ] && ! grep -q '^\[padroes\]' .streamlit/secrets.toml 2>/dev/null; then
  echo "== migrando dados pessoais do codigo para [padroes] no secrets.toml"
  python fases/migrar_padroes.py || { echo "ERRO na migracao; nada foi alterado no codigo"; exit 1; }
fi
echo "== aplicando fase $N"; python "$SCRIPT" || restaurar
python -m py_compile "$APP" || restaurar
echo "== teste: comparar com a linha de base"
if ! python tests/gircp_testes.py comparar; then
  if [ "$N" = "3" ]; then
    echo; echo "A fase 3 muda rotulos de KPI de proposito (veja as diferencas acima)."
    r="${GIRCP_ACEITAR:-}"; [ -z "$r" ] && read -r -p "Sao apenas rotulos? Aceitar como nova linha de base? [s/N] " r
    if [ "$r" = "s" ]; then python tests/gircp_testes.py salvar || restaurar; else restaurar; fi
  else
    restaurar
  fi
fi
if [ "$N" != "5" ]; then echo "== teste: laudo corrompido"; python tests/gircp_testes.py corrompido || restaurar; fi
if [ "$N" = "2" ]; then echo "== teste: seguranca"; python tests/gircp_testes.py seguranca || restaurar; fi
if [ "$N" -ge 6 ]; then echo "== teste: exportacoes (PDF, Excel, KML, upload)"; python tests/gircp_exportacoes.py || restaurar; fi
echo; echo ">>> FASE $N OK. Backup em $BAK.py (apague quando terminar)."
echo ">>> O selo mudou: regrave o hash no secrets.toml antes de subir o app (veja verificar.sh)."
