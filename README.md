# ⚡ GIRCP - Gerador Inteligente de Relatórios e Controle Fotográfico

Aplicação web de missão crítica desenvolvida em Python com Streamlit para criação, edição, gerenciamento analítico e exportação de relatórios fotográficos técnicos (laudos corporativos) em PDF, seguindo padrões de excelência corporativa.

---

## ✨ O que há de novo na v3.5.0?

A versão 3.5.0 expande o módulo de Roteirização Tática com exportação completa de roteiros, rastreamento de materiais por evidência e inteligência de status no mapa tático do Dashboard.

### 📤 Exportação de Roteiro (PDF e Excel)
Após otimizar a rota, um novo painel de exportação é gerado automaticamente abaixo do mapa:
* **PDF do Roteiro:** Documento A4 corporativo com KPIs operacionais (sites atendidos, quilometragem, windshield time, densidade), resumo de severidades, tabela de sequenciamento com coordenadas e seção de evidências com thumbs fotográficos e materiais apontados por site.
* **Planilha Excel (.xlsx):** Três abas estruturadas — *KPIs da Operação*, *Sequenciamento* e *Evidências e Materiais* — com formatação condicional por severidade (verde/amarelo/vermelho).
* **Persistência de estado:** Os arquivos gerados ficam disponíveis para download mesmo após interações subsequentes na interface, via `session_state`.

### 🔧 Campo "Material Necessário" nas Evidências
Novo campo adicionado ao formulário de cada foto, tanto no cadastro de novos laudos quanto na edição de laudos existentes:
* Aparece logo abaixo do campo **Descrição** em cada evidência.
* Salvo no banco de dados junto com os demais metadados da foto.
* Exibido no **PDF do laudo** com destaque visual (borda vermelha) quando preenchido.
* Exibido na **planilha e PDF do roteiro** na coluna "Material Necessário" por site.
* Preservado corretamente ao reordenar (⬆️⬇️) ou excluir evidências.

### 🗺️ Mapa Tático com Status de Visitas
O mapa do Dashboard foi reformulado para exibir o andamento operacional de cada site:
* 🟢 **Concluída** — relatório com evidências fotográficas cadastradas.
* 🟠 **Em Andamento** — relatório cadastrado mas sem fotos ainda.
* 🔴 **Anomalia Crítica** — visita concluída com evidência de severidade Crítica detectada.
* **Seletor de filtro** (radio horizontal) para exibir apenas um status no mapa.
* **3 contadores** acima do mapa: Concluídas / Em Andamento / Com Anomalia Crítica.
* **Tooltip enriquecido** com ícone de status, alerta de anomalia, técnico, data e endereço.
* **Legenda lateral** explicando cada cor diretamente na interface.

---

## ✨ Histórico — v3.4.1

A versão 3.4.1 trouxe inteligência logística e renderização antibloqueio:
* **Módulo de Roteirização (Field Service):** Algoritmo do Vizinho Mais Próximo (TSP local) integrado à API do OpenRouteService (ORS) para sequenciamento de atendimento, trajeto rua a rua e métricas de *Windshield Time*, Quilometragem e Densidade da Rota.
* **Cartografia Avançada (PyDeck):** Substituição do motor gráfico nativo. Renderização em RGB condicional e tooltips interativos, com numeração da ordem de visitação dos sites.
* **Segurança e Sanitização (Anti-XSS e SQLi):** Blindagem contra injeção de scripts e queries SQL parametrizadas.
* **Geolocalização Flexível:** Importação de `.KML` e `.XLSX` com filtros em cascata, mais inserção manual de coordenadas.
* **Compressão On-the-Fly:** Otimização de imagens no upload via PIL/Pillow.
* **Reordenação Dinâmica:** Reordenação de evidências fotográficas antes de salvar ou durante edição.
* **Geração Autonumérica:** Número sequencial automático de relatório (`GIRCP-YYYY-XXXX`) e controle de revisão.

---

## 🛠️ Funcionalidades Principais

* **Cadastro de Laudos:** Formulário completo para identificação da infraestrutura, dados do cliente, metadados da vistoria e coordenadas GPS.
* **Evidências com Metadados Completos:** Upload múltiplo com título, descrição, severidade, categoria e **material necessário para correção** por foto.
* **Banco de Dados Local Otimizado:** SQLite com `PRAGMA journal_mode=WAL`, metadados em JSON e imagens comprimidas em disco.
* **Motor de Edição:** Pesquisa, expansão de card, edição de textos e coordenadas, reordenação e adição de novas fotos inline.
* **PDF Corporativo:** WeasyPrint renderizando HTML/CSS com marca d'água, logotipo, badges de severidade, campo de material necessário, assinatura digital e rodapé LGPD.
* **Dashboard Analítico:** KPIs gerais, gráfico de produtividade por site, distribuição de severidade, mapa tático com status de visitas e linha do tempo de vistorias.
* **Roteirização Tática:** Otimização TSP + ORS, mapa de rota, métricas de field service, painel de evidências/materiais por site e exportação em PDF e Excel.

---

## 💻 Tecnologias Utilizadas

| Biblioteca | Papel |
|---|---|
| **Streamlit** | Interface web e gerenciamento de estado (`session_state`) |
| **PyDeck** | Mapas táticos geoespaciais com camadas e tooltips |
| **Plotly** | Gráficos analíticos (barras, pizza, linha do tempo) |
| **SQLite3** | Banco de dados relacional embutido (WAL mode) |
| **WeasyPrint** | Renderização HTML/CSS para PDF A4 corporativo |
| **Pandas** | Manipulação e análise de DataFrames |
| **OpenPyXL** | Geração de planilhas Excel com formatação condicional |
| **Requests** | Integração com API OpenRouteService (ORS) |
| **Pillow (PIL)** | Compressão e redimensionamento de imagens |
| **xml.etree** | Extração de coordenadas de arquivos KML |
| **Auxiliares** | `base64`, `json`, `os`, `datetime`, `hashlib`, `math` |

---

## ⚙️ Instalação e Execução

**1. Clone o repositório**
```bash
git clone https://github.com/CLAUDEVANI/GIRCP.git
cd GIRCP
```

**2. Crie e ative o ambiente virtual**
```bash
python -m venv meu_ambiente
source meu_ambiente/bin/activate  # Linux/Mac
meu_ambiente\Scripts\activate     # Windows
```

**3. Instale as dependências**
```bash
pip install streamlit weasyprint pandas openpyxl pillow plotly pydeck requests
```

**4. Execute**
```bash
streamlit run app_relatorio.py
```

A aplicação abre em `http://localhost:8501`. Senha padrão configurável via `st.secrets` (chave `senha_acesso`), default: `GIRCP2026`.

---

## 🔄 Fluxograma de Utilização

```mermaid
graph TD
    A[Início do Fluxo] --> B{Possui Base KML/Excel?}
    B -- Sim --> C[Fazer Upload do Arquivo Base]
    C --> D[Selecionar Grupo e Site - Filtro Cascata]
    B -- Não --> E[Digitar Manualmente ID e Coordenadas]
    D --> F[Preencher Dados Cadastrais Restantes]
    E --> F
    F --> G[Upload de Evidências Fotográficas]
    G --> H[Inserir Metadados: Título, Descrição, Severidade, Material Necessário]
    H --> I[Upload de Anexos Extras]
    I --> J{Deseja Reordenar Fotos?}
    J -- Sim --> K[Usar Botões ⬆️ e ⬇️]
    K --> L[Salvar Relatório no BD]
    J -- Não --> L

    L --> M((Operações Posteriores))

    M --> N[Aba: Pesquisar e Exportar]
    M --> O[Aba: Dashboard Analítico]
    M --> U[Aba: Roteirização Tática]

    N --> P[Editar Laudo / Corrigir Coordenadas / Gerenciar Fotos]
    P --> Q[Gerar PDF Corporativo com Material Necessário]

    O --> R[Analisar KPIs de Severidade e Produtividade]
    O --> S[Mapa Tático com Status: Concluída / Em Andamento / Crítica]

    U --> V[Definir Ponto de Partida]
    V --> W[Selecionar Sites Alvo]
    W --> X[Otimização TSP + API ORS]
    X --> Y[Métricas de Rota e Windshield Time]
    Y --> Z[Apontar Materiais por Evidência]
    Z --> AA[Exportar PDF ou Excel do Roteiro]
```

---

## 🔒 Segurança e Conformidade

* Controle de acesso por senha configurável via `st.secrets`.
* Sanitização de todos os inputs com `html.escape` (Anti-XSS).
* Queries SQL 100% parametrizadas (Anti-SQLi).
* Rodapé LGPD em todos os PDFs gerados.
* Dados armazenados localmente — sem envio a servidores externos (exceto API ORS, opcional).