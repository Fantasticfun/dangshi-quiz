import sys, os, json, re
sys.stdout.reconfigure(encoding='utf-8')

BASE = r"C:\Users\13083\Desktop\dangshi-quiz"
SRC = os.path.join(BASE, "build", "questions_final3.json")
OUT = os.path.join(BASE, "build", "questions_final4.json")
LET = "ABCD"

qs = json.load(open(SRC, encoding="utf-8"))
# an option marker embedded anywhere, including right after punctuation
INL = re.compile(r"([ABCD])\s*[\.、．,，:：]\s*")


def split_markers(text):
    marks = [(m.start(), m.end(), m.group(1)) for m in INL.finditer(text)]
    if not marks:
        return None
    head = text[:marks[0][0]].strip()
    out = []
    for i, (a, b, L) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        out.append((L, text[b:end].strip()))
    return head, out


TYPE_TAG = re.compile(r"^[【\[]?\s*(单选题|多选题|判断题|多选|单选|判断)\s*[】\]]?\s*")


changed = 0
for q in qs:
    if q["type"] == "judge":
        q["options"] = {}
        continue

    opts = {k: str(v).strip() for k, v in q["options"].items() if str(v).strip()}
    stem = q["stem"]

    # 1. options that leaked into the stem: pull them back out
    r = split_markers(stem)
    if r:
        head, found = r
        recovered = {}
        for L, body in found:
            if body and L not in opts and L not in recovered:
                recovered[L] = body
        if len(recovered) >= 2 and len(head) >= 6:
            stem = head
            for L, body in recovered.items():
                opts.setdefault(L, body)

    # 2. a body may itself carry a following option's marker glued on
    for L in list("ABCD"):
        v = opts.get(L, "")
        if not v:
            continue
        r2 = split_markers(v)
        if r2:
            head2, found2 = r2
            if head2:
                opts[L] = head2
            for LL, body in found2:
                if body and LL not in opts:
                    opts[LL] = body

    # 3. strip a leftover type tag from the stem
    stem = TYPE_TAG.sub("", stem).strip()
    # 4. trim trailing punctuation-only junk
    stem = re.sub(r"[、，。\s]+$", "", stem)

    present = [k for k in LET if opts.get(k)]
    if len(present) >= len(q["options"]):
        q["stem"] = stem if len(stem) >= 6 else q["stem"]
        q["options"] = {k: opts[k] for k in present}
        changed += 1

print("questions adjusted:", changed)

from collections import Counter
print("option-count dist:", Counter(len(q["options"]) for q in qs if q["type"] != "judge"))
short = [q for q in qs if len(q["stem"]) < 10]
print("stems <10 chars:", len(short))
for q in short:
    print("   ", q["unit_no"], q["type"], "|", q["stem"], "|", q["options"])
blank = [q for q in qs if q["type"] != "judge" and any(not v for v in q["options"].values())]
print("blank options:", len(blank))

json.dump(qs, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("saved", OUT)
