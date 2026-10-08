import sys, os, json, re
sys.stdout.reconfigure(encoding='utf-8')

BASE = r"C:\Users\13083\Desktop\dangshi-quiz"
LET = "ABCD"

qs = json.load(open(os.path.join(BASE, "build", "final_answered.json"), encoding="utf-8"))

# ---- 1. repair the mis-typed question (was classified judge, actually a single-choice) ----
fixed_typo = 0
for q in qs:
    if q["stem"].startswith("单选题】党的十三大指出"):
        q["stem"] = "党的十三大指出，（）是建设有中国特色的社会主义的首要问题，是我们制定和执行正确的路线和政策的根本依据"
        q["options"] = {
            "A": "正确认识我国社会现在所处的历史阶段",
            "B": "正确认识我国社会的主要矛盾",
            "C": "正确理解我国的社会主义制度",
            "D": "正确把握我国社会主义建设的主线",
        }
        q["type"] = "single"
        q["answer"] = "A"
        q["answer_src"] = "kb"
        fixed_typo += 1
    # the badly garbled judge item: drop it rather than show a broken stem
DROP_PREFIX = "年5月，毛泽东根据多年"
before = len(qs)
qs = [q for q in qs if not q["stem"].startswith(DROP_PREFIX)]
dropped = before - len(qs)
print("retyped:", fixed_typo, " dropped garbled:", dropped)

json.dump(qs, open(os.path.join(BASE, "build", "final_answered.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# ---- rebuild payload ----
def clean(s):
    s = re.sub(r"\s+", "", s or "")
    s = re.sub(r"^[（(【\[]?\s*共\s*\d+\s*题\s*[)）】\]]?", "", s)
    return s.strip(" 　。，、；：")

seen, final = set(), []
def key(s):
    return re.sub(r"[\s，。、；：（）()【】\[\]“”\"'？！,.;:!?]", "", s or "")[:64]

for q in qs:
    stem = clean(q["stem"])
    if len(stem) < 10:
        continue
    k = key(stem)
    if k in seen:
        continue
    typ = q["type"]
    rec = {"u": q["unit_no"], "t": typ, "q": stem}
    if typ != "judge":
        o = q["options"]
        if len(o) != 4 or any(not str(o.get(x, "")).strip() for x in LET):
            continue
        rec["o"] = [clean(o[x]) for x in LET]
        if any(not v for v in rec["o"]):
            continue
    a = q.get("answer", "")
    if a:
        if typ == "judge":
            if a in ("T", "F"):
                rec["a"] = a
        else:
            a = "".join(sorted(set(c for c in a if c in LET)))
            if a and all(LET.index(c) < 4 for c in a):
                rec["a"] = a
        if rec.get("a") and q.get("answer_src") == "kb":
            rec["ak"] = "kb"
    seen.add(k)
    final.append(rec)

units = {}
for q in qs:
    units.setdefault(q["unit_no"], q["unit_title"])
present = {r["u"] for r in final}
unit_list = [{"no": no, "title": units[no], "chapter": int(no.split(".")[0])}
             for no in sorted(units, key=lambda x: (int(x.split(".")[0]), int(x.split(".")[1])))
             if no in present]

from collections import Counter
ans = sum(1 for r in final if r.get("a"))
print(f"FINAL: {len(final)} questions, {len(unit_list)} units, {ans} with answer ({round(ans/len(final)*100)}%)")
print("types:", Counter(r["t"] for r in final))
print("chapters:", len({u['chapter'] for u in unit_list}))

data = {"units": unit_list, "questions": final}
for path in (os.path.join(BASE, "questions.js"), os.path.join(BASE, "site", "questions.js")):
    with open(path, "w", encoding="utf-8") as f:
        f.write("// 党史题库 — 由 PDF 题库经 OCR 提取整理；单选题与判断题答案依据党史知识补录\n")
        f.write("window.QUIZ_DATA = ")
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")
print("questions.js rebuilt")
