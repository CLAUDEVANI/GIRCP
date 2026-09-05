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
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime
from weasyprint import HTML

# ══════════════════════════════════════════════════════════════════════════
# CONSTANTES DE DESIGN — ENGEMON
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
LBL_TITULO = "TÍTULO"
LBL_DESCRICAO = "DESCRIÇÃO"
OPT_DIGITAR_MANUAL = "-- Digitar Manualmente --"

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
            endereco    TEXT,
            data_hora   TEXT,
            fotos_json  TEXT DEFAULT '[]',
            extras_json TEXT DEFAULT '[]',
            criado_em   TEXT DEFAULT (datetime('now','localtime'))
        )
    ''')
    try:
        c.execute("ALTER TABLE relatorios ADD COLUMN criado_em TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE relatorios ADD COLUMN endereco TEXT")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()

def sanitizar(texto: str) -> str:
    return re.sub(r'<[^>]*>', '', str(texto or '')).strip()

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
    .watermark {{
        position: fixed; top: 38%; left: 50%;
        transform: translate(-50%, -50%);
        z-index: -999; width: 65%; opacity: 0.06;
    }}
    .watermark img {{ width: 100%; }}
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
    .header-data {{ text-align: right; color: {COR_CINZA}; font-size: 9pt; }}
    .header-data strong {{ color: {COR_AZUL}; font-size: 11pt; }}
    .section-header {{
        background: {COR_AZUL}; color: #fff; font-weight: 700; font-size: 10pt;
        padding: 7px 14px; margin-top: 22px; margin-bottom: 14px;
        text-transform: uppercase; letter-spacing: 0.5px;
        border-left: 5px solid {COR_VERMELHO}; border-radius: 2px;
    }}
    .dados-table {{
        width: 100%; border-collapse: collapse; margin-bottom: 18px;
        border: 1px solid {COR_BORDA}; border-radius: 4px; overflow: hidden;
    }}
    .dados-table td {{ border: 1px solid {COR_BORDA}; padding: 9px 13px; vertical-align: middle; }}
    .dados-table td.label {{
        background: {COR_AZUL_LIGHT}; font-weight: 700; color: {COR_AZUL}; text-transform: uppercase;
        font-size: 7.8pt; width: 20%; letter-spacing: 0.3px;
    }}
    .dados-table td.value {{ color: {COR_TEXTO}; font-size: 9.5pt; width: 30%; }}
    .card-evidencia {{
        width: 100%; border-collapse: collapse; margin-bottom: 14px;
        border: 1px solid {COR_BORDA}; border-radius: 6px; overflow: hidden;
        page-break-inside: avoid; background: #fff;
    }}
    .card-evidencia td {{ vertical-align: top; }}
    .card-num {{
        background: {COR_AZUL}; color: #fff; font-size: 8pt; font-weight: 700;
        padding: 3px 8px; text-align: center; writing-mode: vertical-rl; min-width: 22px;
    }}
    .col-foto {{ width: 43%; background: {COR_CINZA_LIGHT}; padding: 10px; text-align: center; border-right: 1px solid {COR_BORDA}; }}
    .col-foto img {{ width: 100%; max-height: 210px; object-fit: contain; border-radius: 3px; background: #fff; }}
    .col-texto {{ width: 57%; padding: 14px 16px; }}
    .foto-titulo {{
        font-weight: 800; color: {COR_AZUL}; font-size: 11pt; text-transform: uppercase;
        border-bottom: 2px solid {COR_AZUL_LIGHT}; padding-bottom: 7px; margin-bottom: 10px;
    }}
    .label-desc {{ font-size: 8pt; font-weight: 700; color: {COR_AZUL}; margin-bottom: 4px; }}
    .foto-desc {{
        font-size: 9pt; color: {COR_TEXTO}; background: {COR_CINZA_LIGHT}; padding: 9px 11px;
        border-left: 3px solid {COR_VERMELHO}; border-radius: 0 4px 4px 0; line-height: 1.5; white-space: pre-wrap;
    }}
    .assinatura-wrapper {{ margin: 44px auto 0 auto; width: 300px; text-align: center; page-break-inside: avoid; }}
    .assinatura-img {{ max-width: 180px; height: auto; display: block; margin: 0 auto -10px auto; }}
    .assinatura-linha {{ border-top: 1.5px solid {COR_TEXTO}; margin: 0 0 6px 0; }}
    .assinatura-nome {{ font-weight: 700; color: {COR_AZUL}; font-size: 9.5pt; }}
    .assinatura-cargo {{ font-size: 8pt; color: {COR_CINZA}; }}
    .logo-wrapper {{ margin-top: 14px; }}
    .logo-img {{ max-width: 140px; height: auto; display: block; margin: 0 auto; }}
    """

def gerar_pdf(dados: dict, fotos: list, extras: list = None) -> str:
    extras = extras or []
    b64_wm  = _carregar_b64("WhatsApp Image 2026-06-25 at 05.46.59.jpeg") or _carregar_b64("logo_engemon.png")
    b64_sig = _carregar_b64("assinatura_claudevani.png")
    b64_logo = _carregar_b64("logo_engemon.png")

    wm_html = f'<div class="watermark"><img src="data:image/jpeg;base64,{b64_wm}"/></div>' if b64_wm else ""
    sig_img = f'<img class="assinatura-img" src="data:image/png;base64,{b64_sig}"/>' if b64_sig else '<div style="height:40px;"></div>'
    logo_img = f'<img class="logo-img" src="data:image/png;base64,{b64_logo}"/>' if b64_logo else ""

    fotos_html = ""
    for i, f in enumerate(fotos, 1):
        mime = f.get('type', 'image/jpeg')
        b64  = f.get('base64', '')
        tit  = sanitizar(f.get('titulo', f'Evidência {i}')).upper()
        desc = sanitizar(f.get('comentarios', 'N/A'))
        fotos_html += f"""
        <table class="card-evidencia">
          <tr>
            <td class="card-num">{i:02d}</td>
            <td class="col-foto"><img src="data:{mime};base64,{b64}"/></td>
            <td class="col-texto">
              <div class="foto-titulo">{tit}</div>
              <div class="label-desc">Descrição Técnica:</div>
              <div class="foto-desc">{desc}</div>
            </td>
          </tr>
        </table>"""

    extras_html = ""
    if extras:
        extras_html = '<div style="page-break-before:always;"></div><div class="section-header">3 &nbsp; ANEXOS ADICIONAIS</div>'
        for i, f in enumerate(extras, 1):
            mime = f.get('type', 'image/jpeg')
            b64  = f.get('base64', '')
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
<html lang="pt-BR">
<head><meta charset="utf-8"><style>{_css_pdf()}</style></head>
<body>
{wm_html}
<div class="page-header">
  <div>
    <div class="header-acento"></div>
    <div class="header-titulo">Relatório de Visita Técnica</div>
  </div>
  <div class="header-data">Data da Vistoria:<br><strong>{sanitizar(dados.get('data_hora',''))}</strong></div>
</div>

<div class="section-header">1 &nbsp; DADOS CADASTRAIS DA INFRAESTRUTURA</div>
<table class="dados-table">
  <tr>
    <td class="label">SITE / IDENTIFICAÇÃO</td><td class="value">{sanitizar(dados.get('site_id',''))}</td>
    <td class="label">TÍTULO</td><td class="value">{sanitizar(dados.get('titulo',''))}</td>
  </tr>
  <tr>
    <td class="label">ENDEREÇO FÍSICO</td><td class="value" colspan="3">{sanitizar(dados.get('endereco',''))}</td>
  </tr>
  <tr>
    <td class="label">EMPRESA</td><td class="value">{sanitizar(dados.get('empresa',''))}</td>
    <td class="label">CONTATO TÉCNICO</td><td class="value">{sanitizar(dados.get('contato',''))}</td>
  </tr>
  <tr>
    <td class="label">TELEFONE</td><td class="value">{sanitizar(dados.get('telefone',''))}</td>
    <td class="label">E-MAIL</td><td class="value">{sanitizar(dados.get('email',''))}</td>
  </tr>
</table>

<div class="section-header">2 &nbsp; REGISTRO FOTOGRÁFICO E EVIDÊNCIAS</div>
{fotos_html}
{extras_html}
<div class="assinatura-wrapper">
  {sig_img}
  <div class="assinatura-linha"></div>
  <div class="assinatura-nome">{sanitizar(dados.get('contato','Responsável Técnico'))}</div>
  <div class="assinatura-cargo">Responsável técnico | Engemon Opservices</div>
  <div class="logo-wrapper">{logo_img}</div>
</div>
</body></html>"""

    nome = f"Relatorio_{sanitizar(dados.get('site_id','SITE')).replace(' ','_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    path = os.path.join(os.getcwd(), nome)
    HTML(string=html).write_pdf(path)
    return path

def aplicar_estilo():
    st.markdown(f"""<style>
    [data-testid="stAppViewContainer"] {{ background: #F8FAFC; }}
    [data-testid="stSidebar"] {{ background: {COR_AZUL} !important; }}
    [data-testid="stSidebar"] * {{ color: #fff !important; }}
    [data-testid="stSidebar"] .stRadio label {{ color: #fff !important; }}
    [data-testid="stSidebar"] hr {{ border-color: rgba(255,255,255,0.2) !important; }}
    .eng-banner {{
        background: linear-gradient(135deg, {COR_AZUL} 0%, {COR_AZUL_MED} 100%);
        color: #fff; padding: 20px 28px; border-radius: 10px; margin-bottom: 24px; display: flex; align-items: center; justify-content: space-between;
        box-shadow: 0 4px 16px rgba(0,32,96,0.18);
    }}
    .eng-banner-title {{ font-size: 22px; font-weight: 900; letter-spacing: 1.2px; text-transform: uppercase; }}
    .eng-banner-badge {{ background: {COR_VERMELHO}; color: #fff; padding: 5px 14px; border-radius: 20px; font-size: 11px; font-weight: 700; letter-spacing: 0.5px; }}
    .eng-section {{
        background: {COR_AZUL}; color: #fff; padding: 10px 18px; border-radius: 6px; margin: 24px 0 14px 0;
        font-weight: 700; font-size: 13px; text-transform: uppercase; letter-spacing: 0.6px; border-left: 5px solid {COR_VERMELHO};
    }}
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {{ border: 1.5px solid {COR_BORDA} !important; border-radius: 6px !important; color: {COR_TEXTO} !important; -webkit-text-fill-color: {COR_TEXTO} !important; }}
    .stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus {{ border-color: {COR_AZUL} !important; box-shadow: 0 0 0 3px rgba(0,32,96,0.08) !important; }}
    </style>""", unsafe_allow_html=True)

def banner(subtitulo: str = ""):
    st.markdown(f"""
    <div class="eng-banner">
      <div><div class="eng-banner-title">⚡ GIRCP</div><div style="font-size: 12px; opacity: 0.75; margin-top: 2px;">GERADOR INTELIGENTE DE RELATÓRIOS E CONTROLE FOTOGRÁFICO{'— ' + subtitulo if subtitulo else ''}</div></div>
      <div class="eng-banner-badge">ENGEMON OPSERVICES</div>
    </div>""", unsafe_allow_html=True)

def secao(icone: str, titulo: str):
    st.markdown(f'<div class="eng-section">{icone} &nbsp; {titulo}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# SUBFUNÇÕES PARA MANIPULAÇÃO DE KML E ARQUIVOS BASE (BAIXA COMPLEXIDADE)
# ══════════════════════════════════════════════════════════════════════════
def _extrair_valor_dado_kml(data_element, local_name_fn):
    n_attr = data_element.get('name')
    val = ""
    for sub in data_element:
        if local_name_fn(sub.tag) == 'value' and sub.text:
            val = sub.text.strip()
    return n_attr, val

def _mapear_atributo_kml(n_attr, val, campos):
    if not n_attr or not val:
        return campos
    n_upper = n_attr.upper()
    if 'ENDEREÇO' in n_upper or 'ENDERECO' in n_upper:
        campos['endereco'] = val
    elif 'BAIRRO' in n_upper:
        campos['bairro'] = val
    elif 'MUNICIPIO' in n_upper or 'MUNÍCIPIO' in n_upper:
        campos['municipio'] = val
    elif 'CEP' in n_upper:
        campos['cep'] = val
    elif 'AREA' in n_upper or 'ÁREA' in n_upper:
        campos['area'] = val
    elif 'TIPO DE INFRA' in n_upper or 'INFRA' in n_upper:
        campos['tipo_infra'] = val
    return campos

def _extrair_dados_extended_data(ext_data, local_name_fn):
    campos = {'endereco': '', 'bairro': '', 'municipio': '', 'cep': '', 'area': '', 'tipo_infra': ''}
    if ext_data is not None:
        for data in ext_data.iter():
            if local_name_fn(data.tag) == 'Data':
                n_attr, val = _extrair_valor_dado_kml(data, local_name_fn)
                _mapear_atributo_kml(n_attr, val, campos)
    return campos

def _processar_placemark_kml(placemark, local_name_fn):
    site_id = "SEM NOME"
    ext_data = None
    for child in placemark:
        tag = local_name_fn(child.tag)
        if tag == 'name' and child.text:
            site_id = child.text.strip()
        elif tag == 'ExtendedData':
            ext_data = child
            
    c = _extrair_dados_extended_data(ext_data, local_name_fn)
    partes_loc = [p for p in [c['endereco'], c['bairro'], c['municipio'], f"CEP: {c['cep']}" if c['cep'] and c['cep'] != "0" else ""] if p and p != "0"]
    endereco_completo = " - ".join(partes_loc) if partes_loc else c['endereco']
    
    return {
        'SITE': site_id, 
        'ENDEREÇO': endereco_completo, 
        'AREA': c['area'], 
        'MODELO': c['tipo_infra']
    }

def _parse_kml_to_dataframe(arquivo_kml):
    tree = ET.parse(arquivo_kml)
    root = tree.getroot()
    
    def local_name(tag):
        return tag.split('}')[-1] if '}' in tag else tag

    dados = []
    for placemark in root.iter():
        if local_name(placemark.tag) == 'Placemark':
            dados.append(_processar_placemark_kml(placemark, local_name))
    return pd.DataFrame(dados)

def _carregar_base_dados(arquivo):
    if not arquivo:
        return None
    try:
        if arquivo.name.lower().endswith('.kml'):
            return _parse_kml_to_dataframe(arquivo)
        else:
            return pd.read_excel(arquivo)
    except Exception as e:
        st.error(f"Erro ao processar a base de dados: {e}")
        return None

def _atualizar_selecao_site(df_sites, col_site):
    escolha = st.session_state.get("filtro_escolha_site", OPT_DIGITAR_MANUAL)
    if not escolha or escolha == OPT_DIGITAR_MANUAL or df_sites is None:
        st.session_state["novo_site"] = ""
        st.session_state["novo_endereco"] = ""
        st.session_state["novo_modelo"] = ""
        return

    col_end = next((col for col in df_sites.columns if 'ENDERE' in str(col).upper() or 'RUA' in str(col).upper()), None)
    col_mod = next((col for col in df_sites.columns if 'MODELO' in str(col).upper() or 'INFRA' in str(col).upper()), None)
    
    linha = df_sites[df_sites[col_site] == escolha]
    if not linha.empty:
        st.session_state["novo_site"] = escolha
        st.session_state["novo_endereco"] = str(linha.iloc[0][col_end]) if col_end else ""
        st.session_state["novo_modelo"] = str(linha.iloc[0][col_mod]) if col_mod else ""
    else:
        st.session_state["novo_site"] = escolha
        st.session_state["novo_endereco"] = ""
        st.session_state["novo_modelo"] = ""

def _filtrar_por_grupo(df_sites, col_area):
    if not col_area:
        return df_sites
    grupos = ["-- Todos --"] + sorted(df_sites[col_area].dropna().astype(str).unique().tolist())
    grupo_sel = st.selectbox("📌 1. Filtrar por Área (Zoneamento SPC):", grupos, key="filtro_grupo_spc")
    if grupo_sel != "-- Todos --":
        return df_sites[df_sites[col_area] == grupo_sel]
    return df_sites

def _selecionar_site(df_filtrado, col_site):
    lista_sites = df_filtrado[col_site].dropna().astype(str).unique().tolist()
    return st.selectbox(
        "📌 2. Selecione o Site:", 
        [OPT_DIGITAR_MANUAL] + sorted(lista_sites), 
        key="filtro_escolha_site",
        on_change=_atualizar_selecao_site,
        args=(df_filtrado, col_site)
    )

def _extrair_detalhes_site(df_sites, col_site, escolha):
    if escolha == OPT_DIGITAR_MANUAL:
        return "", ""
    col_end = next((col for col in df_sites.columns if 'ENDERE' in str(col).upper() or 'RUA' in str(col).upper()), None)
    col_mod = next((col for col in df_sites.columns if 'MODELO' in str(col).upper() or 'INFRA' in str(col).upper()), None)
    endereco_val, modelo_val = "", ""
    linha = df_sites[df_sites[col_site] == escolha]
    if not linha.empty:
        if col_end:
            endereco_val = str(linha.iloc[0][col_end])
        if col_mod:
            modelo_val = str(linha.iloc[0][col_mod])
    return endereco_val, modelo_val

def _obter_filtros_cascata(df_sites):
    if df_sites is None or df_sites.empty:
        return "", "", ""
    col_site = next((col for col in df_sites.columns if str(col).upper() in ['SITE', 'SITES', 'IDENTIFICAÇÃO', 'NOME DO SITE']), None)
    if not col_site:
        return "", "", ""
    col_area = next((col for col in df_sites.columns if 'AREA' in str(col).upper() or 'ÁREA' in str(col).upper()), None)
    
    c1, c2 = st.columns(2)
    with c1:
        df_filtrado = _filtrar_por_grupo(df_sites, col_area)
    with c2:
        escolha = _selecionar_site(df_filtrado, col_site)
        
    endereco_val, modelo_val = _extrair_detalhes_site(df_sites, col_site, escolha)
    if escolha != OPT_DIGITAR_MANUAL:
        st.session_state["novo_site"] = escolha
        st.session_state["novo_endereco"] = endereco_val
        st.session_state["novo_modelo"] = modelo_val
        
    return st.session_state.get("novo_site", ""), st.session_state.get("novo_endereco", ""), st.session_state.get("novo_modelo", "")

def _processar_arquivos_upload(arquivos, prefixo_titulo):
    processadas = []
    if not arquivos:
        return processadas
    for i, arquivo in enumerate(arquivos):
        c_img, c_dados = st.columns([1, 3])
        with c_img: 
            st.image(arquivo, use_container_width=True)
        with c_dados:
            tit = st.text_input(LBL_TITULO, key=f"t_{prefixo_titulo}_{i}")
            com = st.text_area(LBL_DESCRICAO, key=f"c_{prefixo_titulo}_{i}", height=75)
            processadas.append({
                "base64": base64.b64encode(arquivo.getvalue()).decode("utf-8"),
                "type": arquivo.type, 
                "titulo": tit.strip() or f"{prefixo_titulo} {i+1}",
                "comentarios": com.strip() or "N/A"
            })
    return processadas

def _salvar_novo_relatorio(dados_cad, fotos, extras):
    if not dados_cad['site_id'].strip():
        st.error("⚠️ A IDENTIFICAÇÃO DO SITE É OBRIGATÓRIA.")
        return

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''INSERT INTO relatorios 
                 (titulo, contato, empresa, telefone, email, site_id, endereco, data_hora, fotos_json, extras_json)
                 VALUES (?,?,?,?,?,?,?,?,?,?)''',
              (sanitizar(dados_cad['titulo']), sanitizar(dados_cad['contato']), 
               sanitizar(dados_cad['empresa']), sanitizar(dados_cad['telefone']),
               sanitizar(dados_cad['email']), sanitizar(dados_cad['site_id']), 
               sanitizar(dados_cad['endereco']), dados_cad['data_hora'],
               json.dumps(fotos), json.dumps(extras)))
    conn.commit()
    conn.close()
    st.success(f"✅ RELATÓRIO **{dados_cad['site_id']}** SALVO COM SUCESSO! ACESSE A ABA PARA GERAR PDF.")
    st.balloons()

def _limpar_tudo():
    for k in ["_lista_ev", "_lista_ex", "_gen_ev", "_gen_ex"]:
        st.session_state.pop(k, None)
    st.rerun()

def _render_secao_formulario_novo(modelo_autofill):
    if modelo_autofill:
        st.success(f"🏢 **Modelo de Site Detectado:** {modelo_autofill}")

    with st.form("form_relatorio_novo"):
        secao("📋", "1. IDENTIFICAÇÃO DA INFRAESTRUTURA")
        c1, c2, c3 = st.columns(3)
        with c1:
            titulo  = st.text_input("TÍTULO DO RELATÓRIO", value="Relatório Técnico de Vistoria")
            contato = st.text_input("CONTATO / TÉCNICO RESPONSÁVEL", value=st.session_state.get("_tecnico_global", ""))
        with c2:
            empresa  = st.text_input("EMPRESA", value="Engemon")
            telefone = st.text_input("TELEFONE", value="(11) 94741-4606")
        with c3:
            email   = st.text_input("E-MAIL", value="tecnico@engemon.com.br")
            st.text_input("IDENTIFICAÇÃO DO SITE", key="novo_site", value=st.session_state.get("novo_site", ""), placeholder="Ex: SMSMT15")
            
        st.text_input("ENDEREÇO FÍSICO DO SITE", key="novo_endereco", value=st.session_state.get("novo_endereco", ""), placeholder="Rua, Número, Bairro - UF")
        
        col_d, col_h = st.columns(2)
        with col_d:
            data_vis = st.date_input("DATA DA VISITA", value=datetime.today())
        with col_h:
            hora_vis = st.time_input("HORA", value=datetime.now().time())
        
        data_hora = f"{data_vis.strftime('%d/%m/%Y')} às {hora_vis.strftime('%H:%M')}"
        
        dados_cad = {
            "titulo": titulo, "contato": contato, "empresa": empresa, 
            "telefone": telefone, "email": email, "site_id": st.session_state.get("novo_site", ""), 
            "endereco": st.session_state.get("novo_endereco", ""), "data_hora": data_hora
        }

        st.divider()
        secao("📸", "2. EVIDÊNCIAS FOTOGRÁFICAS PRINCIPAIS")
        arq_fotos = st.file_uploader("FOTOS QUE DOCUMENTAM INTERVENÇÕES", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
        fotos_proc = _processar_arquivos_upload(arq_fotos, "Evidência")

        secao("📎", "3. ANEXOS ADICIONAIS")
        arq_extras = st.file_uploader("SITUAÇÃO ANTERIOR OU CONTEXTO GERAL", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
        extras_proc = _processar_arquivos_upload(arq_extras, "Anexo")
        
        submit = st.form_submit_button("💾 SALVAR RELATÓRIO NO BANCO DE DADOS", type="primary", use_container_width=True)

    if submit:
        dados_cad["site_id"] = st.session_state.get("novo_site", "")
        dados_cad["endereco"] = st.session_state.get("novo_endereco", "")
        _salvar_novo_relatorio(dados_cad, fotos_proc, extras_proc)

def tela_novo():
    banner("NOVO RELATÓRIO")
    
    if "novo_site" not in st.session_state: st.session_state["novo_site"] = ""
    if "novo_endereco" not in st.session_state: st.session_state["novo_endereco"] = ""
    if "novo_modelo" not in st.session_state: st.session_state["novo_modelo"] = ""

    st.info("💡 **Inteligência Analítica:** Importe o seu arquivo **.KML** ou **.XLSX** para criar um filtro em cascata e autopreencher os dados do formulário.")
    arquivo_base = st.file_uploader("Importar Base de Sites (Opcional)", type=["kml", "xlsx", "xls"])
    
    df_sites = _carregar_base_dados(arquivo_base)
    _, _, modelo_autofill = _obter_filtros_cascata(df_sites)
    
    _render_secao_formulario_novo(modelo_autofill)


# ══════════════════════════════════════════════════════════════════════════
# COMPONENTES DE EDIÇÃO MODULAR E PESQUISA
# ══════════════════════════════════════════════════════════════════════════
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


def _render_edicao_lista(fotos, lid, titulo_sec, icone, prefixo, ignore_keys=None):
    secao(icone, titulo_sec)
    editados = []
    ignore_keys = ignore_keys or []
    for k, f in enumerate(fotos):
        if k in ignore_keys:
            continue
        col_i, col_d = st.columns([1, 4])
        with col_i:
            st.image(f"data:{f['type']};base64,{f['base64']}", width=110)
        with col_d:
            nt = st.text_input(LBL_TITULO, value=f.get('titulo', ''), key=f"{prefixo}t_{lid}_{k}")
            nc = st.text_area(LBL_DESCRICAO, value=f.get('comentarios', ''), key=f"{prefixo}c_{lid}_{k}", height=65)
        fc = f.copy()
        fc['titulo'] = nt
        fc['comentarios'] = nc
        editados.append(fc)
    return editados


def _render_novas_fotos(lid, db_existentes):
    secao("➕", "ADICIONAR NOVAS FOTOS")
    arq = st.file_uploader("ENVIAR NOVAS IMAGENS", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True, key=f"new_{lid}")
    novas = []
    if arq:
        import hashlib as _hl
        ids = {f.get("foto_id") for f in db_existentes}
        for idx_n, a in enumerate(arq):
            raw = a.getvalue()
            fid = _hl.sha256(raw).hexdigest()[:16]
            col_i, col_d = st.columns([1, 4])
            with col_i:
                st.image(a, width=90)
                st.caption(f"ID: {fid}")
            with col_d:
                if fid in ids:
                    st.warning(f"⚠️ DUPLICATA IGNORADA: {a.name}")
                    continue
                nt = st.text_input(LBL_TITULO, key=f"n_t_{lid}_{idx_n}")
                nc = st.text_area(LBL_DESCRICAO, key=f"n_c_{lid}_{idx_n}", height=55)
            novas.append({
                "foto_id": fid, "base64": base64.b64encode(raw).decode("utf-8"),
                "type": a.type, "titulo": nt.strip() if nt else f"Nova Foto {idx_n+1}",
                "comentarios": nc.strip() if nc else "N/A", "filename": a.name
            })
            ids.add(fid)
    return novas

def _tratar_botoes_acao_pdf(lid, row, state):
    if st.button(f"📄 GERAR PDF — {row['site_id']}", key=f"pdf_{lid}", type="primary"):
        dados_pdf = {
            "titulo": row['titulo'], "contato": row['contato'], "empresa": row['empresa'],
            "telefone": row['telefone'], "email": row['email'], "site_id": row['site_id'],
            "endereco": row['endereco'] if 'endereco' in row.keys() else "", "data_hora": row['data_hora']
        }
        with st.spinner("GERANDO PDF..."):
            path = gerar_pdf(dados_pdf, state["fotos_db"], state["extras_db"])
        with open(path, "rb") as f_pdf:
            st.download_button("⬇️ BAIXAR PDF", data=f_pdf, file_name=os.path.basename(path), mime="application/pdf", key=f"dl_{lid}")

def _tratar_botoes_acao(lid, state):
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        if state["excluir_sel"] != "-- SELECIONE --":
            if st.button("❌ CONFIRMAR EXCLUSÃO", key=f"xbt_{lid}"):
                idx = int(state["excluir_sel"].split("#")[1].split(":")[0]) - 1
                st.session_state[state["key_del"]].append(idx)
                st.success("EVIDÊNCIA REMOVIDA. CLIQUE EM SALVAR ALTERAÇÕES.")
                st.rerun()
    with col_b:
        if st.button("🗑️ LIMPAR TODAS AS FOTOS", key=f"lim_{lid}"):
            st.session_state[f"conf_lim_{lid}"] = True
    with col_c:
        _tratar_botoes_acao_pdf(lid, state["row"], state)


def _tratar_limpeza(lid):
    if st.session_state.get(f"conf_lim_{lid}"):
        st.warning("⚠️ TEM CERTEZA? ESTA AÇÃO APAGARÁ **TODAS** AS FOTOS.")
        cs, cn = st.columns(2)
        if cs.button("✅ SIM, APAGAR TUDO", key=f"sim_{lid}"):
            conn2 = sqlite3.connect(DB_NAME)
            c2 = conn2.cursor()
            c2.execute("UPDATE relatorios SET fotos_json='[]', extras_json='[]' WHERE id=?", (lid,))
            conn2.commit()
            conn2.close()
            st.session_state.pop(f"conf_lim_{lid}", None)
            st.rerun()
        if cn.button("❌ CANCELAR", key=f"nao_{lid}"):
            st.session_state.pop(f"conf_lim_{lid}", None)
            st.rerun()


def _salvar_edicoes(lid, state):
    fotos_finais_edit = []
    idx_edit = 0
    kd = st.session_state[state["key_del"]]
    for k, f in enumerate(state["fotos_db"]):
        if k not in kd:
            if idx_edit < len(state["fotos_edit"]):
                fotos_finais_edit.append(state["fotos_edit"][idx_edit])
                idx_edit += 1
            else:
                fotos_finais_edit.append(f)
    fotos_finais_edit += state["novas"]
    st.session_state[state["key_del"]] = []

    d = state["cad"]
    conn3 = sqlite3.connect(DB_NAME)
    c3 = conn3.cursor()
    c3.execute('''UPDATE relatorios
                    SET titulo=?,contato=?,empresa=?,telefone=?,email=?,site_id=?,endereco=?,data_hora=?,
                        fotos_json=?,extras_json=? WHERE id=?''',
                (d["tit"], d["con"], d["emp"], d["tel"], d["eml"], d["sit"], d["end"], d["dat"],
                 json.dumps(fotos_finais_edit), json.dumps(state["extras_edit"]), lid))
    conn3.commit()
    conn3.close()
    st.success("✅ RELATÓRIO ATUALIZADO COM SUCESSO!")
    st.rerun()


def _processar_acoes_relatorio(state: dict):
    lid = state["lid"]
    _tratar_botoes_acao(lid, state)
    _tratar_limpeza(lid)
    if state["salvar"]:
        _salvar_edicoes(lid, state)


def _render_dados_cadastrais_form(row, lid, fotos_db, extras_db):
    key_del = f"del_{lid}"
    if key_del not in st.session_state:
        st.session_state[key_del] = []

    with st.form(f"form_ed_{lid}"):
        cad = _render_cadastrais(row, lid)
        fotos_edit = _render_edicao_lista(fotos_db, lid, "EDITAR EVIDÊNCIAS", "📸", "f", st.session_state[key_del])
        extras_edit = _render_edicao_lista(extras_db, lid, "EDITAR ANEXOS", "📎", "e")
        novas = _render_novas_fotos(lid, fotos_db + extras_db)

        col_s, col_del = st.columns([2, 1])
        with col_s:
            salvar = st.form_submit_button("🔄  SALVAR ALTERAÇÕES", type="primary", use_container_width=True)
        with col_del:
            excluir_sel = st.selectbox(
                "EXCLUIR EVIDÊNCIA:",
                ["-- SELECIONE --"] + [f"#{k+1}: {f.get('titulo','')}" for k, f in enumerate(fotos_db) if k not in st.session_state[key_del]],
                key=f"sel_{lid}"
            )

    return {
        "lid": lid, "row": row, "salvar": salvar, "excluir_sel": excluir_sel,
        "key_del": key_del, "fotos_db": fotos_db, "extras_db": extras_db,
        "fotos_edit": fotos_edit, "extras_edit": extras_edit, "novas": novas, "cad": cad
    }

def _render_relatorio_expander(row):
    lid = row['id']
    fotos_db = json.loads(row['fotos_json'] or "[]")
    extras_db = json.loads(row['extras_json'] or "[]") if 'extras_json' in row.keys() else []
    
    with st.expander(f"📍 **{row['site_id']}**  |  {row['data_hora']}  |  {len(fotos_db)} evidência(s)  {len(extras_db)} anexo(s)  |  ID #{lid}"):
        state = _render_dados_cadastrais_form(row, lid, fotos_db, extras_db)
        _processar_acoes_relatorio(state)

def _executar_busca_relatorios(termo, limite):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    if termo.strip():
        c.execute("SELECT * FROM relatorios WHERE site_id LIKE ? OR titulo LIKE ? ORDER BY id DESC LIMIT ?", (f'%{termo}%', f'%{termo}%', limite))
    else:
        c.execute("SELECT * FROM relatorios ORDER BY id DESC LIMIT ?", (limite,))
    rows = c.fetchall()
    conn.close()
    return rows

def _render_metricas_pesquisa(rows):
    st.markdown("<br>", unsafe_allow_html=True)
    ta, tb, tc = st.columns(3)
    with ta:
        st.markdown(f'<div class="eng-metric"><div class="eng-metric-val">{len(rows)}</div><div class="eng-metric-label">RESULTADOS</div></div>', unsafe_allow_html=True)
    with tb:
        total_ev = sum(len(json.loads(r['fotos_json'] or "[]")) for r in rows)
        st.markdown(f'<div class="eng-metric"><div class="eng-metric-val">{total_ev}</div><div class="eng-metric-label">EVIDÊNCIAS</div></div>', unsafe_allow_html=True)
    with tc:
        total_ex = sum(len(json.loads(r['extras_json'] or "[]")) if 'extras_json' in r.keys() else 0 for r in rows)
        st.markdown(f'<div class="eng-metric"><div class="eng-metric-val">{total_ex}</div><div class="eng-metric-label">ANEXOS</div></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)


def tela_pesquisa():
    banner("PESQUISAR, EDITAR E EXPORTAR")
    secao("🔍", "BUSCAR RELATÓRIOS")
    
    col_busca, col_lim = st.columns([3, 1])
    with col_busca:
        termo = st.text_input("NOME DO SITE OU PARTE DO TÍTULO:", placeholder="Ex: SMSMT15")
    with col_lim:
        limite = st.selectbox("EXIBIR", [10, 25, 50, 100], index=0)

    rows = _executar_busca_relatorios(termo, limite)

    if not rows:
        st.info("NENHUM RELATÓRIO ENCONTRADO. CRIE UM NA ABA 'NOVO RELATÓRIO'.")
        return

    _render_metricas_pesquisa(rows)

    for row in rows:
        _render_relatorio_expander(row)


def tela_dashboard():
    banner("DASHBOARD")
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM relatorios ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()

    if not rows:
        st.info("NENHUM RELATÓRIO CADASTRADO AINDA.")
        return

    total_rel  = len(rows)
    total_ev   = sum(len(json.loads(r['fotos_json'] or "[]")) for r in rows)
    total_ex   = sum(len(json.loads(r['extras_json'] or "[]")) if 'extras_json' in r.keys() else 0 for r in rows)
    sites_uniq = len({r['site_id'] for r in rows})

    secao("📊", "RESUMO GERAL")
    m1, m2, m3, m4 = st.columns(4)
    for col, val, lbl in [
        (m1, total_rel,  "RELATÓRIOS"),
        (m2, sites_uniq, "SITES ÚNICOS"),
        (m3, total_ev,   "EVIDÊNCIAS"),
        (m4, total_ex,   "ANEXOS"),
    ]:
        col.markdown(f'<div class="eng-metric"><div class="eng-metric-val">{val}</div><div class="eng-metric-label">{lbl}</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    secao("📈", "ANÁLISE DE PRODUTIVIDADE (TOP 10 SITES COM MAIS FOTOS)")
    df_chart = pd.DataFrame([{
        "SITE": r['site_id'],
        "TOTAL FOTOS": len(json.loads(r['fotos_json'] or "[]")) + (len(json.loads(r['extras_json'] or "[]")) if 'extras_json' in r.keys() else 0)
    } for r in rows])
    
    if not df_chart.empty:
        df_agrupado = df_chart.groupby("SITE").sum().reset_index().sort_values("TOTAL FOTOS", ascending=False).head(10)
        st.bar_chart(data=df_agrupado.set_index("SITE"), color="#DA291C", height=350)

    st.markdown("---")
    secao("📋", "ÚLTIMOS 10 RELATÓRIOS")
    df = pd.DataFrame([{
        "ID": r['id'],
        "SITE": r['site_id'],
        "ENDEREÇO": r['endereco'] if 'endereco' in r.keys() else "",
        "DATA/HORA": r['data_hora'],
        "EVIDÊNCIAS": len(json.loads(r['fotos_json'] or "[]")),
        "ANEXOS": len(json.loads(r['extras_json'] or "[]")) if 'extras_json' in r.keys() else 0,
    } for r in rows[:10]])
    st.dataframe(df, use_container_width=True, hide_index=True)


st.set_page_config(
    page_title="GIRCP | Engemon OpServices",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)
init_db()
aplicar_estilo()

with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:20px 0 10px 0;">
      <div style="font-size:28px;">⚡</div>
      <div style="font-size:18px;font-weight:900;letter-spacing:1.5px;color:#fff;">GIRCP</div>
      <div style="font-size:10px;opacity:0.65;color:#fff;margin-top:2px;">
        ENGEMON OPSERVICES
      </div>
    </div>""", unsafe_allow_html=True)
    st.markdown("---")

    tec = st.text_input("👷 TÉCNICO EM CAMPO:", value=st.session_state.get("_tecnico_global", ""), placeholder="Seu nome", key="_tec_sidebar_rel")
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

rule_map = {
    "📝 NOVO RELATÓRIO": tela_novo,
    "🔍 PESQUISAR E EXPORTAR": tela_pesquisa,
    "📊 DASHBOARD": tela_dashboard
}
if menu in rule_map:
    rule_map[menu]()