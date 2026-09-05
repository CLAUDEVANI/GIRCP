import streamlit as st
import sqlite3
import os
import uuid
from datetime import datetime
from fpdf import FPDF
from PIL import Image, ImageDraw, ImageFont
import io

# 1. Configuração do Banco de Dados
def init_db():
    conn = sqlite3.connect("laudos_fotograficos.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS relatorios
                 (id INTEGER PRIMARY KEY, data_criacao TEXT, empresa TEXT, 
                  contato TEXT, telefone TEXT, localizacao TEXT, titulo TEXT, pdf_path TEXT)''')
    conn.commit()
    conn.close()

# 2. Processamento UX nas Imagens (Compressão e Carimbo)
def processar_imagem_ux(upload_file, localizacao, data_str):
    """Aplica compressão, resize e carimbo de rastreabilidade na imagem"""
    img = Image.open(upload_file).convert('RGB')
    
    # Compressão e Resize (Max 800px mantendo proporção)
    img.thumbnail((800, 800), Image.Resampling.LANCZOS)
    
    # Carimbo de Metadados (Tarja semitransparente)
    draw = ImageDraw.Draw(img, 'RGBA')
    w, h = img.size
    draw.rectangle(((0, h - 30), (w, h)), fill=(0, 0, 0, 160))
    
    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except IOError:
        font = ImageFont.load_default()
        
    texto_carimbo = f"SITE: {localizacao} | DATA: {data_str}"
    draw.text((10, h - 22), texto_carimbo, font=font, fill=(255, 255, 255, 255))
    
    return img

# 3. Classe de Geração de PDF (Padrão Industrial com Cores)
class RelatorioPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.set_text_color(218, 41, 28) # Vermelho Claro/Engemon
        self.cell(0, 10, 'RELATORIO FOTOGRAFICO TECNICO', 0, 1, 'C')
        self.line(10, 22, 200, 22)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def gerar_pdf(dados, fotos):
    pdf = RelatorioPDF()
    pdf.add_page()
    
    # Cabeçalho de Dados
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0)
    pdf.cell(100, 6, f"Titulo: {dados['titulo']}", 0, 0)
    pdf.cell(90, 6, f"Data: {dados['data_criacao']}", 0, 1)
    pdf.cell(100, 6, f"Empresa: {dados['empresa']}", 0, 0)
    pdf.cell(90, 6, f"Localizacao: {dados['localizacao']}", 0, 1)
    pdf.cell(100, 6, f"Contato: {dados['contato']}", 0, 0)
    pdf.cell(90, 6, f"Telefone: {dados['telefone']}", 0, 1)
    pdf.line(10, pdf.get_y() + 2, 200, pdf.get_y() + 2)
    pdf.ln(10)

    # Injeção das Fotos, Comentários e Severidade
    for i, foto_data in enumerate(fotos):
        if pdf.get_y() > 220:
            pdf.add_page()
            
        y_before = pdf.get_y()
        
        # Salva imagem temporária otimizada
        temp_img_path = f"temp_img_{uuid.uuid4().hex[:8]}_{i}.jpg"
        foto_data['img_processada'].save(temp_img_path, format="JPEG", quality=75)
        
        # Desenha a imagem
        pdf.image(temp_img_path, x=10, y=y_before, w=90)
        
        # Título da Imagem com Cor Baseada na Severidade
        pdf.set_xy(105, y_before)
        if foto_data['severidade'] == "Crítico":
            pdf.set_text_color(218, 41, 28) # Vermelho
        elif foto_data['severidade'] == "Observação":
            pdf.set_text_color(217, 119, 6) # Amarelo escuro
        else:
            pdf.set_text_color(22, 163, 74) # Verde
            
        pdf.set_font('Arial', 'B', 11)
        # Remove caracteres especiais complexos para evitar erro no FPDF
        tit_limpo = str(foto_data['titulo']).encode('ascii', 'ignore').decode('ascii')
        pdf.cell(90, 6, f"Foto {i+1} [{foto_data['categoria']}]: {tit_limpo}", 0, 1)
        
        # Badge de Severidade em texto e Comentário
        pdf.set_xy(105, y_before + 8)
        pdf.set_font('Arial', 'B', 9)
        pdf.cell(90, 5, f"Status: {foto_data['severidade']}", 0, 1)
        
        pdf.set_xy(105, y_before + 14)
        pdf.set_font('Arial', '', 10)
        pdf.set_text_color(50) # Cinza escuro para o texto
        com_limpo = str(foto_data['comentario']).encode('ascii', 'ignore').decode('ascii')
        pdf.multi_cell(90, 5, com_limpo)
        
        pdf.set_y(y_before + 80) # Espaçamento para a próxima foto
        
        if os.path.exists(temp_img_path):
            os.remove(temp_img_path)

    nome_arquivo = f"Relatorio_{dados['localizacao'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    pdf.output(nome_arquivo)
    return nome_arquivo

# 4. Interface da Aplicação
st.set_page_config(page_title="Gerador de Relatórios", layout="wide", page_icon="📸")
init_db()

# Inicializa o estado persistente para a ordenação das fotos
if "ordem_fotos" not in st.session_state:
    st.session_state["ordem_fotos"] = []

st.title("📸 Sistema de Emissão de Relatório Fotográfico")

with st.form("form_relatorio"):
    st.subheader("📋 Dados da Vistoria")
    col1, col2 = st.columns(2)
    with col1:
        titulo = st.text_input("Título", value="Relatório Fotográfico Claro")
        empresa = st.text_input("Empresa", value="Engemon")
        contato = st.text_input("Nome do Contato")
    with col2:
        localizacao = st.text_input("Localização (Site ID)", value="SMSPB08")
        telefone = st.text_input("Telefone")
        
    st.subheader("🖼️ Anexar Evidências")
    arquivos_fotos = st.file_uploader("Selecione as fotos", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)
    
    # Sincroniza a ordem atual caso novos arquivos sejam adicionados
    if arquivos_fotos:
        atuais = [f.name for f in arquivos_fotos]
        # Remove do estado o que não está mais nos arquivos
        st.session_state["ordem_fotos"] = [f for f in st.session_state["ordem_fotos"] if f in atuais]
        # Adiciona novos arquivos ao estado de ordem
        for f in atuais:
            if f not in st.session_state["ordem_fotos"]:
                st.session_state["ordem_fotos"].append(f)
    else:
        st.session_state["ordem_fotos"] = []
    
    fotos_processadas = []
    
    if arquivos_fotos:
        # Cria um dicionário para acesso rápido ao arquivo real
        dict_arquivos = {a.name: a for a in arquivos_fotos}
        
        for idx, filename in enumerate(st.session_state["ordem_fotos"]):
            arquivo = dict_arquivos[filename]
            safe_key = filename.replace(".", "_").replace(" ", "_")
            
            st.markdown(f"---")
            col_img, col_txt, col_ctrl = st.columns([1.5, 2.5, 0.5])
            
            with col_img:
                # Processamento da imagem no frontend para UX (lazy/resize)
                img_ux = processar_imagem_ux(arquivo, localizacao, datetime.now().strftime("%d/%m/%Y %H:%M"))
                st.image(img_ux, use_container_width=True, caption=f"ID: {uuid.uuid4().hex[:6]}")
                
            with col_txt:
                tit = st.text_input(f"Título da evidência", key=f"t_{safe_key}")
                
                c_tags1, c_tags2 = st.columns(2)
                with c_tags1:
                    cat = st.selectbox("Categoria", ["Geral", "Antes", "Depois"], key=f"cat_{safe_key}")
                with c_tags2:
                    sev = st.selectbox("Severidade", ["Normal", "Observação", "Crítico"], key=f"sev_{safe_key}")
                
                com = st.text_area(f"Comentários técnicos", height=68, key=f"c_{safe_key}")
                
                fotos_processadas.append({
                    "file": arquivo, 
                    "img_processada": img_ux,
                    "titulo": tit, 
                    "comentario": com,
                    "categoria": cat,
                    "severidade": sev
                })
                
            with col_ctrl:
                # Controles robustos de ordenação vertical
                st.markdown("<br>", unsafe_allow_html=True)
                if idx > 0:
                    if st.form_submit_button("⬆️", key=f"up_{safe_key}"):
                        # Swap logic
                        ordem = st.session_state["ordem_fotos"]
                        ordem[idx], ordem[idx-1] = ordem[idx-1], ordem[idx]
                        st.rerun()
                if idx < len(st.session_state["ordem_fotos"]) - 1:
                    if st.form_submit_button("⬇️", key=f"dw_{safe_key}"):
                        # Swap logic
                        ordem = st.session_state["ordem_fotos"]
                        ordem[idx], ordem[idx+1] = ordem[idx+1], ordem[idx]
                        st.rerun()

    submit = st.form_submit_button("💾 Salvar e Gerar PDF", type="primary")

if submit:
    if not arquivos_fotos:
        st.error("Adicione pelo menos uma foto para gerar o laudo.")
    else:
        dados = {
            "titulo": titulo, "empresa": empresa, "contato": contato,
            "localizacao": localizacao, "telefone": telefone,
            "data_criacao": datetime.now().strftime("%d/%m/%Y %H:%M")
        }
        
        with st.spinner("Otimizando imagens, compilando metadados e gravando PDF..."):
            pdf_path = gerar_pdf(dados, fotos_processadas)
            
            conn = sqlite3.connect("laudos_fotograficos.db")
            c = conn.cursor()
            c.execute('''INSERT INTO relatorios (data_criacao, empresa, contato, telefone, localizacao, titulo, pdf_path)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                      (dados["data_criacao"], empresa, contato, telefone, localizacao, titulo, pdf_path))
            conn.commit()
            conn.close()
            
            st.success("✅ Relatório auditado e emitido com sucesso!")
            with open(pdf_path, "rb") as f:
                st.download_button("📥 Baixar PDF Seguro", f, file_name=pdf_path, mime="application/pdf")