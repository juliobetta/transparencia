# Design Doc: Redesign da Página da Saúde

**Data:** 2026-07-27  
**Status:** Em Revisão

---

## 1. Visão Geral

Este projeto realiza a reformulação e expansão da página de Saúde (`/[portalSlug]/saude`), integrando a narrativa visual consolidada do repositório, novos cartões de acompanhamento orçamentário (do empenho ao pagamento), uma visão detalhada sobre contratações públicas do Fundo Municipal de Saúde (incluindo caronas/adesões a atas) e o detalhamento das emendas parlamentares destinadas à saúde.

---

## 2. Ajustes alinhados com o Usuário

1. **Breadcrumb Padrão**: Utilizar a classe padrão `inline-block font-semibold text-accent text-xs uppercase tracking-wider` em todas as seções/hero.
2. **Navegação Declarativa**: Utilizar o componente `Link` de `next/link` no lugar da tag nativa `<a>` no cabeçalho de licitações.
3. **Componentes KPI**: Reutilizar rigorosamente os componentes `KPICard` e `KPIGrid` da `@transparencia/ui` em todas as seções (Hero, Contratação, Farmacêutica e Emendas).

---

## 3. Ordem Final das Seções

1. **Hero (Novo)**: Narrativa em destaque, card lateral com funil orçamentário (`Empenhado → Liquidado → Pago → Medicamentos`) e 4 KPIs na base.
2. **O que entrou no fundo (Existente)**: Gráfico donut de fontes de receita e repasses.
3. **Empenhado no ano (Existente)**: Gráfico de tendência temporal da execução orçamentária.
4. **Como o Fundo contrata (Novo)**: Alerta descritivo de adesão a ata, 4 KPIs, link para `/[portalSlug]/licitacoes` via `Link` e gráfico/quadro de distribuição de modalidades.
5. **Insumos e assistência farmacêutica (Existente)**: KPIs de medicamentos, judicialização e concentração de mercado (HHI).
6. **Emendas parlamentares destinadas à Saúde (Existente + Detalhado)**: Alerta com status de execução/empenho, 4 KPIs e tabela detalhada por autor e objeto com rodapé de totalização.

---

## 4. Alterações na Camada de Dados (`@transparencia/db`)

### `getHistoriaSaude(year: number, empresaIds?: string[] | string | null)`

A consulta em `packages/db/src/queries/historia_saude.ts` será estendida para retornar:

- **`orcamento`**:
  - `dotacao`: Dotação atualizada.
  - `empenhado`: Valor total empenhado.
  - `liquidado`: Valor total liquidado.
  - `pago`: Valor total pago.
  - `taxaExecucao`: Percentual do empenho vs dotação.
  - `alertaSubExecucao`: Indicador de execução abaixo de 70%.
  - `medicamentosInsumos`: Valor gasto na subfunção 303/farmacêutica.
  - `contratosVinculadosCount`: Quantidade de contratos ativos da saúde.
  - `fornecedoresAtivosCount`: Quantidade de fornecedores únicos com empenhos na saúde.

- **`licitacoesSaude`**:
  - `adesaoCaronaCount`: Número de licitações via carona (adesão).
  - `adesaoCaronaValor`: Valor total contratado via carona.
  - `empenhosAtaExternaCount`: Quantidade de notas de empenho via ata externa.
  - `pagoAtaExternaValor`: Valor pago em empenhos via ata externa.
  - `modalidades`: Lista de modalidades com nome, valor e percentual (`Pregão eletrônico`, `Adesão a ata (carona)`, `Dispensa de licitação`, `Inexigibilidade`, `Tomada de preços / outros`).

- **`emendasStats`**:
  - `totalAutorizado`: Soma dos valores autorizados.
  - `totalEmpenhado`: Soma dos valores empenhados.
  - `taxaEmpenho`: Percentual de empenho (`totalEmpenhado / totalAutorizado`).
  - `maiorEmenda`: Maior valor individual de emenda autorizada.
  - `lista`: Coleção detalhada das emendas (`EmendaSaude[]`).

---

## 5. Alterações na Camada de Apresentação (`@transparencia/ui` & `apps/web`)

1. **`packages/ui`**:
   - `SaudeHeroSection`: Renderização responsiva do hero da saúde.
   - `SaudeContratacaoSection`: Layout de contratações com alerta, KPIs e barras de modalidades.
   - `SaudeEmendasSection`: Layout de emendas com alerta de empenho, KPIs e tabela com linha de total.

2. **`apps/web/app/[portalSlug]/saude/page.tsx`**:
   - Atualizar a integração com os dados retornados de `getHistoriaSaude`.
   - Organizar a renderização das 6 seções sequencialmente.

---

## 6. Plano de Verificação

- **Testes Unitários/Paridade**: Executar `pnpm test` (ou `make test/ts`) em `@transparencia/db` para garantir que o tipo retornado por `getHistoriaSaude` satisfaz os contratos.
- **Validação de Build**: Executar `pnpm build` para assegurar ausência de erros de tipagem TypeScript no Next.js.
