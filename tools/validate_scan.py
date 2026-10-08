import sys, os, json, re, random
sys.stdout.reconfigure(encoding='utf-8')
import numpy as np, cv2
from rapidocr_onnxruntime import RapidOCR

BASE = r"C:\Users\13083\Desktop\dangshi-quiz"
PAGES = os.path.join(BASE, "build", "pages")
qs = json.load(open(os.path.join(BASE, "build", "final_answered.json"), encoding="utf-8"))
LET = "ABCD"
eng = RapidOCR()

# The scan prints "我的答案：" and the submitted answer right after it, on the same
# visual row or the row below, inside x≈200..420 (OCR 2x coords). OCR often missed it,
# so re-OCR a tight crop at high zoom.
def read_scan_answer(page, y_label):
    img = cv2.imread(os.path.join(PAGES, f"page-{page:03d}.png"), cv2.IMREAD_GRAYSCALE)
    if img is None:
        return ""
    a = max(0, int(y_label / 2) - 8)
    b = min(img.shape[0], int(y_label / 2) + 40)
    c, d = int(190 / 2), int(560 / 2)
    band = img[a:b, c:d]
    if band.size == 0:
        return ""
    for s in (6, 8, 10):
        up = cv2.resize(band, (band.shape[1] * s, band.shape[0] * s), interpolation=cv2.INTER_CUBIC)
        res, _ = eng(up)
        if not res:
            continue
        txt = "".join(t for _, t, _ in res)
        txt = re.sub(r"[^ABCDTF对错]", "", txt)
        m = re.search(r"[ABCD]{1,4}", txt)
        if m:
            return m.group(0)
    return ""

withpage = [q for q in qs if "page" in q and "y" in q]
print("questions with page/y:", len(withpage), "/", len(qs))

# focus on choice questions whose answer came from knowledge (kb) — these are what we must validate
targets = [q for q in withpage if q.get("answer_src") == "kb" and q["type"] in ("single", "multi")]
print("kb-sourced choice questions to validate:", len(targets))

random.seed(7)
sample = random.sample(targets, min(60, len(targets)))
found = agree = disagree = 0
conf = []
for q in sample:
    sa = read_scan_answer(q["page"], q["y"])
    if not sa:
        continue
    found += 1
    if sorted(sa) == sorted(q["answer"]):
        agree += 1
    else:
        disagree += 1
        conf.append({"unit": q["unit_no"], "stem": q["stem"][:74], "scan": sa,
                     "ours": q["answer"], "page": q["page"]})

print(f"\nsample of {len(sample)}: scan answer readable for {found}")
print(f"  agree={agree}  disagree={disagree}")
if found:
    print(f"  agreement rate: {round(agree/found*100)}%")
print("\n=== disagreements ===")
for c in conf:
    print(f"  [{c['unit']}] scan={c['scan']} ours={c['ours']} p{c['page']}")
    print(f"     {c['stem']}")
