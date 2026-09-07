# ⚡ GIRCP - Gerador Inteligente de Relatórios e Controle Fotográfico

Este projeto é uma aplicação web de missão crítica desenvolvida em Python com Streamlit para a criação, edição, gerenciamento analítico e exportação de relatórios fotográficos técnicos (laudos corporativos) em formato PDF, seguindo os padrões de excelência Engemon OpServices.

## ✨ O que há de novo na v3.4.1?
A versão 3.4.1 trouxe um salto de maturidade tática e de segurança para o sistema, incorporando inteligência logística e renderização antibloqueio:
* **Módulo de Roteirização (Field Service):** Algoritmo do Vizinho Mais Próximo (TSP local) integrado à API do OpenRouteService (ORS) para gerar a sequência lógica de atendimento, plotar o trajeto rua a rua e calcular métricas vitais como *Windshield Time* (tempo de direção), Quilometragem Total e Densidade da Rota.
* **Cartografia Avançada (PyDeck):** Substituição do motor gráfico nativo pelo PyDeck. Garante evasão de firewalls corporativos, renderização em RGB condicional (vermelho para anomalias críticas) e tooltips interativos flutuantes, além de rotular numericamente a ordem de visitação dos sites.
* **Segurança e Sanitização (Anti-XSS e SQLi):** Blindagem pesada contra injeção de scripts maliciosos através da sanitização de inputs HTML e implementação rigorosa de queries SQL parametrizadas.
* **Geolocalização Flexível:** Importação de arquivos `.KML` e `.XLSX` via filtros em cascata para autopreenchimento, com a nova adição de inserção ou correção manual de Latitude e Longitude para sites sem mapeamento prévio.
* **Compressão On-the-Fly:** Otimização de imagens no upload (via PIL/Pillow) para garantir PDFs mais leves sem perda de qualidade visual.
* **Reordenação Dinâmica:** Capacidade de reordenar evidências fotográficas interativamente (para cima/para baixo) antes de salvar ou durante a edição.
* **Geração Autonumérica:** Controle automático de número de relatório sequencial (ex: `GIRCP-YYYY-XXXX`) e versão de revisão.

## 🛠️ Funcionalidades Principais
* **Cadastro de Laudos:** Formulário completo para identificação da infraestrutura, dados do cliente e metadados da vistoria técnica.
* **Processamento de Imagens e Metadados:** Upload múltiplo de evidências e anexos, com suporte a categorização, tags de severidade, títulos e descrições técnicas detalhadas para cada foto.
* **Banco de Dados Local Otimizado:** Armazenamento estruturado utilizando SQLite (`laudos_corp_v3.db` com `PRAGMA journal_mode=WAL` para maior velocidade), persistindo imagens em Base64 e metadados em JSON.
* **Motor de Edição:** Interface avançada para pesquisar laudos anteriores. Expanda o card para modificar textos, corrigir coordenadas, reordenar evidências ou anexar novas fotos.
* **Geração de PDF Corporativo:** Motor alimentado pelo `weasyprint`, convertendo HTML/CSS em documentos bem formatados com marca d'água, logotipos, badges coloridos, assinatura digital e rodapé de conformidade com a LGPD.

## 💻 Tecnologias Utilizadas
* **Python 3.x**
* **Streamlit:** Interface gráfica web e roteamento de estados.
* **PyDeck & Plotly:** Renderização de mapas táticos geoespaciais e gráficos de alta fidelidade.
* **SQLite3:** Banco de dados relacional embutido.
* **WeasyPrint:** Motor de renderização HTML/CSS de alta fidelidade para PDF.
* **Pandas & OpenPyXL:** Manipulação de DataFrames e exportação analítica.
* **Requests:** Comunicação HTTP direta com a API do OpenRouteService.
* **Pillow (PIL):** Processamento, compressão e redimensionamento nativo de imagens.
* **Bibliotecas auxiliares:** `base64`, `json`, `os`, `datetime`, `hashlib`, `math`, `xml.etree.ElementTree` (extração KML).

## ⚙️ Instalação e Execução

**1. Clone ou baixe o projeto**
Coloque os arquivos do projeto em um diretório local seguro.

**2. Instale as dependências**
No terminal do seu ambiente virtual, execute:
```bash
pip install streamlit weasyprint pandas openpyxl pillow plotly pydeck requests

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
    B -- Não --> E[Digitar Manualmente a Identificação e Coordenadas]
    D --> F[Preencher Dados Cadastrais Restantes]
    E --> F
    F --> G[Upload de Evidências Fotográficas]
    G --> H[Upload de Anexos Extras]
    H --> I[Inserir Metadados: Título, Descrição, Severidade]
    I --> J{Deseja Reordenar Fotos?}
    J -- Sim --> K[Usar Botões ⬆️ e ⬇️]
    K --> L[Salvar Relatório no BD]
    J -- Não --> L
    
    L --> M((Operações Posteriores))
    
    M --> N[Aba: Pesquisar e Exportar]
    M --> O[Aba: Dashboard Analítico]
    M --> U[Aba: Roteirização Tática]
    
    N --> P[Editar Laudo / Corrigir Coordenadas / Gerenciar Fotos]
    P --> Q[Gerar PDF Corporativo Final]
    
    O --> R[Analisar KPIs de Severidade e Produtividade]
    O --> S[Visualizar Mapa de Dispersão Global]
    
    U --> V[Definir Ponto de Partida]
    V --> W[Selecionar Múltiplos Sites Alvo]
    W --> X[Processar Otimização TSP + API ORS]
    X --> Y[Gerar Projeções de Rota, ETA e Windshield Time]