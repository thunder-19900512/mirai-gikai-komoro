#!/bin/zsh
# みらい議会＠小諸市：自動更新パイプライン（週次で launchd から実行）。
#
#   1) fetch_sessions.py で小諸市議会サイトの新着PDFを検知・DL
#   2) 新着を会期コード(R0712 等)ごとにまとめ、draft_session.sh で claude が原典PDFから
#      議案データJSONを下書き生成（data/<slug>.json）
#   3) import-session.ts で Supabase に draft（非公開）投入
#   4) notify.py で山田に「要レビュー・公開待ち」メール
#
# 公開は行わない（他者が閲覧する公開物なので、最後の公開判断は必ず人間）。
#
# 環境変数: komoro/pipeline/.env（本番Supabaseの URL/SECRET_KEY）を読む。無ければ repo .env。
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
LOG_DIR="$HERE/logs"; mkdir -p "$LOG_DIR"
TS="$(date +%Y%m%d_%H%M%S)"
TSX="$REPO/packages/seed/node_modules/.bin/tsx"
# 通知メールは google ライブラリ入りの CLT python で送る（Homebrew の python3 には入っていない）
PY_NOTIFY="/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9"; [[ -x "$PY_NOTIFY" ]] || PY_NOTIFY=python3
ADMIN_URL="${ADMIN_URL:-http://localhost:3001}"

# --- env 読み込み（pipeline/.env 優先、無ければ repo/.env） ---
if [[ -f "$HERE/.env" ]]; then set -a; . "$HERE/.env"; set +a
elif [[ -f "$REPO/.env" ]]; then set -a; . "$REPO/.env"; set +a; fi

if [[ -z "${SUPABASE_URL:-}" || -z "${SUPABASE_SECRET_KEY:-}" ]]; then
  echo "❌ SUPABASE_URL / SUPABASE_SECRET_KEY 未設定。pipeline/.env を用意してください。" >&2
  exit 1
fi

echo "▶ [$TS] pipeline start" >&2

# 1) 新着検知
FETCH_JSON="$(python3 "$HERE/fetch_sessions.py" 2>>"$LOG_DIR/fetch.log")"
NEW_COUNT="$(echo "$FETCH_JSON" | python3 -c 'import sys,json; print(json.load(sys.stdin)["new_count"])')"
echo "  新着PDF: $NEW_COUNT" >&2

if [[ "$NEW_COUNT" -eq 0 ]]; then
  echo "  新着なし。終了。" >&2
  exit 0
fi

# 新着PDFの会期コード（R\d{4}）を一意に
CODES=(${(f)"$(echo "$FETCH_JSON" | python3 -c '
import sys, json, re
d = json.load(sys.stdin)
codes = set()
for it in d["downloaded"]:
    m = re.search(r"/(R\d{4})", it["path"])
    if m: codes.add(m.group(1))
print("\n".join(sorted(codes)))
')"})

echo "  対象会期: ${CODES[*]}" >&2

SUMMARY_ITEMS=""  # notify 用 JSON 断片を貯める

for CODE in "${CODES[@]}"; do
  echo "── 会期 $CODE の下書き生成 ──" >&2
  BEFORE="$(ls "$REPO/komoro/data"/*.json 2>/dev/null | sort)"
  "$HERE/draft_session.sh" "$CODE" >>"$LOG_DIR/draft_${CODE}_${TS}.log" 2>&1 || {
    echo "  ⚠ $CODE の下書き生成に失敗（ログ: draft_${CODE}_${TS}.log）" >&2; continue; }
  AFTER="$(ls "$REPO/komoro/data"/*.json 2>/dev/null | sort)"
  NEWJSON="$(comm -13 <(echo "$BEFORE") <(echo "$AFTER") | head -1)"
  # 既存slugを上書き生成したケースも拾う: 直近1分で更新された json
  if [[ -z "$NEWJSON" ]]; then
    NEWJSON="$(ls -t "$REPO/komoro/data"/*.json 2>/dev/null | head -1)"
  fi
  [[ -z "$NEWJSON" ]] && { echo "  ⚠ $CODE: 生成JSONが見つからない" >&2; continue; }

  echo "  投入: $NEWJSON" >&2
  IMPORT_OUT="$("$TSX" "$REPO/komoro/import-session.ts" "$NEWJSON" 2>&1)"
  echo "$IMPORT_OUT" >&2

  # サマリ抽出（import の ✅ 行）
  RESULTS="$(echo "$IMPORT_OUT" | grep '✅' | sed 's/^[[:space:]]*✅[[:space:]]*//')"
  ITEM="$(SLUG="$(basename "$NEWJSON" .json)" RES="$RESULTS" python3 -c '
import os, json
res = [l for l in os.environ.get("RES","").splitlines() if l.strip()]
print(json.dumps({"slug": os.environ["SLUG"], "name": os.environ["SLUG"], "bill_count": len(res), "results": res}, ensure_ascii=False))
')"
  SUMMARY_ITEMS+="$ITEM"$'\n'
done

# 4) 通知
echo "$SUMMARY_ITEMS" | python3 -c '
import sys, json, os
items = [json.loads(l) for l in sys.stdin if l.strip()]
print(json.dumps({"sessions": items, "admin_url": os.environ.get("ADMIN_URL","http://localhost:3001"), "error": None}, ensure_ascii=False))
' ADMIN_URL="$ADMIN_URL" | "$PY_NOTIFY" "$HERE/notify.py" 2>>"$LOG_DIR/notify.log"

echo "✔ [$TS] pipeline done" >&2
