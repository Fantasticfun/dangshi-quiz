import sys, os, json, re
sys.stdout.reconfigure(encoding='utf-8')

BASE = r"C:\Users\13083\Desktop\dangshi-quiz"
src = open(os.path.join(BASE, "questions.js"), encoding="utf-8").read()
data = json.loads(re.search(r"window\.QUIZ_DATA\s*=\s*(\{.*\});\s*$", src, re.S).group(1))
LET = "ABCD"
qs = data["questions"]
units = data["units"]

kept, dropped = [], []
for q in qs:
    if q["t"] == "judge":
        kept.append(q); continue
    o = q.get("o") or []
    a = q.get("a") or ""
    ok = (len(o) == 4 and all(str(x).strip() for x in o)
          and (not a or all(str(o[LET.index(c)]).strip() for c in a)))
    if ok:
        kept.append(q)
    else:
        dropped.append(q)

print(f"kept {len(kept)}  dropped {len(dropped)}")
for q in dropped:
    print("   dropped:", q["u"], q["t"], "|", q["q"][:60])

# drop units that lost all their questions
used = {q["u"] for q in kept}
units = [u for u in units if u["no"] in used]

data = {"units": units, "questions": kept}
for target in (os.path.join(BASE, "site", "questions.js"), os.path.join(BASE, "questions.js")):
    with open(target, "w", encoding="utf-8") as f:
        f.write("// 党史题库 — 由 PDF 题库经 OCR 提取整理\n")
        f.write("window.QUIZ_DATA = ")
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")

from collections import Counter
print("FINAL questions:", len(kept), "units:", len(units))
print("types:", Counter(q["t"] for q in kept))
print("with answers:", sum(1 for q in kept if q.get("a")))
print("option lens:", Counter(len(q.get("o", [])) for q in kept if q["t"] != "judge"))
print("chapters:", Counter(u["chapter"] for u in units))
