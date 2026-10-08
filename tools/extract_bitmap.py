import sys, os, time
sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
import pdfplumber

PDF = r"C:\Users\13083\Desktop\党史题库(2).pdf"
OUT = r"C:\Users\13083\Desktop\dangshi-quiz\build"
os.makedirs(OUT, exist_ok=True)

t0 = time.time()
with pdfplumber.open(PDF) as pdf:
    print("pages:", len(pdf.pages))
    s0 = pdf.pages[0].images[0]["stream"]
    raw = s0.get_data()
    arr = np.frombuffer(raw, dtype=np.uint8)
    expected = 785 * 29219 * 3
    print("decoded:", len(raw), "expected:", expected)
    arr = arr[:expected].reshape(29219, 785, 3)
    img = Image.fromarray(arr, "RGB")
    print("bitmap:", img.size)
    g = img.convert("L")
    p = os.path.join(OUT, "full-bitmap-gray.png")
    g.save(p)
    print("saved", p, os.path.getsize(p) // 1024, "KB in", round(time.time() - t0, 1), "s")
