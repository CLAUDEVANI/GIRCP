import streamlit as st
import sqlite3
import os
from datetime import datetime
from fpdf import FPDF
from PIL import Image
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

# 2. Classe de Geração de PDF (Padrão Industrial)
class RelatorioPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.set_text_color(218, 41, 28) # Vermelho Claro/Engemon
        self.cell(0, 10, 'RELATÓRIO FOTOGRÁFICO TÉCNICO', 0, 1, 'C')
        self.line(10, 22, 200, 22)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def gerar_pdf(dados, fotos):
    pdf = RelatorioPDF()
    pdf.add_page()
    
    # Cabeçalho de Dados
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0)
    pdf.cell(100, 6, f"Título: {dados['titulo']}", 0, 0)
    pdf.cell(90, 6, f"Data: {dados['data_criacao']}", 0, 1)
    pdf.cell(100, 6, f"Empresa: {dados['empresa']}", 0, 0)
    pdf.cell(90, 6, f"Localização: {dados['localizacao']}", 0, 1)
    pdf.cell(100, 6, f"Contato: {dados['contato']}", 0, 0)
    pdf.cell(90, 6, f"Telefone: {dados['telefone']}", 0, 1)
    pdf.line(10, pdf.get_y() + 2, 200, pdf.get_y() + 2)
    pdf.ln(10)

    # Injeção das Fotos e Comentários
    for i, foto_data in enumerate(fotos):
        if pdf.get_y() > 220:
            pdf.add_page()
            
        y_before = pdf.get_y()
        
        # Salva imagem temporária para o FPDF ler
        img = Image.open(foto_data['file'])
        img = img.convert('RGB')
        temp_img_path = f"temp_img_{i}.jpg"
        img.save(temp_img_path, format="JPEG", quality=70)
        
        # Desenha a imagem e o texto
        pdf.image(temp_img_path, x=10, y=y_before, w=90)
        pdf.set_xy(105, y_before)
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(90, 6, f"Foto {i+1}: {foto_data['titulo']}", 0, 1)
        pdf.set_xy(105, y_before + 8)
        pdf.set_font('Arial', '', 10)
        pdf.multi_cell(90, 5, foto_data['comentario'])
        
        pdf.set_y(y_before + 75) # Espaçamento para a próxima foto
        os.remove(temp_img_path)

    nome_arquivo = f"Relatorio_{dados['localizacao'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M')}.pdf"
    pdf.output(nome_arquivo)
    return nome_arquivo

# 3. Interface da Aplicação
st.set_page_config(page_title="Gerador de Relatórios", layout="wide")
init_db()

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
    
    fotos_processadas = []
    if arquivos_fotos:
        for i, arquivo in enumerate(arquivos_fotos):
            st.markdown(f"**Imagem {i+1}**")
            col_img, col_txt = st.columns([1, 2])
            with col_img:
                st.image(arquivo, width=200)
            with col_txt:
                tit = st.text_input(f"Título da foto {i+1}", key=f"t_{i}")
                com = st.text_area(f"Comentários da foto {i+1}", key=f"c_{i}")
                fotos_processadas.append({"file": arquivo, "titulo": tit, "comentario": com})

    submit = st.form_submit_button("💾 Salvar e Gerar PDF")

if submit:
    if not arquivos_fotos:
        st.error("Adicione pelo menos uma foto.")
    else:
        dados = {
            "titulo": titulo, "empresa": empresa, "contato": contato,
            "localizacao": localizacao, "telefone": telefone,
            "data_criacao": datetime.now().strftime("%d/%m/%Y %H:%M")
        }
        
        with st.spinner("Compilando PDF e gravando no banco..."):
            pdf_path = gerar_pdf(dados, fotos_processadas)
            
            conn = sqlite3.connect("laudos_fotograficos.db")
            c = conn.cursor()
            c.execute('''INSERT INTO relatorios (data_criacao, empresa, contato, telefone, localizacao, titulo, pdf_path)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                      (dados["data_criacao"], empresa, contato, telefone, localizacao, titulo, pdf_path))
            conn.commit()
            conn.close()
            
            st.success("✅ Relatório emitido com sucesso!")
            with open(pdf_path, "rb") as f:
                st.download_button("📥 Baixar PDF", f, file_name=pdf_path, mime="application/pdf")