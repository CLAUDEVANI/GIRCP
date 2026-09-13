# ⚡ GIRCP - Gerador Inteligente de Relatórios e Controle Fotográfico

Aplicação web de missão crítica desenvolvida em Python com Streamlit para criação, edição, gerenciamento analítico e exportação de relatórios fotográficos técnicos (laudos corporativos) em PDF, seguindo padrões de excelência corporativa.

---

## ✨ O que há de novo na v3.7.2 (Blindagem SecOps)?

A versão 3.7.2 introduz uma blindagem robusta de infraestrutura de missão crítica (SecOps), focada em defesa em profundidade, mitigação de vazamentos e proteção do Sistema Operacional:
* **Varredura Assíncrona (ClamAV):** Imagens enviadas passam por uma varredura silenciosa em background via `subprocess` e `threading`. Arquivos políglotas ou maliciosos são deletados do servidor imediatamente.
* **Autenticação Fail-Closed & Anti-Bruteforce:** O sistema bloqueia acessos de forma global caso a credencial de segurança no arquivo `st.secrets` seja removida. Implementação de trava temporária após 5 tentativas de login incorretas.
* **Prevenção de Information Disclosure:** Erros de parser (falhas ao ler planilhas ou KMLs) não "vazam" mais *Stack Traces* na interface do usuário. As falhas são registradas silenciosamente no log de auditoria interno.
* **Proteção Anti-DoS e Trava de SO:** Limite de tamanho de upload (`maxUploadSize`) ativado no Streamlit para barrar bombas de descompressão, além do travamento da pasta de imagens com restrições (`chmod 755` e `644`) impedindo a execução de qualquer script no diretório.

---

## ✨ Histórico — v3.6.0

A versão 3.6.0 transforma o campo de material livre em um painel estruturado de itens por evidência, permitindo controle completo de quantidade, unidade e custo unitário para geração de orçamentos precisos.

### 🔧 Materiais por Evidência — Estrutura de Orçamento
O campo "Material Necessário" foi reformulado de texto livre para um painel de itens por linha, disponível no cadastro de novos laudos e na edição de laudos existentes:
* **4 colunas por item:** Descrição | Unidade (un / m / kg / kit / cx / hr) | Quantidade | Custo Unitário R$.
* Botão **＋ Adicionar material** para múltiplos itens por evidência e botão ❌ para remover[cite: 4].
* **Subtotal por evidência** calculado em tempo real quando o custo é informado[cite: 4].
* **Retrocompatível:** laudos antigos com material em texto puro são migrados automaticamente para a nova estrutura ao abrir para edição[cite: 4].
* O campo `material_necessario` legado é mantido como string concatenada para não quebrar exportações existentes[cite: 4].

### 💰 Painel de Orçamento no Dashboard
Nova seção "Painel de Orçamento — Materiais Necessários" ao final do Dashboard Analítico[cite: 4]:
* **4 KPIs:** Total Estimado (R$) / Itens Críticos / Materiais Distintos / Itens sem Custo Informado[cite: 4].
* **Tabela consolidada** com todos os materiais de todos os laudos filtrados, exibindo site, evidência, severidade, material, unidade, quantidade, custo unitário e total por linha[cite: 4].
* **Filtro por severidade** (Todas / Critico / Observacao / Normal)[cite: 4].
* **Exportação Excel** do orçamento completo com um clique[cite: 4].
* Alerta automático quando há itens sem custo unitário preenchido, indicando que o total estimado pode estar incompleto[cite: 4].

### 📄 PDF do Laudo — Tabela de Materiais
O bloco de material no PDF do laudo foi atualizado de texto simples para mini-tabela por evidência[cite: 4]:
* Colunas: Material | Un. | Qtd. | Unit. R$ | Total R$[cite: 4].
* Subtotal por evidência em destaque vermelho[cite: 4].
* Evidências sem material continuam sem o bloco, sem poluir o documento[cite: 4].

---

## ✨ Histórico — v3.5.0

A versão 3.5.0 expandiu o módulo de Roteirização Tática com exportação completa de roteiros, rastreamento de materiais por evidência e inteligência de status no mapa tático do Dashboard[cite: 4].

### 📤 Exportação de Roteiro (PDF e Excel)
Após otimizar a rota, um novo painel de exportação é gerado automaticamente abaixo do mapa[cite: 4]:
* **PDF do Roteiro:** Documento A4 corporativo com KPIs operacionais (sites atendidos, quilometragem, windshield time, densidade), resumo de severidades, tabela de sequenciamento com coordenadas e seção de evidências com thumbs fotográficos e materiais apontados por site[cite: 4].
* **Planilha Excel (.xlsx):** Três abas estruturadas — *KPIs da Operação*, *Sequenciamento* e *Evidências e Materiais* — com formatação condicional por severidade (verde/amarelo/vermelho)[cite: 4].
* **Persistência de estado:** Os arquivos gerados ficam disponíveis para download mesmo após interações subsequentes na interface, via `session_state`[cite: 4].

### 🔧 Campo "Material Necessário" nas Evidências
Novo campo adicionado ao formulário de cada foto, tanto no cadastro de novos laudos quanto na edição de laudos existentes[cite: 4]:
* Aparece logo abaixo do campo **Descrição** em cada evidência[cite: 4].
* Salvo no banco de dados junto com os demais metadados da foto[cite: 4].
* Exibido no **PDF do laudo** com destaque visual (borda vermelha) quando preenchido[cite: 4].
* Exibido na **planilha e PDF do roteiro** na coluna "Material Necessário" por site[cite: 4].
* Preservado corretamente ao reordenar (⬆️⬇️) ou excluir evidências[cite: 4].

### 🗺️ Mapa Tático com Status de Visitas
O mapa do Dashboard foi reformulado para exibir o andamento operacional de cada site[cite: 4]:
* 🟢 **Concluída** — relatório com evidências fotográficas cadastradas[cite: 4].
* 🟠 **Em Andamento** — relatório cadastrado mas sem fotos ainda[cite: 4].
* 🔴 **Anomalia Crítica** — visita concluída com evidência de severidade Crítica detectada[cite: 4].
* **Seletor de filtro** (radio horizontal) para exibir apenas um status no mapa[cite: 4].
* **3 contadores** acima do mapa: Concluídas / Em Andamento / Com Anomalia Crítica[cite: 4].
* **Tooltip enriquecido** com ícone de status, alerta de anomalia, técnico, data e endereço[cite: 4].
* **Legenda lateral** explicando cada cor diretamente na interface[cite: 4].

---

## ✨ Histórico — v3.4.1

A versão 3.4.1 trouxe inteligência logística e renderização antibloqueio[cite: 4]:
* **Módulo de Roteirização (Field Service):** Algoritmo do Vizinho Mais Próximo (TSP local) integrado à API do OpenRouteService (ORS) para sequenciamento de atendimento, trajeto rua a rua e métricas de *Windshield Time*, Quilometragem e Densidade da Rota[cite: 4].
* **Cartografia Avançada (PyDeck):** Substituição do motor gráfico nativo. Renderização em RGB condicional e tooltips interativos, com numeração da ordem de visitação dos sites[cite: 4].
* **Segurança e Sanitização (Anti-XSS e SQLi):** Blindagem contra injeção de scripts e queries SQL parametrizadas[cite: 4].
* **Geolocalização Flexível:** Importação de `.KML` e `.XLSX` com filtros em cascata, mais inserção manual de coordenadas[cite: 4].
* **Compressão On-the-Fly:** Otimização de imagens no upload via PIL/Pillow[cite: 4].
* **Reordenação Dinâmica:** Reordenação de evidências fotográficas antes de salvar ou durante edição[cite: 4].
* **Geração Autonumérica:** Número sequencial automático de relatório (`GIRCP-YYYY-XXXX`) e controle de revisão[cite: 4].

---

## 🛠️ Funcionalidades Principais

* **Cadastro de Laudos:** Formulário completo para identificação da infraestrutura, dados do cliente, metadados da vistoria e coordenadas GPS[cite: 4].
* **Evidências com Metadados Completos:** Upload múltiplo com título, descrição, severidade, categoria e **material necessário para correção** por foto[cite: 4].
* **Banco de Dados Local Otimizado:** SQLite com `PRAGMA journal_mode=WAL`, metadados em JSON e imagens comprimidas em disco[cite: 4].
* **Motor de Edição:** Pesquisa, expansão de card, edição de textos e coordenadas, reordenação e adição de novas fotos inline[cite: 4].
* **PDF Corporativo:** WeasyPrint renderizando HTML/CSS com marca d'água, logotipo, badges de severidade, campo de material necessário, assinatura digital e rodapé LGPD[cite: 4].
* **Dashboard Analítico:** KPIs gerais, gráfico de produtividade por site, distribuição de severidade, mapa tático com status de visitas, linha do tempo de vistorias e **painel de orçamento** consolidado com exportação Excel[cite: 4].
* **Controle de Orçamento:** Materiais estruturados por evidência (descrição, unidade, quantidade, custo unitário), subtotal por foto, total consolidado por laudo e visão gerencial no Dashboard[cite: 4].
* **Roteirização Tática:** Otimização TSP + ORS, mapa de rota, métricas de field service, painel de evidências/materiais por site e exportação em PDF e Excel[cite: 4].

---

## 💻 Tecnologias Utilizadas

| Biblioteca | Papel |
|---|---|
| **Streamlit** | Interface web e gerenciamento de estado (`session_state`)[cite: 4] |
| **PyDeck** | Mapas táticos geoespaciais com camadas e tooltips[cite: 4] |
| **Plotly** | Gráficos analíticos (barras, pizza, linha do tempo)[cite: 4] |
| **SQLite3** | Banco de dados relacional embutido (WAL mode)[cite: 4] |
| **WeasyPrint** | Renderização HTML/CSS para PDF A4 corporativo[cite: 4] |
| **Pandas** | Manipulação e análise de DataFrames[cite: 4] |
| **OpenPyXL** | Geração de planilhas Excel com formatação condicional[cite: 4] |
| **Requests** | Integração com API OpenRouteService (ORS)[cite: 4] |
| **Pillow (PIL)** | Compressão e redimensionamento de imagens[cite: 4] |
| **xml.etree** | Extração de coordenadas de arquivos KML[cite: 4] |
| **ClamAV & OS Mods** | Varredura assíncrona antimalware (`subprocess`, `threading`)[cite: 10] |
| **Auxiliares** | `base64`, `json`, `os`, `datetime`, `hashlib`, `math`[cite: 4] |

---

## ⚙️ Instalação e Execução

**1. Clone o repositório**
```bash
git clone [https://github.com/CLAUDEVANI/GIRCP.git](https://github.com/CLAUDEVANI/GIRCP.git)
cd GIRCP

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
    O --> T[Painel de Orçamento — Materiais Consolidados]
    T --> AB[Exportar Orçamento Excel]

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