from pathlib import Path

def trocar(caminho, pares):
    p = Path(caminho)
    s = p.read_text(encoding="utf-8")
    for old, new in pares:
        assert s.count(old) == 1, f"{caminho}: trecho nao encontrado (ou repetido): " + old[:70]
        s = s.replace(old, new)
    p.write_text(s, encoding="utf-8")

# cabecalho do codigo
trocar("app_relatorio.py", [
    ("| v3.8.1 (Fixes de Robustez, Concorrência, Testabilidade)", "| v3.9.1 (Refatoração Segura, KPIs com Rótulos Fiéis e Hardening de Login)"),
])

H = "## ✨ O que há de novo na v3.9.0 (Estatísticas, Painel SLA e Roteirização)?"
trocar("README.md", [
    (H, '''## ✨ O que há de novo na v3.9.1 (Refatoração Segura e Segurança)?

Refatoração em fases, cada uma validada contra uma linha de base de testes (nenhuma tela mudou, exceto os rótulos de KPI descritos abaixo):
* **Rede de proteção:** `tests/gircp_testes.py` roda o app inteiro sobre um banco sintético, em pasta temporária (não toca no seu `.db`, nas fotos nem no `secrets.toml`). Modos: `salvar` e `comparar` (cada tela é comparada com a linha de base), `corrompido` (laudo com JSON quebrado não derruba nenhuma tela) e `seguranca` (login, busca, padrões e geocodificação). `aplicar_fase.sh` aplica cada fase com backup e reversão automática se algum teste falhar.
* **Regras únicas:** `_carregar_lista_json`, `_custo_item`, `_tem_critico` e `_PRAZOS_ORD` substituem cálculos repetidos no Dashboard, PDF, orçamento e mapa. Um laudo com JSON corrompido não derruba mais o Dashboard nem a Pesquisa.
* **Dados pessoais fora do código:** os valores padrão do cadastro (contato, telefone, e-mail, técnico, ART/RRT) vêm de `st.secrets["padroes"]`; sem a seção, os campos começam vazios. O técnico herda o contato quando não definido, evitando dois nomes para a mesma pessoa.
* **Login:** falhas de login são registradas na auditoria; o bloqueio (5 falhas em 5 minutos) é por usuário e persiste ao recarregar a página; o primeiro login em banco ainda inexistente não quebra mais a auditoria.
* **Busca e geocodificação:** `%` e `_` na busca são tratados como texto; a geocodificação guarda acertos em cache e respeita 1 consulta por segundo; MD5 trocado por SHA-256 nas chaves de widget; sem `except:` nus.
* **KPIs com rótulos fiéis:** o mapa usa *Com evidências* / *Sem evidências* (o status *Pendente* nunca era atribuído e saiu); *Laudos c/ anomalia crítica*; *Materiais em itens críticos* no orçamento; e a rota informa se distância e tempo vêm do ORS ou de linha reta a 40 km/h.
* **Dashboard modular:** `tela_dashboard` (440 linhas) foi dividida em seis funções por seção (`_dash_resumo`, `_dash_sla`, `_dash_mapa`, `_dash_tendencia`, `_dash_orcamento`, `_dash_auditoria`), sem mudar o que aparece na tela.

```bash
python tests/gircp_testes.py salvar      # antes de refatorar
python tests/gircp_testes.py comparar    # depois de cada mudança
```

---

''' + H),
    ("* Use senhas fortes e únicas, e restrinja o arquivo: `chmod 600 .streamlit/secrets.toml`.",
     "* Use senhas fortes e únicas, e restrinja o arquivo: `chmod 600 .streamlit/secrets.toml`.\n* **Padrões do cadastro (opcional):** uma tabela `[padroes]` com `contato`, `telefone`, `email`, `tecnico` e `art_rrt` preenche os campos iniciais do novo laudo sem deixar dados pessoais no código. Sem a tabela, os campos começam vazios."),
    ("e bloqueio temporário após 5 tentativas incorretas.",
     "e bloqueio temporário (5 falhas em 5 minutos, por usuário, persistente ao recarregar a página)."),
    ("eventos de login, bloqueios,", "eventos de login (inclusive falhas), bloqueios,"),
    ("* O contador de tentativas de login é **por sessão do navegador**: recarregar a página o reinicia. Para exposição além da rede interna, use também limitação de taxa no proxy reverso.",
     "* O bloqueio de login (5 falhas em 5 minutos) é **por usuário e persistente** (usa a auditoria), mas um atacante pode travar um usuário conhecido por 5 minutos. Para exposição além da rede interna, use também limitação de taxa no proxy reverso."),
])
print("OK: cabecalho do codigo e README atualizados (v3.9.1)")
