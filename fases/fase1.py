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

# 0) leitura segura do JSON (10 usos); feito ANTES de criar as funcoes para nao alterar o proprio helper
sub_re(r"json\.loads\(([^()]*?)\s+or\s+([\"'])\[\]\2\)", r"_carregar_lista_json(\1)", 10)

# 1) funcoes unicas (logo apos sanitizar)
sub("def sanitizar(texto: str) -> str:\n    return html_mod.escape(str(texto or '').strip())\n",
'''def sanitizar(texto: str) -> str:
    return html_mod.escape(str(texto or '').strip())

def _carregar_lista_json(valor):
    """Lê uma lista JSON do banco sem derrubar a tela: ausente, inválido ou de outro tipo vira []."""
    if valor is None:
        return []
    if isinstance(valor, (list, tuple)):
        return list(valor)
    try:
        dados = json.loads(valor or "[]")
    except (ValueError, TypeError):
        return []
    return dados if isinstance(dados, list) else []

def _num(valor, padrao=0.0):
    try:
        return float(valor)
    except (ValueError, TypeError):
        return padrao

def _custo_item(m):
    """Custo de uma linha de material (quantidade x custo unitário). Texto ou nulo viram o padrão."""
    m = m or {}
    return _num(m.get('quantidade', 1), 1.0) * _num(m.get('custo_unit', 0.0))

def _sev_da_foto(f):
    return normalizar_sev(f.get('severidade', 'Normal'))

def _tem_critico(fotos):
    return any(_sev_da_foto(f) == 'Critico' for f in fotos)
''')

# 2) leitura segura do JSON
sub("fotos = json.loads(row[0])", "fotos = _carregar_lista_json(row[0])")
sub("fotos_db = json.loads(row['fotos_json'] if row['fotos_json'] else \"[]\")", "fotos_db = _carregar_lista_json(row['fotos_json'])")
sub("extras_db = json.loads(ext_str)", "extras_db = _carregar_lista_json(ext_str)")
sub("len(json.loads(r['fotos_json'] if r['fotos_json'] else '[]'))", "len(_carregar_lista_json(r['fotos_json']))")
sub("len(json.loads(r['extras_json'] if 'extras_json' in r.keys() and r['extras_json'] else '[]'))",
    "len(_carregar_lista_json(r['extras_json'] if 'extras_json' in r.keys() else None))")
sub("fotos_ev = json.loads(row_ev[0]) if row_ev and row_ev[0] else []", "fotos_ev = _carregar_lista_json(row_ev[0] if row_ev else None)")
sub("json.loads(_row_dict.get('fotos_json') or '[]')", "_carregar_lista_json(_row_dict.get('fotos_json'))")

# 3) prazos: uma unica definicao (a global _PRAZOS_ORD)
sub_re(r"^(\s*)_prazos_ord = \[.*\]$", r"\1_prazos_ord = list(_PRAZOS_ORD)", 2, re.M)

# 4) custo por item: uma unica regra
sub("total_custo = sum(m.get('quantidade',0)*m.get('custo_unit',0) for m in all_mats)", "total_custo = sum(_custo_item(m) for m in all_mats)")
sub("subtotal_ev = sum(m.get('quantidade',0)*m.get('custo_unit',0) for m in mats_list)", "subtotal_ev = sum(_custo_item(m) for m in mats_list)")
sub("f\"{m.get('quantidade',0)*m.get('custo_unit',0):.2f}\"", "f\"{_custo_item(m):.2f}\"")
sub('subtotal = sum(m.get("quantidade", 0) * m.get("custo_unit", 0) for m in mats)', "subtotal = sum(_custo_item(m) for m in mats)")
sub("'Total_R$':  float(m.get('quantidade',1)) * float(m.get('custo_unit',0.0)),", "'Total_R$':  _custo_item(m),")
sub('''                try:
                    q = float(m.get("quantidade", 1))
                    cu = float(m.get("custo_unit", 0.0))
                except (ValueError, TypeError):
                    q, cu = 1.0, 0.0
                n_mat += 1
                custo += q * cu
''', '''                cu = _num(m.get("custo_unit", 0.0))
                n_mat += 1
                custo += _custo_item(m)
''')

# 5) severidade critica: uma unica regra
sub("n_criticos = sum(1 for f in fotos if normalizar_sev(f.get('severidade','')) == 'Critico')", "n_criticos = sum(1 for f in fotos if _sev_da_foto(f) == 'Critico')")
sub("n_crit_res = sum(1 for f in fotos_res if normalizar_sev(f.get('severidade','Normal')) == 'Critico')", "n_crit_res = sum(1 for f in fotos_res if _sev_da_foto(f) == 'Critico')")
sub('''            tem_critico = any(
                normalizar_sev(f.get('severidade', 'Normal')) == 'Critico'
                for f in fotos_row
            )''', "            tem_critico = _tem_critico(fotos_row)")
sub('''lambda x: any(normalizar_sev(f.get("severidade", "Normal")) == "Critico"
                          for f in _carregar_lista_json(x))''', "lambda x: _tem_critico(_carregar_lista_json(x))")

p.write_text(s, encoding="utf-8")
print("OK: Fase 1 aplicada em", p)
