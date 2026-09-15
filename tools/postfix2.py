import sys, os, json, re
sys.stdout.reconfigure(encoding='utf-8')

BASE = r"C:\Users\13083\Desktop\dangshi-quiz"
SRC = os.path.join(BASE, "build", "questions_repaired.json")
OUT = os.path.join(BASE, "build", "questions_final3.json")
qs = json.load(open(SRC, encoding="utf-8"))
LET = "ABCD"
# option marker without requiring punctuation after the letter
INL = re.compile(r"([ABCD])\s*[\.、．,，:：]?\s*")


def split_markers(text):
    marks = [(m.start(), m.end(), m.group(1)) for m in INL.finditer(text)]
    # keep only a strictly increasing, mostly-complete sequence A,B,C,D
    seq, seen = [], set()
    for a, b, L in marks:
        if L in seen:
            continue
        if seq and LET.index(L) <= LET.index(seq[-1][2]):
            continue
        if not seq and L != "A":
            continue
        seq.append((a, b, L)); seen.add(L)
    if len(seq) < 2:
        return None
    head = text[:seq[0][0]].strip()
    out = []
    for i, (a, b, L) in enumerate(seq):
        end = seq[i + 1][0] if i + 1 < len(seq) else len(text)
        out.append((L, text[b:end].strip()))
    return head, out


TYPE_TAG = re.compile(r"^[【\[]?\s*(单选题|多选题|判断题|多选|单选|判断)\s*[】\]]?\s*")
NUMTAG = re.compile(r"^\d{1,2}\s*[\.．]\s*")

fixed = 0
for q in qs:
    if q["type"] == "judge":
        q["options"] = {}
        continue
    opts = {k: str(v).strip() for k, v in q["options"].items() if str(v).strip()}
    stem = q["stem"]

    # pull embedded options out of the stem
    r = split_markers(stem)
    if r:
        head, found = r
        got = {L: b for L, b in found if b}
        if len(got) >= 2 and len(head) >= 6 and (len(got) > len(opts) or not all(opts.get(k) for k in LET)):
            stem, opts = head, got

    # an option body may itself carry the next option's marker
    for L in list(LET):
        v = opts.get(L, "")
        if not v:
            continue
        r2 = split_markers(v)
        if r2:
            h2, f2 = r2
            if h2:
                opts[L] = h2
            for LL, body in f2:
                if body and LL != L and not opts.get(LL):
                    opts[LL] = body

    # fill a hole with the longest orphan fragment still sitting in the stem tail
    present = [k for k in LET if opts.get(k)]
    if len(present) == 4 or not present:
        pass
    stem = NUMTAG.sub("", TYPE_TAG.sub("", stem)).strip()
    stem = re.sub(r"[、，。\s]+$", "", stem)
    if len(stem) < 6:
        stem = q["stem"]

    before = (q["stem"], dict(q["options"]))
    q["stem"] = stem
    q["options"] = {k: opts[k] for k in present}
    if (before[0], before[1]) != (q["stem"], q["options"]):
        fixed += 1

print("questions modified:", fixed)
from collections import Counter
print("option-count dist:", Counter(len(q["options"]) for q in qs if q["type"] != "judge"))

# remaining stems that still embed marker sequences
left = [q for q in qs if q["type"] != "judge" and split_markers(q["stem"])]
print("stems still embedding markers:", len(left))
for q in left[:10]:
    print("   ", q["unit_no"], "|", q["stem"][:85])
    print("        opts:", {k: v[:34] for k, v in q["options"].items()})

json.dump(qs, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("saved", OUT)
