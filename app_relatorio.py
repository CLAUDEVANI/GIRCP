"""
GIRCP — Gerador Inteligente de Relatórios e Controle Fotográfico
| v3.3 (Cartografia de Alta Precisão e Tipografia Escalada)
"""

import streamlit as st
import sqlite3
import base64
import json
import os
import io
import hashlib
import html as html_mod
import pandas as pd
import plotly.express as px
import xml.etree.ElementTree as ET
from datetime import datetime
from PIL import Image
from weasyprint import HTML

# ==============================================================================
# 0. CONTROLE DE ACESSO E SEGURANÇA (LGPD)
# ==============================================================================
def check_password():
    def password_entered():
        senha_correta = st.secrets.get("senha_acesso", "GIRCP2026")
        if st.session_state["password_input"] == senha_correta:
            st.session_state["password_correct"] = True
            del st.session_state["password_input"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.markdown("### 🔒 GIRCP - Acesso Restrito")
    st.text_input("Digite a senha de acesso", type="password", on_change=password_entered, key="password_input")
    
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 Senha incorreta.")
    return False

# ══════════════════════════════════════════════════════════════════════════
# CONSTANTES E CONFIGURAÇÕES
# ══════════════════════════════════════════════════════════════════════════
COR_AZUL        = "#002060"
COR_AZUL_MED    = "#003087"
COR_AZUL_LIGHT  = "#EBF0FA"
COR_VERMELHO    = "#DA291C"
COR_CINZA       = "#64748B"
COR_CINZA_LIGHT = "#F1F5F9"
COR_BORDA       = "#CBD5E1"
COR_TEXTO       = "#1E293B"
COR_VERDE       = "#16A34A"
COR_AMARELO     = "#D97706"

DB_NAME = "laudos_corp_v3.db"
FOTOS_DIR = "banco_fotos_gircp"
LBL_TITULO = "TÍTULO"
LBL_DESCRICAO = "DESCRIÇÃO"
OPT_DIGITAR_MANUAL = "-- Digitar Manualmente --"
OPT_SELECIONE = "-- SELECIONE --"

os.makedirs(FOTOS_DIR, exist_ok=True)

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
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
                endereco    TEXT,
                data_hora   TEXT,
                fotos_json  TEXT DEFAULT '[]',
                extras_json TEXT DEFAULT '[]',
                criado_em   TEXT DEFAULT (datetime('now','localtime'))
            )
        ''')
        for col in ("criado_em TEXT", "endereco TEXT", "tecnico TEXT", "numero_relatorio TEXT", "revisao TEXT", "latitude REAL", "longitude REAL"):
            try:
                c.execute(f"ALTER TABLE relatorios ADD COLUMN {col}")
            except sqlite3.OperationalError:
                pass
        c.execute("CREATE TABLE IF NOT EXISTS seq_relatorio (ultimo INTEGER DEFAULT 0)")
        c.execute("INSERT INTO seq_relatorio SELECT 0 WHERE NOT EXISTS (SELECT 1 FROM seq_relatorio)")
        conn.commit()

def sanitizar(texto: str) -> str:
    """Escapa entidades HTML e previne injeção de script (XSS)."""
    return html_mod.escape(str(texto or '').strip())

def comprimir_para_pdf(raw: bytes, max_px: int = 1200, qualidade: int = 78) -> bytes:
    img = Image.open(io.BytesIO(raw)).convert('RGB')
    img.thumbnail((max_px, max_px), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=qualidade, optimize=True)
    return buf.getvalue()

def proximo_numero_relatorio(conn) -> str:
    conn.execute("UPDATE seq_relatorio SET ultimo = ultimo + 1")
    ultimo = conn.execute("SELECT ultimo FROM seq_relatorio").fetchone()[0]
    return f"GIRCP-{datetime.now().year}-{ultimo:04d}"

def _carregar_b64(caminho: str) -> str:
    if os.path.exists(caminho):
        with open(caminho, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')
    return ""

def _css_pdf() -> str:
    return f"""
    @page {{ size: A4; margin: 14mm 14mm 18mm 14mm; 
        @bottom-left {{ content: "CONFIDENCIAL • USO INTERNO • Dados protegidos pela LGPD | Sistema Corporativo GIRCP"; font-size: 7pt; color: {COR_CINZA}; font-family: 'Segoe UI', Arial, sans-serif; }}
        @bottom-right {{ content: "Página " counter(page) " de " counter(pages); font-size: 7pt; color: {COR_CINZA}; font-family: 'Segoe UI', Arial, sans-serif; }}
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Segoe UI', Helvetica, Arial, sans-serif; color: {COR_TEXTO}; font-size: 9.5pt; line-height: 1.5; background: #fff; }}
    .watermark {{ position: fixed; top: 38%; left: 50%; transform: translate(-50%, -50%); z-index: -999; width: 65%; opacity: 0.06; }}
    .watermark img {{ width: 100%; }}
    .page-header {{ display: flex; justify-content: space-between; align-items: flex-end; border-bottom: 3px solid {COR_AZUL}; padding-bottom: 10px; margin-bottom: 22px; }}
    .header-titulo {{ color: {COR_AZUL}; font-size: 19pt; font-weight: 900; text-transform: uppercase; letter-spacing: 0.8px; }}
    .header-acento {{ display: inline-block; width: 36px; height: 4px; background: {COR_VERMELHO}; margin-bottom: 4px; }}
    .header-data {{ text-align: right; color: {COR_CINZA}; font-size: 9pt; }}
    .header-data strong {{ color: {COR_AZUL}; font-size: 11pt; }}
    .section-header {{ background: {COR_AZUL}; color: #fff; font-weight: 700; font-size: 10pt; padding: 7px 14px; margin-top: 22px; margin-bottom: 14px; text-transform: uppercase; border-left: 5px solid {COR_VERMELHO}; border-radius: 2px; }}
    .dados-table {{ width: 100%; border-collapse: collapse; margin-bottom: 18px; border: 1px solid {COR_BORDA}; border-radius: 4px; overflow: hidden; }}
    .dados-table td {{ border: 1px solid {COR_BORDA}; padding: 9px 13px; vertical-align: middle; }}
    .dados-table td.label {{ background: {COR_AZUL_LIGHT}; font-weight: 700; color: {COR_AZUL}; text-transform: uppercase; font-size: 7.8pt; width: 20%; }}
    .dados-table td.value {{ color: {COR_TEXTO}; font-size: 9.5pt; width: 30%; }}
    .card-evidencia {{ width: 100%; border-collapse: collapse; margin-bottom: 14px; border: 1px solid {COR_BORDA}; border-radius: 6px; overflow: hidden; page-break-inside: avoid; background: #fff; }}
    .card-evidencia td {{ vertical-align: top; }}
    .card-num {{ background: {COR_AZUL}; color: #fff; font-size: 8pt; font-weight: 700; padding: 3px 8px; text-align: center; writing-mode: vertical-rl; min-width: 22px; }}
    .col-foto {{ width: 43%; background: {COR_CINZA_LIGHT}; padding: 10px; text-align: center; border-right: 1px solid {COR_BORDA}; }}
    .col-foto img {{ width: 100%; max-height: 210px; object-fit: contain; border-radius: 3px; background: #fff; }}
    .col-texto {{ width: 57%; padding: 14px 16px; }}
    .foto-titulo {{ font-weight: 800; color: {COR_AZUL}; font-size: 11pt; text-transform: uppercase; border-bottom: 2px solid {COR_AZUL_LIGHT}; padding-bottom: 7px; margin-bottom: 10px; }}
    .label-desc {{ font-size: 8pt; font-weight: 700; color: {COR_AZUL}; margin-bottom: 4px; }}
    .foto-desc {{ font-size: 9pt; color: {COR_TEXTO}; background: {COR_CINZA_LIGHT}; padding: 9px 11px; border-left: 3px solid {COR_VERMELHO}; border-radius: 0 4px 4px 0; line-height: 1.5; white-space: pre-wrap; }}
    .assinatura-wrapper {{ margin: 44px auto 0 auto; width: 300px; text-align: center; page-break-inside: avoid; }}
    .assinatura-img {{ max-width: 180px; height: auto; display: block; margin: 0 auto -10px auto; }}
    .assinatura-linha {{ border-top: 1.5px solid {COR_TEXTO}; margin: 0 0 6px 0; }}
    .assinatura-nome {{ font-weight: 700; color: {COR_AZUL}; font-size: 9.5pt; }}
    .assinatura-cargo {{ font-size: 8pt; color: {COR_CINZA}; }}
    .logo-wrapper {{ margin-top: 14px; }}
    .logo-img {{ max-width: 140px; height: auto; display: block; margin: 0 auto; }}
    .badge {{ display:inline-block; padding:2px 10px; border-radius:12px; font-size:7.5pt; font-weight:700; margin-bottom:6px; }}
    .badge-critico  {{ background:#DA291C; color:#fff; }}
    .badge-obs      {{ background:#D97706; color:#fff; }}
    .badge-normal   {{ background:#16A34A; color:#fff; }}
    """

def _obter_b64_de_foto(f: dict) -> str:
    if "caminho" in f and os.path.exists(f["caminho"]):
        with open(f["caminho"], "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    return f.get('base64', '')

def gerar_pdf(dados: dict, fotos: list, extras: list = None) -> tuple[bytes, str]:
    extras = extras or []
    b64_wm  = _carregar_b64("logo_empresa.png")
    b64_sig = _carregar_b64("assinatura_tecnico.png")
    b64_logo = _carregar_b64("logo_empresa.png")

    wm_html = f'<div class="watermark"><img src="data:image/jpeg;base64,{b64_wm}"/></div>' if b64_wm else ""
    sig_img = f'<img class="assinatura-img" src="data:image/png;base64,{b64_sig}"/>' if b64_sig else '<div style="height:40px;"></div>'
    logo_img = f'<img class="logo-img" src="data:image/png;base64,{b64_logo}"/>' if b64_logo else ""

    fotos_html = ""
    for i, f in enumerate(fotos, 1):
        b64 = _obter_b64_de_foto(f)
        mime = 'image/jpeg'
        tit  = sanitizar(f.get('titulo', f'Evidência {i}')).upper()
        desc = sanitizar(f.get('comentarios', 'N/A'))
        sev  = f.get('severidade', 'Normal')
        cls_b = {'Crítico': 'badge-critico', 'Critico': 'badge-critico', 'Observação': 'badge-obs',  'Observacao': 'badge-obs'}.get(sev, 'badge-normal')
        cat  = sanitizar(f.get('categoria', 'Geral'))
        fotos_html += f"""
        <table class="card-evidencia">
          <tr>
            <td class="card-num">{i:02d}</td>
            <td class="col-foto"><img src="data:{mime};base64,{b64}"/></td>
            <td class="col-texto">
              <div class="foto-titulo">{tit}</div>
              <span class="badge {cls_b}">{sanitizar(sev)}</span>
              <span style="font-size:7.5pt;color:{COR_CINZA};margin-left:6px;">{cat}</span>
              <div class="label-desc" style="margin-top:6px;">Descrição Técnica:</div>
              <div class="foto-desc">{desc}</div>
            </td>
          </tr>
        </table>"""

    extras_html = ""
    if extras:
        extras_html = '<div style="page-break-before:always;"></div><div class="section-header">3 &nbsp; ANEXOS ADICIONAIS</div>'
        for i, f in enumerate(extras, 1):
            b64  = _obter_b64_de_foto(f)
            mime = f.get('type', 'image/jpeg')
            tit  = sanitizar(f.get('titulo', f'Anexo {i}')).upper()
            desc = sanitizar(f.get('comentarios', 'N/A'))
            extras_html += f"""
            <table class="card-evidencia">
              <tr>
                <td class="card-num">A{i:02d}</td>
                <td class="col-foto"><img src="data:{mime};base64,{b64}"/></td>
                <td class="col-texto">
                  <div class="foto-titulo">{tit}</div>
                  <div class="label-desc">Descrição / Contexto:</div>
                  <div class="foto-desc">{desc}</div>
                </td>
              </tr>
            </table>"""

    html = f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8"><style>{_css_pdf()}</style></head>
<body>
{wm_html}
<div class="page-header">
  <div><div class="header-acento"></div><div class="header-titulo">Relatório de Visita Técnica</div></div>
  <div class="header-data">Data da Vistoria:<br><strong>{sanitizar(dados.get('data_hora',''))}</strong></div>
</div>
<div class="section-header">1 &nbsp; DADOS CADASTRAIS DA INFRAESTRUTURA</div>
<table class="dados-table">
  <tr><td class="label">N.º DO RELATÓRIO</td><td class="value">{sanitizar(dados.get('numero_relatorio','-'))}</td><td class="label">REVISÃO</td><td class="value">{sanitizar(dados.get('revisao','Rev.00'))}</td></tr>
  <tr><td class="label">SITE / IDENTIFICAÇÃO</td><td class="value">{sanitizar(dados.get('site_id',''))}</td><td class="label">TÍTULO</td><td class="value">{sanitizar(dados.get('titulo',''))}</td></tr>
  <tr><td class="label">ENDEREÇO FÍSICO</td><td class="value" colspan="3">{sanitizar(dados.get('endereco',''))}</td></tr>
  <tr><td class="label">TÉCNICO EM CAMPO</td><td class="value" colspan="3">{sanitizar(dados.get('tecnico', dados.get('contato','')))}</td></tr>
  <tr><td class="label">EMPRESA</td><td class="value">{sanitizar(dados.get('empresa',''))}</td><td class="label">CONTATO TÉCNICO</td><td class="value">{sanitizar(dados.get('contato',''))}</td></tr>
  <tr><td class="label">TELEFONE</td><td class="value">{sanitizar(dados.get('telefone',''))}</td><td class="label">E-MAIL</td><td class="value">{sanitizar(dados.get('email',''))}</td></tr>
</table>
<div class="section-header">2 &nbsp; REGISTRO FOTOGRÁFICO E EVIDÊNCIAS</div>
{fotos_html}
{extras_html}
<div class="assinatura-wrapper">{sig_img}<div class="assinatura-linha"></div><div class="assinatura-nome">{sanitizar(dados.get('contato','Responsável Técnico'))}</div><div class="assinatura-cargo">Responsável Técnico</div><div class="logo-wrapper">{logo_img}</div></div>
</body></html>"""

    nome = f"Relatorio_{sanitizar(dados.get('site_id','SITE')).replace(' ','_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    pdf_bytes = HTML(string=html).write_pdf()
    return pdf_bytes, nome

def aplicar_estilo():
    st.markdown(f"""<style>
    [data-testid="stAppViewContainer"] {{ background: #F8FAFC; }}
    [data-testid="stSidebar"] {{ background: {COR_AZUL} !important; }}
    [data-testid="stSidebar"] * {{ color: #fff !important; }}
    .eng-banner {{ background: linear-gradient(135deg, {COR_AZUL} 0%, {COR_AZUL_MED} 100%); color: #fff; padding: 20px 28px; border-radius: 10px; margin-bottom: 24px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 4px 16px rgba(0,32,96,0.18); }}
    .eng-banner-title {{ font-size: 22px; font-weight: 900; letter-spacing: 1.2px; text-transform: uppercase; }}
    .eng-banner-badge {{ background: {COR_VERMELHO}; color: #fff; padding: 5px 14px; border-radius: 20px; font-size: 11px; font-weight: 700; letter-spacing: 0.5px; }}
    .eng-section {{ background: {COR_AZUL}; color: #fff; padding: 10px 18px; border-radius: 6px; margin: 24px 0 14px 0; font-weight: 700; font-size: 13px; text-transform: uppercase; border-left: 5px solid {COR_VERMELHO}; }}
    </style>""", unsafe_allow_html=True)

def banner(subtitulo: str = ""):
    subtitulo_seguro = sanitizar(subtitulo)
    sub_html = f" &mdash; {subtitulo_seguro}" if subtitulo_seguro else ""
    st.markdown(f"""
    <div class="eng-banner">
      <div>
        <div class="eng-banner-title">⚡ GIRCP</div>
        <div style="font-size: 12px; opacity: 0.75; margin-top: 2px;">GERADOR INTELIGENTE DE RELATÓRIOS E CONTROLE FOTOGRÁFICO{sub_html}</div>
      </div>
      <div class="eng-banner-badge">SISTEMA CORPORATIVO</div>
    </div>""", unsafe_allow_html=True)

def secao(icone: str, titulo: str):
    st.markdown(f'<div class="eng-section">{sanitizar(icone)} &nbsp; {sanitizar(titulo)}</div>', unsafe_allow_html=True)

def _parse_kml_to_dataframe(arquivo_kml):
    tree = ET.parse(arquivo_kml)
    root = tree.getroot()
    
    for elem in root.iter():
        if '}' in elem.tag:
            elem.tag = elem.tag.split('}', 1)[1]
            
    dados = []
    for placemark in root.findall('.//Placemark'):
        name_node = placemark.find('.//name')
        site_id = name_node.text.strip() if name_node is not None and name_node.text else "SEM NOME"
        
        lat, lon = 0.0, 0.0
        
        # 1. Padrão KML Genérico (coordinates)
        coords_node = placemark.find('.//coordinates')
        if coords_node is not None and coords_node.text:
            coords_str = coords_node.text.strip().split()
            if coords_str:
                valores = coords_str[0].split(',')
                try:
                    lon, lat = float(valores[0]), float(valores[1])
                except (ValueError, IndexError):
                    pass

        # 2. Extração Avançada KML Claro/Telecom (ExtendedData / SimpleData)
        ext_data = placemark.find('.//ExtendedData')
        endereco, grupo = "", ""
        if ext_data is not None:
            # Varredura do formato padrão Google Earth
            for data in ext_data.findall('.//Data'):
                n_attr = str(data.get('name', '')).upper()
                v_node = data.find('.//value')
                val = v_node.text.strip() if v_node is not None and v_node.text else ""
                
                if 'ENDERE' in n_attr or 'RUA' in n_attr: endereco = val
                elif n_attr in ['GRUPO', 'ÁREA', 'AREA']: grupo = val
                elif 'LATITUDE' in n_attr or 'LAT' == n_attr:
                    try: lat = float(val.replace(',', '.'))
                    except ValueError: pass
                elif 'LONGITUDE' in n_attr or 'LON' == n_attr:
                    try: lon = float(val.replace(',', '.'))
                    except ValueError: pass
            
            # Varredura do formato Claro/Ericsson
            for sdata in ext_data.findall('.//SimpleData'):
                n_attr = str(sdata.get('name', '')).upper()
                val = sdata.text.strip() if sdata.text else ""
                
                if 'ENDERE' in n_attr or 'RUA' in n_attr: endereco = val
                elif n_attr in ['GRUPO', 'ÁREA', 'AREA']: grupo = val
                elif 'LATITUDE' in n_attr or 'LAT' == n_attr:
                    try: lat = float(val.replace(',', '.'))
                    except ValueError: pass
                elif 'LONGITUDE' in n_attr or 'LON' == n_attr:
                    try: lon = float(val.replace(',', '.'))
                    except ValueError: pass
                
        dados.append({'SITE': site_id, 'ENDEREÇO': endereco, 'GRUPO': grupo, 'LATITUDE': lat, 'LONGITUDE': lon})
    return pd.DataFrame(dados)

def _carregar_base_dados(arquivo):
    if not arquivo: return None
    try:
        if arquivo.name.lower().endswith('.kml'): return _parse_kml_to_dataframe(arquivo)
        else: return pd.read_excel(arquivo)
    except Exception as e:
        st.error(f"Erro ao processar a base: {e}")
        return None

def _obter_filtros_cascata(df_sites):
    if df_sites is None or df_sites.empty: return "", "", 0.0, 0.0
    col_site = next((col for col in df_sites.columns if str(col).upper() in ['SITE', 'SITES', 'IDENTIFICAÇÃO', 'NOME DO SITE']), None)
    if not col_site: return "", "", 0.0, 0.0
    col_grupo = next((col for col in df_sites.columns if 'GRUPO' in str(col).upper() or 'ÁREA' in str(col).upper() or 'AREA' in str(col).upper()), None)
    
    df_filtrado = df_sites
    c1, c2 = st.columns(2)
    with c1:
        if col_grupo:
            grupos = ["-- Todos --"] + sorted(df_sites[col_grupo].dropna().astype(str).unique().tolist())
            grupo_sel = st.selectbox("📌 1. Filtrar por Grupo/Tecnologia:", grupos, key="filtro_grupo_spc")
            if grupo_sel != "-- Todos --": df_filtrado = df_sites[df_sites[col_grupo] == grupo_sel]
    with c2:
        lista_sites = df_filtrado[col_site].dropna().astype(str).unique().tolist()
        escolha = st.selectbox("📌 2. Selecione o Site:", [OPT_DIGITAR_MANUAL] + sorted(lista_sites), key="filtro_escolha_site")
    
    if escolha == OPT_DIGITAR_MANUAL: return "", "", 0.0, 0.0
    col_end = next((col for col in df_sites.columns if 'ENDERE' in str(col).upper() or 'RUA' in str(col).upper()), None)
    endereco_val, lat_val, lon_val = "", 0.0, 0.0
    
    linha = df_sites[df_sites[col_site] == escolha]
    if not linha.empty: 
        if col_end: endereco_val = str(linha.iloc[0][col_end])
        if 'LATITUDE' in linha.columns: lat_val = float(linha.iloc[0]['LATITUDE'])
        if 'LONGITUDE' in linha.columns: lon_val = float(linha.iloc[0]['LONGITUDE'])
            
    return escolha, endereco_val, lat_val, lon_val

def _salvar_novo_relatorio(dados_cad, fotos, extras):
    if not dados_cad['site_id'].strip():
        st.error("⚠️ A IDENTIFICAÇÃO DO SITE É OBRIGATÓRIA.")
        return
    with sqlite3.connect(DB_NAME) as conn:
        num_rel = proximo_numero_relatorio(conn)
        conn.execute(
            '''INSERT INTO relatorios
               (titulo, contato, empresa, telefone, email, site_id, endereco,
                data_hora, fotos_json, extras_json, tecnico, numero_relatorio, revisao, latitude, longitude)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (sanitizar(dados_cad['titulo']), sanitizar(dados_cad['contato']),
             sanitizar(dados_cad['empresa']), sanitizar(dados_cad['telefone']),
             sanitizar(dados_cad['email']), sanitizar(dados_cad['site_id']),
             sanitizar(dados_cad['endereco']), sanitizar(dados_cad['data_hora']),
             json.dumps(fotos), json.dumps(extras),
             sanitizar(dados_cad.get('tecnico', dados_cad['contato'])),
             num_rel, 'Rev.00', dados_cad['latitude'], dados_cad['longitude']))
    st.success(f"✅ RELATÓRIO **{sanitizar(dados_cad['site_id'])}** SALVO! ACESSE A ABA PARA GERAR PDF.")
    st.balloons()

def tela_novo():
    banner("NOVO RELATÓRIO")
    if "ordem_evidencias" not in st.session_state: st.session_state["ordem_evidencias"] = []

    st.info("💡 **Inteligência Analítica:** Importe arquivo **.KML** ou **.XLSX** para criar filtro em cascata.")
    arquivo_base = st.file_uploader("Importar Base de Sites (Opcional)", type=["kml", "xlsx", "xls"])
    df_sites = _carregar_base_dados(arquivo_base)
    site_selecionado, endereco_autofill, lat_autofill, lon_autofill = _obter_filtros_cascata(df_sites)

    secao("📸", "2. EVIDÊNCIAS FOTOGRÁFICAS PRINCIPAIS")
    arq_fotos = st.file_uploader("FOTOS QUE DOCUMENTAM INTERVENÇÕES", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="up_evidencias_principal")
    
    if arq_fotos:
        atuais = [f.name for f in arq_fotos]
        st.session_state["ordem_evidencias"] = [f for f in st.session_state["ordem_evidencias"] if f in atuais]
        for f in atuais:
            if f not in st.session_state["ordem_evidencias"]:
                st.session_state["ordem_evidencias"].append(f)
    else: st.session_state["ordem_evidencias"] = []

    if arq_fotos and len(st.session_state["ordem_evidencias"]) > 1:
        st.caption("🔀 Reordene as fotos antes de preencher os metadados:")
        for idx, filename in enumerate(st.session_state["ordem_evidencias"]):
            c_n, c_u, c_d = st.columns([10, 1, 1])
            c_n.write(f"`{idx+1}.` {sanitizar(filename)}")
            total = len(st.session_state["ordem_evidencias"])
            if idx > 0 and c_u.button("⬆️", key=f"up_ev_{idx}"):
                o = st.session_state["ordem_evidencias"]
                o[idx], o[idx-1] = o[idx-1], o[idx]; st.rerun()
            if idx < total - 1 and c_d.button("⬇️", key=f"dw_ev_{idx}"):
                o = st.session_state["ordem_evidencias"]
                o[idx], o[idx+1] = o[idx+1], o[idx]; st.rerun()
        st.divider()

    with st.form("form_relatorio_novo"):
        secao("📋", "1. IDENTIFICAÇÃO DA INFRAESTRUTURA")
        c1, c2, c3 = st.columns(3)
        with c1:
            titulo  = st.text_input(LBL_TITULO, value="", placeholder="Relatório Técnico", key="novo_titulo")
            contato = st.text_input("CONTATO / TÉCNICO", value=st.session_state.get("_tecnico_global", ""), key="novo_contato")
        with c2:
            empresa  = st.text_input("EMPRESA", value="", placeholder="Empresa Parceira", key="novo_empresa")
            telefone = st.text_input("TELEFONE", value="", placeholder="(11) 99999-9999", key="novo_telefone")
        with c3:
            email   = st.text_input("E-MAIL", value="", placeholder="tecnico@empresa.com.br", key="novo_email")
            site_id = st.text_input("IDENTIFICAÇÃO DO SITE", value=site_selecionado)

        tecnico  = st.text_input("TÉCNICO EM CAMPO", value=st.session_state.get("_tecnico_global", ""), key="novo_tecnico")
        endereco = st.text_input("ENDEREÇO FÍSICO", value=endereco_autofill)

        col_d, col_h = st.columns(2)
        with col_d: data_vis = st.date_input("DATA DA VISITA", value=datetime.today(), key="novo_data")
        with col_h: hora_vis = st.time_input("HORA", value=datetime.now().time(), key="novo_hora")
        data_hora = f"{data_vis.strftime('%d/%m/%Y')} às {hora_vis.strftime('%H:%M')}"

        dados_cad = {
            "titulo": titulo, "contato": contato, "empresa": empresa, "telefone": telefone,
            "email": email, "site_id": site_id, "endereco": endereco, "data_hora": data_hora,
            "tecnico": tecnico or contato, "latitude": lat_autofill, "longitude": lon_autofill
        }

        st.divider()
        secao("📸", "2. METADADOS DAS EVIDÊNCIAS")

        fotos_proc = []
        if arq_fotos and st.session_state["ordem_evidencias"]:
            dict_arquivos = {a.name: a for a in arq_fotos}
            for idx, filename in enumerate(st.session_state["ordem_evidencias"]):
                arquivo  = dict_arquivos[filename]
                raw      = arquivo.getvalue()
                raw_comp = comprimir_para_pdf(raw)
                foto_id  = hashlib.sha256(raw).hexdigest()[:16]
                safe_key = f"ev_{idx}_{hashlib.md5(filename.encode()).hexdigest()[:8]}"
                
                caminho_foto = os.path.join(FOTOS_DIR, f"ev_{foto_id}.jpg")
                with open(caminho_foto, "wb") as f_out: f_out.write(raw_comp)

                st.markdown("---")
                c_img, c_dados = st.columns([1, 3])
                with c_img:
                    st.image(arquivo, use_container_width=True)
                    st.caption(f"ID: {sanitizar(foto_id)}")
                with c_dados:
                    tit = st.text_input(LBL_TITULO, key=f"t_{safe_key}")
                    com = st.text_area(LBL_DESCRICAO, key=f"c_{safe_key}", height=75)
                    c_sev, c_cat = st.columns(2)
                    with c_sev: sev = st.selectbox("SEVERIDADE", ["Normal", "Observacao", "Critico"], key=f"sev_{safe_key}")
                    with c_cat: cat = st.selectbox("CATEGORIA",  ["Geral", "Antes", "Depois", "Detalhe"], key=f"cat_{safe_key}")
                    
                    fotos_proc.append({
                        "foto_id": foto_id, "caminho": caminho_foto, "type": "image/jpeg",
                        "titulo": tit.strip() or f"Evidência {idx+1}", "comentarios": com.strip() or "N/A",
                        "filename": arquivo.name, "severidade": sev, "categoria": cat,
                    })

        secao("📎", "3. ANEXOS ADICIONAIS")
        arq_extras = st.file_uploader("SITUAÇÃO ANTERIOR OU CONTEXTO GERAL", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="up_extras_principal")
        extras_proc = []
        if arq_extras:
            for idx_ex, arq_ex in enumerate(arq_extras):
                raw_ex = arq_ex.getvalue()
                raw_comp_ex = comprimir_para_pdf(raw_ex)
                fid_ex = hashlib.sha256(raw_ex).hexdigest()[:16]
                
                caminho_extra = os.path.join(FOTOS_DIR, f"ex_{fid_ex}.jpg")
                with open(caminho_extra, "wb") as f_out_ex: f_out_ex.write(raw_comp_ex)
                
                c_img_ex, c_dados_ex = st.columns([1, 3])
                with c_img_ex: st.image(arq_ex, use_container_width=True)
                with c_dados_ex:
                    t_ex = st.text_input(LBL_TITULO, key=f"t_ex_{idx_ex}")
                    c_ex = st.text_area(LBL_DESCRICAO, key=f"c_ex_{idx_ex}", height=75)
                    extras_proc.append({
                        "foto_id": fid_ex, "caminho": caminho_extra, "type": "image/jpeg",
                        "titulo": t_ex.strip() or f"Anexo {idx_ex+1}", "comentarios": c_ex.strip() or "N/A",
                        "filename": arq_ex.name
                    })
        
        submit = st.form_submit_button("💾 SALVAR RELATÓRIO NO BANCO DE DADOS", type="primary", use_container_width=True)

    if submit: _salvar_novo_relatorio(dados_cad, fotos_proc, extras_proc)

def _render_cadastrais(row, lid):
    secao("📋", "DADOS CADASTRAIS")
    e1, e2, e3 = st.columns(3)
    with e1:
        tit = st.text_input(LBL_TITULO, value=row['titulo'], key=f"tit_{lid}")
        con = st.text_input("CONTATO", value=row['contato'], key=f"con_{lid}")
    with e2:
        emp = st.text_input("EMPRESA", value=row['empresa'], key=f"emp_{lid}")
        tel = st.text_input("TELEFONE", value=row['telefone'], key=f"tel_{lid}")
    with e3:
        eml = st.text_input("E-MAIL", value=row['email'], key=f"eml_{lid}")
        sit = st.text_input("SITE", value=row['site_id'], key=f"sit_{lid}")
        dat = st.text_input("DATA E HORA", value=row['data_hora'], key=f"dat_{lid}")
    end = st.text_input("ENDEREÇO", value=row['endereco'] if 'endereco' in row.keys() else "", key=f"end_{lid}")
    return {"tit": tit, "con": con, "emp": emp, "tel": tel, "eml": eml, "sit": sit, "dat": dat, "end": end}

def _executar_acao_inline(lid, fid, acao, prefixo, db_field):
    if db_field not in ("fotos_json", "extras_json"):
        return
    with sqlite3.connect(DB_NAME) as conn:
        row = conn.execute(f"SELECT {db_field} FROM relatorios WHERE id=?", (lid,)).fetchone()
        if not row or not row[0]: return
        fotos = json.loads(row[0])
        for i in range(len(fotos)):
            cfid = fotos[i].get("foto_id", fotos[i].get("base64", "")[:16])
            t_val = st.session_state.get(f"{prefixo}t_{lid}_{cfid}")
            c_val = st.session_state.get(f"{prefixo}c_{lid}_{cfid}")
            if t_val is not None: fotos[i]["titulo"] = t_val
            if c_val is not None: fotos[i]["comentarios"] = c_val
        
        k = next((i for i, f in enumerate(fotos) if f.get("foto_id", f.get("base64", "")[:16]) == fid), -1)
        if k != -1:
            if acao == "up" and k > 0: fotos[k], fotos[k-1] = fotos[k-1], fotos[k]
            elif acao == "down" and k < len(fotos)-1: fotos[k], fotos[k+1] = fotos[k+1], fotos[k]
            elif acao == "del":
                caminho_del = fotos[k].get("caminho")
                if caminho_del and os.path.exists(caminho_del):
                    try: os.remove(caminho_del)
                    except: pass
                fotos.pop(k)
            conn.execute(f"UPDATE relatorios SET {db_field}=? WHERE id=?", (json.dumps(fotos), lid))
            conn.commit()

def _render_item_edicao(f, k, lid, prefixo, total_fotos, db_field):
    fid = f.get("foto_id", f.get("base64", "")[:16])
    st.markdown(
        f'<div style="background:#fff;border:1px solid {COR_BORDA};border-left:4px solid {COR_AZUL};'
        f'border-radius:8px;padding:12px;margin-bottom:10px;">'
        f'<span style="background:{COR_AZUL};color:#fff;font-size:10px;font-weight:700;'
        f'padding:2px 8px;border-radius:12px;">FOTO {k+1:02d}</span>'
        f'&nbsp;<span style="font-size:9px;color:{COR_CINZA};font-family:monospace;">ID: {sanitizar(fid)}</span></div>',
        unsafe_allow_html=True
    )
    col_i, col_d, col_ctrl = st.columns([1, 3, 0.4])
    b64_data = _obter_b64_de_foto(f)
    uri = f"data:{f.get('type', 'image/jpeg')};base64,{b64_data}"
    
    if b64_data: col_i.markdown(f'<img src="{uri}" style="width:100%;border-radius:6px;"/>', unsafe_allow_html=True)
    with col_d:
        nt = st.text_input(LBL_TITULO, value=f.get('titulo', ''), key=f"{prefixo}t_{lid}_{fid}")
        nc = st.text_area(LBL_DESCRICAO, value=f.get('comentarios', ''), key=f"{prefixo}c_{lid}_{fid}", height=65)
    with col_ctrl:
        st.markdown("<br>", unsafe_allow_html=True)
        if k > 0 and st.form_submit_button("⬆️", key=f"{prefixo}up_{lid}_{fid}"):
            _executar_acao_inline(lid, fid, "up", prefixo, db_field); st.rerun()
        if k < total_fotos-1 and st.form_submit_button("⬇️", key=f"{prefixo}dn_{lid}_{fid}"):
            _executar_acao_inline(lid, fid, "down", prefixo, db_field); st.rerun()
        if st.form_submit_button("❌", key=f"{prefixo}del_{lid}_{fid}"):
            _executar_acao_inline(lid, fid, "del", prefixo, db_field); st.rerun()
    fc = f.copy(); fc['titulo'] = nt; fc['comentarios'] = nc
    return fc

def _render_edicao_lista(fotos, lid, titulo_sec, icone, prefixo):
    secao(icone, titulo_sec)
    editados = []
    db_field = "fotos_json" if prefixo == "f" else "extras_json"
    for k, f in enumerate(fotos):
        fc = _render_item_edicao(f, k, lid, prefixo, len(fotos), db_field)
        editados.append(fc)
        st.divider()
    return editados

def _render_novas_fotos(lid, db_existentes):
    secao("➕", "ADICIONAR NOVAS FOTOS")
    arq = st.file_uploader("ENVIAR NOVAS IMAGENS", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True, key=f"new_{lid}")
    novas = []
    if arq:
        ids = {f.get("foto_id") for f in db_existentes}
        for idx_n, a in enumerate(arq):
            raw = a.getvalue(); raw_comp = comprimir_para_pdf(raw)
            fid = hashlib.sha256(raw).hexdigest()[:16]
            caminho_foto = os.path.join(FOTOS_DIR, f"new_{lid}_{fid}.jpg")
            with open(caminho_foto, "wb") as f_out: f_out.write(raw_comp)
                
            col_i, col_d = st.columns([1, 4])
            with col_i: st.image(a, width=90); st.caption(f"ID: {sanitizar(fid)}")
            with col_d:
                if fid in ids: st.warning(f"⚠️ DUPLICATA IGNORADA: {sanitizar(a.name)}"); continue
                nt = st.text_input(LBL_TITULO, key=f"n_t_{lid}_{idx_n}")
                nc = st.text_area(LBL_DESCRICAO, key=f"n_c_{lid}_{idx_n}", height=55)
            novas.append({
                "foto_id": fid, "caminho": caminho_foto, "type": a.type, 
                "titulo": nt.strip() if nt else f"Nova Foto {idx_n+1}",
                "comentarios": nc.strip() if nc else "N/A", "filename": a.name
            })
            ids.add(fid)
    return novas

def _tratar_botoes_acao_pdf(lid, row, state):
    if st.button(f"📄 GERAR PDF — {sanitizar(row['site_id'])}", key=f"pdf_{lid}", type="primary"):
        num_rel = (row['numero_relatorio'] if 'numero_relatorio' in row.keys() else None) or ""
        if not num_rel.strip():
            with sqlite3.connect(DB_NAME) as conn:
                num_rel = proximo_numero_relatorio(conn)
                conn.execute("UPDATE relatorios SET numero_relatorio=?, revisao=? WHERE id=?", (num_rel, "Rev.00", lid))
        dados_pdf = {
            "titulo": row['titulo'], "contato": row['contato'], "empresa": row['empresa'], "telefone": row['telefone'],
            "email": row['email'], "site_id": row['site_id'], "endereco": row['endereco'] if 'endereco' in row.keys() else "",
            "data_hora": row['data_hora'], "tecnico": (row['tecnico'] if 'tecnico' in row.keys() else None) or row['contato'],
            "numero_relatorio": num_rel, "revisao": (row['revisao'] if 'revisao' in row.keys() else None) or "Rev.00",
        }
        with st.spinner("GERANDO PDF EM MEMÓRIA..."):
            pdf_bytes, file_name = gerar_pdf(dados_pdf, state["fotos_db"], state["extras_db"])
        
        st.download_button("⬇️ BAIXAR PDF GERADO", data=pdf_bytes, file_name=file_name, mime="application/pdf", key=f"dl_{lid}")

def _tratar_botoes_acao(lid, state):
    col_b, col_c = st.columns(2)
    with col_b:
        if st.button("🗑️ LIMPAR TODAS AS FOTOS", key=f"lim_{lid}"): st.session_state[f"conf_lim_{lid}"] = True
    with col_c: _tratar_botoes_acao_pdf(lid, state["row"], state)

def _tratar_limpeza(lid):
    if st.session_state.get(f"conf_lim_{lid}"):
        st.warning("⚠️ TEM CERTEZA? ESTA AÇÃO APAGARÁ **TODAS** AS FOTOS E ANEXOS.")
        cs, cn = st.columns(2)
        if cs.button("✅ SIM, APAGAR TUDO", key=f"sim_{lid}"):
            with sqlite3.connect(DB_NAME) as conn:
                conn.execute("UPDATE relatorios SET fotos_json='[]', extras_json='[]' WHERE id=?", (lid,))
                conn.commit()
            st.session_state.pop(f"conf_lim_{lid}", None); st.rerun()
        if cn.button("❌ CANCELAR", key=f"nao_{lid}"):
            st.session_state.pop(f"conf_lim_{lid}", None); st.rerun()

def _salvar_edicoes(lid, state):
    fotos_finais = state["fotos_edit"] + state["novas"]
    extras_finais = state["extras_edit"] 
    d = state["cad"]
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('''UPDATE relatorios
                        SET titulo=?,contato=?,empresa=?,telefone=?,email=?,
                            site_id=?,endereco=?,data_hora=?,
                            fotos_json=?,extras_json=? WHERE id=?''',
                     (d["tit"], d["con"], d["emp"], d["tel"], d["eml"],
                      d["sit"], d["end"], d["dat"],
                      json.dumps(fotos_finais), json.dumps(extras_finais), lid))
        conn.commit()
    st.success("✅ RELATÓRIO ATUALIZADO COM SUCESSO!"); st.rerun()

def _processar_acoes_relatorio(state: dict):
    lid = state["lid"]
    _tratar_botoes_acao(lid, state)
    _tratar_limpeza(lid)
    if state["salvar"]: _salvar_edicoes(lid, state)

def _render_dados_cadastrais_form(row, lid, fotos_db, extras_db):
    with st.form(f"form_ed_{lid}"):
        cad = _render_cadastrais(row, lid)
        fotos_edit = _render_edicao_lista(fotos_db, lid, "EDITAR EVIDÊNCIAS", "📸", "f")
        extras_edit = _render_edicao_lista(extras_db, lid, "EDITAR ANEXOS", "📎", "e")
        novas = _render_novas_fotos(lid, fotos_db + extras_db)
        salvar = st.form_submit_button("🔄  SALVAR ALTERAÇÕES", type="primary", use_container_width=True)
    return {"lid": lid, "row": row, "salvar": salvar, "fotos_db": fotos_db, "extras_db": extras_db, "fotos_edit": fotos_edit, "extras_edit": extras_edit, "novas": novas, "cad": cad}

def _render_relatorio_expander(row):
    lid = row['id']
    fotos_db = json.loads(row['fotos_json'] or "[]")
    extras_db = json.loads(row['extras_json'] or "[]") if 'extras_json' in row.keys() else []
    with st.expander(f"📍 **{sanitizar(row['site_id'])}**  |  {sanitizar(row['data_hora'])}  |  ID #{lid}"):
        state = _render_dados_cadastrais_form(row, lid, fotos_db, extras_db)
        _processar_acoes_relatorio(state)

def tela_pesquisa():
    banner("PESQUISAR, EDITAR E EXPORTAR")
    secao("🔍", "BUSCAR RELATÓRIOS")
    col_busca, col_lim = st.columns([3, 1])
    with col_busca: termo = st.text_input("NOME DO SITE OU PARTE DO TÍTULO:", placeholder="Ex: SMSMT15")
    with col_lim: limite = st.selectbox("EXIBIR", [10, 25, 50, 100], index=0)

    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        if termo.strip():
            rows = conn.execute("SELECT * FROM relatorios WHERE site_id LIKE ? OR titulo LIKE ? ORDER BY id DESC LIMIT ?", (f'%{termo}%', f'%{termo}%', limite)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM relatorios ORDER BY id DESC LIMIT ?", (limite,)).fetchall()

    if not rows:
        st.info("NENHUM RELATÓRIO ENCONTRADO. CRIE UM NA ABA 'NOVO RELATÓRIO'.")
        return

    st.markdown("<br>", unsafe_allow_html=True)
    ta, tb, tc = st.columns(3)
    with ta: st.markdown(f'<div class="eng-metric"><div class="eng-metric-val">{len(rows)}</div><div class="eng-metric-label">RESULTADOS</div></div>', unsafe_allow_html=True)
    with tb: st.markdown(f'<div class="eng-metric"><div class="eng-metric-val">{sum(len(json.loads(r["fotos_json"] or "[]")) for r in rows)}</div><div class="eng-metric-label">EVIDÊNCIAS</div></div>', unsafe_allow_html=True)
    with tc: st.markdown(f'<div class="eng-metric"><div class="eng-metric-val">{sum(len(json.loads(r["extras_json"] or "[]")) if "extras_json" in r.keys() else 0 for r in rows)}</div><div class="eng-metric-label">ANEXOS</div></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()

    for row in rows: _render_relatorio_expander(row)

def tela_dashboard():
    banner("DASHBOARD")
    with sqlite3.connect(DB_NAME) as conn:
        df = pd.read_sql_query("SELECT * FROM relatorios ORDER BY id DESC", conn)

    if df.empty:
        st.info("NENHUM RELATÓRIO CADASTRADO AINDA.")
        return

    df['tecnico'] = df['tecnico'].fillna(df['contato'])
    df['qtd_fotos'] = df['fotos_json'].apply(lambda x: len(json.loads(x or "[]")))
    df['qtd_extras'] = df.get('extras_json', pd.Series(['[]']*len(df))).apply(lambda x: len(json.loads(x or "[]")))
    df['total_imagens'] = df['qtd_fotos'] + df['qtd_extras']
    
    try:
        df['data_formatada'] = pd.to_datetime(df['data_hora'].str.extract(r'(\d{2}/\d{2}/\d{4})')[0], format='%d/%m/%Y', errors='coerce')
    except:
        df['data_formatada'] = pd.NaT

    st.markdown("### 🎛️ Filtros Analíticos")
    c_tec, c_site = st.columns(2)
    with c_tec:
        lista_tecnicos = df['tecnico'].dropna().unique().tolist()
        tec_sel = st.multiselect("Filtrar por Técnico:", lista_tecnicos, default=lista_tecnicos)
    with c_site:
        lista_sites = df['site_id'].dropna().unique().tolist()
        site_sel = st.multiselect("Filtrar por Site:", lista_sites, default=lista_sites)
    
    df_filtrado = df[(df['tecnico'].isin(tec_sel)) & (df['site_id'].isin(site_sel))]

    if df_filtrado.empty:
        st.warning("Nenhum dado corresponde aos filtros selecionados.")
        return

    secao("📊", "RESUMO GERAL")
    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(f'<div class="eng-metric"><div class="eng-metric-val">{len(df_filtrado)}</div><div class="eng-metric-label">RELATÓRIOS</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="eng-metric"><div class="eng-metric-val">{df_filtrado["site_id"].nunique()}</div><div class="eng-metric-label">SITES ÚNICOS</div></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="eng-metric"><div class="eng-metric-val">{df_filtrado["qtd_fotos"].sum()}</div><div class="eng-metric-label">EVIDÊNCIAS</div></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="eng-metric"><div class="eng-metric-val">{df_filtrado["qtd_extras"].sum()}</div><div class="eng-metric-label">ANEXOS</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        secao("📈", "PRODUTIVIDADE (TOP SITES)")
        df_agrupado = df_filtrado.groupby("site_id")['total_imagens'].sum().reset_index().sort_values("total_imagens", ascending=False).head(10)
        if not df_agrupado.empty:
            fig_bar = px.bar(df_agrupado, x="site_id", y="total_imagens", text="total_imagens", color="total_imagens", 
                             color_continuous_scale=px.colors.sequential.Reds, labels={"site_id": "Site", "total_imagens": "Total de Imagens"})
            fig_bar.update_layout(margin=dict(l=0, r=0, t=30, b=0), showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)

    with col_chart2:
        secao("🚨", "DISTRIBUIÇÃO DE SEVERIDADE")
        severidades = {"Critico": 0, "Observacao": 0, "Normal": 0}
        
        cores_mapa = []
        for _, r in df_filtrado.iterrows():
            tem_critico = False
            for foto in json.loads(r['fotos_json'] or "[]"):
                sev = foto.get('severidade', 'Normal')
                sev_norm = {'Crítico': 'Critico', 'Observação': 'Observacao'}.get(sev, sev)
                severidades[sev_norm] = severidades.get(sev_norm, 0) + 1
                if sev_norm == 'Critico':
                    tem_critico = True
            cores_mapa.append(COR_VERMELHO if tem_critico else COR_AZUL)
            
        df_filtrado['cor_pino'] = cores_mapa
        
        df_sev = pd.DataFrame(list(severidades.items()), columns=['Severidade', 'Quantidade'])
        if df_sev['Quantidade'].sum() > 0:
            fig_pie = px.pie(df_sev, values='Quantidade', names='Severidade', hole=0.4, 
                             color='Severidade', color_discrete_map={"Critico": COR_VERMELHO, "Observacao": COR_AMARELO, "Normal": COR_VERDE})
            fig_pie.update_layout(margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Sem dados de severidade para exibir.")

    st.markdown("---")
    
    secao("🌍", "MAPA TÁTICO DE VISTORIAS (GEOLOCALIZAÇÃO)")
    
    df_mapa = df_filtrado.copy()
    if 'latitude' in df_mapa.columns and 'longitude' in df_mapa.columns:
        df_mapa['latitude'] = pd.to_numeric(df_mapa['latitude'], errors='coerce')
        df_mapa['longitude'] = pd.to_numeric(df_mapa['longitude'], errors='coerce')
        df_mapa = df_mapa.dropna(subset=['latitude', 'longitude'])
        df_mapa = df_mapa[(df_mapa['latitude'] != 0.0) & (df_mapa['longitude'] != 0.0)]

        if not df_mapa.empty:
            if hasattr(px, "scatter_map"):
                fig_mapa = px.scatter_map(
                    df_mapa, lat="latitude", lon="longitude", hover_name="site_id",
                    hover_data={"latitude": False, "longitude": False, "tecnico": True, "data_hora": True},
                    color="cor_pino", color_discrete_map="identity", zoom=8, height=450
                )
                fig_mapa.update_layout(map_style="carto-positron", margin={"r":0,"t":0,"l":0,"b":0})
            elif hasattr(px, "scatter_mapbox"):
                fig_mapa = px.scatter_mapbox(
                    df_mapa, lat="latitude", lon="longitude", hover_name="site_id",
                    hover_data={"latitude": False, "longitude": False, "tecnico": True, "data_hora": True},
                    color="cor_pino", color_discrete_map="identity", zoom=8, height=450
                )
                fig_mapa.update_layout(mapbox_style="carto-positron", margin={"r":0,"t":0,"l":0,"b":0})
            else:
                fig_mapa = px.scatter_geo(
                    df_mapa, lat="latitude", lon="longitude", hover_name="site_id",
                    color="cor_pino", color_discrete_map="identity"
                )
                fig_mapa.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
                
            st.plotly_chart(fig_mapa, use_container_width=True)
            st.markdown(f"<span style='color:{COR_AZUL};font-weight:bold;'>🔵 Operação Normal</span> &nbsp;&nbsp; | &nbsp;&nbsp; <span style='color:{COR_VERMELHO};font-weight:bold;'>🔴 Contém Anomalia Crítica</span>", unsafe_allow_html=True)
        else:
            st.info("💡 Nenhum relatório filtrado possui coordenadas de GPS salvas para plotagem no mapa.")
    else:
        st.info("💡 O banco de dados atual não possui as colunas de Latitude/Longitude preenchidas.")

    st.markdown("---")
    secao("📅", "TENDÊNCIA TEMPORAL DE VISTORIAS")
    df_tempo = df_filtrado.dropna(subset=['data_formatada']).groupby('data_formatada').size().reset_index(name='Laudos')
    if not df_tempo.empty:
        fig_line = px.line(df_tempo, x='data_formatada', y='Laudos', markers=True, labels={"data_formatada": "Data da Vistoria"})
        fig_line.update_traces(line_color=COR_AZUL_MED)
        fig_line.update_layout(margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("Dados de data insuficientes para gerar a linha do tempo.")

    st.markdown("---")
    secao("📋", "ÚLTIMOS LAUDOS (VISUALIZAÇÃO INTELIGENTE)")
    
    df_table = df_filtrado[['id', 'site_id', 'tecnico', 'data_hora', 'qtd_fotos', 'qtd_extras']].head(15)
    st.dataframe(
        df_table,
        column_config={
            "id": st.column_config.NumberColumn("ID", format="#%d"),
            "site_id": st.column_config.TextColumn("📍 Identificação do Site"),
            "tecnico": st.column_config.TextColumn("👷 Técnico"),
            "data_hora": st.column_config.TextColumn("📅 Data e Hora"),
            "qtd_fotos": st.column_config.ProgressColumn("📸 Evidências", format="%d", min_value=0, max_value=int(max(df['qtd_fotos'].max(), 1))),
            "qtd_extras": st.column_config.ProgressColumn("📎 Anexos", format="%d", min_value=0, max_value=int(max(df['qtd_extras'].max(), 1))),
        },
        hide_index=True,
        use_container_width=True
    )

# ==============================================================================
# ENTRY POINT
# ==============================================================================
st.set_page_config(page_title="GIRCP | Controle Fotográfico", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

if not check_password():
    st.stop()

init_db()
aplicar_estilo()

with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:20px 0 10px 0;">
      <div style="font-size:42px;">⚡</div>
      <div style="font-size:27px;font-weight:900;letter-spacing:1.5px;color:#fff;">GIRCP</div>
      <div style="font-size:15px;opacity:0.65;color:#fff;margin-top:2px;">SISTEMA CORPORATIVO</div>
    </div>""", unsafe_allow_html=True)
    st.markdown("---")
    tec = st.text_input("👷 TÉCNICO EM CAMPO:", value=st.session_state.get("_tecnico_global", ""), placeholder="Seu nome", key="_tec_sidebar_rel")
    if tec.strip(): st.session_state["_tecnico_global"] = tec.strip()
    st.markdown("---")
    menu = st.radio("NAVEGAÇÃO:", ["📝 NOVO RELATÓRIO", "🔍 PESQUISAR E EXPORTAR", "📊 DASHBOARD"], label_visibility="collapsed")

if menu == "📝 NOVO RELATÓRIO": tela_novo()
elif menu == "🔍 PESQUISAR E EXPORTAR": tela_pesquisa()
elif menu == "📊 DASHBOARD": tela_dashboard()