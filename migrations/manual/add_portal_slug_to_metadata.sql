-- Adiciona portal_slug à tabela metadata e atualiza a primary key
-- para suporte multi-portal (opção B: slug gravado na origem pelo ELT)

ALTER TABLE raw_porciuncula_prefeitura.metadata ADD COLUMN IF NOT EXISTS portal_slug text;

UPDATE raw_porciuncula_prefeitura.metadata SET portal_slug = 'porciuncula_prefeitura' WHERE portal_slug IS NULL;

ALTER TABLE raw_porciuncula_prefeitura.metadata ALTER COLUMN portal_slug SET NOT NULL;

ALTER TABLE raw_porciuncula_prefeitura.metadata DROP CONSTRAINT metadata_pkey;

ALTER TABLE raw_porciuncula_prefeitura.metadata ADD PRIMARY KEY (portal_slug, key);
