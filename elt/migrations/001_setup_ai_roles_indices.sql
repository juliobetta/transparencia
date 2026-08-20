-- ==============================================================================
-- TransparenciaWeb Migration: 001_setup_ai_roles_indices.sql
-- Descrição: Ativação de extensões nativas do PostgreSQL e configuração de
--            statement_timeout nas Roles nativas do Supabase (anon, authenticated, service_role).
-- ==============================================================================

-- 1. Habilitar Extensões PostgreSQL Nativas
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 2. Configurar Timeouts Diferenciados nas Roles Nativas do Supabase (Zero Gestão de Senhas)
-- Role 'anon': Usuários anônimos / públicos sem login (Timeout rígido de 3s para proteger CPU)
ALTER ROLE anon SET statement_timeout = '3s';

-- Role 'authenticated': Usuários logados via Supabase Auth (Timeout de 7s)
ALTER ROLE authenticated SET statement_timeout = '7s';

-- Role 'service_role': Backend / Server Admin / Dashboards da Web (Timeout de 15s)
ALTER ROLE service_role SET statement_timeout = '15s';
