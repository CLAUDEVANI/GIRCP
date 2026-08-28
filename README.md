# GIRCP - Sistema de Emissão de Relatórios Técnicos

Este projeto é uma aplicação web desenvolvida em Python com Streamlit para a criação, edição, gerenciamento e exportação de relatórios fotográficos técnicos (laudos corporativos) em formato PDF.

## Funcionalidades Principais
* **Cadastro de Laudos:** Formulário completo para identificação da infraestrutura, dados do cliente e metadados da vistoria técnica.
* **Processamento de Imagens:** Upload múltiplo de evidências e anexos adicionais com suporte a títulos e descrições individuais para cada foto.
* **Banco de Dados Local:** Armazenamento estruturado utilizando SQLite (`laudos_corp_v2.db`), persistindo imagens em Base64 e metadados em JSON.
* **Motor de Edição:** Interface avançada para pesquisar laudos anteriores pelo nome do site, editar títulos e descrições, adicionar novas fotos ou remover evidências específicas de forma individual ou em massa.
* **Geração de PDF Corporativo:** Motor de PDF alimentado pelo `weasyprint`, convertendo HTML/CSS em documentos bem formatados com marca d'água, logotipo, tabelas estruturadas, assinatura digital do responsável (CRT) e rodapé de conformidade com a LGPD.

## Tecnologias Utilizadas
* **Python 3.x**
* **Streamlit:** Interface gráfica web e roteamento de estados.
* **SQLite3:** Banco de dados relacional nativo do Python.
* **WeasyPrint:** Motor de renderização HTML/CSS para PDF.
* **Bibliotecas nativas:** `base64`, `json`, `os`, `datetime`.

## Instalação e Execução

**1. Clone ou baixe o projeto**
Coloque os arquivos do projeto em um diretório local.

**2. Instale as dependências**
No terminal do seu ambiente virtual, execute:
```bash
pip install streamlit weasyprint
```

**3. Configure os ativos visuais**
Para que o PDF corporativo seja gerado perfeitamente, certifique-se de que os seguintes arquivos de imagem estejam salvos no mesmo diretório do script principal:
* `assinatura_claudevani.png` (Arquivo de assinatura)
* `logo_engemon.png` (Logotipo da empresa)
* `WhatsApp Image 2026-06-25 at 05.46.59.jpeg` (Marca d'água de fundo)

**4. Execute a aplicação**
```bash
streamlit run app_relatorio_final.py
```

## Estrutura do Banco de Dados
O sistema inicializa automaticamente a tabela `relatorios` se ela não existir. A estrutura inclui:
* `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
* `titulo`, `contato`, `empresa`, `telefone`, `email`, `identificacao_site`, `data_hora` (TEXT)
* `fotos_json` (TEXT - Lista de dicionários das evidências principais)
* `fotos_extras_json` (TEXT - Lista de dicionários dos anexos adicionais)

## Fluxo de Uso
* **Aba "Novo Relatório":** Preencha os dados do site, faça o upload das imagens principais e extras, insira as descrições técnicas e clique em "Salvar Laudo no Banco de Dados".
* **Aba "Pesquisar, Editar e Exportar":** Busque pelo nome de identificação do site. Expanda o card do laudo desejado para modificar textos, marcar fotos para exclusão ou fazer upload de novos arquivos. Clique em "Salvar Alterações" para gravar no banco e, em seguida, utilize o botão "Gerar PDF Corporativo" para realizar o download do documento finalizado.