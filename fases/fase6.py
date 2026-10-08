import json, re
from pathlib import Path

p = Path("app_relatorio.py")
s = p.read_text(encoding="utf-8")

def sub(old, new):
    global s
    assert s.count(old) == 1, "trecho nao encontrado (ou repetido): " + old[:70]
    s = s.replace(old, new)

# 1) PDF: a quantidade mostrada preserva decimais (2,5 nao vira 2) e tolera texto
sub("def _sev_da_foto(f):", '''def _fmt_qtd(valor):
    """Quantidade para exibição: preserva decimais (2,5 não vira 2) e tolera texto."""
    return f"{_num(valor, 1.0):.3f}".rstrip("0").rstrip(".")

def _sev_da_foto(f):''')
sub("str(int(m.get('quantidade',1)))", "_fmt_qtd(m.get('quantidade', 1))")

# 2) coordenada da base sai do codigo: [padroes] rota_partida no secrets.toml (migrada do valor atual)
m = re.search(r'^ROTA_PARTIDA_PADRAO = "([^"]*)"$', s, re.M)
assert m, "ROTA_PARTIDA_PADRAO nao encontrada (a fase 6 ja foi aplicada?)"
sec = Path(".streamlit/secrets.toml")
txt = sec.read_text(encoding="utf-8")
if "rota_partida" not in txt:
    assert "[padroes]" in txt, "[padroes] nao encontrado no secrets.toml (rode a fase 2 antes)"
    sec.write_text(txt.replace("[padroes]\n", "[padroes]\nrota_partida = " + json.dumps(m.group(1), ensure_ascii=False) + "\n", 1), encoding="utf-8")
sub(m.group(0), 'ROTA_PARTIDA_PADRAO = ""  # a base vem de st.secrets["padroes"]["rota_partida"]')
sub("value=ROTA_PARTIDA_PADRAO, key=\"rota_ponto_partida\"", "value=_padrao(\"rota_partida\", ROTA_PARTIDA_PADRAO), key=\"rota_ponto_partida\"")
sub("Use coordenadas (-23.5051209,-46.8109935) ou um endereço completo, ex.: Rua Petrolina, 296, Jardim Mutinga, Barueri, SP",
    "Use coordenadas (ex.: -23.55,-46.63) ou um endereço completo, ex.: Av. Paulista, 1000, São Paulo, SP")

p.write_text(s, encoding="utf-8")
print("OK: Fase 6 aplicada em", p)
