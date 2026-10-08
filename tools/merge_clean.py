import sys, os, json, re
sys.stdout.reconfigure(encoding='utf-8')
BASE = r"C:\Users\13083\Desktop\dangshi-quiz"
LET = "ABCD"

def strip_headers(s):
    s = re.sub(r"^[^\u4e00-\u9fff]{0,4}", "", s or "")
    # remove section-header debris that OCR glued onto a stem
    s = re.sub(r"[（(【\[]?\s*共\s*\d+\s*题\s*[)）】\]]?", "", s)
    s = re.sub(r"^[（(【\[]?\s*页\s*", "", s)
    s = re.sub(r"^[一二三四五六七八九十]{1,3}\s*[\.、．,，]?\s*(单选题|多选题|判断题|多选|单选|判断)[^\u4e00-\u9fff]{0,3}", "", s)
    s = re.sub(r"^[【\[]\s*(单选题|多选题|判断题|多选|单选|判断)\s*[】\]]?", "", s)
    s = re.sub(r"^[（(]\s*(单选题|多选题|判断题|多选|单选|判断)\s*[)）]", "", s)
    return s.strip(" 　。，、；：")

def norm(s):
    s = re.sub(r"[\s，。、；：（）()【】\[\]“”\"'？！,.;:!?]", "", s or "")
    return (s.replace("〇", "0").replace("O", "0").replace("o", "0")
             .replace("０", "0").replace("Ⅰ", "1").replace("l", "1"))

js = open(os.path.join(BASE, "questions.js"), encoding="utf-8").read()
live = json.loads(re.search(r"window\.QUIZ_DATA\s*=\s*(?P<d>\{.*\});\s*$", js, re.S).group("d"))
lu = {u["no"]: u["title"] for u in live["units"]}
live_qs = [{"unit_no": q["u"], "unit_title": lu.get(q["u"], ""), "type": q["t"],
            "stem": q["q"], "options": dict(zip(LET, q["o"])) if q.get("o") else {},
            "answer": q.get("a", "")} for q in live["questions"]]

v8 = json.load(open(os.path.join(BASE, "build", "parsed_v8.json"), encoding="utf-8"))

OPT_MARK = re.compile(r"(^|\s)[ABCD]\s*[、\.．,，:：]")

def clean_and_check(q):
    stem = strip_headers(q["stem"])
    if len(stem) < 10: return None, "short"
    if "共" in stem[:12] and "题" in stem[:14]: return None, "header"
    if re.match(r"^[（(【\[]", stem): return None, "leading bracket"
    typ = q["type"]
    opts = {k: strip_headers(v) for k, v in q["options"].items() if v.strip()}
    if typ != "judge":
        if len(opts) != 4: return None, "options %d" % len(opts)
        if any(len(v) < 1 for v in opts.values()): return None, "empty option"
    if typ == "judge":
        # a judge stem must not contain option markers
        if OPT_MARK.search(stem): return None, "judge with markers"
        opts = {}
    stem = re.sub(r"\s+", "", stem)
    if len(stem) < 12: return None, "short2"
    return {"unit_no": q["unit_no"], "unit_title": q["unit_title"], "type": typ,
            "stem": stem, "options": opts, "answer": re.sub(r"[^ABCD]", "", q["answer"])}, "ok"

live_keys = {norm(strip_headers(q["stem"]))[:60] for q in live_qs}
adds, rej = [], {}
for q in v8:
    c, why = clean_and_check(q)
    rej[why] = rej.get(why, 0) + 1
    if not c: continue
    k = norm(c["stem"])[:60]
    if not k or k in live_keys: continue
    live_keys.add(k)
    adds.append(c)

print("rejection reasons:", rej)
print("clean additions:", len(adds))
from collections import Counter
print("addition types:", Counter(q["type"] for q in adds))

merged = live_qs + adds
print("\nMERGED:", len(merged), "types:", Counter(q["type"] for q in merged))
print("answers kept:", sum(1 for q in merged if q["answer"]))
print("units:", len({q["unit_no"] for q in merged}))
json.dump(merged, open(os.path.join(BASE, "build", "merged.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("saved merged.json")
print("\n=== additions sample ===")
for q in adds[:8]:
    print(f"  [{q['unit_no']} {q['type']}] {q['stem'][:74]}")
    for k in LET:
        if q["options"].get(k): print(f"      {k}. {q['options'][k][:58]}")
