#!/usr/bin/env bash
# ==============================================================================
# GIRCP — Script de Instalação e Recuperação Completa
# v3.7.2 — Gerador Inteligente de Relatórios e Controle Fotográfico
# Uso: bash setup_gircp.sh
# ==============================================================================

set -euo pipefail

# ── Cores para output ──────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'; BOLD='\033[1m'

ok()   { echo -e "${GREEN}✔${NC} $1"; }
info() { echo -e "${CYAN}→${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }
err()  { echo -e "${RED}✘ ERRO:${NC} $1"; exit 1; }
hdr()  { echo -e "\n${BOLD}${BLUE}══ $1 ══${NC}"; }

# ── Detectar sistema ───────────────────────────────────────────────────────────
OS="$(uname -s)"
PYTHON=""
for cmd in python3.12 python3.11 python3.10 python3; do
    if command -v "$cmd" &>/dev/null; then PYTHON="$cmd"; break; fi
done
[[ -z "$PYTHON" ]] && err "Python 3.10+ não encontrado. Instale antes de continuar."
PY_VER=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
info "Python encontrado: $PYTHON ($PY_VER)"

# ── Diretório base = onde o script está ───────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
info "Diretório do projeto: $SCRIPT_DIR"

# ==============================================================================
# 1. ESTRUTURA DE PASTAS
# ==============================================================================
hdr "1. Estrutura de Pastas"

mkdir -p .streamlit
mkdir -p banco_fotos_gircp
mkdir -p backups
ok "Pastas criadas: .streamlit / banco_fotos_gircp / backups"

# ==============================================================================
# 2. ARQUIVO .gitignore
# ==============================================================================
hdr "2. .gitignore"

if [[ ! -f ".gitignore" ]]; then
cat > .gitignore << 'EOF'
# GIRCP — Arquivos a NÃO versionar
.streamlit/secrets.toml
*.db
*.db-wal
*.db-shm
banco_fotos_gircp/
backups/
__pycache__/
*.pyc
*.pyo
.venv/
venv/
env/
.DS_Store
Thumbs.db
EOF
    ok ".gitignore criado"
else
    warn ".gitignore já existe — mantido sem alteração"
fi

# ==============================================================================
# 3. STREAMLIT — config.toml
# ==============================================================================
hdr "3. Streamlit config.toml"

if [[ ! -f ".streamlit/config.toml" ]]; then
cat > .streamlit/config.toml << 'EOF'
# GIRCP — Configuração Streamlit

[theme]
primaryColor              = "#002060"
backgroundColor           = "#FFFFFF"
secondaryBackgroundColor  = "#F1F5F9"
textColor                 = "#1E293B"
font                      = "sans serif"

[server]
maxUploadSize             = 200
enableCORS                = false
enableXsrfProtection      = true
headless                  = true

[browser]
gatherUsageStats          = false

[runner]
fastReruns                = true
EOF
    ok ".streamlit/config.toml criado"
else
    warn ".streamlit/config.toml já existe — mantido sem alteração"
fi

# ==============================================================================
# 4. STREAMLIT — secrets.toml (só cria se não existir — não sobrescreve senhas!)
# ==============================================================================
hdr "4. Streamlit secrets.toml"

if [[ -f ".streamlit/secrets.toml" ]]; then
    warn ".streamlit/secrets.toml já existe — NÃO sobrescrito (senhas preservadas)"
else
cat > .streamlit/secrets.toml << 'EOF'
# GIRCP — Segredos de Aplicação
# ATENÇÃO: NÃO versionar este arquivo

# Senha principal usada por check_password()
senha_acesso = "gircp@2026"

[usuarios.admin]
senha  = "gircp@admin2026"
perfil = "administrador"
nome   = "Claudevani Pereira"
email  = "clauevani.pereira@engemon.com.br"

[usuarios.tecnico1]
senha  = "gircp@campo1"
perfil = "tecnico"
nome   = "Técnico em Campo"
email  = ""

[database]
# url = "postgresql://usuario:senha@host:5432/gircp_db"

[integracao]
# webhook_url = ""
# api_token   = ""
EOF
    ok ".streamlit/secrets.toml criado"
    warn "⚠  Altere a senha 'gircp@2026' antes de usar em produção!"
fi

# ==============================================================================
# 5. AMBIENTE VIRTUAL PYTHON
# ==============================================================================
hdr "5. Ambiente Virtual Python"

if [[ ! -d "venv" ]]; then
    info "Criando venv..."
    $PYTHON -m venv venv
    ok "venv criado"
else
    warn "venv já existe — reutilizando"
fi

# Ativar venv
if [[ "$OS" == "MINGW"* ]] || [[ "$OS" == "CYGWIN"* ]]; then
    VENV_PYTHON="venv/Scripts/python"
    VENV_PIP="venv/Scripts/pip"
else
    VENV_PYTHON="venv/bin/python"
    VENV_PIP="venv/bin/pip"
fi

# ==============================================================================
# 6. DEPENDÊNCIAS PYTHON
# ==============================================================================
hdr "6. Dependências Python"

info "Atualizando pip..."
$VENV_PIP install --upgrade pip -q

# Criar requirements.txt se não existir
if [[ ! -f "requirements.txt" ]]; then
cat > requirements.txt << 'EOF'
streamlit>=1.35.0
pandas>=2.0.0
plotly>=5.18.0
pydeck>=0.9.0
Pillow>=10.0.0
weasyprint>=61.0
openpyxl>=3.1.0
requests>=2.31.0
defusedxml>=0.7.1
filetype>=1.2.0
qrcode[pil]>=7.4.2
EOF
    ok "requirements.txt criado"
fi

if $VENV_PYTHON -c "import streamlit, pandas, plotly, pydeck, PIL, weasyprint, openpyxl, requests, defusedxml, filetype, qrcode" &>/dev/null 2>&1; then
    warn "Pacotes já instalados — pulando instalação"
else
    info "Instalando pacotes Python (pode demorar alguns minutos)..."
    $VENV_PIP install -r requirements.txt -q
    ok "Pacotes instalados"
fi

# Verificar dependências do sistema necessárias para WeasyPrint
hdr "6b. Verificando dependências do sistema (WeasyPrint)"
if [[ "$OS" == "Linux" ]]; then
    MISSING_PKGS=()
    for pkg in libpango-1.0-0 libcairo2 libgdk-pixbuf2.0-0; do
        dpkg -s "$pkg" &>/dev/null 2>&1 || MISSING_PKGS+=("$pkg")
    done
    if [[ ${#MISSING_PKGS[@]} -gt 0 ]]; then
        warn "Pacotes de sistema ausentes para WeasyPrint: ${MISSING_PKGS[*]}"
        warn "Execute: sudo apt-get install -y ${MISSING_PKGS[*]}"
    else
        ok "Dependências do sistema para WeasyPrint OK"
    fi
elif [[ "$OS" == "Darwin" ]]; then
    if ! command -v brew &>/dev/null; then
        warn "Homebrew não encontrado. Para WeasyPrint no macOS: instale Homebrew e execute: brew install pango cairo gdk-pixbuf"
    else
        ok "Homebrew encontrado — WeasyPrint deve funcionar"
    fi
fi

# ==============================================================================
# 7. BANCO DE DADOS SQLite — inicialização e migração
# ==============================================================================
hdr "7. Banco de Dados SQLite"

DB_FILE="laudos_corp_v3.db"

$VENV_PYTHON << 'PYEOF'
import sqlite3, os, shutil, datetime

DB = "laudos_corp_v3.db"

# Backup se já existir
if os.path.exists(DB):
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    bkp = f"backups/{DB.replace('.db', '')}_{ts}.db"
    shutil.copy2(DB, bkp)
    print(f"  → Backup do banco existente: {bkp}")

conn = sqlite3.connect(DB)
c = conn.cursor()
c.execute("PRAGMA journal_mode=WAL")

# Tabela principal
c.execute('''
    CREATE TABLE IF NOT EXISTS relatorios (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo           TEXT,
        contato          TEXT,
        empresa          TEXT,
        telefone         TEXT,
        email            TEXT,
        site_id          TEXT NOT NULL,
        endereco         TEXT,
        data_hora        TEXT,
        fotos_json       TEXT DEFAULT '[]',
        extras_json      TEXT DEFAULT '[]',
        criado_em        TEXT DEFAULT (datetime('now','localtime'))
    )
''')

# Migração incremental de colunas (idempotente)
colunas_novas = [
    "criado_em TEXT", "endereco TEXT", "tecnico TEXT",
    "numero_relatorio TEXT", "revisao TEXT",
    "latitude REAL", "longitude REAL",
    "art_rrt TEXT", "conclusao TEXT",
    "status_laudo TEXT", "hash_integridade TEXT"
]
for col in colunas_novas:
    try:
        c.execute(f"ALTER TABLE relatorios ADD COLUMN {col}")
    except sqlite3.OperationalError:
        pass  # coluna já existe

# Sequência de numeração de relatórios
c.execute("CREATE TABLE IF NOT EXISTS seq_relatorio (ultimo INTEGER DEFAULT 0)")
c.execute("INSERT INTO seq_relatorio SELECT 0 WHERE NOT EXISTS (SELECT 1 FROM seq_relatorio)")

# Log de auditoria
c.execute('''
    CREATE TABLE IF NOT EXISTS audit_log (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        criado_em    TEXT DEFAULT (datetime('now','localtime')),
        tecnico      TEXT,
        acao         TEXT,
        id_relatorio INTEGER,
        detalhe      TEXT
    )
''')

conn.commit()
conn.close()
print("  ✔ Banco laudos_corp_v3.db inicializado/migrado com sucesso")
PYEOF

ok "Banco de dados OK"

# ==============================================================================
# 8. DIRETÓRIO DE FOTOS
# ==============================================================================
hdr "8. Diretório de Fotos"

mkdir -p banco_fotos_gircp
# .gitkeep para versionar pasta vazia
touch banco_fotos_gircp/.gitkeep
ok "banco_fotos_gircp/ pronto"

# ==============================================================================
# 9. SCRIPT DE INICIALIZAÇÃO RÁPIDA
# ==============================================================================
hdr "9. Script de Start"

if [[ ! -f "start.sh" ]]; then
cat > start.sh << 'EOF'
#!/usr/bin/env bash
# GIRCP — Inicialização rápida
cd "$(dirname "${BASH_SOURCE[0]}")"
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null
echo "⚡ Iniciando GIRCP em http://localhost:8503"
streamlit run app_relatorio.py --server.port 8503
EOF
    chmod +x start.sh
    ok "start.sh criado (execute: bash start.sh)"
else
    warn "start.sh já existe — mantido sem alteração"
fi

# ==============================================================================
# 10. RESUMO FINAL
# ==============================================================================
hdr "✅ SETUP CONCLUÍDO"

echo ""
echo -e "  ${BOLD}Estrutura gerada:${NC}"
echo "  ├── app_relatorio.py"
echo "  ├── requirements.txt"
echo "  ├── start.sh"
echo "  ├── .gitignore"
echo "  ├── .streamlit/"
echo "  │   ├── config.toml"
echo "  │   └── secrets.toml   ← NÃO commitar"
echo "  ├── banco_fotos_gircp/"
echo "  ├── backups/"
echo "  └── venv/"
echo ""
echo -e "  ${BOLD}Para iniciar o sistema:${NC}"
echo -e "  ${GREEN}bash start.sh${NC}"
echo ""
echo -e "  ${BOLD}Ou manualmente:${NC}"
echo -e "  ${GREEN}source venv/bin/activate && streamlit run app_relatorio.py --server.port 8503${NC}"
echo ""
echo -e "  ${YELLOW}⚠  Altere a senha em .streamlit/secrets.toml antes de usar em produção!${NC}"
echo ""