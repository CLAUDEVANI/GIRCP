import json, re
from pathlib import Path

app = Path("app_relatorio.py").read_text(encoding="utf-8")
sec = Path(".streamlit/secrets.toml")
campos = {"contato": "novo_contato", "telefone": "novo_telefone", "email": "novo_email",
          "tecnico": "novo_tecnico", "art_rrt": "novo_art_rrt"}
valores = {}
for chave, k in campos.items():
    m = re.search(r'value="([^"]*)",\s*key="%s"' % k, app)
    assert m, f"padrao de {k} nao encontrado no codigo (a Fase 2 ja foi aplicada?)"
    valores[chave] = m.group(1)
txt = sec.read_text(encoding="utf-8")
assert "[padroes]" not in txt, "[padroes] ja existe no secrets.toml"
bloco = "\n[padroes]\n" + "".join(f"{k} = {json.dumps(v, ensure_ascii=False)}\n" for k, v in valores.items())
sec.write_text(txt.rstrip("\n") + "\n" + bloco, encoding="utf-8")
print("OK: [padroes] gravado em", sec, "com", len(valores), "campos")
