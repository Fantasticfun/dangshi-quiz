import sys, os, json, re
sys.stdout.reconfigure(encoding='utf-8')
BASE = r"C:\Users\13083\Desktop\dangshi-quiz"
SRC = os.path.join(BASE, "build", "questions_final4.json")
SITE = os.path.join(BASE, "site")
qs = json.load(open(SRC, encoding="utf-8"))

CHAPTERS = {
    1: "第一编 中国共产党的创建和投身大革命的洪流",
    2: "第二编 掀起土地革命的风暴",
    3: "第三编 全民族抗日战争的中流砥柱",
    4: "第四编 夺取新民主主义革命的全国性胜利",
    5: "第五编 中华人民共和国的成立和社会主义制度的建立",
    6: "第六编 改革开放和社会主义现代化建设新时期",
    7: "第七编 中国特色社会主义进入新时代",
}

out = []
for q in qs:
    rec = {"u": q["unit_no"], "t": q["type"], "q": q["stem"].strip()}
    if q["type"] != "judge":
        o = q["options"]
        rec["o"] = [str(o.get(k, "")).strip() for k in "ABCD"]
    if q.get("answer"):
        rec["a"] = q["answer"]
    out.append(rec)

units = {}
for q in qs:
    units.setdefault(q["unit_no"], q["unit_title"])
unit_list = [{"no": u, "title": units[u], "chapter": int(u.split(".")[0])}
             for u in sorted(units, key=lambda x: (int(x.split(".")[0]), int(x.split(".")[1])))]

data = {"units": unit_list, "questions": out}
for target in (os.path.join(SITE, "questions.js"), os.path.join(BASE, "questions.js")):
    with open(target, "w", encoding="utf-8") as f:
        f.write("// 党史题库 — 由 PDF 题库经 OCR 提取整理\n")
        f.write("window.QUIZ_DATA = ")
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")
    print("wrote", target, os.path.getsize(target) // 1024, "KB")

print("units:", len(unit_list), "questions:", len(out))
print("with answers:", sum(1 for r in out if r.get("a")))
from collections import Counter
print("types:", Counter(r["t"] for r in out))
print("option lens:", Counter(len(r.get("o", [])) for r in out if r["t"] != "judge"))

