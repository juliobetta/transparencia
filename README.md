# Transparencia

Transparencia é uma ferramenta abrangente para coletar, analisar e visualizar dados de transparência pública. Ela agiliza o processo desde a ingestão dos dados até a geração de relatórios e a exploração em um dashboard interativo.

## Funcionalidades

- **Pipeline de Ingestão de Dados:** Coleta e processamento automatizado de conjuntos de dados de transparência pública.
- **Análise de Dados:** Módulos para identificar lacunas em licitações, análise de execução orçamentária, anomalias em contratos, concentração de fornecedores e tendências ano a ano.
- **Relatórios:** Geração automatizada de relatórios em HTML, incluindo relatórios específicos de saúde e comparações.
- **Dashboard:** Um dashboard web interativo para explorar dados processados e insights.

## Pré-requisitos

- [uv](https://github.com/astral-sh/uv): Um gerenciador e instalador de pacotes Python rápido.

## Configuração

1. Clone o repositório.
2. Instale as dependências:

```bash
make install
```

## Uso

O projeto utiliza um `Makefile` para gerenciar tarefas:

### Pipeline de Dados
Para executar o pipeline completo de ingestão de dados:

```bash
make pipeline
```

### Dashboard
Para iniciar o dashboard interativo:

```bash
make dashboard
```

### Relatórios
Para gerar relatórios:

```bash
# Relatórios gerais
make report

# Relatórios específicos (ex: Saúde, Comparação)
make report/saude YEAR=2025
make report/compare YEAR_A=2024 MONTH_A_START=1 MONTH_A_END=12 YEAR_B=2025 MONTH_B_START=1 MONTH_B_END=12
```

## Desenvolvimento

- **Executar testes:** `make test`
- **Lint e formatar código:** `make check`
- **Corrigir problemas de linting:** `make lint/fix`
- **Formatar código:** `make format`
