#!/usr/bin/env python3
"""
GIRCP — gera o selo de integridade (SHA-256) do app_relatorio.py.

Uso:
    python selar_codigo.py                    # usa ./app_relatorio.py
    python selar_codigo.py caminho/do/app.py

Cole a saída no FINAL do .streamlit/secrets.toml (substitua o bloco [seguranca]
se já existir). Rode de novo SEMPRE que editar o app_relatorio.py de forma legítima.
"""
import hashlib
import pathlib
import sys

alvo = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "app_relatorio.py")
if not alvo.is_file():
    sys.exit(f"Arquivo não encontrado: {alvo}")

hash_codigo = hashlib.sha256(alvo.read_bytes()).hexdigest()
print(f"# selo de {alvo.name} — adicione ao FINAL de .streamlit/secrets.toml\n")
print("[seguranca]")
print(f'hash_codigo = "{hash_codigo}"')