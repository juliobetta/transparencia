# DIRETRIZES DE DESENVOLVIMENTO: EFICIÊNCIA DE TOKENS E QUALIDADE FISCAL

Este repositório possui limites estritos de consumo de tokens (Spend Cap). Todos os agentes que atuarem neste projeto devem seguir rigorosamente o seguinte protocolo de desenvolvimento econômico, buscando sempre o equilíbrio ideal entre **máxima eficiência de custo** e **máxima qualidade técnica**.

---

## 1. PRINCÍPIO DA ECONOMIA EXTREMA DE CONTEXTO

- **Buscas Cirúrgicas (Grep/Glob First):** Nunca leia arquivos inteiros para procurar termos ou entender a estrutura do código. Sempre use a ferramenta `grep` com termos direcionados ou `glob` com padrões de nomes antes de ler qualquer arquivo com a ferramenta `read`.
- **Leitura Slicing / Janelamento:** Ao ler um arquivo grande com `read`, use os parâmetros `limit` e `offset` para carregar estritamente a parte do código que será inspecionada ou modificada. Nunca leia mais de 100-200 linhas de uma vez se não for estritamente necessário.
- **Histórico Limpo:** Evite conversas longas e redundantes com o usuário. Seja conciso e direto nas respostas. Cada turno acumulado aumenta o custo exponencialmente a cada chamada subsequente da API.

---

## 2. ARQUITETURA BASEADA EM CAMADAS (DRY / CONTEXT CONSERVATION)

- **Foco na Camada de Negócio (`analysis/`):** Toda a inteligência contábil, cálculos da LRF, queries complexas de bancos de dados, cruzamentos e filtros de licitações pertencem exclusivamente à pasta `analysis/`.
- **A Camada de Apresentação é Burra:** Os componentes de visualização (`dashboard/pages/` e `report/`) devem apenas importar DataFrames estruturados e renderizá-los.
- **Eficiência de Desenvolvimento:** Para alterar qualquer lógica ou corrigir anomalias fiscais, **sempre modifique apenas a camada `analysis/`**. Isso poupa a leitura e modificação de dezenas de arquivos Streamlit e templates HTML, economizando até 70% de tokens por modificação.

---

## 3. USO INTELIGENTE DE SUBAGENTES (CONTEXT TRUNCATION)

- **Minimização de histórico acumulado:** Quando enfrentar um problema complexo que exija múltiplos passos, não tente resolver tudo em um único chat de longos turnos.
- **Delegar para Subagentes (`task`):** Despache subagentes curtos e ultra-focados (via ferramenta `task`) com instruções exatas de pesquisa ou edição. Como cada subagente inicia com um contexto limpo e retorna apenas o resultado final para o agente pai, isso trunca o histórico do chat principal e poupa milhares de tokens em chamadas acumuladas subsequentes.

---

## 4. BASELINE DE QUALIDADE MANDATÓRIA

Não comprometa a estabilidade em nome da pressa. Após qualquer alteração:
1. Sempre execute a suíte de testes de integração via `make test`.
2. Sempre rode as validações estáticas e linters via `make check`.

---

## 5. SINCRONIZAÇÃO OBRIGATÓRIA: dbt models ↔ `tests/conftest.py`

**Contexto:** O banco de testes (`testing.postgresql`) é criado via `SQLModel.metadata.create_all()` e expõe as tabelas raw em `public`. A função `_create_test_views()` em `tests/conftest.py` cria views `fct_*` e o schema `raw_porciuncula_prefeitura` que espelham o que os modelos dbt materializam em produção.

**Regra:** Toda vez que um modelo dbt for criado ou modificado de forma que altere colunas expostas nas views de teste, é **obrigatório** atualizar `tests/conftest.py` na mesma PR/commit:

| Alteração dbt | Ação no conftest |
|---|---|
| Nova coluna em staging `stg_*` que aparece em um mart `fct_*` | Adicionar coluna à view correspondente no conftest |
| Coluna renomeada em staging/mart | Renomear o alias na view do conftest |
| Novo mart `fct_*` | Criar nova view `CREATE OR REPLACE VIEW fct_<nome>` na `_create_test_views()` |
| Novo staging que move dado de raw para `exercicio`/`restos_a_pagar` | Atualizar o UNION ALL da `fct_despesas` view |
| Coluna removida de um mart | Remover da view correspondente |

**Verificação:** Após qualquer alteração em `elt/transform/models/`, executar `make test`. Se algum teste falhar com `UndefinedColumn` ou `UndefinedTable`, o `tests/conftest.py` está desatualizado.

---

## 6. FORMATAÇÃO SQL

- **Sem alinhamento por espaços:** Nunca adicione espaços extras para alinhar colunas, aliases (`AS`) ou qualquer outro elemento em queries SQL de analytics (`analysis/`, `elt/`, `tests/`). Use apenas o espaço mínimo necessário para separar tokens.
