import sys, os, json, re
sys.stdout.reconfigure(encoding='utf-8')

BASE = r"C:\Users\13083\Desktop\dangshi-quiz"
OUT = os.path.join(BASE, "build", "answers")
os.makedirs(OUT, exist_ok=True)

js = open(os.path.join(BASE, "questions.js"), encoding="utf-8").read()
data = json.loads(re.search(r"window\.QUIZ_DATA\s*=\s*(?P<d>\{.*\});\s*$", js, re.S).group("d"))
units = {u["no"]: u["title"] for u in data["units"]}

# questions with NO answer key: single-choice and true/false
need = [(i, q) for i, q in enumerate(data["questions"]) if not q.get("a")]
print("total questions:", len(data["questions"]))
print("needing an answer:", len(need))
from collections import Counter
print("by type:", Counter(q["t"] for _, q in need))

BATCH = 24
batches = [need[i:i + BATCH] for i in range(0, len(need), BATCH)]
print("batches:", len(batches))

for bi, batch in enumerate(batches, 1):
    lines = []
    lines.append(f"# 党史题库 · 待判题批次 {bi}/{len(batches)}")
    lines.append("# 请为每道题给出答案。单选=1个字母；判断=T(正确)/F(错误)。")
    lines.append("# 不确定的题，answer 填 \"?\" 并在 note 说明。")
    lines.append("")
    for gid, q in batch:
        lines.append(f"## id={gid}  [{q['t']}]  单元 {q['u']} {units.get(q['u'], '')}")
        lines.append(f"题干：{q['q']}")
        if q.get("o"):
            for i, o in enumerate(q["o"]):
                lines.append(f"  {'ABCD'[i]}. {o}")
        lines.append("")
    p = os.path.join(OUT, f"batch-{bi:02d}.txt")
    open(p, "w", encoding="utf-8").write("\n".join(lines))

print("wrote", len(batches), "batch files to", OUT)
print("sample batch file:", os.path.join(OUT, "batch-01.txt"))
print()
print(open(os.path.join(OUT, "batch-01.txt"), encoding="utf-8").read()[:1200])

# also save the id list for later merging
json.dump([gid for gid, _ in need], open(os.path.join(OUT, "ids.json"), "w"), ensure_ascii=False)
