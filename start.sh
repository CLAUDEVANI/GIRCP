#!/usr/bin/env bash
# GIRCP — Inicialização rápida
cd "$(dirname "${BASH_SOURCE[0]}")"
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null
echo "⚡ Iniciando GIRCP em http://localhost:8503"
streamlit run app_relatorio.py --server.port 8503
