# Transparencia

[![CI](https://github.com/juliobetta/transparencia/actions/workflows/ci.yml/badge.svg)](https://github.com/juliobetta/transparencia/actions/workflows/ci.yml)

Transparencia é uma ferramenta abrangente para coletar, transformar e visualizar dados de transparência pública municipal. Ela agiliza o processo desde a extração dos dados brutos dos portais públicos até a modelagem analítica (dbt) e a exploração em um dashboard web interativo.

## Funcionalidades

- **Pipeline de Extração e Carga (ELT):** Extração e carga automatizadas de dados brutos de portais de transparência pública, por portal (ex: `porciuncula_prefeitura`).
- **Transformação Analítica (dbt):** Modelagem em camadas (staging → marts) sobre PostgreSQL, com testes de dados e documentação geradas via dbt.
- **Análise de Dados:** Módulos para posição fiscal, execução orçamentária, lacunas em licitações, anomalias contratuais, concentração de fornecedores, folha vs. serviços, fontes de receita, CAPREM, saúde e tendências ano a ano.
- **Dashboard Web:** Aplicação Next.js interativa para explorar os dados dos marts dbt, com componentes e queries compartilhados entre pacotes do monorepo.

## Arquitetura

Monorepo com pipeline Python (ELT + dbt) e frontend TypeScript (Next.js):

- `elt/` — extração, carga e transformação (dbt) dos dados públicos; projeto Python gerenciado com `uv`.
- `apps/web/` — dashboard Next.js (App Router).
- `packages/db/` — camada de queries Kysely sobre os marts dbt (schema `public`), consumida pelo `apps/web`.
- `packages/ui/` — componentes de visualização compartilhados.

## Pré-requisitos

- [uv](https://github.com/astral-sh/uv): gerenciador e instalador de pacotes Python (Python 3.13).
- [pnpm](https://pnpm.io/): gerenciador de pacotes do monorepo TypeScript (Node conforme `.nvmrc`).
- [Docker](https://www.docker.com/): para subir o PostgreSQL local usado pelo ELT/dbt e pelo dashboard.

## Configuração

1. Clone o repositório.
2. Suba o PostgreSQL local:

```bash
docker compose up -d postgres
```

3. Instale as dependências:

```bash
make install   # dependências Python (elt/)
pnpm install   # dependências do monorepo TypeScript
```

4. Copie `.env.example` para `.env` e ajuste `DATABASE_URL`/`PORTAL_SLUG` conforme necessário.

## Uso

O projeto utiliza um `Makefile` para gerenciar as tarefas do ELT/dbt e scripts `pnpm`/`turbo` para o monorepo TypeScript.

### Pipeline ELT (extração e carga)

```bash
make elt/extract PORTAL=porciuncula_prefeitura [YEARS="2024 2025"] [ONLY=DespesasGerais]
make elt/load PORTAL=porciuncula_prefeitura [DIR=data/raw_runs/20250101_120000]
```

### Transformação (dbt)

```bash
make dbt/deps    # instala pacotes dbt
make dbt/seed    # carrega seeds
make dbt/run     # roda os models [SELECT=...]
make dbt/test    # roda os testes de dados [SELECT=...]
make dbt/docs    # gera e serve a documentação dbt
```

### Dashboard Web (Next.js + TypeScript)

Para iniciar o servidor de desenvolvimento do portal web:

```bash
pnpm dev
# ou
make dev
```

Para compilar e testar os pacotes do monorepo:

```bash
pnpm build
pnpm test
```

## Desenvolvimento

- **Executar testes Python (ELT/dbt):** `make test`
- **Lint e formatar código Python:** `make check`
- **Executar testes TS (Kysely, web):** `make test/ts` (ou `pnpm test`)

## Licença

Este projeto é distribuído sob a [GNU Affero General Public License v3.0](LICENSE). Uso, modificação e distribuição (incluindo como serviço web) são permitidos, desde que a atribuição seja mantida e, no caso de versões modificadas rodando como serviço, o código-fonte correspondente seja disponibilizado.
