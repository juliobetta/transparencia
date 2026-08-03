-- fase 2.5: renomear public (raw tables legadas) → raw_porciuncula_prefeitura
-- executar manualmente antes de `make dbt/run`
-- pré-requisito: encerrar conexões ativas no schema public

alter schema public rename to raw_porciuncula_prefeitura;

create schema if not exists public;
grant all on schema public to postgres;
grant all on schema public to public;
