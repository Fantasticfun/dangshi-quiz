import sys, os, json, re, glob
sys.stdout.reconfigure(encoding='utf-8')

BASE = r"C:\Users\13083\Desktop\dangshi-quiz"
LET = "ABCD"

qs = json.load(open(os.path.join(BASE, "build", "merged_fixed.json"), encoding="utf-8"))
units = {}
for q in qs:
    units.setdefault(q["unit_no"], q["unit_title"])
print("questions:", len(qs), " units:", len(units))

# ---------- collect subagent answers ----------
answers = {}
files = sorted(glob.glob(os.path.join(BASE, "build", "answers2", "out-*.json")))
print("answer files found:", len(files))
for f in files:
    try:
        raw = open(f, encoding="utf-8").read().strip()
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.S)
        arr = json.loads(raw)
    except Exception as e:
        print(f"  !! {os.path.basename(f)} parse failed: {e}")
        continue
    n = 0
    for item in arr:
        try:
            gid = int(item["id"]); ans = str(item["answer"]).strip().upper()
        except Exception:
            continue
        if gid in answers:
            continue
        answers[gid] = ans
        n += 1
    print(f"  {os.path.basename(f)}: +{n}")

print("total answers collected:", len(answers))
from collections import Counter
print("answer values:", Counter(answers.values()).most_common(12))

# ---------- apply ----------
applied = 0
unknown = 0
for i, q in enumerate(qs):
    if q["answer"]:
        q["answer_src"] = "pdf"
        continue
    a = answers.get(i)
    if not a or a == "?":
        unknown += 1
        continue
    if q["type"] == "judge":
        if a in ("T", "F"):
            q["answer"] = a
        elif a in ("对", "正确", "√"):
            q["answer"] = "T"
        elif a in ("错", "错误", "×", "X"):
            q["answer"] = "F"
    else:
        a = "".join(sorted(set(c for c in a if c in LET)))
        if a and not any(LET.index(c) >= len(q["options"]) for c in a):
            q["answer"] = a
    if q["answer"]:
        q["answer_src"] = "kb"          # 依据党史知识补录
        applied += 1
    else:
        unknown += 1

print(f"\nnewly answered: {applied}   still unknown: {unknown}")
tot_ans = sum(1 for q in qs if q["answer"])
print(f"total with answer: {tot_ans}/{len(qs)}  ({round(tot_ans/len(qs)*100)}%)")
print("with answer by type:", Counter(q["type"] for q in qs if q["answer"]))

# ---------- build questions.js payload ----------
CHAPTERS = {
    0: "绪论 · 综合练习",
    1: "第一章 · 中国共产党的创建和投身大革命的洪流（一）",
    2: "第一章 · 中国共产党的创建和投身大革命的洪流（二）",
    3: "第二章 · 掀起土地革命的风暴（一）",
    4: "第二章 · 掀起土地革命的风暴（二）",
    5: "第三章 · 全民族抗日战争的中流砥柱（一）",
    6: "第三章 · 全民族抗日战争的中流砥柱（二）",
    7: "第四章 · 夺取新民主主义革命的全国性胜利",
    8: "第五章 · 中华人民共和国的成立和社会主义制度的建立",
    9: "第六章 · 社会主义建设的探索和曲折发展",
    10: "第七章 · 改革开放的起步与伟大转折",
    11: "第八章 · 改革开放的全面展开",
    12: "第九章 · 把中国特色社会主义推向 21 世纪",
    13: "第十章 · 建立社会主义市场经济体制",
    14: "第十一章 · 全面建设小康社会与推动科学发展",
    15: "第十二章 · 中国特色社会主义进入新时代",
}

# clean and de-dup one more time
seen, final = set(), []
def key(s):
    return re.sub(r"[\s，。、；：（）()【】\[\]“”\"'？！,.;:!?]", "", s or "")[:64]

for q in qs:
    stem = re.sub(r"\s+", "", q["stem"]).strip(" 　。，、；：")
    if len(stem) < 10:
        continue
    k = key(stem)
    if k in seen:
        continue
    seen.add(k)
    typ = q["type"]
    rec = {"u": q["unit_no"], "t": typ, "q": stem}
    if typ != "judge":
        o = q["options"]
        if len(o) != 4 or any(not str(o.get(x, "")).strip() for x in LET):
            continue
        rec["o"] = [re.sub(r"\s+", "", str(o[x])) for x in LET]
    if q["answer"]:
        rec["a"] = q["answer"]
        if q.get("answer_src") == "kb":
            rec["ak"] = "kb"
    final.append(rec)

print(f"\nFINAL questions in payload: {len(final)}")
print("types:", Counter(r["t"] for r in final))
print("with answer:", sum(1 for r in final if r.get("a")))
print("units used:", len({r["u"] for r in final}))

unit_list = []
present = {r["u"] for r in final}
for no in sorted(units, key=lambda x: (int(x.split(".")[0]), int(x.split(".")[1]))):
    if no in present:
        unit_list.append({"no": no, "title": units[no], "chapter": int(no.split(".")[0])})

data = {"units": unit_list, "questions": final}
for path in (os.path.join(BASE, "questions.js"), os.path.join(BASE, "site", "questions.js")):
    with open(path, "w", encoding="utf-8") as f:
        f.write("// 党史题库 — 由 PDF 题库经 OCR 提取整理，并按党史知识补录答案\n")
        f.write("window.QUIZ_DATA = ")
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")
    print("wrote", path, os.path.getsize(path) // 1024, "KB")
