import sys, os, json, re, glob
sys.stdout.reconfigure(encoding='utf-8')

BASE = r"C:\Users\13083\Desktop\dangshi-quiz"
LET = "ABCD"

qs = json.load(open(os.path.join(BASE, "build", "final_answered.json"), encoding="utf-8"))
print("questions:", len(qs))

# ---- scan anchors in document order ----
ocr_rows = []
for p in sorted(glob.glob(os.path.join(BASE, "build", "ocr", "page-*.json"))):
    page = int(re.search(r"page-(\d+)", p).group(1))
    for it in json.load(open(p, encoding="utf-8")):
        t = re.sub(r"\s+", "", it["t"])
        if t:
            ocr_rows.append({"page": page, "y": it["y0"], "x": it["x0"], "t": t})
ocr_rows.sort(key=lambda r: (r["page"], r["y"]))

MINE = re.compile(r"^我的答案")
SCORE = re.compile(r"^0?(\d{1,3})\s*[\.．]?\d*\s*分$")
ANS = re.compile(r"^[ABCD]{1,4}$")
SCORE_ANY = re.compile(r"(\d{1,3})\s*[\.．]?\d*\s*分")

anchors = []
for i, r in enumerate(ocr_rows):
    if not MINE.match(r["t"]):
        continue
    page, y = r["page"], r["y"]
    tail = MINE.sub("", r["t"]).lstrip("：: 　")
    ans = tail if ANS.match(tail) else ""
    score = None
    for j in range(i + 1, min(i + 6, len(ocr_rows))):
        n = ocr_rows[j]
        if n["page"] != page or n["y"] - y > 220:
            break
        if not ans and ANS.match(n["t"]) and n["x"] < 520:
            ans = n["t"]
        m = SCORE.match(n["t"])
        if m:
            score = float(m.group(1)); break
        m2 = SCORE_ANY.search(n["t"])
        if m2 and len(n["t"]) <= 8:
            score = float(m2.group(1)); break
    anchors.append({"page": page, "y": y, "ans": ans, "score": score})

print("anchors:", len(anchors), " with letter:", sum(1 for a in anchors if a["ans"]),
      " with score:", sum(1 for a in anchors if a["score"] is not None))

if len(anchors) == len(qs):
    print("counts match -> pairing in document order")
    pairs = list(zip(qs, anchors))
else:
    print("count mismatch, pairing by nearest (page,y)")
    pairs = []
    for q in qs:
        if "page" not in q or "y" not in q:
            pairs.append((q, None)); continue
        bd, best = 1e9, None
        for a in anchors:
            d = abs(a["page"] - q["page"]) * 100000 + abs(a["y"] - q["y"])
            if d < bd: bd, best = d, a
        pairs.append((q, best))

# ---- verification ----
checked = agree = disagree = unver = 0
conflicts = []
for q, a in pairs:
    if not a or not a["ans"] or a["score"] is None:
        unver += 1; continue
    if q["type"] == "judge":
        unver += 1; continue          # judge answers are 对/错, not letters
    ours = q.get("answer", "")
    if not ours:
        unver += 1; continue
    checked += 1
    graded_ok = a["score"] > 0
    ours_ok = sorted(a["ans"]) == sorted(ours)
    if ours_ok == graded_ok:
        agree += 1
    else:
        disagree += 1
        conflicts.append({"unit": q["unit_no"], "type": q["type"], "stem": q["stem"][:78],
                          "scan_submitted": a["ans"], "scan_score": a["score"],
                          "our_key": ours, "src": q.get("answer_src"),
                          "page": a["page"]})

print(f"\ncross-checked choice questions: {checked}")
print(f"  agree   : {agree}  ({round(agree/checked*100) if checked else 0}%)")
print(f"  disagree: {disagree}")
print(f"  not verifiable (no letter/score/judge): {unver}")

print("\n=== conflicts ===")
for c in conflicts:
    print(f"  [{c['unit']} {c['type']}] src={c['src']} p{c['page']}")
    print(f"     {c['stem']}")
    print(f"     scan submitted {c['scan_submitted']} -> {c['scan_score']}分 ; our key = {c['our_key']}")

json.dump(conflicts, open(os.path.join(BASE, "build", "answer_conflicts.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\nsaved answer_conflicts.json")
