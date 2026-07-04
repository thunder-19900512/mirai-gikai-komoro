#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""みらい議会＠小諸市：議案PDFの新着ウォッチャー。

小諸市議会サイトの「提出議案等一覧」「審議結果等」を浅くクロールし、
定例会・臨時会ごとの PDF（提出議案一覧・審議結果）を収集する。
前回実行時の状態（state/seen_pdfs.json）と比較し、新規/更新された PDF を検出して
downloads/ にダウンロードし、標準出力に JSON で「新着セッション」を返す。

このスクリプトは取得のみ（公開はしない）。後段の draft 生成→draft投入→通知は run.sh が行う。

使い方:
    python3 fetch_sessions.py            # 新着を検出しDLして JSON を出力
    python3 fetch_sessions.py --years 2  # 直近何年分の年別ページを見るか（既定2）

出典（クロール起点）:
  提出議案等一覧: .../komoroshigikai/shigikaiteishutsugiannadoichiran/index.html
  審議結果等:     .../komoroshigikai/shingikekkato/index.html
"""
import json
import os
import re
import sys
import urllib.request
import urllib.parse
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_PATH = os.path.join(HERE, "state", "seen_pdfs.json")
DL_DIR = os.path.join(HERE, "downloads")
BASE = "https://www.city.komoro.lg.jp"

INDEX_PAGES = {
    "gian": f"{BASE}/official/shisei_machizukuri/komoroshigikai/shigikaiteishutsugiannadoichiran/index.html",
    "kekka": f"{BASE}/official/shisei_machizukuri/komoroshigikai/shingikekkato/index.html",
}
UA = "mirai-gikai-komoro-watcher/1.0 (personal; contact thunder.ymd@gmail.com)"


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for k, v in attrs:
                if k == "href" and v:
                    self.links.append(v)


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def absolutize(href: str) -> str:
    if href.startswith("//"):
        return "https:" + href
    if href.startswith("http"):
        return href
    if href.startswith("/"):
        return BASE + href
    return href


def links_on(url: str) -> list[str]:
    try:
        p = LinkParser()
        p.feed(fetch(url))
        return [absolutize(h) for h in p.links]
    except Exception as e:
        print(f"[warn] fetch failed: {url}: {e}", file=sys.stderr)
        return []


def is_council_pdf(url: str) -> bool:
    # 議会事務局のファイル群（group/29）配下の PDF のみ対象
    return url.lower().endswith(".pdf") and "/material/files/group/29/" in url


def crawl_pdfs(years: int) -> dict[str, str]:
    """起点インデックス→年別ページ→（会期ページ）→PDF を浅く収集。
    戻り値: {pdf_url: label(推定)}。ラベルは近傍テキストが取れないので URL 由来。"""
    found: dict[str, str] = {}
    for kind, index_url in INDEX_PAGES.items():
        year_pages = [
            u for u in links_on(index_url)
            if re.search(r"/(shigikaiteishutsugiannadoichiran|shingikekkato)/\d+\.html$", u)
        ]
        # 新しい年から years 個（URL末尾の数値が大きいほど新しい傾向）
        year_pages = sorted(set(year_pages), key=lambda u: int(re.search(r"/(\d+)\.html$", u).group(1)), reverse=True)[:years]
        for yp in year_pages:
            sub = links_on(yp)
            for u in sub:
                if is_council_pdf(u):
                    found[u] = kind
            # 会期ページ（gianR07/16709.html 等）をもう一段だけ辿る
            session_pages = [u for u in sub if re.search(r"/2/\d+/[^/]+/\d+\.html$", u) or re.search(r"gianR\d+/\d+\.html$", u)]
            for sp in set(session_pages):
                for u in links_on(sp):
                    if is_council_pdf(u):
                        found[u] = kind
    return found


def load_state() -> dict:
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"seen": {}}


def save_state(state: dict) -> None:
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def download(url: str) -> str:
    os.makedirs(DL_DIR, exist_ok=True)
    name = os.path.basename(urllib.parse.urlparse(url).path)
    dest = os.path.join(DL_DIR, name)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r, open(dest, "wb") as out:
        out.write(r.read())
    return dest


def main():
    years = 2
    if "--years" in sys.argv:
        years = int(sys.argv[sys.argv.index("--years") + 1])

    state = load_state()
    seen = state.get("seen", {})
    current = crawl_pdfs(years)

    new_pdfs = {u: k for u, k in current.items() if u not in seen}
    downloaded = []
    for u, kind in new_pdfs.items():
        try:
            path = download(u)
            downloaded.append({"url": u, "kind": kind, "path": path})
            seen[u] = {"kind": kind}
            print(f"[new] {kind}: {u}", file=sys.stderr)
        except Exception as e:
            print(f"[warn] download failed {u}: {e}", file=sys.stderr)

    state["seen"] = seen
    save_state(state)

    # 後段が扱いやすいよう、新着PDFを JSON で標準出力へ
    print(json.dumps({"new_count": len(downloaded), "downloaded": downloaded}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
