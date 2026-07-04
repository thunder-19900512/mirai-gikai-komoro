#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""みらい議会＠小諸市：ドラフト投入完了メールを山田宛に送る小物。

scratch/automation/notify_mail.py（receipt-bot認証を流用する共通ヘルパー）を再利用する。
標準入力から JSON（run.sh が渡すサマリ）を受け取り、HTMLメールを送る。

JSON 形式:
  {"sessions": [{"slug": "...", "name": "...", "bill_count": 5, "results": ["議案67号 認定", ...]}],
   "admin_url": "http://localhost:3001", "error": null}
"""
import json
import os
import sys

# scratch の共通メールヘルパーを import できるようにパスを通す
SCRATCH_AUTOMATION = os.path.expanduser("~/.gemini/antigravity/scratch/automation")
sys.path.insert(0, SCRATCH_AUTOMATION)


def main():
    payload = json.load(sys.stdin)
    try:
        from notify_mail import send_mail, a  # type: ignore
    except Exception as e:
        print(f"[warn] notify_mail を読み込めませんでした（メール送信スキップ）: {e}", file=sys.stderr)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    admin_url = payload.get("admin_url", "http://localhost:3001")
    sessions = payload.get("sessions", [])
    err = payload.get("error")

    if err:
        subject = "【みらい議会＠小諸市】自動更新でエラー"
        html = f"<p>議案ドラフトの自動生成でエラーが発生しました。</p><pre>{err}</pre>"
        send_mail(subject, html)
        return

    if not sessions:
        # 新着なし → メールは送らない（静かに終わる。voiceswatch と同じ思想）
        print("[info] 新着セッションなし。メールは送信しません。", file=sys.stderr)
        return

    total = sum(s.get("bill_count", 0) for s in sessions)
    subject = f"【みらい議会＠小諸市】新しい議案ドラフト {total}件（要レビュー・公開待ち）"

    parts = [
        "<p>小諸市議会サイトの更新を検知し、議案の下書き（draft）を自動投入しました。<br>",
        "<b>まだ公開されていません。</b>admin で内容を原典と照合し、問題なければ公開ボタンを押してください。</p>",
    ]
    for s in sessions:
        parts.append(f"<h3>{s.get('name', s['slug'])}（{s.get('bill_count', 0)}件）</h3><ul>")
        for r in s.get("results", []):
            parts.append(f"<li>{r}</li>")
        parts.append("</ul>")
    parts.append(
        "<hr><p>👉 レビュー＆公開: "
        + a(admin_url, "admin を開く")
        + "</p><p style='color:#888;font-size:12px'>※ 金額・改正内容・否決理由など、原典（議案書・会議録）が必要な項目は下書き段階では未確認のまま「原典を確認」と明記されています。公開前に必ず確認してください。</p>"
    )
    send_mail(subject, "".join(parts))
    print(f"[info] 通知メール送信: {total}件", file=sys.stderr)


if __name__ == "__main__":
    main()
