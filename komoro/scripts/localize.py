#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""みらい議会＠小諸市：本家由来コードの「国会→市議会」系文言を機械的にローカライズする。

本家(team-mirai/mirai-gikai)を merge した後に走らせると、新しく入ってきたコードの
「法案／国会／衆議院／参議院」等を小諸市議会版の表記に置換する。冪等（何度流しても安全）。
※ブランディング（サービス名・色・ロゴ・免責・プロンプト本文の書き換え等）は
  機械変換ではなく個別編集なので、このスクリプトの対象外（git merge がそのまま保持）。

使い方:
    python3 komoro/scripts/localize.py           # 置換を適用
    python3 komoro/scripts/localize.py --check    # 置換せず、要ローカライズ箇所を一覧（CI/追従チェック用）

対象: web/src, packages/*/src, packages/seed, admin/src の .ts/.tsx（node_modules除く）
"""
import os
import re
import subprocess
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# 置換ルール（順序が重要：特定パターンを先に）。
# タプル (old, new)。old を除去する向きなので基本的に冪等。
RULES = [
    ("衆議院で審議中", "小諸市議会で審議中"),
    ("参議院で審議中", "小諸市議会で審議中"),
    ("両院で可決、成立", "本会議で可決、成立"),
    ("衆議院本会議で否決", "本会議で否決"),
    ("衆議院本会議", "本会議"),
    ("参議院本会議", "本会議"),
    ("衆議院で否決", "本会議で否決"),
    ("参議院で否決", "本会議で否決"),
    ("衆議院提出", "小諸市議会提出"),
    ("衆議院の議案ページURL", "小諸市議会の議案ページURL"),
    ("衆議院URL", "議案ページURL"),
    ("衆議院ページ", "議案ページ"),
    ('HR: "衆議院"', 'HR: "小諸市議会"'),
    ('HC: "参議院"', 'HC: "小諸市議会"'),
    ("衆議院", "小諸市議会"),
    ("参議院", "小諸市議会"),
    ("国会審議中", "市議会審議中"),
    ("国会会期", "議会会期"),
    ("国会に提出", "市議会に提出"),
    ("国会", "市議会"),
    ("法案", "議案"),
    ("議案成立", "可決"),
    ("議案提出前", "提出前"),
]

# 意図的に残している「国会」表記（本家＝国会版への言及など）。
# これらを含む行では「国会」系の置換をスキップする。
PROTECTED_LINE_SUBSTRINGS = [
    "国会版",          # 本家「みらい議会」（国会版）
    "国会から小諸市議会",  # shared-sections: 対象を国会から小諸市議会に置き換え
]

# 置換後に「まだローカライズされていない」と見なす検出語（--check用）。
# 意図的に残す語（shugiin.go.jp のURL等はローマ字なので誤検知しない）。
STRAY_PATTERN = re.compile(r"法案|国会|衆議院|参議院")


def target_files():
    dirs = ["web/src", "packages", "admin/src"]
    out = []
    for d in dirs:
        base = os.path.join(REPO, d)
        for root, _, files in os.walk(base):
            if "node_modules" in root:
                continue
            for f in files:
                if f.endswith((".ts", ".tsx")):
                    out.append(os.path.join(root, f))
    return out


def localize_text(text: str) -> str:
    out_lines = []
    for line in text.split("\n"):
        protected = any(p in line for p in PROTECTED_LINE_SUBSTRINGS)
        for old, new in RULES:
            if protected and ("国会" in old):
                continue  # 意図的に残す国会言及の行では国会系置換をしない
            line = line.replace(old, new)
        out_lines.append(line)
    return "\n".join(out_lines)


def run_apply():
    changed = 0
    for path in target_files():
        with open(path, encoding="utf-8") as f:
            s = f.read()
        t = localize_text(s)
        if t != s:
            with open(path, "w", encoding="utf-8") as f:
                f.write(t)
            changed += 1
            print(f"  localized: {os.path.relpath(path, REPO)}")
    print(f"\n✅ {changed} ファイルをローカライズしました（0なら既に適用済み＝冪等）。")


def run_check():
    hits = 0
    for path in target_files():
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
        for i, line in enumerate(lines, 1):
            if any(p in line for p in PROTECTED_LINE_SUBSTRINGS):
                continue
            if STRAY_PATTERN.search(line):
                # コメント内の英語URL等の誤検知を避けたいが、まずは素朴に報告
                print(f"  {os.path.relpath(path, REPO)}:{i}: {line.strip()[:90]}")
                hits += 1
    if hits == 0:
        print("✅ 要ローカライズ箇所なし（本家追従クリーン）。")
    else:
        print(f"\n⚠ {hits}件。localize.py（--checkなし）で機械置換→残りは手当。")
    return hits


if __name__ == "__main__":
    if "--check" in sys.argv:
        sys.exit(1 if run_check() else 0)
    run_apply()
