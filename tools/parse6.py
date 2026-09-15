import sys, os, json, glob, re
sys.stdout.reconfigure(encoding='utf-8')
BASE = r"C:\Users\13083\Desktop\dangshi-quiz"
OCR = os.path.join(BASE, "ocr")
OUT = os.path.join(BASE, "build")

boxes = []
for p in sorted(glob.glob(os.path.join(OCR, "page-*.json"))):
    page = int(re.search(r"page-(\d+)", p).group(1))
    for it in json.load(open(p, encoding="utf-8")):
        t = re.sub(r"\s+", " ", it["t"]).strip()
        if t:
            boxes.append({"page": page, "y": it["y0"], "x": it["x0"], "x1": it["x1"], "t": t, "s": it["s"]})
boxes.sort(key=lambda b: (b["page"], b["y"], b["x"]))

MARK_RE  = re.compile(r"^[【\[]\s*(单选题|多选题|判断题|多选|单选|判断)\s*[】\]]?")
SEC_RE   = re.compile(r"^[一二三四五六七八九十]{1,3}\s*[\.\、．,，]?\s*(单选题|多选题|判断题|多选|单选|判断)")
SCORE_RE = re.compile(r"^0?[\d]{1,3}\s*[\.．]?\d*\s*分$")
MINE_RE  = re.compile(r"^我的答案")
UNIT_RE  = re.compile(r"^(\d{1,2})\s*[\.．]\s*(\d{1,2})\s*(\D.{1,44})$")
OPT_RE   = re.compile(r"^([ABCD])\s*[、\.．,，:：]?\s*(.*)$")
QW_NUM   = re.compile(r"^(\d{1,2})\s*[\.．,，]\s*(\D.{2,})$")
ANSLET   = re.compile(r"^[ABCD]{1,4}$")
NOISE    = re.compile(r"^(页码|第\s*\d+\s*页|共\s*\d+\s*页)")
SENT_END = re.compile(r"[。！？]$")

def qtype(s):
    if "单选" in s: return "single"
    if "多选" in s: return "multi"
    return "judge"

for b in boxes:
    t = b["t"]; b["kind"] = "text"; b["qtype"] = None; b["tail"] = ""
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
    # question number glued to the stem, e.g. "2.以下各项中..."
    m = QW_NUM.match(t)
    if m and b["x"] < 340 and not OPT_RE.match(t):
        b["kind"] = "qnum"; b["num"] = int(m.group(1)); b["body"] = m.group(2).strip()

# join same-row fragments that sit to the LEFT of a far-right marker
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

questions, skipped = [], []
cur_unit = {"no": "0.0", "title": "绪论 · 综合练习"}
cur_type = None
cur = None
paper_no = 0
n_in_paper = 0

def flush():
    global cur
    if not cur: return
    cur["stem"] = cur["stem"].strip()
    cur["options"] = {k: re.sub(r"\s+", "", v).strip() for k, v in cur["options"].items() if v.strip()}
    cur.pop("_await", None); cur.pop("_my", None)
    if cur["stem"] and (cur["options"] or cur["type"] == "judge"):
        questions.append(cur)
    else:
        skipped.append(cur)
    cur = None

def new_q(typ, stem, b):
    global cur, n_in_paper
    flush(); n_in_paper += 1
    cur = {"unit_no": cur_unit["no"], "unit_title": cur_unit["title"],
           "type": typ or cur_type or "single", "stem": stem, "options": {}, "answer": "",
           "page": b["page"], "y": b["y"], "paper": paper_no, "n": n_in_paper}

for b in boxes:
    k = b["kind"]
    if k == "consumed": continue
    # stop waiting for an answer letter that never came
    if cur is not None and cur.get("_await"):
        pg, my = cur["_my"]
        near = (b["page"] == pg and (b["y"] - my) < 150)
        if not (k == "anslet" and near):
            flush()
    if k == "unit":
        flush(); cur_unit = {"no": b["unit_no"], "title": b["unit_title"]}
    elif k == "sec":
        flush(); paper_no += 1; n_in_paper = 0; cur_type = b["qtype"]
    elif k == "qmark":
        new_q(b["qtype"], MARK_RE.sub("", b["t"]).strip(" 　】]"), b)
    elif k == "qnum":
        new_q(cur_type, b["body"], b)
    elif k == "score":
        flush()
    elif cur is None:
        continue
    elif k == "mine":
        if b["tail"]:
            cur["answer"] = b["tail"]; flush()
        else:
            cur["_await"] = True; cur["_my"] = (b["page"], b["y"])
    elif k == "anslet":
        cur["answer"] += b["t"]; cur.pop("_await", None); flush()
    elif k == "opt":
        L = b["letter"]
        if L in cur["options"] and cur["options"][L]:
            cur["options"][L] += b["body"]        # wrapped option
        else:
            cur["options"][L] = cur["options"].get(L, "") + b["body"]
    elif k == "text":
        t = b["t"]
        if NOISE.match(t): continue
        if cur["options"]:
            if b["x"] > 900 and SENT_END.search(t):
                continue
            cur["options"][sorted(cur["options"])[-1]] += t
        else:
            # an unmarked new question: previous stem already ended a sentence
            # and this line is a fresh long sentence -> treat as continuation unless
            # the previous question already has options (handled above)
            if SENT_END.search(t) and len(t) > 14 and not cur["stem"]:
                cur["stem"] += t
            else:
                cur["stem"] += t
flush()

from collections import Counter
print("questions:", len(questions), "skipped:", len(skipped))
print("types:", Counter(q["type"] for q in questions))
print("with answer:", sum(1 for q in questions if q["answer"]), Counter(q["type"] for q in questions if q["answer"]))
print("no options:", Counter(q["type"] for q in questions if not q["options"]))
print("opt dist:", Counter(len(q["options"]) for q in questions))
print("units:", len({q["unit_no"] for q in questions}))
for i, q in enumerate(questions):
    q["id"] = f"q{i+1:04d}"
json.dump(questions, open(os.path.join(OUT, "questions_final.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("saved questions_final.json")
