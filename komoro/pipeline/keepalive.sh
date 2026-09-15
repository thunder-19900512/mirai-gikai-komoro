#!/bin/zsh
# Supabase Free プランの自動一時停止（7日間アクセスなし）を防ぐため、本番DBに軽いREST問い合わせを1本送る。
# 週次の run.sh は新着PDFが無い週はDBに触らないので、別ジョブとして毎日動かす。
set -eu
DIR="${0:A:h}"
set -a; . "$DIR/.env"; set +a

TS=$(date +%Y%m%d_%H%M%S)
CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 30 \
  "${SUPABASE_URL}/rest/v1/bills?select=id&limit=1" \
  -H "apikey: ${SUPABASE_SECRET_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_SECRET_KEY}") || CODE="000"
echo "[${TS}] keepalive HTTP ${CODE}"
[[ "$CODE" == "200" ]]
