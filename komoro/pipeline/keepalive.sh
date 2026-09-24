#!/bin/zsh
# Supabase Free プランの自動一時停止（7日間アクセスなし）を防ぐ。
# 週次の run.sh は新着PDFが無い週はDBに触らないので、別ジョブとして1日数回動かす。
#   - 読み（bills を1件）と書き（ops_keepalive を update）の両方を送る
#   - 失敗したらメールで知らせる（run.sh と同じ notify_mail を使う）
set -uo pipefail
DIR="${0:A:h}"
set -a; . "$DIR/.env"; set +a

TS=$(date +%Y%m%d_%H%M%S)
AUTH=(-H "apikey: ${SUPABASE_SECRET_KEY}" -H "Authorization: Bearer ${SUPABASE_SECRET_KEY}")

READ=$(curl -s -o /dev/null -w "%{http_code}" --max-time 30 \
  "${SUPABASE_URL}/rest/v1/bills?select=id&limit=1" "${AUTH[@]}") || READ="000"

WRITE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 30 -X PATCH \
  "${SUPABASE_URL}/rest/v1/ops_keepalive?id=eq.1" "${AUTH[@]}" \
  -H "Content-Type: application/json" -H "Prefer: return=minimal" \
  -d "{\"pinged_at\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}") || WRITE="000"

echo "[${TS}] keepalive read=${READ} write=${WRITE}"

# 2xx 以外が出たら1回だけ再試行し、それでもダメならメール
if [[ "$READ" != 2* || "$WRITE" != 2* ]]; then
  sleep 20
  READ2=$(curl -s -o /dev/null -w "%{http_code}" --max-time 30 \
    "${SUPABASE_URL}/rest/v1/bills?select=id&limit=1" "${AUTH[@]}") || READ2="000"
  echo "[${TS}] retry read=${READ2}"
  if [[ "$READ2" != 2* ]]; then
    PY="/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9"
    [[ -x "$PY" ]] || PY=python3
    SUBJECT="【みらい議会＠小諸市】Supabaseに繋がりません（read=${READ}/${READ2} write=${WRITE}）"
    "$PY" - "$SUBJECT" <<'PY' || echo "[${TS}] メール送信もできませんでした"
import sys, os
sys.path.insert(0, os.path.expanduser("~/.gemini/antigravity/scratch/06_基盤/automation"))
from notify_mail import send_mail
send_mail(sys.argv[1], "<p>keepalive が本番Supabaseに接続できませんでした。"
          "一時停止されている場合は Supabase ダッシュボードから Restore してください。</p>"
          "<p>https://supabase.com/dashboard/project/uefyokvrlhmprltozgnh</p>")
PY
    exit 1
  fi
fi
