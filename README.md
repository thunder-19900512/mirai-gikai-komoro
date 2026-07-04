# みらい議会＠小諸市

> **これは、政党チームみらいが公開しているオープンソース「みらい議会」の非公式フォークです。**
> 対象を国会から**小諸市議会**に置き換え、小諸市在住の山田雄司が個人として運営しています。
> 政党チームみらいが運営しているものではありません。
>
> - 本家（国会版）: https://gikai.team-mir.ai/
> - 本家リポジトリ: https://github.com/team-mirai/mirai-gikai
> - ライセンス: [AGPL-3.0](./LICENSE)（フォーク条件は [FORK_GUIDELINES.md](./FORK_GUIDELINES.md) 参照）

## 本家からの主な変更点（AGPL-3.0 §5(a) に基づく変更明示）

2026-07-05 山田雄司によりフォーク。以下を変更:

- **対象を国会 → 小諸市議会に変更**（会期＝定例会/臨時会、議案＝条例・予算・請願陳情等）。二院制前提のUI（衆議院/参議院）を単院（小諸市議会）に読み替え
- サービス名を「みらい議会＠小諸市」に変更
- ロゴ・OGP・ヒーロー画像・PWAアイコン・favicon を独自のものに差し替え
- primary カラーを `#2aa693`（緑）→ `#2b6cb0`（青）に変更
- フッター等に免責文言を追加、運営者情報・本家リンクを掲載
- 政党（チームみらい）固有の記述・寄附導線・党スタンス表示を、中立な運営者情報に置き換え（**公選法配慮のため、議案の事実整理・解説に徹し、投票呼びかけや候補者支持を行わない**）
- AIチャット/インタビューのシステムプロンプトを小諸市議会向けに調整
- ローカル開発時のテーブル権限不足を補う migration を追加（`20260705000000_restore_default_table_grants.sql`）

詳細な運用・自動化設計は [`docs/KOMORO_OPERATIONS.md`](./docs/KOMORO_OPERATIONS.md) を参照。

---

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/team-mirai-volunteer/mirai-gikai)
[![codecov](https://codecov.io/gh/team-mirai/mirai-gikai/branch/develop/graph/badge.svg)](https://codecov.io/gh/team-mirai/mirai-gikai)

## セットアップ

```bash
# Supabaseの起動
npx supabase start

# 環境変数の設定（必要に応じて.envの内容を変更してください）
cp .env.example .env

# パッケージインストール
pnpm install

# SupabaseのDB初期化, 開発用シードデータのセットアップ
pnpm db:reset

# サーバー起動
pnpm dev
```

## マイグレーション

```bash
# マイグレーションファイル生成
npx supabase migration new マイグレーション名

# マイグレーション実行 & 型ファイル更新
pnpm db:migrate
```

## Adminユーザーの作成

1. Supabase Studio上で Authentication > Add User からユーザーを作成
2. Supabase Studio上で以下のSQLを実行

```sql
UPDATE auth.users
SET raw_app_meta_data = raw_app_meta_data || '{"roles": ["admin"]}'::jsonb
WHERE email = '<1で作成したユーザーのemail>';
```

> [!NOTE]
> 開発環境では、seedデータによって、`email: admin@example.com, password: admin123456` のAdminユーザーが作成されます。

## Fork して独自サービスを運営する場合

本リポジトリを fork して独自にサービスを運営する場合は、[Fork ガイドライン](./FORK_GUIDELINES.md) を確認してください。本家サービスとの混同防止のため、ロゴ・カラー・サービス名称などの変更が必要です。
