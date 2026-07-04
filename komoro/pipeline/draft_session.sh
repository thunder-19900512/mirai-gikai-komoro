#!/bin/zsh
# みらい議会＠小諸市：指定セッションのPDFから議案データJSONを claude(ヘッドレス) で下書き生成する。
#
# 使い方:
#   ./draft_session.sh R0712            # downloads/ の R0712*.pdf を原典に data/<slug>.json を生成
#   ./draft_session.sh R0712 "令和7年12月定例会"   # 会期名ヒントを渡す（任意）
#
# 前提: claude CLI がPATHにあること。読む/書くツールのみ許可して headless 実行する。
# 出力: komoro/data/<slug>.json（claude が Write ツールで作成）。公開はしない（後段で draft 投入）。
set -euo pipefail

CODE="${1:?session code required, e.g. R0712}"
HINT="${2:-}"
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
DL="$HERE/downloads"

# 対象PDFを収集（提出議案・審議結果の両方）
PDFS=(${(f)"$(ls "$DL"/${CODE}*.pdf 2>/dev/null || true)"})
if [[ ${#PDFS[@]} -eq 0 ]]; then
  echo "❌ downloads/ に ${CODE}*.pdf が見つかりません。先に fetch_sessions.py を実行してください。" >&2
  exit 1
fi

echo "📄 原典PDF (${#PDFS[@]}件):" >&2
for p in "${PDFS[@]}"; do echo "   - $p" >&2; done

PDF_LIST=""
for p in "${PDFS[@]}"; do PDF_LIST+=$'\n- '"$p"; done

PROMPT="$(cat "$HERE/draft_prompt.md")

---

## この会期の作業指示

会期コード: ${CODE}${HINT:+（ヒント: $HINT）}

原典PDF（Readツールで必ず全て読むこと）:${PDF_LIST}

実例フォーマット（構造を合わせる）: ${REPO}/komoro/data/reiwa7-09.json
出力先: ${REPO}/komoro/data/ 配下に <slug>.json をWriteツールで作成。

作業を開始してください。"

cd "$REPO"
# Read/Write のみ許可（ネット送信やコマンド実行はさせない）。権限確認をスキップして headless 実行。
claude -p "$PROMPT" \
  --allowedTools "Read" "Write" \
  --permission-mode acceptEdits \
  2>&1

echo "✅ draft_session.sh: ${CODE} の下書き生成コマンドが完了しました（data/ を確認）。" >&2
