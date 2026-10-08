import sys, os, json, glob, re
sys.stdout.reconfigure(encoding='utf-8')

"""parse8 —— 以 400 个「我的答案」为唯一真值锚点重建题目。

每个答案标签恰好对应一道题。对每个标签，向前回溯收集该题的题干与选项，
直到遇到上一个答案标签、或一个大题标题、或一个单元标题为止。
"""

BASE = r"C:\Users\13083\Desktop\dangshi-quiz"
OCR = os.path.join(BASE, "build", "ocr")
OUT = os.path.join(BASE, "build")
LET = "ABCD"

boxes = []
for p in sorted(glob.glob(os.path.join(OCR, "page-*.json"))):
    page = int(re.search(r"page-(\d+)", p).group(1))
    for it in json.load(open(p, encoding="utf-8")):
        t = re.sub(r"\s+", " ", it["t"]).strip()
        if t:
            boxes.append({"page": page, "y": it["y0"], "x": it["x0"], "x1": it["x1"], "t": t, "s": it["s"]})
boxes.sort(key=lambda b: (b["page"], b["y"], b["x"]))

MARK_RE  = re.compile(r"^[【\[]\s*(单选题|多选题|判断题|多选|单选|判断)\s*[】\]]?")
SEC_RE   = re.compile(r"^[一二三四五六七八九十]{1,3}\s*[\.、．,，]?\s*(单选题|多选题|判断题|多选|单选|判断)")
SCORE_RE = re.compile(r"^0?[\d]{1,3}\s*[\.．]?\d*\s*分$")
MINE_RE  = re.compile(r"^我的答案")
UNIT_RE  = re.compile(r"^(\d{1,2})\s*[\.．]\s*(\d{1,2})\s*(\D.{1,44})$")
OPT_RE   = re.compile(r"^([ABCD])\s*[、\.．,，:：]?\s*(.*)$")
QW_NUM   = re.compile(r"^(\d{1,2})\s*[\.．,，]\s*(\D.{2,})$")
ANSLET   = re.compile(r"^[ABCD]{1,4}$")
NOISE    = re.compile(r"^(页码|第\s*\d+\s*页|共\s*\d+\s*页)$")

def qtype(s):
    if "单选" in s: return "single"
    if "多选" in s: return "multi"
    return "judge"

# ---------- classify ----------
for b in boxes:
    t = b["t"]; b["kind"] = "text"; b["qtype"] = None; b["tail"] = ""; b["letter"] = None
    m = MARK_RE.match(t)
    if m: b["kind"], b["qtype"] = "qmark", qtype(m.group(1)); continue
    m = SEC_RE.match(t)
    if m and len(t) < 34: b["kind"], b["qtype"] = "sec", qtype(m.group(1)); continue
    if SCORE_RE.match(t): b["kind"] = "score"; continue
    if MINE_RE.match(t):
        b["kind"] = "mine"
        tail = MINE_RE.sub("", t).lstrip("：: 　")
        tail = re.sub(r"^[^A-D\u4e00-\u9fff]+", "", tail)
        b["tail"] = tail if ANSLET.match(tail) else ""
        continue
    m = UNIT_RE.match(t)
    if m and len(t) < 50 and "题" not in t and "分" not in t and not OPT_RE.match(t) and not ANSLET.match(t):
        b["kind"] = "unit"; b["unit_no"] = f"{int(m.group(1))}.{int(m.group(2))}"
        b["unit_title"] = m.group(3).strip(); continue
    if ANSLET.match(t): b["kind"] = "anslet"; continue
    m = OPT_RE.match(t)
    if m: b["kind"], b["letter"], b["body"] = "opt", m.group(1), m.group(2); continue
    m = QW_NUM.match(t)
    if m and b["x"] < 360: b["kind"], b["num"], b["body"] = "qnum", int(m.group(1)), m.group(2).strip()

# fragment on the left of a far-right option marker
for i, b in enumerate(boxes):
    if b["x1"] > 900 and b["kind"] in ("opt", "qnum", "text"):
        for j in range(i + 1, min(i + 4, len(boxes))):
            n = boxes[j]
            if n["page"] != b["page"] or abs(n["y"] - b["y"]) > 22: break
            if n["kind"] == "text" and n["x"] < b["x"]:
                if b["kind"] == "opt": b["body"] = n["t"] + b["body"]
                elif b["kind"] == "qnum": b["body"] = n["t"] + b["body"]
                else: b["t"] = n["t"] + b["t"]
                n["kind"] = "consumed"
                break

# ---------- linear stream with unit / section context ----------
stream = []
unit = {"no": "0.0", "title": "绪论 · 综合练习"}
sec = None
paper = 0
for b in boxes:
    k = b["kind"]
    if k == "consumed":
        continue
    if k == "unit":
        unit = {"no": b["unit_no"], "title": b["unit_title"]}
        continue
    if k == "sec":
        paper += 1; sec = b["qtype"]
        continue
    if k == "score":
        continue
    stream.append(dict(b, unit=dict(unit), sec=sec, paper=paper))

print("stream rows:", len(stream))

# ---------- find anchors ----------
anchor_idx = [i for i, r in enumerate(stream) if r["kind"] == "mine"]
print("answer anchors:", len(anchor_idx))
BOUNDARY = ("qmark", "sec")

def parse_block(rows):
    """rows = content belonging to ONE question (before its answer label)."""
    stem_parts, options, cur = [], {}, None
    for r in rows:
        k = r["kind"]
        if k == "qmark":
            stem_parts.append(MARK_RE.sub("", r["t"]).strip(" 　】]"))
            continue
        if k == "qnum":
            stem_parts.append(r["body"])
            continue
        if k == "text":
            t = r["t"]
            if NOISE.match(t): continue
            if cur:
                options[cur] = (options[cur] + t).strip()
            else:
                stem_parts.append(t)
            continue
        if k == "opt":
            L = r["letter"]
            body = r["body"]
            if L in options and options[L] and (len(options) > LET.index(L)):
                options[L] = (options[L] + body).strip()
            elif L in options:
                options[L] = (options[L] + body).strip()
            else:
                options[L] = body
            cur = L
            continue
    return "".join(stem_parts).strip(), options

questions = []
for n, ai in enumerate(anchor_idx):
    top = anchor_idx[n - 1] + 1 if n > 0 else 0
    rows = stream[top:ai]
    # drop leading rows belonging to the previous question's answer letters
    while rows and rows[0]["kind"] == "anslet":
        rows.pop(0)
    if not rows:
        continue
    anchor = stream[ai]
    stem, options = parse_block(rows)
    # answer letters may follow this label on the very next row(s)
    answer = anchor["tail"]
    j = ai + 1
    while j < len(stream) and stream[j]["kind"] == "anslet":
        answer += stream[j]["t"].strip()
        j += 1
    answer = re.sub(r"[^ABCD]", "", answer)

    typ = anchor["sec"] or "single"
    if not options:
        typ = "judge"
    questions.append({
        "unit_no": anchor["unit"]["no"], "unit_title": anchor["unit"]["title"],
        "type": typ, "stem": stem, "options": options, "answer": answer,
        "page": anchor["page"], "y": anchor["y"], "paper": anchor["paper"],
    })

print("\nquestions:", len(questions))
from collections import Counter
print("types:", Counter(q["type"] for q in questions))
print("with answer:", sum(1 for q in questions if q["answer"]),
      Counter(q["type"] for q in questions if q["answer"]))
print("option-count dist:", Counter(len(q["options"]) for q in questions))
print("units:", len({q["unit_no"] for q in questions}))

for i, q in enumerate(questions):
    q["id"] = f"net{i+1:04d}"
json.dump(questions, open(os.path.join(OUT, "parsed_v8.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("saved parsed_v8.json")
