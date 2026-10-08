import sys, os, json, re
sys.stdout.reconfigure(encoding='utf-8')
BASE = r"C:\Users\13083\Desktop\dangshi-quiz"
qs = json.load(open(os.path.join(BASE, "build", "merged.json"), encoding="utf-8"))
LET = "ABCD"

# candidate misreadings: scan the corpus for rare / suspicious character bigrams
alltext = []
for q in qs:
    alltext.append(q["stem"])
    for v in q["options"].values():
        alltext.append(v)
blob = "\n".join(alltext)
print("corpus chars:", len(blob))

# 1) characters that are individually rare in modern Chinese party-history text
from collections import Counter
cnt = Counter(ch for ch in blob if "\u4e00" <= ch <= "\u9fff")
print("distinct hanzi:", len(cnt))

SUSPECT = ["净", "成", "已", "由", "巢", "具", "车", "式", "哇", "挂", "折",
           "障", "效", "空", "培", "旧", "日", "白", "遣", "文", "俊", "具"]
print("\n=== frequency of known-misread chars ===")
for ch in SUSPECT:
    if cnt.get(ch):
        # show contexts
        ctx = []
        for m in re.finditer(re.escape(ch), blob):
            s = max(0, m.start() - 6); e = min(len(blob), m.end() + 6)
            ctx.append(blob[s:e].replace("\n", "|"))
            if len(ctx) >= 3: break
        print(f"  {ch} x{cnt[ch]:4d}  e.g. {ctx}")

# 2) find bigrams containing the classic OCR confusions
CONF = {
    "战净": "战争", "净": None,
    "戊成": "戊戌", "古由": "古田", "古田": "古田",
    "自的": "目的", "保特": "保持", "名种": "各种",
    "遣挫折": "遭挫折", "盲动主文": "盲动主义",
    "井岗山": "井冈山", "宁岗": "宁冈",
}
print("\n=== explicit confusions present ===")
for bad, good in CONF.items():
    n = blob.count(bad)
    if n:
        print(f"  {bad!r} x{n} -> {good!r}")

# 3) count how many questions contain any suspect char
hits = [q for q in qs if any(ch in q["stem"] or any(ch in v for v in q["options"].values()) for ch in "净戌巢具车")]
print("\nquestions containing suspect chars:", len(hits))
