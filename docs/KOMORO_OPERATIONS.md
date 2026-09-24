# みらい議会＠小諸市 運用ガイド

本家「みらい議会」（team-mirai）を小諸市議会版にフォークしたものの、**セットアップ・自動更新・公選法配慮**をまとめたドキュメント。
（本家からの変更点一覧は [`README.md`](../README.md) 冒頭を参照）

---

## 1. 全体像

```
小諸市議会サイト（提出議案一覧PDF・審議結果PDF＝原典）
        │  週1で新着チェック（launchd: com.yamada.mirai-gikai-komoro）
        ▼
 fetch_sessions.py … 新着PDFを検知・DL（komoro/pipeline/downloads）
        ▼
 draft_session.sh … claude(ヘッドレス)が原典PDFを読み、議案データJSONを下書き
        ▼            （komoro/data/<slug>.json）※金額・詳細は「要原典確認」と明記
 import-session.ts … Supabaseに draft（非公開）で投入
        ▼
 notify.py … 山田に「要レビュー・公開待ち」メール（scratch/automation/notify_mail.py 流用）
        ▼
 【人間】admin で原典照合 → 問題なければ公開ボタン ← ここだけ手作業（公選法・正確性のため必須）
        ▼
 公開サイト（Vercel）: 市民が議案をやさしく読める／AIに質問できる
```

- **公開物なので「公開の最終判断は必ず人間」**（scratch の運用ルール「他者が閲覧する自動化は半自動に倒す」に準拠）。
- 会期は年4回（3・6・9・12月）＋臨時会なので、週1チェックで十分。新着が無い週はメールも送らず静かに終了。

## 2. 構成（どこに何があるか）

| 場所 | 役割 |
|---|---|
| `web/` | 公開サイト（Next.js / Vercel） |
| `admin/` | 管理画面（Next.js / Vercel）。議案の編集・**公開/非公開**・タグ |
| `supabase/` | DB（bills / bill_contents / diet_sessions / tags ほか） |
| `komoro/import-session.ts` | 会期JSON → Supabase 投入（全件 draft） |
| `komoro/data/*.json` | 会期ごとの議案データ（原典転記＋解説）。git管理 |
| `komoro/pipeline/` | 自動更新パイプライン一式（下記） |

### pipeline の中身
- `fetch_sessions.py` … 新着PDFウォッチャー。状態は `state/seen_pdfs.json`
- `draft_prompt.md` … claude への下書き指示（公選法・正確性ルール込み）
- `draft_session.sh` … `claude -p` で会期PDF→JSON下書き（Read/Writeツールのみ許可）
- `run.sh` … オーケストレータ（fetch→draft→import→notify）
- `notify.py` … 完了メール（scratch の notify_mail.py 流用）
- `com.yamada.mirai-gikai-komoro.plist` … launchd定義（毎週月7:15）
- `keepalive.sh` ＋ `com.yamada.mirai-gikai-komoro-keepalive.plist` … 本番Supabaseへの生存アクセス。Free プランは7日間アクセスが無いと一時停止されるため（2026-09-14 停止予告メールを受けて追加）。
  - **2026-09-24 強化**: 毎日1回の読み取りだけでは止められず、9/24早朝に一時停止の通知が届いた（ログ上は9/15〜9/24の毎日 HTTP 200、9/23のみ000。通知後の9/24 12:10も200で、その時点では動いていた）。読み取りだけでは「活動」と見なされない可能性があるため、**1日3回（8:10/14:10/20:10）に増やし、`ops_keepalive` テーブルへの update（書き込み）も送る**ようにした。失敗が続くと山田にメールが飛ぶ。
  - ログは `logs/keepalive.log`（`read=200 write=204` が正常）。テーブルは migration `20260924080000_add_ops_keepalive.sql`
  - それでも止まる場合の選択肢: ①Supabaseダッシュボードから Restore（90日以内ならデータそのまま）②サイトを公開して実アクセスを発生させる ③Proプラン（$25/月）

## 3. ローカル開発

```bash
cd ~/mirai-gikai-komoro
npx supabase start          # Docker で Supabase ローカル起動
cp .env.example .env        # 値は `npx supabase status` を見て設定（下記）
pnpm install
pnpm db:reset               # マイグレーション＋デモseed
pnpm dev                    # web:3000 / admin:3001
```

`.env` の要点:
- `SUPABASE_SECRET_KEY` はローカルでは `npx supabase status` の **service_role キー（JWT形式 `eyJ...`）** を使う（`sb_secret_...` 形式だと seed が permission denied になる）
- `AI_GATEWAY_API_KEY` を入れると AIチャット/難易度生成が有効（未設定でも議案表示は動く）
- `CHAT_DAILY_TOTAL_COST_LIMIT_USD` などで AIチャットのコスト上限を必ず設定

実議案を入れる:
```bash
set -a && . ./.env && set +a
./packages/seed/node_modules/.bin/tsx komoro/import-session.ts komoro/data/reiwa7-09.json
```

## 4. 本番デプロイ（山田の手が必要）

1. **Supabase**: クラウドプロジェクト作成 → `supabase link` → `supabase db push`（この規模なら無料枠で十分）
2. **GitHub**: 公開リポジトリを作成して push（AGPL のソース公開義務を自然に満たす）
3. **Vercel**: `web/` と `admin/` を別プロジェクトでデプロイ。環境変数に本番 Supabase キー・`AI_GATEWAY_API_KEY`・`ADMIN_MCP_TOKEN` 等を設定
4. **公開前レビュー期間**: `web` の `BASIC_AUTH_USER/PASSWORD` を設定して Basic認証を掛け、限定公開で内容を詰める
5. `komoro/pipeline/.env` に**本番の** `SUPABASE_URL` / `SUPABASE_SECRET_KEY` / `ADMIN_URL` を書く（自動更新の投入先を本番にする）

### 4.1 進捗（2026-09-06 Claude実施分と残り）

**済み**
- Supabase Cloud: project `uefyokvrlhmprltozgnh`（ap-northeast-1, Free）作成済。URL `https://uefyokvrlhmprltozgnh.supabase.co`
- GitHub: `thunder-19900512/mirai-gikai-komoro`（**まずprivate**。AGPLの公開義務はサイト公開時までに public 化＝人間判断）に `komoro-fork` を push 済。`origin` 登録済
- Vercel: `mirai-gikai-komoro-web`（root `web`）／`mirai-gikai-komoro-admin`（root `admin`）作成・GitHub連携済。Production の環境変数は投入済（Supabase URL/publishable, AI_GATEWAY_API_KEY, REVALIDATE_SECRET, ADMIN_URL, NEXT_PUBLIC_*_URL, コスト上限, webのBASIC_AUTH_USER=komoro＋パスワード, adminのADMIN_MCP_TOKEN）。生成した値の控えは repo ルートの `.env` 末尾 `PROD_*`（gitignore済）

**2026-09-06 夜に完了**
- ✅ DBスキーマ: `supabase link` + `db push` 93本（山田）
- ✅ `SUPABASE_SECRET_KEY` を web/admin の Vercel に登録（Sensitive 扱い＝あとから取り出せないので、必要なら再度ダッシュボードからコピー）
- ✅ 初回デプロイ: web https://mirai-gikai-komoro-web.vercel.app（Basic認証 user=komoro）／admin https://mirai-gikai-komoro-admin.vercel.app
  - ハマり: `web/` 内で `vercel deploy` → 「Root Directory "web" does not exist」→ repo ルートで `vercel link --repo`（モノレポ連結）に切替で解決
  - ハマり: web だけ Framework Preset が None で公開URLがエッジ 404 → API で `framework=nextjs` に設定して再デプロイで解決
  - Basic認証は HTML ナビゲーションだけ掛かる仕様（curl の `*/*` は素通し。ブラウザは 401）
- ✅ 議案データ投入（全件 draft）: 令和7年9月 5件／12月 36件／一般質問 18件 → bills 59・bill_contents 118・tags 13
- ✅ `komoro/pipeline/.env` 本番化（chmod 600）＋ launchd `com.yamada.mirai-gikai-komoro` ロード
- ✅ `draft_session.sh` に長寿命トークン注入（無人実行でOAuth切れしない）
- ✅ 週次パイプライン試運転（2026-09-06）: 新着4PDF検知 → 令和8年6月定例会19件・9月定例会29件を自動下書き→draft投入→レビュー依頼メール到着。直したバグ3つ＝①`run.sh` の `$CODE_$TS`（zshで未定義変数扱い）②`notify.py` の scratch パスが再構成前 ③通知は google ライブラリ入りの CLT python3.9 で送る必要（Homebrew python3 には無い）。※失敗時は `state/seen_pdfs.json` から該当URLを消せば再処理される

**残り（山田）**
1. admin ログイン用 Google OAuth を Supabase Authentication > Providers で有効化（`ADMIN_AUTH_CALLBACK_URL` = `https://mirai-gikai-komoro-admin.vercel.app/api/auth/callback`）。これが無いと admin で公開操作ができない
2. admin で内容レビュー → 公開（人間の判断）
3. サイト公開のタイミングで Basic 認証を外し、GitHub リポジトリを public に（AGPL）

## 5. 自動更新の有効化（デプロイ後）

```bash
cp komoro/pipeline/com.yamada.mirai-gikai-komoro.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.yamada.mirai-gikai-komoro.plist
# 手動で1回試す:
./komoro/pipeline/run.sh
```

- kenkocheck（基盤の健康診断）は `com.yamada.*` を動的スキャンするので、load すれば自動で点検対象に入る。
- **朝ブリーフィング（news-bot）に「みらい議会：公開待ちドラフト◯件」欄を足す**と、公開忘れを防げる（要検討）。

## 6. 公選法・正確性の鉄則

- サイトは**議案の事実整理と分かりやすい解説に徹する**。特定候補・政党への投票呼びかけ、支持/不支持の誘導は書かない。
- 「山田のスタンス表明」機能（mirai_stances）は**当面オフ**（未使用）。
- AI下書きは**確定事実（議案番号・件名・付託委員会・議決結果）＋種別の一般説明**のみ。金額・改正の中身・否決理由など原典が要る事項は「原典を確認」と明記し、創作しない。
- **公開ボタンを押す前に、必ず議案書本文・会議録の原典と照合する**（この一手だけは自動化しない）。
- 本家運用ガイドライン: https://note.com/team_mirai_jp/n/nc59ec347e8c7

## 7. 本家（team-mirai）への追従 — 元祖から離れすぎないための運用

**方針: コードは本家のまま、価値はデータで足す。** 一般質問・請願・テーマ（争点）・両論併記・市民の声の集約は、**新しいコードを書かず**、本家が既に持つ機能（`bills`＝審議対象の器／`tags`＝テーマ／`bill_contents`＝両論併記の解説／AIインタビュー＋トピック分析＝目安箱／`is_featured`＝注目枠）に**データとして盛る**。凝った独自UIは作らない（＝乖離の源だから）。自動化は `komoro/` フォルダに隔離してあるので本家と衝突しない。

### 本家由来の乖離は2種類だけ
1. **ブランディング**（サービス名・色・ロゴ・免責・プロンプト本文の書き換え）＝ 少数ファイルの個別編集。`git merge` がそのまま保持。本家が同じ行を変えた時だけ手で解決。
2. **「国会→市議会」系の機械的な文言置換**＝ 広範囲だが機械的。`komoro/scripts/localize.py` で**冪等に再適用できる**ようにしてある。

### 追従ワークフロー（本家の更新を取り込む時）
```bash
cd ~/mirai-gikai-komoro
git fetch upstream                       # 本家(team-mirai)の最新を取得
git checkout komoro-fork
git merge upstream/main                  # 衝突が出たら手で解決（主にブランディング箇所）
python3 komoro/scripts/localize.py       # 新しく入った「法案/国会/衆参」を市議会表記へ機械変換（冪等）
python3 komoro/scripts/localize.py --check  # 取りこぼしゼロを確認（本家追従クリーン）
pnpm install && pnpm typecheck && pnpm -r test   # 壊れていないか確認
```
- `localize.py` は本家＝国会版への意図的な言及（「（国会版）」等）は保護して置換しない。
- リモート構成: `upstream` = team-mirai/mirai-gikai（追従元）。Phase4で山田の公開リポジトリを作ったら `origin` に登録して push する。

## 8. コンテンツの2段階（重要）

提出議案一覧PDFは「議案名・番号・付託委員会・議決結果」までしか分からない。改正の中身や審議の論点は**会議録が公開されてから**（数週間〜数か月後）でないと書けない。したがって:

- **Stage A（議案提出時）**: 件名・種別・（判明していれば）結果 → 基本の下書き
- **Stage B（会議録公開後）**: 審議の論点・賛否・理由を加筆 → 内容を充実

`run.sh` は毎週走るので、会議録PDFが新たに出れば `fetch_sessions.py` が拾い、同じ会期を再ドラフト（upsert）して Stage B に更新できる。
