#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""みらい議会＠小諸市：小諸市議会 会議録システム(DiscussVision)から会議録全文を取得する。

会議録システム ssp.kaigiroku.net の内部API（JSONP）を直接叩き、指定会期・開催日の
逐語全文をテキスト化して minutes/ に保存する。モデルを介さないので安価・自動化向き。

API（POST・フォーム）:
  https://ssp.kaigiroku.net/dnp/search/councils/view        … 会期一覧（council_id を得る）
  https://ssp.kaigiroku.net/dnp/search/minutes/get_schedule_all … 開催日一覧（schedule_id）
  https://ssp.kaigiroku.net/dnp/search/minutes/get_minute   … 本文（body=逐語HTML）

小諸の tenant_id=164。

使い方:
  python3 fetch_minutes.py --council 141 --schedules 3,4,5 --prefix R0712
  python3 fetch_minutes.py --list-councils            # 会期と council_id の一覧を表示
"""
import argparse
import html
import json
import os
import re
import sys
import urllib.error
import urllib.request
import urllib.parse

BASE = "https://ssp.kaigiroku.net/dnp/search"
TENANT = 164
HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "minutes")
UA = "mirai-gikai-komoro/1.0 (personal; contact thunder.ymd@gmail.com)"


def _post(path: str, params: dict) -> dict:
    """JSONP エンドポイントを叩き、JSON部を返す。"""
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(
        f"{BASE}/{path}",
        data=data,
        headers={
            "User-Agent": UA,
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://ssp.kaigiroku.net/tenant/komoro/SpMinuteView.html",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read().decode("utf-8", errors="replace")
    # callback(...) で包まれている場合は中身を取り出す
    m = re.search(r"^[^({]*\((.*)\)\s*;?\s*$", raw, re.S)
    if m:
        raw = m.group(1)
    return json.loads(raw)


def list_councils(start: int = 130, end: int = 170):
    """会期一覧を出す。

    注意: `councils/view` は 400 を返す（2026-11-08確認）。代わりに
    `minutes/get_schedule_all` を council_id で走査し、開催日から会期を判別する。
    未公開/存在しない council_id は 403 を返すので、そこで打ち切る。
    """
    found = 0
    for cid in range(start, end + 1):
        try:
            d = _post("minutes/get_schedule_all", {"tenant_id": TENANT, "council_id": cid})
        except urllib.error.HTTPError as e:
            if e.code == 403:
                # 403 が続いたら以降は未公開とみなして終了
                if found:
                    break
                continue
            raise
        sch = d.get("schedules_and_materials") or []
        if not sch:
            continue
        found += 1
        print(f"council_id={cid}  {len(sch)}日  {sch[0]['name']} 〜 {sch[-1]['name']}")
        for x in sch:
            print(f"    schedule_id={x['schedule_id']}  {x['name']}")


def minute_text(council_id: int, schedule_id: int) -> str:
    d = _post("minutes/get_minute", {
        "tenant_id": TENANT, "council_id": council_id,
        "schedule_id": schedule_id, "power_user": "false",
    })
    out = []
    for m in d.get("tenant_minutes", []):
        body = re.sub(r"<[^>]+>", "", m.get("body", ""))
        out.append(html.unescape(body))
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--council", type=int)
    ap.add_argument("--schedules", help="カンマ区切りの schedule_id 群")
    ap.add_argument("--prefix", default="minutes")
    ap.add_argument("--list-councils", action="store_true")
    a = ap.parse_args()

    if a.list_councils:
        list_councils()
        return

    if not (a.council and a.schedules):
        print("--council と --schedules を指定してください（または --list-councils）", file=sys.stderr)
        sys.exit(1)

    os.makedirs(OUT_DIR, exist_ok=True)
    for sid in [int(x) for x in a.schedules.split(",")]:
        txt = minute_text(a.council, sid)
        path = os.path.join(OUT_DIR, f"{a.prefix}_council{a.council}_sid{sid}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(txt)
        print(f"saved {path}: {len(txt)}字")


if __name__ == "__main__":
    main()
