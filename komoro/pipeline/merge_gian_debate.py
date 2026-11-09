#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""会議録から生成した議案の質疑・討論要約を、議案データJSONに差し込む。

merge_answers.py の議案版。キーは議員名ではなく「議案第◯号」。
「## 🌐 議論の記録を見る」の直前に挿入し、normal/hard 両方に同じ節を入れる
（本家の作法＝難易度で節構成は変えない）。

使い方:
  python3 merge_gian_debate.py <target.json> <debate1.json> [...] [--skip 議案第104号,...]

--skip は「すでに手で厚く書いた議案」を上書きしないための除外リスト。
"""
import json
import re
import sys


def norm_num(s: str) -> str:
    """議案第１０４号 / 議案第104号 の表記ゆれを吸収"""
    z = "０１２３４５６７８９"
    for i, c in enumerate(z):
        s = s.replace(c, str(i))
    return s.replace(" ", "").replace("　", "").strip()


def main():
    args = sys.argv[1:]
    skip = set()
    if "--skip" in args:
        i = args.index("--skip")
        skip = {norm_num(x) for x in args[i + 1].split(",") if x.strip()}
        args = args[:i] + args[i + 2:]
    target, srcs = args[0], args[1:]
    if not srcs:
        print("差し込む要約JSONを1つ以上指定してください", file=sys.stderr)
        sys.exit(1)

    deb = {}
    for f in srcs:
        try:
            for k, v in json.load(open(f, encoding="utf-8")).items():
                deb[norm_num(k)] = v.strip()
        except FileNotFoundError:
            print(f"  (skip) {f} が無い", file=sys.stderr)

    d = json.load(open(target, encoding="utf-8"))
    anchor = "## 🌐 議論の記録を見る"
    merged, skipped = 0, []

    for b in d.get("bills", []):
        if b.get("kind") == "一般質問":
            continue
        num = norm_num(b.get("bill_number", ""))
        if num in skip:
            print(f"  (skip) {b['bill_number']} は手書きを保持")
            continue
        sec = deb.get(num)
        if not sec:
            skipped.append(b.get("bill_number"))
            continue
        for lv in ("normal", "hard"):
            c = b[lv]["content"]
            # 既存の同種の節があれば差し替える
            c = re.sub(r"## 🏛️ 市の説明と議会での質疑（要点）.*?(?=## 🌐 議論の記録を見る)", "", c, flags=re.S)
            i = c.find(anchor)
            block = sec.strip() + "\n\n"
            b[lv]["content"] = (c[:i] + block + c[i:]) if i >= 0 else (c.rstrip() + "\n\n" + sec.strip())
        merged += 1

    json.dump(d, open(target, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"✅ {merged}件に質疑・討論を差し込み（対象外={len(skipped)}件）")


if __name__ == "__main__":
    main()
