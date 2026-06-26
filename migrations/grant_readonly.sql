GRANT SELECT ON ALL TABLES IN SCHEMA public TO read_only;

DO $$
DECLARE
  r record;
BEGIN
  FOR r IN SELECT tablename FROM pg_tables WHERE schemaname = 'public'
  LOOP
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY;', r.tablename);
    EXECUTE format('DROP POLICY IF EXISTS read_only_select ON %I;', r.tablename);
    EXECUTE format('CREATE POLICY read_only_select ON %I FOR SELECT TO read_only USING (true);', r.tablename);
  END LOOP;
END
$$;
