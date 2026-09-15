import sys, os, time, json
sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
import cv2
import pdfplumber

PDF = r"C:\Users\13083\Desktop\党史题库(2).pdf"
OUT = r"C:\Users\13083\Desktop\dangshi-quiz\pages"
os.makedirs(OUT, exist_ok=True)

DPI = 150  # native bitmap is ~105 dpi; 150 gives a modest supersample before the 2x OCR upscale

t0 = time.time()
with pdfplumber.open(PDF) as pdf:
    n = len(pdf.pages)
    for i, p in enumerate(pdf.pages):
        dst = os.path.join(OUT, f"page-{i+1:03d}.png")
        if os.path.exists(dst):
            continue
        img = p.to_image(resolution=DPI).original
        img = img.convert("L")  # grayscale is enough for OCR
        img.save(dst, format="PNG", optimize=True)
        if (i + 1) % 20 == 0:
            print(f"rendered {i+1}/{n}  {time.time()-t0:.0f}s", flush=True)
print("DONE rendered", n, "pages in", round(time.time() - t0, 1), "s")
