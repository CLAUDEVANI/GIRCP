"""
GIRCP — Gerador Inteligente de Relatórios e Controle Fotográfico
Engemon OpServices | v3.0
"""

import streamlit as st
import sqlite3
import base64
import json
import os
import re
from datetime import datetime

# ══════════════════════════════════════════════════════════════════════════
# CONSTANTES DE DESIGN — ENGEMON
# ══════════════════════════════════════════════════════════════════════════
COR_AZUL        = "#002060"   # Azul Engemon primário
COR_AZUL_MED    = "#003087"   # Azul médio
COR_AZUL_LIGHT  = "#EBF0FA"   # Azul claro (fundo)
COR_VERMELHO    = "#DA291C"   # Vermelho Claro/acento
COR_CINZA       = "#64748B"   # Texto secundário
COR_CINZA_LIGHT = "#F1F5F9"   # Fundo neutro
COR_BORDA       = "#CBD5E1"   # Borda suave
COR_TEXTO       = "#1E293B"   # Texto principal
COR_VERDE       = "#16A34A"   # Sucesso
COR_AMARELO     = "#D97706"   # Aviso

DB_NAME = "laudos_corp_v3.db"

# ══════════════════════════════════════════════════════════════════════════
# BANCO DE DADOS
# ══════════════════════════════════════════════════════════════════════════
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("PRAGMA journal_mode=WAL")
    c.execute('''
        CREATE TABLE IF NOT EXISTS relatorios (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo      TEXT,
            contato     TEXT,
            empresa     TEXT,
            telefone    TEXT,
            email       TEXT,
            site_id     TEXT NOT NULL,
            data_hora   TEXT,
            fotos_json  TEXT DEFAULT '[]',
            extras_json TEXT DEFAULT '[]',
            criado_em   TEXT DEFAULT (datetime('now','localtime'))
        )
    ''')
    # Migration: adicionar criado_em se não existir
    try:
        c.execute("ALTER TABLE relatorios ADD COLUMN criado_em TEXT")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()


def sanitizar(texto: str) -> str:
    """Remove tags HTML perigosas preservando entidades seguras."""
    return re.sub(r'<[^>]*>', '', str(texto or '')).strip()


# ══════════════════════════════════════════════════════════════════════════
# GERADOR DE PDF — HTML/CSS via WeasyPrint
# ══════════════════════════════════════════════════════════════════════════
def _carregar_b64(caminho: str) -> str:
    if os.path.exists(caminho):
        with open(caminho, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')
    return ""


def _css_pdf() -> str:
    return f"""
    @page {{
        size: A4;
        margin: 14mm 14mm 18mm 14mm;
        @bottom-left {{
            content: "CONFIDENCIAL  •  USO INTERNO  •  Dados protegidos pela LGPD (Lei 13.709/2018)  |  Sistema GIRCP";
            font-size: 7pt;
            color: {COR_CINZA};
            font-family: 'Segoe UI', Arial, sans-serif;
        }}
        @bottom-right {{
            content: "Página " counter(page) " de " counter(pages);
            font-size: 7pt;
            color: {COR_CINZA};
            font-family: 'Segoe UI', Arial, sans-serif;
        }}
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
        font-family: 'Segoe UI', Helvetica, Arial, sans-serif;
        color: {COR_TEXTO};
        font-size: 9.5pt;
        line-height: 1.5;
        background: #fff;
    }}

    /* ── WATERMARK ── */
    .watermark {{
        position: fixed; top: 38%; left: 50%;
        transform: translate(-50%, -50%);
        z-index: -999; width: 65%; opacity: 0.06;
    }}
    .watermark img {{ width: 100%; }}

    /* ── CABEÇALHO ── */
    .page-header {{
        display: flex; justify-content: space-between; align-items: flex-end;
        border-bottom: 3px solid {COR_AZUL};
        padding-bottom: 10px; margin-bottom: 22px;
    }}
    .header-titulo {{
        color: {COR_AZUL}; font-size: 19pt; font-weight: 900;
        text-transform: uppercase; letter-spacing: 0.8px;
    }}
    .header-acento {{
        display: inline-block; width: 36px; height: 4px;
        background: {COR_VERMELHO}; margin-bottom: 4px;
    }}
    .header-data {{
        text-align: right; color: {COR_CINZA}; font-size: 9pt;
    }}
    .header-data strong {{ color: {COR_AZUL}; font-size: 11pt; }}

    /* ── SEÇÕES ── */
    .section-header {{
        background: {COR_AZUL}; color: #fff;
        font-weight: 700; font-size: 10pt;
        padding: 7px 14px;
        margin-top: 22px; margin-bottom: 14px;
        text-transform: uppercase; letter-spacing: 0.5px;
        border-left: 5px solid {COR_VERMELHO};
        border-radius: 2px;
    }}

    /* ── TABELA CADASTRAL ── */
    .dados-table {{
        width: 100%; border-collapse: collapse;
        margin-bottom: 18px;
        border: 1px solid {COR_BORDA};
        border-radius: 4px; overflow: hidden;
    }}
    .dados-table td {{
        border: 1px solid {COR_BORDA}; padding: 9px 13px;
        vertical-align: middle;
    }}
    .dados-table td.label {{
        background: {COR_AZUL_LIGHT}; font-weight: 700;
        color: {COR_AZUL}; text-transform: uppercase;
        font-size: 7.8pt; width: 22%; letter-spacing: 0.3px;
    }}
    .dados-table td.value {{
        color: {COR_TEXTO}; font-size: 9.5pt; width: 28%;
    }}

    /* ── CARD DE EVIDÊNCIA ── */
    .card-evidencia {{
        width: 100%; border-collapse: collapse;
        margin-bottom: 14px;
        border: 1px solid {COR_BORDA};
        border-radius: 6px; overflow: hidden;
        page-break-inside: avoid;
        background: #fff;
    }}
    .card-evidencia td {{ vertical-align: top; }}

    .card-num {{
        background: {COR_AZUL}; color: #fff;
        font-size: 8pt; font-weight: 700;
        padding: 3px 8px; text-align: center;
        writing-mode: vertical-rl;
        min-width: 22px;
    }}

    .col-foto {{
        width: 43%; background: {COR_CINZA_LIGHT};
        padding: 10px; text-align: center;
        border-right: 1px solid {COR_BORDA};
    }}
    .col-foto img {{
        width: 100%; max-height: 210px;
        object-fit: contain; border-radius: 3px;
        background: #fff;
    }}
    .foto-filename {{
        font-size: 7pt; color: {COR_CINZA};
        margin-top: 5px; font-style: italic;
    }}

    .col-texto {{ width: 57%; padding: 14px 16px; }}
    .foto-titulo {{
        font-weight: 800; color: {COR_AZUL};
        font-size: 11pt; text-transform: uppercase;
        border-bottom: 2px solid {COR_AZUL_LIGHT};
        padding-bottom: 7px; margin-bottom: 10px;
    }}
    .label-desc {{
        font-size: 8pt; font-weight: 700;
        color: {COR_AZUL}; margin-bottom: 4px;
    }}
    .foto-desc {{
        font-size: 9pt; color: {COR_TEXTO};
        background: {COR_CINZA_LIGHT};
        padding: 9px 11px;
        border-left: 3px solid {COR_VERMELHO};
        border-radius: 0 4px 4px 0;
        line-height: 1.5;
        white-space: pre-wrap;
    }}

    /* ── ASSINATURA ── */
    .assinatura-wrapper {{
        margin: 44px auto 0 auto;
        width: 300px; text-align: center;
        page-break-inside: avoid;
    }}
    .assinatura-img {{
        max-width: 180px; height: auto;
        display: block; margin: 0 auto -10px auto;
    }}
    .assinatura-linha {{
        border-top: 1.5px solid {COR_TEXTO};
        margin: 0 0 6px 0;
    }}
    .assinatura-nome {{
        font-weight: 700; color: {COR_AZUL}; font-size: 9.5pt;
    }}
    .assinatura-cargo {{
        font-size: 8pt; color: {COR_CINZA};
    }}
    .logo-wrapper {{ margin-top: 14px; }}
    .logo-img {{
        max-width: 140px; height: auto;
        display: block; margin: 0 auto;
    }}
    """


def gerar_pdf(dados: dict, fotos: list, extras: list = None) -> str:
    extras = extras or []

    # Carregar assets
    b64_wm  = _carregar_b64("WhatsApp Image 2026-06-25 at 05.46.59.jpeg") or \
              _carregar_b64("logo_engemon.png")
    b64_sig = _carregar_b64("assinatura_claudevani.png")
    b64_logo = _carregar_b64("logo_engemon.png")

    wm_html = f'<div class="watermark"><img src="data:image/jpeg;base64,{b64_wm}"/></div>' \
              if b64_wm else ""

    sig_img = f'<img class="assinatura-img" src="data:image/png;base64,{b64_sig}"/>' \
              if b64_sig else '<div style="height:40px;"></div>'

    logo_img = f'<img class="logo-img" src="data:image/png;base64,{b64_logo}"/>' \
               if b64_logo else ""

    # Monta HTML das evidências principais
    fotos_html = ""
    for i, f in enumerate(fotos, 1):
        mime = f.get('type', 'image/jpeg')
        b64  = f.get('base64', '')
        tit  = sanitizar(f.get('titulo', f'Evidência {i}')).upper()
        desc = sanitizar(f.get('comentarios', 'N/A'))
        fname = sanitizar(f.get('filename', ''))
        fotos_html += f"""
        <table class="card-evidencia">
          <tr>
            <td class="card-num">{i:02d}</td>
            <td class="col-foto">
              <img src="data:{mime};base64,{b64}"/>
              {'<div class="foto-filename">' + fname + '</div>' if fname else ''}
            </td>
            <td class="col-texto">
              <div class="foto-titulo">{tit}</div>
              <div class="label-desc">Descrição Técnica:</div>
              <div class="foto-desc">{desc}</div>
            </td>
          </tr>
        </table>"""

    # Monta HTML dos anexos
    extras_html = ""
    if extras:
        extras_html = '<div style="page-break-before:always;"></div>'
        extras_html += f'<div class="section-header">3 &nbsp; ANEXOS ADICIONAIS</div>'
        for i, f in enumerate(extras, 1):
            mime = f.get('type', 'image/jpeg')
            b64  = f.get('base64', '')
            tit  = sanitizar(f.get('titulo', f'Anexo {i}')).upper()
            desc = sanitizar(f.get('comentarios', 'N/A'))
            extras_html += f"""
            <table class="card-evidencia">
              <tr>
                <td class="card-num">A{i:02d}</td>
                <td class="col-foto">
                  <img src="data:{mime};base64,{b64}"/>
                </td>
                <td class="col-texto">
                  <div class="foto-titulo">{tit}</div>
                  <div class="label-desc">Descrição / Contexto:</div>
                  <div class="foto-desc">{desc}</div>
                </td>
              </tr>
            </table>"""

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="utf-8">
<style>{_css_pdf()}</style>
</head>
<body>
{wm_html}

<div class="page-header">
  <div>
    <div class="header-acento"></div>
    <div class="header-titulo">Relatório de Visita Técnica</div>
  </div>
  <div class="header-data">
    Data da Vistoria:<br>
    <strong>{sanitizar(dados.get('data_hora',''))}</strong>
  </div>
</div>

<div class="section-header">1 &nbsp; DADOS CADASTRAIS DA INFRAESTRUTURA</div>
<table class="dados-table">
  <tr>
    <td class="label">SITE / IDENTIFICAÇÃO</td>
    <td class="value">{sanitizar(dados.get('site_id',''))}</td>
    <td class="label">TÍTULO</td>
    <td class="value">{sanitizar(dados.get('titulo',''))}</td>
  </tr>
  <tr>
    <td class="label">EMPRESA</td>
    <td class="value">{sanitizar(dados.get('empresa',''))}</td>
    <td class="label">CONTATO TÉCNICO</td>
    <td class="value">{sanitizar(dados.get('contato',''))}</td>
  </tr>
  <tr>
    <td class="label">TELEFONE</td>
    <td class="value">{sanitizar(dados.get('telefone',''))}</td>
    <td class="label">E-MAIL</td>
    <td class="value">{sanitizar(dados.get('email',''))}</td>
  </tr>
</table>

<div class="section-header">2 &nbsp; REGISTRO FOTOGRÁFICO E EVIDÊNCIAS</div>
{fotos_html}

{extras_html}

<div class="assinatura-wrapper">
  {sig_img}
  <div class="assinatura-linha"></div>
  <div class="assinatura-nome">{sanitizar(dados.get('contato','Responsável Técnico'))}</div>
  <div class="assinatura-cargo">Responsável técnico | Engemon OpServices</div>
  <div class="logo-wrapper">{logo_img}</div>
</div>

</body></html>"""

    from weasyprint import HTML as WP
    nome = f"Relatorio_{sanitizar(dados.get('site_id','SITE')).replace(' ','_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    path = os.path.join(os.getcwd(), nome)
    WP(string=html).write_pdf(path)
    return path


# ══════════════════════════════════════════════════════════════════════════
# ESTILO FRONTEND — DESIGN SYSTEM ENGEMON
# ══════════════════════════════════════════════════════════════════════════
def aplicar_estilo():
    st.markdown(f"""<style>
    /* ── Reset e base ── */
    [data-testid="stAppViewContainer"] {{ background: #F8FAFC; }}
    [data-testid="stSidebar"] {{
        background: {COR_AZUL} !important;
    }}
    [data-testid="stSidebar"] * {{ color: #fff !important; }}
    [data-testid="stSidebar"] .stRadio label {{ color: #fff !important; }}
    [data-testid="stSidebar"] hr {{ border-color: rgba(255,255,255,0.2) !important; }}

    /* ── Banner topo ── */
    .eng-banner {{
        background: linear-gradient(135deg, {COR_AZUL} 0%, {COR_AZUL_MED} 100%);
        color: #fff; padding: 20px 28px; border-radius: 10px;
        margin-bottom: 24px; display: flex; align-items: center;
        justify-content: space-between;
        box-shadow: 0 4px 16px rgba(0,32,96,0.18);
    }}
    .eng-banner-title {{
        font-size: 22px; font-weight: 900; letter-spacing: 1.2px;
        text-transform: uppercase;
    }}
    .eng-banner-sub {{ font-size: 12px; opacity: 0.75; margin-top: 2px; }}
    .eng-banner-badge {{
        background: {COR_VERMELHO}; color: #fff;
        padding: 5px 14px; border-radius: 20px;
        font-size: 11px; font-weight: 700; letter-spacing: 0.5px;
    }}

    /* ── Seção card ── */
    .eng-section {{
        background: {COR_AZUL}; color: #fff;
        padding: 10px 18px; border-radius: 6px;
        margin: 24px 0 14px 0;
        font-weight: 700; font-size: 13px; text-transform: uppercase;
        letter-spacing: 0.6px;
        border-left: 5px solid {COR_VERMELHO};
        display: flex; align-items: center; gap: 10px;
    }}

    /* ── Card de foto preview ── */
    .foto-card {{
        background: #fff; border: 1px solid {COR_BORDA};
        border-radius: 10px; padding: 14px;
        margin-bottom: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border-left: 4px solid {COR_AZUL};
    }}
    .foto-card:hover {{ box-shadow: 0 4px 16px rgba(0,32,96,0.12); }}
    .foto-num {{
        background: {COR_AZUL}; color: #fff;
        font-size: 10px; font-weight: 700; padding: 2px 8px;
        border-radius: 12px; display: inline-block; margin-bottom: 8px;
    }}

    /* ── Badge de status ── */
    .badge-ok {{
        background: #DCFCE7; color: {COR_VERDE};
        padding: 3px 10px; border-radius: 12px;
        font-size: 11px; font-weight: 700;
    }}
    .badge-warn {{
        background: #FEF3C7; color: {COR_AMARELO};
        padding: 3px 10px; border-radius: 12px;
        font-size: 11px; font-weight: 700;
    }}

    /* ── Métricas customizadas ── */
    .eng-metric {{
        background: #fff; border: 1px solid {COR_BORDA};
        border-radius: 10px; padding: 16px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }}
    .eng-metric-val {{
        font-size: 28px; font-weight: 900; color: {COR_AZUL};
    }}
    .eng-metric-label {{
        font-size: 11px; color: {COR_CINZA}; text-transform: uppercase;
        letter-spacing: 0.4px; margin-top: 2px;
    }}

    /* ── Botão primário ── */
    .stButton > button[data-testid="baseButton-primary"] {{
        background: {COR_AZUL} !important; color: #fff !important;
        border: none !important; border-radius: 8px !important;
        font-weight: 700 !important; text-transform: uppercase !important;
        letter-spacing: 0.4px !important;
    }}
    .stButton > button[data-testid="baseButton-primary"]:hover {{
        background: {COR_AZUL_MED} !important;
        box-shadow: 0 4px 12px rgba(0,32,96,0.25) !important;
    }}

    /* ── Inputs ── */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {{
        border: 1.5px solid {COR_BORDA} !important;
        border-radius: 6px !important;
    }}
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {{
        border-color: {COR_AZUL} !important;
        box-shadow: 0 0 0 3px rgba(0,32,96,0.08) !important;
    }}

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 4px; background: {COR_AZUL_LIGHT}; border-radius: 8px; padding: 4px;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 6px !important; font-weight: 600 !important;
        text-transform: uppercase; font-size: 12px;
        letter-spacing: 0.3px;
    }}
    .stTabs [aria-selected="true"] {{
        background: {COR_AZUL} !important; color: #fff !important;
    }}

    /* ── Divider ── */
    hr {{ border-color: {COR_BORDA}; }}
    </style>""", unsafe_allow_html=True)


def banner(subtitulo: str = ""):
    st.markdown(f"""
    <div class="eng-banner">
      <div>
        <div class="eng-banner-title">⚡ GIRCP</div>
        <div class="eng-banner-sub">GERADOR INTELIGENTE DE RELATÓRIOS E CONTROLE FOTOGRÁFICO
        {'— ' + subtitulo if subtitulo else ''}</div>
      </div>
      <div class="eng-banner-badge">ENGEMON OPSERVICES</div>
    </div>""", unsafe_allow_html=True)


def secao(icone: str, titulo: str):
    st.markdown(f'<div class="eng-section">{icone} &nbsp; {titulo}</div>',
                unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
# COMPONENTES REUTILIZÁVEIS
# ══════════════════════════════════════════════════════════════════════════
def _render_lista_fotos(key_lista: str, prefixo: str):
    """Renderiza a lista acumulada de fotos com campos editáveis e botão de remoção.
    Retorna a lista atualizada com os valores atuais dos campos."""
    fotos = st.session_state.get(key_lista, [])
    if not fotos:
        st.caption("NENHUMA FOTO ADICIONADA AINDA.")
        return fotos

    fotos_atualizadas = []
    for i, foto in enumerate(fotos):
        st.markdown(
            f'<div class="foto-card">'
            f'<span class="foto-num">FOTO {i+1:02d}</span>'
            f'&nbsp;&nbsp;<span style="font-size:9px;color:{COR_CINZA};font-family:monospace;">'
            f'ID: {foto.get("foto_id","—")}</span>'
            f'</div>',
            unsafe_allow_html=True
        )
        col_img, col_dados, col_del = st.columns([1, 3, 0.4])
        with col_img:
            st.image(
                f"data:{foto['type']};base64,{foto['base64']}",
                use_container_width=True
            )
        with col_dados:
            tit = st.text_input(
                f"TÍTULO {i+1}",
                value=foto.get("titulo", ""),
                placeholder="Ex: RELÓGIO NOVO INSTALADO",
                key=f"{prefixo}_tit_{i}"
            )
            desc = st.text_area(
                f"DESCRIÇÃO TÉCNICA {i+1}",
                value=foto.get("comentarios", ""),
                placeholder="Descreva o que a foto documenta...",
                key=f"{prefixo}_com_{i}",
                height=75
            )
        with col_del:
            st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
            if st.button("🗑️", key=f"{prefixo}_del_{i}",
                         help="Remover esta foto da lista"):
                fotos.pop(i)
                st.session_state[key_lista] = fotos
                st.rerun()

        foto_atualizada = foto.copy()
        foto_atualizada["titulo"]      = tit.strip() or f"Foto {i+1}"
        foto_atualizada["comentarios"] = desc.strip() or "N/A"
        fotos_atualizadas.append(foto_atualizada)
        st.divider()

    # Persiste as edições de título/descrição em tempo real
    st.session_state[key_lista] = fotos_atualizadas
    return fotos_atualizadas


def _uploader_com_lista(titulo_sec: str, caption: str,
                        key_up: str, key_lista: str,
                        key_gen: str, prefixo: str,
                        icone: str):
    """Uploader desacoplado do form: adiciona fotos à lista do session_state."""
    secao(icone, titulo_sec)
    st.caption(caption)

    # Geração dinâmica da key para resetar o uploader após adicionar
    if key_gen not in st.session_state:
        st.session_state[key_gen] = 0
    if key_lista not in st.session_state:
        st.session_state[key_lista] = []

    arquivos = st.file_uploader(
        f"SELECIONAR {titulo_sec}",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        key=f"{key_up}_{st.session_state[key_gen]}"
    )

    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        if st.button(
            f"➕ ADICIONAR À LISTA",
            key=f"btn_add_{key_up}",
            disabled=not arquivos,
            type="secondary",
            use_container_width=True
        ):
            import hashlib
            lista = st.session_state.get(key_lista, [])
            # IDs já presentes em ambas as listas — evita duplicatas cruzadas
            ids_ev = {f.get("foto_id") for f in st.session_state.get("_lista_ev", [])}
            ids_ex = {f.get("foto_id") for f in st.session_state.get("_lista_ex", [])}
            ids_existentes = ids_ev | ids_ex

            adicionadas = 0
            duplicadas  = []
            for arq in arquivos:
                raw     = arq.getvalue()
                foto_id = hashlib.sha256(raw).hexdigest()[:16]
                if foto_id in ids_existentes:
                    duplicadas.append(arq.name)
                    continue
                lista.append({
                    "foto_id":     foto_id,
                    "base64":      base64.b64encode(raw).decode("utf-8"),
                    "type":        arq.type,
                    "titulo":      "",
                    "comentarios": "",
                    "filename":    arq.name
                })
                ids_existentes.add(foto_id)
                adicionadas += 1

            st.session_state[key_lista] = lista
            st.session_state[key_gen] += 1

            if duplicadas:
                st.warning(
                    f"⚠️ {len(duplicadas)} FOTO(S) IGNORADA(S) POR DUPLICATA: "
                    + ", ".join(duplicadas)
                )
            if adicionadas:
                st.rerun()

    with col_info:
        n = len(st.session_state.get(key_lista, []))
        badge = "badge-ok" if n > 0 else "badge-warn"
        label = f"{n} FOTO(S) NA LISTA" if n > 0 else "LISTA VAZIA"
        st.markdown(
            f'<div style="margin-top:6px;">'
            f'<span class="{badge}">{label}</span></div>',
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)
    _render_lista_fotos(key_lista, prefixo)


# ══════════════════════════════════════════════════════════════════════════
# TELA: NOVO RELATÓRIO
# ══════════════════════════════════════════════════════════════════════════
def tela_novo():
    banner("NOVO RELATÓRIO")

    # ── Dados cadastrais (dentro de form para capturar no submit) ──
    secao("📋", "1. IDENTIFICAÇÃO DA INFRAESTRUTURA")
    c1, c2, c3 = st.columns(3)
    with c1:
        titulo  = st.text_input("TÍTULO DO RELATÓRIO",
                                value="Relatório Técnico de Vistoria",
                                key="novo_titulo")
        contato = st.text_input("CONTATO / TÉCNICO RESPONSÁVEL",
                                value=st.session_state.get("_tecnico_global", ""),
                                key="novo_contato")
    with c2:
        empresa  = st.text_input("EMPRESA", value="Engemon", key="novo_empresa")
        telefone = st.text_input("TELEFONE", value="(11) 94741-4606",
                                 key="novo_telefone")
    with c3:
        email   = st.text_input("E-MAIL", value="tecnico@engemon.com.br",
                                key="novo_email")
        site_id = st.text_input("IDENTIFICAÇÃO DO SITE",
                                placeholder="Ex: SMSMT15", key="novo_site")
        col_d, col_h = st.columns(2)
        with col_d:
            data_vis = st.date_input("DATA DA VISITA",
                                     value=datetime.today(), key="novo_data")
        with col_h:
            hora_vis = st.time_input("HORA", value=datetime.now().time(),
                                     key="novo_hora")
    data_hora = f"{data_vis.strftime('%d/%m/%Y')} às {hora_vis.strftime('%H:%M')}"

    st.divider()

    # ── Evidências (fora do form — lista editável em session_state) ──
    _uploader_com_lista(
        titulo_sec="2. EVIDÊNCIAS FOTOGRÁFICAS PRINCIPAIS",
        caption="FOTOS QUE DOCUMENTAM INTERVENÇÕES E SITUAÇÕES ENCONTRADAS.",
        key_up="up_ev", key_lista="_lista_ev",
        key_gen="_gen_ev", prefixo="ev", icone="📸"
    )

    st.divider()

    _uploader_com_lista(
        titulo_sec="3. ANEXOS ADICIONAIS (CONTEXTO / ANTES E DEPOIS)",
        caption="SITUAÇÃO ANTERIOR, PEÇAS SUBSTITUÍDAS, CONTEXTO GERAL.",
        key_up="up_ex", key_lista="_lista_ex",
        key_gen="_gen_ex", prefixo="ex", icone="📎"
    )

    st.divider()

    # ── Métricas ──
    fotos_ev = st.session_state.get("_lista_ev", [])
    fotos_ex = st.session_state.get("_lista_ex", [])
    mc1, mc2, mc3 = st.columns(3)
    with mc1:
        st.markdown(f'<div class="eng-metric"><div class="eng-metric-val">'
                    f'{len(fotos_ev)}</div>'
                    f'<div class="eng-metric-label">EVIDÊNCIAS</div></div>',
                    unsafe_allow_html=True)
    with mc2:
        st.markdown(f'<div class="eng-metric"><div class="eng-metric-val">'
                    f'{len(fotos_ex)}</div>'
                    f'<div class="eng-metric-label">ANEXOS</div></div>',
                    unsafe_allow_html=True)
    with mc3:
        total = len(fotos_ev) + len(fotos_ex)
        badge = "badge-ok" if total > 0 else "badge-warn"
        label = "PRONTO PARA SALVAR" if total > 0 else "SEM FOTOS"
        st.markdown(f'<div class="eng-metric"><div class="eng-metric-val">'
                    f'{total}</div>'
                    f'<div class="eng-metric-label">'
                    f'<span class="{badge}">{label}</span></div></div>',
                    unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Botão salvar (fora do form) ──
    col_save, col_clear = st.columns([3, 1])
    with col_save:
        if st.button("💾  SALVAR RELATÓRIO NO BANCO DE DADOS",
                     type="primary", use_container_width=True):
            if not site_id.strip():
                st.error("⚠️ A IDENTIFICAÇÃO DO SITE É OBRIGATÓRIA.")
                return
            if not fotos_ev:
                st.error("⚠️ ADICIONE PELO MENOS UMA EVIDÊNCIA FOTOGRÁFICA.")
                return

            dados = {
                "titulo":    sanitizar(titulo),
                "contato":   sanitizar(contato),
                "empresa":   sanitizar(empresa),
                "telefone":  sanitizar(telefone),
                "email":     sanitizar(email),
                "site_id":   sanitizar(site_id),
                "data_hora": data_hora
            }
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute('''INSERT INTO relatorios
                         (titulo,contato,empresa,telefone,email,
                          site_id,data_hora,fotos_json,extras_json)
                         VALUES (?,?,?,?,?,?,?,?,?)''',
                      (dados["titulo"], dados["contato"], dados["empresa"],
                       dados["telefone"], dados["email"], dados["site_id"],
                       dados["data_hora"],
                       json.dumps(fotos_ev), json.dumps(fotos_ex)))
            conn.commit()
            conn.close()

            # Limpar listas após salvar
            for k in ["_lista_ev", "_lista_ex", "_gen_ev", "_gen_ex"]:
                st.session_state.pop(k, None)

            st.success(f"✅ RELATÓRIO **{site_id}** SALVO COM SUCESSO! "
                       "ACESSE 'PESQUISAR E EXPORTAR' PARA GERAR O PDF.")
            st.balloons()
            st.rerun()

    with col_clear:
        if st.button("🗑️ LIMPAR TUDO", use_container_width=True):
            for k in ["_lista_ev", "_lista_ex", "_gen_ev", "_gen_ex"]:
                st.session_state.pop(k, None)
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════
# TELA: PESQUISAR / EDITAR / EXPORTAR
# ══════════════════════════════════════════════════════════════════════════
def tela_pesquisa():
    banner("PESQUISAR, EDITAR E EXPORTAR")

    secao("🔍", "BUSCAR RELATÓRIOS")
    col_busca, col_lim = st.columns([3, 1])
    with col_busca:
        termo = st.text_input("NOME DO SITE OU PARTE DO TÍTULO:",
                               placeholder="Ex: SMSMT15")
    with col_lim:
        limite = st.selectbox("EXIBIR", [10, 25, 50, 100], index=0)

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if termo.strip():
        c.execute("SELECT * FROM relatorios WHERE site_id LIKE ? OR titulo LIKE ? "
                  "ORDER BY id DESC LIMIT ?",
                  (f'%{termo}%', f'%{termo}%', limite))
    else:
        c.execute("SELECT * FROM relatorios ORDER BY id DESC LIMIT ?", (limite,))
    rows = c.fetchall()
    conn.close()

    if not rows:
        st.info("NENHUM RELATÓRIO ENCONTRADO. CRIE UM NA ABA 'NOVO RELATÓRIO'.")
        return

    # Totalizadores
    st.markdown("<br>", unsafe_allow_html=True)
    ta, tb, tc = st.columns(3)
    with ta:
        st.markdown(f'<div class="eng-metric"><div class="eng-metric-val">'
                    f'{len(rows)}</div><div class="eng-metric-label">RESULTADOS</div></div>',
                    unsafe_allow_html=True)
    with tb:
        total_ev = sum(len(json.loads(r[8] or "[]")) for r in rows)
        st.markdown(f'<div class="eng-metric"><div class="eng-metric-val">'
                    f'{total_ev}</div><div class="eng-metric-label">EVIDÊNCIAS</div></div>',
                    unsafe_allow_html=True)
    with tc:
        total_ex = sum(len(json.loads(r[9] or "[]")) for r in rows if len(r) > 9)
        st.markdown(f'<div class="eng-metric"><div class="eng-metric-val">'
                    f'{total_ex}</div><div class="eng-metric-label">ANEXOS</div></div>',
                    unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    for row in rows:
        lid  = row[0]
        fotos_db  = json.loads(row[8] or "[]")
        extras_db = json.loads(row[9] or "[]") if len(row) > 9 else []
        n_fotos = len(fotos_db)
        n_extras = len(extras_db)

        with st.expander(
            f"📍 **{row[6]}**  |  {row[7]}  |  "
            f"{n_fotos} evidência(s)  {n_extras} anexo(s)  |  ID #{lid}"
        ):
            key_del = f"del_{lid}"
            if key_del not in st.session_state:
                st.session_state[key_del] = []

            with st.form(f"form_ed_{lid}"):
                secao("📋", "DADOS CADASTRAIS")
                e1, e2, e3 = st.columns(3)
                with e1:
                    ed_tit  = st.text_input("TÍTULO", value=row[1], key=f"tit_{lid}")
                    ed_cont = st.text_input("CONTATO", value=row[2], key=f"con_{lid}")
                with e2:
                    ed_emp  = st.text_input("EMPRESA", value=row[3], key=f"emp_{lid}")
                    ed_tel  = st.text_input("TELEFONE", value=row[4], key=f"tel_{lid}")
                with e3:
                    ed_mail = st.text_input("E-MAIL", value=row[5], key=f"eml_{lid}")
                    ed_site = st.text_input("SITE", value=row[6], key=f"sit_{lid}")
                    ed_data = st.text_input("DATA E HORA", value=row[7], key=f"dat_{lid}")

                secao("📸", "EDITAR EVIDÊNCIAS")
                fotos_edit = []
                for k, f in enumerate(fotos_db):
                    if k in st.session_state[key_del]:
                        continue
                    col_i, col_d = st.columns([1, 4])
                    with col_i:
                        st.image(f"data:{f['type']};base64,{f['base64']}", width=110)
                    with col_d:
                        nt = st.text_input(f"TÍTULO EVIDÊNCIA #{k+1}",
                                           value=f.get('titulo', ''),
                                           key=f"ft_{lid}_{k}")
                        nc = st.text_area(f"DESCRIÇÃO #{k+1}",
                                          value=f.get('comentarios', ''),
                                          key=f"fc_{lid}_{k}", height=65)
                    fc = f.copy()
                    fc['titulo'] = nt
                    fc['comentarios'] = nc
                    fotos_edit.append(fc)

                secao("📎", "EDITAR ANEXOS")
                extras_edit = []
                for k, f in enumerate(extras_db):
                    col_i, col_d = st.columns([1, 4])
                    with col_i:
                        st.image(f"data:{f['type']};base64,{f['base64']}", width=110)
                    with col_d:
                        nt = st.text_input(f"TÍTULO ANEXO #{k+1}",
                                           value=f.get('titulo', ''),
                                           key=f"et_{lid}_{k}")
                        nc = st.text_area(f"DESCRIÇÃO ANEXO #{k+1}",
                                          value=f.get('comentarios', ''),
                                          key=f"ec_{lid}_{k}", height=65)
                    fc = f.copy()
                    fc['titulo'] = nt
                    fc['comentarios'] = nc
                    extras_edit.append(fc)

                secao("➕", "ADICIONAR NOVAS FOTOS")
                novas_arq = st.file_uploader(
                    "ENVIAR NOVAS IMAGENS",
                    type=['png', 'jpg', 'jpeg'],
                    accept_multiple_files=True,
                    key=f"new_{lid}"
                )
                novas = []
                if novas_arq:
                    import hashlib as _hl
                    ids_existentes = {f.get("foto_id") for f in fotos_db + extras_db}
                    for idx_n, arq in enumerate(novas_arq):
                        raw     = arq.getvalue()
                        foto_id = _hl.sha256(raw).hexdigest()[:16]
                        col_i, col_d = st.columns([1, 4])
                        with col_i:
                            st.image(arq, width=90)
                            st.caption(f"ID: {foto_id}")
                        with col_d:
                            if foto_id in ids_existentes:
                                st.warning(f"⚠️ DUPLICATA IGNORADA: {arq.name}")
                                continue
                            nt = st.text_input(f"TÍTULO NOVA FOTO {idx_n+1}",
                                               key=f"n_t_{lid}_{idx_n}")
                            nc = st.text_area(f"DESCRIÇÃO NOVA FOTO {idx_n+1}",
                                              key=f"n_c_{lid}_{idx_n}", height=55)
                        novas.append({
                            "foto_id":     foto_id,
                            "base64":      base64.b64encode(raw).decode("utf-8"),
                            "type":        arq.type,
                            "titulo":      nt.strip() if nt else f"Nova Foto {idx_n+1}",
                            "comentarios": nc.strip() if nc else "N/A",
                            "filename":    arq.name
                        })
                        ids_existentes.add(foto_id)

                col_s, col_del = st.columns([2, 1])
                with col_s:
                    salvar = st.form_submit_button(
                        "🔄  SALVAR ALTERAÇÕES",
                        type="primary", use_container_width=True
                    )
                with col_del:
                    excluir_sel = st.selectbox(
                        "EXCLUIR EVIDÊNCIA:",
                        ["-- SELECIONE --"] + [
                            f"#{k+1}: {f.get('titulo','')}"
                            for k, f in enumerate(fotos_db)
                            if k not in st.session_state[key_del]
                        ],
                        key=f"sel_{lid}"
                    )

            # Ações fora do form
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                if excluir_sel != "-- SELECIONE --":
                    if st.button(f"❌ CONFIRMAR EXCLUSÃO", key=f"xbt_{lid}"):
                        idx = int(excluir_sel.split("#")[1].split(":")[0]) - 1
                        st.session_state[key_del].append(idx)
                        st.success("EVIDÊNCIA REMOVIDA. CLIQUE EM SALVAR ALTERAÇÕES.")
                        st.rerun()

            with col_b:
                if st.button("🗑️ LIMPAR TODAS AS FOTOS", key=f"lim_{lid}"):
                    st.session_state[f"conf_lim_{lid}"] = True

            with col_c:
                if st.button(f"📄 GERAR PDF — {row[6]}", key=f"pdf_{lid}",
                             type="primary"):
                    dados_pdf = {
                        "titulo": row[1], "contato": row[2], "empresa": row[3],
                        "telefone": row[4], "email": row[5],
                        "site_id": row[6], "data_hora": row[7]
                    }
                    with st.spinner("GERANDO PDF..."):
                        path = gerar_pdf(dados_pdf, fotos_db, extras_db)
                    with open(path, "rb") as f_pdf:
                        st.download_button(
                            "⬇️ BAIXAR PDF",
                            data=f_pdf,
                            file_name=os.path.basename(path),
                            mime="application/pdf",
                            key=f"dl_{lid}"
                        )

            # Confirmação limpar tudo
            if st.session_state.get(f"conf_lim_{lid}"):
                st.warning("⚠️ TEM CERTEZA? ESTA AÇÃO APAGARÁ **TODAS** AS FOTOS.")
                cs, cn = st.columns(2)
                if cs.button("✅ SIM, APAGAR TUDO", key=f"sim_{lid}"):
                    conn2 = sqlite3.connect(DB_NAME)
                    c2 = conn2.cursor()
                    c2.execute("UPDATE relatorios SET fotos_json='[]', extras_json='[]' WHERE id=?",
                               (lid,))
                    conn2.commit()
                    conn2.close()
                    st.session_state.pop(f"conf_lim_{lid}", None)
                    st.rerun()
                if cn.button("❌ CANCELAR", key=f"nao_{lid}"):
                    st.session_state.pop(f"conf_lim_{lid}", None)
                    st.rerun()

            # Salvar alterações
            if salvar:
                fotos_finais = [f for k, f in enumerate(fotos_db)
                                if k not in st.session_state[key_del]]
                fotos_finais += novas
                fotos_finais_edit = []
                idx_edit = 0
                for k, f in enumerate(fotos_db):
                    if k not in st.session_state[key_del]:
                        if idx_edit < len(fotos_edit):
                            fotos_finais_edit.append(fotos_edit[idx_edit])
                            idx_edit += 1
                        else:
                            fotos_finais_edit.append(f)
                fotos_finais_edit += novas
                st.session_state[key_del] = []

                conn3 = sqlite3.connect(DB_NAME)
                c3 = conn3.cursor()
                c3.execute('''UPDATE relatorios
                              SET titulo=?,contato=?,empresa=?,telefone=?,
                                  email=?,site_id=?,data_hora=?,
                                  fotos_json=?,extras_json=?
                              WHERE id=?''',
                           (ed_tit, ed_cont, ed_emp, ed_tel, ed_mail,
                            ed_site, ed_data,
                            json.dumps(fotos_finais_edit),
                            json.dumps(extras_edit),
                            lid))
                conn3.commit()
                conn3.close()
                st.success("✅ RELATÓRIO ATUALIZADO COM SUCESSO!")
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════
# TELA: DASHBOARD
# ══════════════════════════════════════════════════════════════════════════
def tela_dashboard():
    banner("DASHBOARD")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, site_id, data_hora, fotos_json, extras_json, criado_em FROM relatorios ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()

    if not rows:
        st.info("NENHUM RELATÓRIO CADASTRADO AINDA.")
        return

    total_rel  = len(rows)
    total_ev   = sum(len(json.loads(r[3] or "[]")) for r in rows)
    total_ex   = sum(len(json.loads(r[4] or "[]")) for r in rows if r[4])
    sites_uniq = len(set(r[1] for r in rows))

    secao("📊", "RESUMO GERAL")
    m1, m2, m3, m4 = st.columns(4)
    for col, val, lbl in [
        (m1, total_rel,  "RELATÓRIOS"),
        (m2, sites_uniq, "SITES ÚNICOS"),
        (m3, total_ev,   "EVIDÊNCIAS"),
        (m4, total_ex,   "ANEXOS"),
    ]:
        col.markdown(f'<div class="eng-metric"><div class="eng-metric-val">{val}</div>'
                     f'<div class="eng-metric-label">{lbl}</div></div>',
                     unsafe_allow_html=True)

    secao("📋", "ÚLTIMOS 10 RELATÓRIOS")
    import pandas as pd
    df = pd.DataFrame([{
        "ID": r[0],
        "SITE": r[1],
        "DATA/HORA": r[2],
        "EVIDÊNCIAS": len(json.loads(r[3] or "[]")),
        "ANEXOS": len(json.loads(r[4] or "[]")) if r[4] else 0,
    } for r in rows[:10]])
    st.dataframe(df, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="GIRCP | Engemon OpServices",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)
init_db()
aplicar_estilo()

with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center;padding:20px 0 10px 0;">
      <div style="font-size:28px;">⚡</div>
      <div style="font-size:18px;font-weight:900;letter-spacing:1.5px;color:#fff;">GIRCP</div>
      <div style="font-size:10px;opacity:0.65;color:#fff;margin-top:2px;">
        ENGEMON OPSERVICES
      </div>
    </div>""", unsafe_allow_html=True)
    st.markdown("---")

    # Técnico global
    tec = st.text_input("👷 TÉCNICO EM CAMPO:",
                         value=st.session_state.get("_tecnico_global", ""),
                         placeholder="Seu nome",
                         key="_tec_sidebar_rel")
    if tec.strip():
        st.session_state["_tecnico_global"] = tec.strip()
    st.markdown("---")

    menu = st.radio(
        "NAVEGAÇÃO:",
        ["📝 NOVO RELATÓRIO", "🔍 PESQUISAR E EXPORTAR", "📊 DASHBOARD"],
        label_visibility="collapsed"
    )
    st.markdown("---")
    st.markdown(f"""<div style="font-size:10px;opacity:0.55;color:#fff;text-align:center;">
    v3.0 · {datetime.now().strftime('%d/%m/%Y')}<br>
    Dados protegidos pela LGPD</div>""", unsafe_allow_html=True)

if menu == "📝 NOVO RELATÓRIO":
    tela_novo()
elif menu == "🔍 PESQUISAR E EXPORTAR":
    tela_pesquisa()
elif menu == "📊 DASHBOARD":
    tela_dashboard()