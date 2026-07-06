#!/bin/zsh
# みらい議会＠小諸市：会議録から一般質問への「市側の答弁」を要約生成する（Stage B）。
#
# 前提: 会議録テキスト（komoro/pipeline/minutes/<prefix>_sid<N>.txt）が用意済み。
#   （fetch_minutes.py で get_minute API から取得・テキスト化しておく）
#
# 使い方:
#   ./resolve_answers.sh <minutes.txt> "議員名1,議員名2,..." <out.json>
# 例:
#   ./resolve_answers.sh minutes/R0712_council141_sid4.txt "丸山正昭,小林哲子,土屋さつき,高橋公,中村美奈子,竹内健一" /tmp/ans_sid4.json
#
# claude(ヘッドレス)が会議録を読み、議員ごとの答弁要約JSONを Write する。
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"

MIN="${1:?minutes.txt required}"
GIIN="${2:?comma-separated giin names required}"
OUT="${3:?out.json required}"

PROMPT="$(cat "$HERE/answer_prompt.md")

---

## この会期・この日の作業

対象議員（この順で処理）: ${GIIN}
会議録テキスト（Readツールで読む）: ${REPO}/${MIN}
出力先: ${OUT} に、議員名→答弁要約Markdown の JSON を Writeツールで作成。

開始してください。"

cd "$REPO"
claude -p "$PROMPT" --allowed-tools "Read" "Write" --permission-mode acceptEdits 2>&1
echo "✅ resolve_answers: $OUT を確認" >&2
