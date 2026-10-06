import ast
from pathlib import Path

p = Path("app_relatorio.py")
src = p.read_text(encoding="utf-8")
linhas = src.split("\n")
tree = ast.parse(src)
fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "tela_dashboard")
assert not fn.decorator_list, "tela_dashboard tem decorator; estrutura inesperada"

NOMES = [("RESUMO GERAL", "resumo"), ("PAINEL SLA", "sla"), ("MAPA TÁTICO", "mapa"),
         ("TENDÊNCIA", "tendencia"), ("PAINEL DE ORÇAMENTO", "orcamento"), ("LOG DE AUDITORIA", "auditoria")]

def lidos(no):
    return {x.id for x in ast.walk(no) if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Load)}

def gravados(no):
    achados, pilha = set(), [no]
    while pilha:
        x = pilha.pop()
        if isinstance(x, (ast.Lambda, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp, ast.FunctionDef)):
            continue
        if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Store):
            achados.add(x.id)
        pilha.extend(ast.iter_child_nodes(x))
    return achados

pre, grupos = [], []
for st_ in fn.body:
    primeira = ast.get_source_segment(src, st_).split("\n")[0].strip()
    if primeira.startswith("secao("):
        grupos.append([primeira, [st_]])
    elif not grupos:
        pre.append(st_)
    else:
        grupos[-1][1].append(st_)
assert len(grupos) == len(NOMES) and all(t in g[0] for g, (t, _) in zip(grupos, NOMES)), "secoes do Dashboard diferentes do esperado"

vars_pre = set().union(*[gravados(x) for x in pre])
fim_pre = pre[-1].end_lineno
defs, chamadas = [], []
for i, (g, (_, nome)) in enumerate(zip(grupos, NOMES)):
    stmts = g[1]
    proprios = set().union(*[gravados(x) for x in stmts])
    params = sorted((set().union(*[lidos(x) for x in stmts]) - proprios) & vars_pre)
    assert set(params) <= {"df", "df_filtrado"}, f"secao {nome} depende de {params}; abortado"
    inicio = (fim_pre if i == 0 else grupos[i - 1][1][-1].end_lineno) + 1
    corpo = "\n".join(linhas[inicio - 1:stmts[-1].end_lineno]).strip("\n")
    defs.append(f"def _dash_{nome}({', '.join(params)}):\n{corpo}\n")
    chamadas.append(f"    _dash_{nome}({', '.join(params)})")

novo = []
for d in defs:
    novo += d.split("\n") + [""]
novo += linhas[fn.lineno - 1:fim_pre] + [""] + chamadas
linhas[fn.lineno - 1:fn.end_lineno] = novo
p.write_text("\n".join(linhas), encoding="utf-8")
print("OK: tela_dashboard dividida em", len(defs), "funcoes de secao:", ", ".join(f"_dash_{n}" for _, n in NOMES))
