import sys, os, json, re
from difflib import SequenceMatcher
sys.stdout.reconfigure(encoding='utf-8')

BASE = r"C:\Users\13083\Desktop\dangshi-quiz"

def norm(s):
    return re.sub(r"[\s，。、；：（）()【】\[\]“”\"'？！,.;:!?]", "", s or "")

qs = json.load(open(os.path.join(BASE, "build", "final_answered.json"), encoding="utf-8"))
v8 = json.load(open(os.path.join(BASE, "build", "parsed_v8.json"), encoding="utf-8"))

idx = {}
for q in v8:
    idx.setdefault(norm(q["stem"])[:70], []).append(q)

matched = 0
for q in qs:
    if "page" in q:
        continue
    k = norm(q["stem"])[:70]
    cand = idx.get(k)
    if not cand:
        # fuzzy fallback
        best, bs = None, 0.0
        for kk, lst in idx.items():
            r = SequenceMatcher(None, k, kk).ratio()
            if r > bs:
                bs, best = r, lst
        if best and bs >= 0.90:
            cand = best
    if cand:
        q["page"] = cand[0]["page"]
        q["y"] = cand[0]["y"]
        matched += 1

withpage = sum(1 for q in qs if "page" in q)
print(f"coords restored: {matched}   now with page/y: {withpage}/{len(qs)}")
json.dump(qs, open(os.path.join(BASE, "build", "final_answered.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("saved")
