import sys, os, json, re
sys.stdout.reconfigure(encoding='utf-8')
import numpy as np, cv2
from rapidocr_onnxruntime import RapidOCR

BASE = r"C:\Users\13083\Desktop\dangshi-quiz"
PAGES = os.path.join(BASE, "pages")
SRC = os.path.join(BASE, "build", "questions_final.json")
OUT = os.path.join(BASE, "build", "questions_repaired.json")

qs = json.load(open(SRC, encoding="utf-8"))
engine = RapidOCR()
LET = "ABCD"


def damaged(q):
    if q["type"] == "judge": return False
    return len(q["options"]) < 4 or any(not str(q["options"].get(k, "")).strip() for k in LET)


def band_items(page, y0, y1, x0=140, x1=2400, scales=(2, 3, 4)):
    """OCR a band and return items in genuine reading order (row-grouped, x-sorted)."""
    img = cv2.imread(os.path.join(PAGES, f"page-{page:03d}.png"), cv2.IMREAD_GRAYSCALE)
    if img is None: return []
    H, W = img.shape
    a, b = max(0, int(y0 / 2)), min(H, int(y1 / 2))
    c, d = max(0, int(x0 / 2)), min(W, int(x1 / 2))
    band = img[a:b, c:d]
    if band.size == 0: return []
    best = []
    for s in scales:
        up = cv2.resize(band, (band.shape[1] * s, band.shape[0] * s), interpolation=cv2.INTER_CUBIC)
        res, _ = engine(up)
        if not res: continue
        items = [{"x": min(p[0] for p in bx) / s + x0 / 2,
                  "y": min(p[1] for p in bx) / s + y0 / 2,
                  "t": t.strip()} for bx, t, sc in res if t.strip()]
        if len(items) > len(best):
            best = items
    # row grouping
    best.sort(key=lambda i: (i["y"], i["x"]))
    rows, cur = [], None
    for it in best:
        if cur is not None and abs(it["y"] - cur[0]) < 34:
            cur[1].append(it)
            cur[0] = min(cur[0], it["y"])
        else:
            cur = [it["y"], [it]]
            rows.append(cur)
    out = []
    for y, group in rows:
        group.sort(key=lambda i: i["x"])
        out.append({"y": y, "text": "".join(g["t"] for g in group), "x": group[0]["x"]})
    return out


MARK = re.compile(r"^([ABCD])\s*[\.、．,，:：]?\s*(.*)$")
# a marker appearing mid-line, e.g. "...意见》B、《新时代公民道德建设实施钢要》C、..."
INLINE = re.compile(r"(?<=[\u4e00-\u9fff）)》】\"'’、。，；])\s*([ABCD])\s*[\.、．,，:：]\s*")


def split_inline(text):
    """Split a line that packs several options, returning [(letter|None, body), ...]."""
    parts, marks = [], []
    last = 0
    for m in INLINE.finditer(text):
        marks.append((m.start(), m.end(), m.group(1)))
    if not marks:
        return [(None, text)]
    parts.append((None, text[:marks[0][0]]))
    for i, (a, b, L) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        parts.append((L, text[b:end]))
    return parts


def parse_block(items, qtype):
    """Split an OCR'd question block into (stem, options{})."""
    stem_parts, options, cur = [], {}, None
    for it in items:
        t = it["text"]
        if re.match(r"^我的答案", t) or re.match(r"^[\d\.]+\s*分$", t):
            break
        for L, body in split_inline(t):
            body = body.strip()
            if L is None:
                if cur:
                    options[cur] = (options[cur] + body).strip()
                else:
                    stem_parts.append(body)
                continue
            if L in options:
                if cur:
                    options[cur] = (options[cur] + body).strip()
                continue
            cur = L
            options[L] = body
    return "".join(stem_parts).strip(), options


fixed = 0
for q in qs:
    if not damaged(q):
        continue
    # widen the search: start a little above the stem, end well past the options
    items = band_items(q["page"], q["y"] - 40, q["y"] + 1500)
    if not items:
        print(f"  !! p{q['page']} y={q['y']}: re-OCR empty")
        continue
    # cut everything after the answer label / score line
    stem, opts = parse_block(items, q["type"])
    # keep whatever we already had if the re-OCR came back worse
    merged = dict(q["options"])
    for k, v in opts.items():
        if v and len(v) > len(merged.get(k, "")):
            merged[k] = v
    # drop blanks and compact the letters if the block only had 2-3 real options
    present = [k for k in LET if str(merged.get(k, "")).strip()]
    new_full = len(present) == 4
    if new_full and stem:
        q["options"] = {k: str(merged[k]).strip() for k in LET}
        if len(stem) > 6:
            q["stem"] = stem
        fixed += 1
        status = "FIXED"
    else:
        status = "PARTIAL(%s)" % (",".join(present) or "none")
        q["options"] = {k: str(merged[k]).strip() for k in present}
        if len(stem) > 6 and len(stem) > len(q["stem"]):
            q["stem"] = stem
    print(f"  {status} p{q['page']} y={q['y']} unit={q['unit_no']} opts={sorted(merged)}")
    print(f"        stem: {q['stem'][:70]}")
    for k in LET:
        print(f"        {k}: {str(q['options'].get(k,''))[:70]}")

print(f"\nfully repaired: {fixed}/{sum(1 for q in qs if damaged(q))}")
json.dump(qs, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("saved", OUT)
