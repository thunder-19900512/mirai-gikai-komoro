#!/bin/zsh
# みらい議会＠小諸市：議案のテーマタグ付けを claude(ヘッドレス) に点検させる。
#
# 使い方:
#   ./tag_audit.sh <分類結果JSON> <出力JSON>
#   例: ./tag_audit.sh state/tags_reiwa8-09-teireikai.json state/tagaudit_reiwa8-09-teireikai.json
#
# 入力は classify_gian_tags.py --apply が出すJSON（[{name, tags}, ...]）。
# 出力は {missed, wrong, missing_extra, new_tag_candidates, uncertain} のJSON。
# タグの付け替えはしない（報告のみ。直すかどうかは人間が決める）。
set -euo pipefail

IN="${1:?分類結果JSONのパスが必要}"
OUT="${2:?出力JSONのパスが必要}"
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"

[[ -f "$IN" ]] || { echo "❌ 入力が見つかりません: $IN" >&2; exit 1; }

PROMPT="$(cat "$HERE/tag_audit_prompt.md")

---

## この回の作業指示

入力（Readツールで読む）: ${IN}
出力（Writeツールで書く）: ${OUT}

点検を開始してください。"

cd "$REPO"
# 無人実行ではログインのOAuthが切れるため長寿命トークンを注入する（draft_session.sh と同じ方式）
HEADLESS_TOKEN_FILE="$HOME/.claude/.headless_token"
if [[ -f "$HEADLESS_TOKEN_FILE" ]]; then
  export CLAUDE_CODE_OAUTH_TOKEN="$(tr -d '[:space:]' < "$HEADLESS_TOKEN_FILE")"
fi
claude -p "$PROMPT" \
  --allowedTools "Read" "Write" \
  --permission-mode acceptEdits \
  2>&1

[[ -f "$OUT" ]] && echo "✅ tag_audit.sh: 点検結果 $OUT" >&2 || echo "⚠ tag_audit.sh: 出力が作られませんでした" >&2
