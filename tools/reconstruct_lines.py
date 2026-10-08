import sys, os, json, re
sys.stdout.reconfigure(encoding='utf-8')

BASE = r"C:\Users\13083\Desktop\dangshi-quiz"
SRC = os.path.join(BASE, "build", "full_ocr", "raw_items.json")
OUT = os.path.join(BASE, "build", "full_ocr")
items = json.load(open(SRC, encoding="utf-8"))
print("raw items:", len(items))

# ---------- 1. group boxes into text lines (spatially, by ink extent) ----------
items.sort(key=lambda d: (d["y0"], d["x0"]))

lines = []
for it in items:
    placed = False
    if lines:
        cur = lines[-1]
        # same line if vertical extents overlap substantially
        ov = min(cur["y1"], it["y1"]) - max(cur["y0"], it["y0"])
        h = min(cur["y1"] - cur["y0"], it["y1"] - it["y0"])
        if h > 0 and ov / h > 0.55 and abs(it["y0"] - cur["y0"]) < 26:
            cur["parts"].append(it)
            cur["y0"] = min(cur["y0"], it["y0"])
            cur["y1"] = max(cur["y1"], it["y1"])
            cur["x1"] = max(cur["x1"], it["x1"])
            placed = True
    if not placed:
        lines.append({"y0": it["y0"], "y1": it["y1"], "x0": it["x0"], "x1": it["x1"], "parts": [it]})

# ---------- 2. join fragments with gap-aware spacing ----------
def join(parts):
    parts = sorted(parts, key=lambda p: p["x0"])
    out = parts[0]["t"]
    prev_x1 = parts[0]["x1"]
    for p in parts[1:]:
        gap = p["x0"] - prev_x1
        if gap <= 6:
            out += p["t"]
        elif gap <= 34:
            out += p["t"]
        else:
            out += " " + p["t"]
        prev_x1 = max(prev_x1, p["x1"])
    return out

rows = []
for ln in lines:
    rows.append({"y": round(ln["y0"], 1), "x": round(ln["x0"], 1), "x1": round(ln["x1"], 1),
                 "t": join(ln["parts"]), "n": len(ln["parts"])})

# ---------- 3. drop rotated / vertical UI chrome ----------
def is_vertical(r):
    return (r["x1"] - r["x"]) < 120 and len(r["t"]) <= 3 and r["t"] in "1234567890"

clean = [r for r in rows if not is_vertical(r)]
print("lines:", len(clean))

json.dump(clean, open(os.path.join(OUT, "lines.json"), "w", encoding="utf-8"), ensure_ascii=False)
with open(os.path.join(OUT, "lines.txt"), "w", encoding="utf-8") as f:
    for r in clean:
        f.write(f"[y={int(r['y']):5d} x={int(r['x']):4d}] {r['t']}\n")
print("saved lines.json / lines.txt")

# quick structural counts
MARK = re.compile(r"[【\[]\s*(单选题|多选题|判断题)")
SEC = re.compile(r"^[一二三四五六七八九十]{1,3}\s*[\.、．,，]?\s*(单选题|多选题|判断题|多选|单选|判断)")
MINE = re.compile(r"我的答案")
SCORE = re.compile(r"^0?[\d]{1,3}\s*[\.．]?\d*\s*分$")
print("qmark:", sum(1 for r in clean if MARK.search(r["t"])))
print("sec:", sum(1 for r in clean if SEC.match(r["t"]) and len(r["t"]) < 34))
print("mine:", sum(1 for r in clean if MINE.match(r["t"])))
print("score:", sum(1 for r in clean if SCORE.match(r["t"])))
print("anslet:", sum(1 for r in clean if re.fullmatch(r"[ABCD]{1,4}", r["t"].strip())))
