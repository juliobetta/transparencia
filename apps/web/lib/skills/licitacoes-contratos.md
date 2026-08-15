# Skill: Licitações, Dispensas e Contratos (Lei 14.133 / Decreto 12.807/2025)

## Tetos de Dispensa de Licitação (Decreto nº 12.807/2025 - em vigor)
1. **Limites Regulamentados de Contratação Direta por Valor**:
   - Obras e Serviços de Engenharia: **R$ 130.984,20**
   - Compras e Demais Serviços: **R$ 65.492,11**
   - Manutenção de Veículos Automotores (incluindo peças): **R$ 10.478,74**
2. **Alerta Jurídico de Fracionamento**:
   - Agrupar por Órgão Executor + Subelemento + Ano Fiscal para identificar potencial fracionamento ilegal.
   - O campo `isento_legalmente` em `fct_licitacoes_gaps_metricas` identifica dispensas respaldadas legalmente ou por consórcios públicos.

## Status de Execução Contratual
- Status em `fct_contratos_servicos_vigentes`: `em_execucao`, `concluido` ou `inexecutado`.
- Contratos vencidos com liquidação zerada (`total_liquidado = 0`) são classificados como `inexecutado`.
