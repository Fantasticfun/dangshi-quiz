import sys, os, json, re
sys.stdout.reconfigure(encoding='utf-8')

BASE = r"C:\Users\13083\Desktop\dangshi-quiz"
qs = json.load(open(os.path.join(BASE, "build", "merged.json"), encoding="utf-8"))
LET = "ABCD"

# Curated OCR corrections: order matters (longer / more specific first).
# Each entry is (regex, replacement). Context-anchored so legitimate uses survive.
FIXES = [
    # 战争 family: 净 is a misread of 争 inside 战净
    (r"战净", "战争"),
    (r"战净争", "战争"),
    (r"净夺", "争夺"),
    # 戊戌
    (r"戊成变法", "戊戌变法"),
    (r"戊成维新", "戊戌维新"),
    (r"戊成", "戊戌"),
    # 古田会议
    (r"古由会议", "古田会议"),
    # 目的 / 保持 / 各种
    (r"自的", "目的"),
    (r"保特", "保持"),
    (r"名种", "各种"),
    (r"保特着", "保持着"),
    (r"保持看着", "保持着"),
    # 挫折 / 主义 / 井冈山 / 宁冈
    (r"遣挫折", "遭挫折"),
    (r"遣到", "遭到"),
    (r"主文", "主义"),
    (r"井岗山", "井冈山"),
    (r"宁岗", "宁冈"),
    # 围剿
    (r"反围巢", "反围剿"),
    (r"围巢", "围剿"),
    # 封建
    (r"哇建", "封建"),
    (r"陡建", "封建"),
    # 湘赣
    (r"湘障赣", "湘赣"),
    (r"相障边界", "湘赣边界"),
    (r"湘聘障", "湘赣"),
    # misc
    (r"思想式器", "思想武器"),
    (r"培部旧日式农民武装", "袁部旧式农民武装"),
    (r"车事和政治", "军事和政治"),
    (r"关关于", "关于"),
    (r"的够从中", "能够从中"),
    (r"控空制力量", "控制力量"),
    (r"比较效好", "比较好"),
    (r"其体措施", "具体措施"),
    (r"士地革命", "土地革命"),
    (r"土地革命战净", "土地革命战争"),
    (r"陡", "陆"),
    (r"党白的建设", "党的建设"),
    (r"薄与", "薄弱"),
    (r"比较薄与", "比较薄弱"),
    (r"自给自足的农业经济，便于部队筹款筹粮", "自给自足的农业经济，便于部队筹款筹粮"),
    (r"苏维埃政府", "苏维埃政府"),
    (r"苏维埃及", "苏维埃"),
    (r"歼灭", "歼灭"),
    (r"车痛期", "阵痛期"),
    (r"自行车厂", "自行车厂"),
]

before = Counter = {}
n_q = 0
applied = 0
for q in qs:
    changed = False
    for field in ("stem",):
        s = q[field]
        for pat, rep in FIXES:
            ns = re.sub(pat, rep, s)
            if ns != s:
                applied += 1
                s = ns
                changed = True
        q[field] = s
    for k in list(q["options"].keys()):
        s = q["options"][k]
        for pat, rep in FIXES:
            ns = re.sub(pat, rep, s)
            if ns != s:
                applied += 1
                s = ns
                changed = True
        q["options"][k] = s
    if changed:
        n_q += 1

print(f"replacements applied: {applied} across {n_q} questions")

# report any remaining classic errors
parts = []
for q in qs:
    parts.append(q["stem"])
    parts.extend(q["options"].values())
blob = "\n".join(parts)
leftovers = {}
for pat in ("战净", "戊成", "古由", "自的", "保特", "名种", "围巢", "哇建", "主文", "井岗山", "遣挫"):
    c = blob.count(pat)
    if c:
        leftovers[pat] = c
print("leftover classic errors:", leftovers or "none")

json.dump(qs, open(os.path.join(BASE, "build", "merged_fixed.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("saved merged_fixed.json")

print("\n=== spot check the previously broken spots ===")
for probe in ("战争", "戊戌", "古田会议", "目的", "井冈山"):
    for q in qs:
        if probe in q["stem"]:
            print(f"  {probe}: {q['stem'][:76]}")
            break
