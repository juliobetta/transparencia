# DIRETRIZES DE DESENVOLVIMENTO: EFICIÊNCIA DE TOKENS E QUALIDADE FISCAL

Este repositório possui limites estritos de consumo de tokens (Spend Cap). Todos os agentes que atuarem neste projeto devem seguir rigorosamente o seguinte protocolo de desenvolvimento econômico, buscando sempre o equilíbrio ideal entre **máxima eficiência de custo** e **máxima qualidade técnica**.

---

## 1. PRINCÍPIO DA ECONOMIA EXTREMA DE CONTEXTO

- **Buscas Cirúrgicas (Grep/Glob First):** Nunca leia arquivos inteiros para procurar termos ou entender a estrutura do código. Sempre use a ferramenta `grep` com termos direcionados ou `glob` com padrões de nomes antes de ler qualquer arquivo com a ferramenta `read`.
- **Leitura Slicing / Janelamento:** Ao ler um arquivo grande com `read`, use os parâmetros `limit` e `offset` para carregar estritamente a parte do código que será inspecionada ou modificada. Nunca leia mais de 100-200 linhas de uma vez se não for estritamente necessário.
- **Histórico Limpo:** Evite conversas longas e redundantes com o usuário. Seja conciso e direto nas respostas. Cada turno acumulado aumenta o custo exponencialmente a cada chamada subsequente da API.

---

## 2. ARQUITETURA BASEADA EM CAMADAS (DRY / CONTEXT CONSERVATION)

- **Camada de Dados / Queries (`packages/db`):** Toda a inteligência contábil, cálculos da LRF, queries Kysely e cruzamentos pertencem exclusivamente a `@transparencia/db/src/queries/`.
- **A Camada de Apresentação é Burra:** Os componentes de visualização (`packages/ui` e `apps/web/app/`) devem apenas importar os dados tipados do `@transparencia/db` e renderizá-los.
- **Eficiência de Desenvolvimento:** Para alterar qualquer lógica ou corrigir anomalias fiscais nas telas web, modifique apenas a camada `@transparencia/db`. Isso evita a alteração desnecessária de componentes de página.

---

## 3. USO INTELIGENTE DE SUBAGENTES (CONTEXT TRUNCATION)

- **Minimização de histórico acumulado:** Quando enfrentar um problema complexo que exija múltiplos passos, não tente resolver tudo em um único chat de longos turnos.
- **Delegar para Subagentes (`task`):** Despache subagentes curtos e ultra-focados (via ferramenta `task`) com instruções exatas de pesquisa ou edição. Como cada subagente inicia com um contexto limpo e retorna apenas o resultado final para o agente pai, isso trunca o histórico do chat principal e poupa milhares de tokens em chamadas acumuladas subsequentes.

---

## 4. BASELINE DE QUALIDADE MANDATÓRIA

Não comprometa a estabilidade em nome da pressa. Após qualquer alteração:
1. **Backend & Modelos DBT (Python):** Sempre execute a suíte de testes de integração via `make test` e as validações estáticas/linters via `make check`.
2. **Frontend & queries Kysely (TypeScript):** Sempre execute a suíte de testes de paridade via `make test/ts` (ou `pnpm test`) e verifique a tipagem executando `pnpm build` ou `tsc --noEmit` nos pacotes correspondentes.

---

## 5. SINCRONIZAÇÃO DE FONTES: dbt models ↔ `elt/conftest.py`

**Contexto:** O banco de testes utiliza uma instância efêmera do PostgreSQL (`testing.postgresql`). A função `_create_raw_schema(eng)` em [conftest.py](file:///Volumes/Projects/transparencia/elt/conftest.py) cria o schema `raw_porciuncula_prefeitura` e as tabelas raw lendo dinamicamente as definições do arquivo de metadados [_sources.yml](file:///Volumes/Projects/transparencia/elt/transform/models/staging/porciuncula_prefeitura/_sources.yml). Durante a inicialização dos testes, as views e tabelas de staging/marts são compiladas e criadas dinamicamente no banco de testes executando as etapas do dbt (`deps`, `seed` e `run --vars '{"test_mode": true}'`).

**Regra:** Toda vez que houver alteração nas tabelas raw de entrada (como novas tabelas ou novas colunas), é **obrigatório** atualizar o arquivo de fontes [_sources.yml](file:///Volumes/Projects/transparencia/elt/transform/models/staging/porciuncula_prefeitura/_sources.yml) correspondente. Não há necessidade de atualizar views ou criar tabelas manualmente no arquivo Python `conftest.py`, pois o pipeline do dbt é executado automaticamente durante o setup de testes para construir toda a estrutura derivada.

**Verificação:** Após qualquer alteração em `elt/transform/models/` ou no schema das tabelas raw, execute `make test`. Se algum teste falhar por falta de colunas ou tabelas raw, certifique-se de que elas foram devidamente declaradas em `_sources.yml`.

---

## 6. FORMATAÇÃO SQL

- **Sem alinhamento por espaços:** Nunca adicione espaços extras para alinhar colunas, aliases (`AS`) ou qualquer outro elemento em queries SQL de analytics (`analysis/`, `elt/`, `tests/`). Use apenas o espaço mínimo necessário para separar tokens.

---

## 7. GERENCIAMENTO DE DEPENDÊNCIAS (PINNED VERSIONS)

- **Versões Exatas (Pinned Versions):** Sempre instale e declare versões exatas de pacotes e dependências (npm/pnpm/pip) nos arquivos de manifesto (`package.json`, `pyproject.toml`, etc.), **sem** prefixos de variação como `^` ou `~` (ex: `"nuqs": "2.9.1"`). Ao rodar instalações via CLI, utilize flags de versão exata (ex: `pnpm add --save-exact <pacote>`).

