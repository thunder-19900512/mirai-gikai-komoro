#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""みらい議会＠小諸市：resolve_answers.sh が作った答弁要約JSONを、一般質問データJSONに差し込む。

各一般質問の normal / hard コンテンツの「## 🌐 議論の記録を見る」の直前に
「## 🏛️ 市の答弁（要点）」節を挿入する（やさしく／くわしく共通）。

使い方:
  python3 merge_answers.py <target_ippan.json> <answers1.json> [<answers2.json> ...]
"""
import json
import re
import sys


def norm(name: str) -> str:
    """議員名の表記ゆれ吸収（高/髙、空白除去）。"""
    return name.replace("髙", "高").replace(" ", "").replace("　", "").strip()


def main():
    target = sys.argv[1]
    ans_files = sys.argv[2:]
    if not ans_files:
        print("答弁JSONを1つ以上指定してください", file=sys.stderr)
        sys.exit(1)

    answers = {}
    for f in ans_files:
        for k, v in json.load(open(f, encoding="utf-8")).items():
            answers[norm(k)] = v.strip()

    d = json.load(open(target, encoding="utf-8"))
    # slug_suffix から議員名を取り出す（name: 〔一般質問〕◯◯ 議員：…）
    def giin_of(bill):
        m = re.search(r"〔一般質問〕(.+?)\s*議員", bill.get("name", ""))
        return norm(m.group(1)) if m else None

    def insert(content: str, section: str) -> str:
        anchor = "## 🌐 議論の記録を見る"
        idx = content.find(anchor)
        block = section.strip() + "\n\n"
        if idx == -1:
            return content.rstrip() + "\n\n" + section.strip()
        return content[:idx] + block + content[idx:]

    merged = 0
    missing = []
    for b in d["bills"]:
        if b.get("kind") != "一般質問":
            continue
        g = giin_of(b)
        sec = answers.get(g) if g else None
        if not sec:
            missing.append(b.get("name"))
            continue
        # 既に答弁節があれば置換、無ければ挿入
        for level in ("normal", "hard"):
            c = b[level]["content"]
            c = re.sub(r"## 🏛️ 市の答弁（要点）.*?(?=## 🌐 議論の記録を見る)", "", c, flags=re.S)
            b[level]["content"] = insert(c, sec)
        merged += 1

    json.dump(d, open(target, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"✅ {merged}件に答弁を差し込み。未マッチ: {missing or 'なし'}")


if __name__ == "__main__":
    main()
