import sys, os, time, json
sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
import cv2
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
from rapidocr_onnxruntime import RapidOCR

BASE = r"C:\Users\13083\Desktop\dangshi-quiz"
SRC = os.path.join(BASE, "build", "full-bitmap-gray.png")
OUT = os.path.join(BASE, "build", "full_ocr")
os.makedirs(OUT, exist_ok=True)

SCALE = 2
BAND = 2400          # source rows per band (memory-safe)
OVERLAP = 100        # source rows of overlap between bands

img = cv2.imread(SRC, cv2.IMREAD_GRAYSCALE)
H, W = img.shape[:2]
print("bitmap", W, "x", H, flush=True)

engine = RapidOCR()
items = []
y = 0
band_no = 0
t0 = time.time()

while y < H:
    y2 = min(H, y + BAND)
    strip = img[y:y2, :]
    up = cv2.resize(strip, (W * SCALE, strip.shape[0] * SCALE), interpolation=cv2.INTER_CUBIC)
    res, _ = engine(up)
    n = 0
    if res:
        for box, text, score in res:
            text = text.strip()
            if not text:
                continue
            xs = [float(p[0]) for p in box]
            ys = [float(p[1]) for p in box]
            gy0 = y + min(ys) / SCALE
            gy1 = y + max(ys) / SCALE
            if band_no > 0 and gy1 <= y + OVERLAP:
                continue                      # already emitted by the previous band
            items.append({
                "x0": round(min(xs) / SCALE, 1), "x1": round(max(xs) / SCALE, 1),
                "y0": round(gy0, 1), "y1": round(gy1, 1),
                "t": text, "s": round(float(score), 3),
            })
            n += 1
    band_no += 1
    print(f"band {band_no}: rows {y}-{y2} (+{n}) total={len(items)} {time.time()-t0:.0f}s", flush=True)
    y += BAND - OVERLAP

# dedupe exact duplicates that survive the overlap
seen = set()
uniq = []
for it in items:
    k = (int(it["y0"]), int(it["x0"]), it["t"])
    if k in seen:
        continue
    seen.add(k)
    uniq.append(it)

uniq.sort(key=lambda d: (d["y0"], d["x0"]))
json.dump(uniq, open(os.path.join(OUT, "raw_items.json"), "w", encoding="utf-8"), ensure_ascii=False)
print("DONE raw items", len(uniq), "in", round(time.time() - t0, 1), "s")
