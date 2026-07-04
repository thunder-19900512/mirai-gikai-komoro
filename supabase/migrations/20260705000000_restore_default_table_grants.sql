-- 小諸市版フォークで追加。
-- 新しめの Supabase CLI ではテーブルへの DML 権限がデフォルト付与されず、
-- 本家の想定（デフォルト権限＋RLSで行レベル制御）と食い違い seed や API が
-- permission denied になるため、従来のデフォルト権限を明示的に付与する。
-- 行レベルの安全性は従来どおり各テーブルの RLS ポリシーが担う。

GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public
  TO anon, authenticated, service_role;

GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public
  TO anon, authenticated, service_role;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES
  TO anon, authenticated, service_role;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES
  TO anon, authenticated, service_role;
