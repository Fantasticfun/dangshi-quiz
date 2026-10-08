import sys, os, time, json, glob
sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
import cv2
from rapidocr_onnxruntime import RapidOCR
from concurrent.futures import ThreadPoolExecutor

PAGES = r"C:\Users\13083\Desktop\dangshi-quiz\build\pages"
OUT = r"C:\Users\13083\Desktop\dangshi-quiz\build\ocr"
os.makedirs(OUT, exist_ok=True)

SCALE = 2
engine = RapidOCR()


def ocr_one(path):
    name = os.path.basename(path)
    dst = os.path.join(OUT, name.replace(".png", ".json"))
    if os.path.exists(dst):
        return name, "cached"
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return name, "MISSING"
    h, w = img.shape[:2]
    up = cv2.resize(img, (w * SCALE, h * SCALE), interpolation=cv2.INTER_CUBIC)
    res, _ = engine(up)
    items = []
    if res:
        for box, text, score in res:
            xs = [float(p[0]) for p in box]
            ys = [float(p[1]) for p in box]
            items.append({
                "x0": round(min(xs), 1), "x1": round(max(xs), 1),
                "y0": round(min(ys), 1), "y1": round(max(ys), 1),
                "t": text, "s": round(float(score), 3),
            })
    items.sort(key=lambda d: (d["y0"], d["x0"]))
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=1)
    return name, len(items)


if __name__ == "__main__":
    files = sorted(glob.glob(os.path.join(PAGES, "page-*.png")))
    print("pages to OCR:", len(files), flush=True)
    t0 = time.time()
    done = 0
    with ThreadPoolExecutor(max_workers=6) as ex:
        for name, info in ex.map(ocr_one, files):
            done += 1
            if done % 10 == 0 or done == len(files):
                print(f"{done}/{len(files)}  {name} -> {info}  {time.time()-t0:.0f}s", flush=True)
    print("DONE ocr in", round(time.time() - t0, 1), "s")
