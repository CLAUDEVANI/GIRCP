from pathlib import Path

def trocar(caminho, pares):
    p = Path(caminho)
    s = p.read_text(encoding="utf-8")
    for old, new in pares:
        assert s.count(old) == 1, f"{caminho}: trecho nao encontrado (ou repetido): " + old[:60]
        s = s.replace(old, new)
    p.write_text(s, encoding="utf-8")

# o orquestrador passa a aceitar as fases 6 e 7 e a rodar os testes de exportacao
trocar("aplicar_fase.sh", [
    ('case "$N" in 1|2|3|4|5) ;; *) echo "uso: ./aplicar_fase.sh 1|2|3|4|5"; exit 1;; esac',
     'case "$N" in 1|2|3|4|5|6|7) ;; *) echo "uso: ./aplicar_fase.sh 1|2|3|4|5|6|7"; exit 1;; esac'),
    ('if [ "$N" -ge 1 ] && [ "$N" -le 4 ]; then echo "== teste: laudo corrompido"',
     'if [ "$N" != "5" ]; then echo "== teste: laudo corrompido"'),
    ('echo; echo ">>> FASE $N OK.',
     'if [ "$N" -ge 6 ]; then echo "== teste: exportacoes (PDF, Excel, KML, upload)"; python tests/gircp_exportacoes.py || restaurar; fi\necho; echo ">>> FASE $N OK.'),
])
# a coordenada da base passa a vir do secrets (rota_partida); o teste da rota injeta o mesmo valor que o codigo usava
trocar("tests/gircp_testes.py", [
    ('        at = _nova(app).run()\n        at.sidebar.radio[0].set_value(MENUS["rota"]).run()\n        sites = list(at.multiselect[0].options)',
     '        at = _nova(app)\n        at.secrets["padroes"] = {"rota_partida": "-23.5051209,-46.8109935"}\n        at = at.run()\n        at.sidebar.radio[0].set_value(MENUS["rota"]).run()\n        sites = list(at.multiselect[0].options)'),
])
print("OK: orquestrador e testes ajustados para as fases 6 e 7")
