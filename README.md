# ⚡ GIRCP - Gerador Inteligente de Relatórios e Controle Fotográfico

Este projeto é uma aplicação web de missão crítica desenvolvida em Python com Streamlit para a criação, edição, gerenciamento analítico e exportação de relatórios fotográficos técnicos (laudos corporativos) em formato PDF, seguindo os padrões de excelência Engemon OpServices.

## ✨ O que há de novo na v3.0?
A versão 3.0 trouxe um salto de maturidade para o sistema, incorporando inteligência analítica, otimização de performance e módulos gerenciais:
* **Autopreenchimento Inteligente (Filtros em Cascata):** Importação de arquivos `.KML` ou `.XLSX` para preencher automaticamente os dados do site, endereço e tecnologia/grupo.
* **Compressão On-the-Fly:** Otimização de imagens no upload (via PIL/Pillow) para garantir PDFs mais leves sem perda de qualidade visual.
* **Reordenação Dinâmica:** Capacidade de reordenar evidências fotográficas interativamente (para cima/para baixo) antes de salvar ou durante a edição.
* **Geração Autonumérica:** Controle automático de número de relatório sequencial (ex: `GIRCP-YYYY-XXXX`) e versão de revisão.
* **Dashboard Gerencial:** Nova aba de métricas com análise de produtividade (Top 10 sites), distribuição de severidade (Crítico, Observação, Normal) e KPIs gerais de vistorias.
* **Exportação Multiformato:** Além do PDF Corporativo, agora é possível exportar a base de dados completa ou resultados de pesquisa customizada para o formato Excel (`.xlsx`).

## 🛠️ Funcionalidades Principais
* **Cadastro de Laudos:** Formulário completo para identificação da infraestrutura, dados do cliente e metadados da vistoria técnica (data e hora).
* **Processamento de Imagens e Metadados:** Upload múltiplo de evidências e anexos, com suporte a categorização, tags de severidade, títulos e descrições técnicas detalhadas para cada foto.
* **Banco de Dados Local Otimizado:** Armazenamento estruturado utilizando SQLite (`laudos_corp_v3.db` com `PRAGMA journal_mode=WAL` para maior velocidade e concorrência), persistindo imagens em Base64 e metadados em JSON.
* **Motor de Edição:** Interface avançada para pesquisar laudos anteriores pelo nome do site. Expanda o card para modificar textos, reordenar evidências, remover fotos específicas ou anexar novas.
* **Geração de PDF Corporativo:** Motor de PDF alimentado pelo `weasyprint`, convertendo HTML/CSS em documentos bem formatados com marca d'água, logotipo da Engemon, tabelas estruturadas, badges coloridos de severidade, assinatura digital do técnico e rodapé de conformidade com a LGPD.

## 💻 Tecnologias Utilizadas
* **Python 3.x**
* **Streamlit:** Interface gráfica web e roteamento de estados.
* **SQLite3:** Banco de dados relacional embutido.
* **WeasyPrint:** Motor de renderização HTML/CSS de alta fidelidade para PDF.
* **Pandas & OpenPyXL:** Manipulação de DataFrames e exportação de relatórios para Excel.
* **Pillow (PIL):** Processamento, compressão e redimensionamento de imagens nativo.
* **Bibliotecas auxiliares:** `base64`, `json`, `os`, `datetime`, `hashlib`, `xml.etree.ElementTree` (para extração de KML).

## ⚙️ Instalação e Execução

**1. Clone ou baixe o projeto**
Coloque os arquivos do projeto em um diretório local seguro.

**2. Instale as dependências**
No terminal do seu ambiente virtual, execute:
```bash
pip install streamlit weasyprint pandas openpyxl pillow

**Execute**
streamlit run app_relatorio.py

🔄 Fluxograma de Utilização


graph TD
    A[Início do Fluxo] --> B{Possui Base KML/Excel?}
    B -- Sim --> C[Fazer Upload do Arquivo Base]
    C --> D[Selecionar Grupo e Site - Filtro Cascata]
    B -- Não --> E[Digitar Manualmente a Identificação do Site]
    D --> F[Preencher Dados Cadastrais Restantes]
    E --> F
    F --> G[Upload de Evidências Fotográficas]
    G --> H[Upload de Anexos Extras]
    H --> I[Inserir Títulos, Descrições, Categoria e Severidade]
    I --> J{Deseja Reordenar Fotos?}
    J -- Sim --> K[Usar Botões ⬆️ e ⬇️]
    K --> L[Salvar Relatório no Banco de Dados]
    J -- Não --> L
    
    L --> M((Fim da Criação))
    
    M --> N[Aba: Pesquisar e Exportar]
    M --> O[Aba: Dashboard]
    
    N --> P[Editar Laudo / Adicionar Fotos / Excluir Fotos]
    P --> Q[Gerar PDF Corporativo Final]
    N --> T[Exportar Busca para Excel]
    
    O --> R[Analisar KPIs de Severidade e Produtividade]
    O --> S[Exportar Base de Dados Completa para Excel]