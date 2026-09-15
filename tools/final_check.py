import sys, os, json, re
sys.stdout.reconfigure(encoding='utf-8')
src = open(r"C:\Users\13083\Desktop\dangshi-quiz\questions.js", encoding="utf-8").read()
data = json.loads(re.search(r"window\.QUIZ_DATA\s*=\s*(\{.*\});\s*$", src, re.S).group(1))
qs = data["questions"]
LET = "ABCD"

print("q:", len(qs), "units:", len(data["units"]))
from collections import Counter
print("types:", Counter(q["t"] for q in qs))
print("option lens:", Counter(len(q.get("o", [])) for q in qs if q["t"] != "judge"))

# answer must fit the available options
bad = []
for q in qs:
    a = q.get("a")
    if not a: continue
    o = q.get("o") or []
    if any(LET.index(c) >= len(o) for c in a):
        bad.append((q["u"], a, len(o), q["q"][:50]))
print("answers referencing missing options:", len(bad))
for b in bad: print("   ", b)

# answers must be non-empty option text
bad2 = [q for q in qs if q.get("a") and any(not (q.get("o") or ["", "", "", ""])[LET.index(c)].strip() for c in q["a"])]
print("answers pointing at empty option text:", len(bad2))
for q in bad2[:5]: print("   ", q["u"], q["a"], q["q"][:50], q.get("o"))

# short stems
short = [q for q in qs if len(q["q"]) < 10]
print("short stems:", len(short))
for q in short: print("   ", q["u"], q["t"], "|", q["q"])

# very long stems (possible runaway merge)
longst = [q for q in qs if len(q["q"]) > 200]
print("stems >200 chars:", len(longst))
for q in longst[:4]: print("   ", q["u"], len(q["q"]), q["q"][:90])

# empty option text anywhere
emp = [(q["u"], i) for q in qs if q["t"] != "judge" for i, o in enumerate(q.get("o") or []) if not o.strip()]
print("empty option slots:", len(emp))
