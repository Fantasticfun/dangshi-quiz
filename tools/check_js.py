import sys, os
sys.stdout.reconfigure(encoding='utf-8')
import esprima

SITE = r"C:\Users\13083\Desktop\dangshi-quiz\site"
ok = True
for name in ("app.js", "questions.js"):
    p = os.path.join(SITE, name)
    src = open(p, encoding="utf-8").read()
    try:
        esprima.parseScript(src)
        print(f"OK   {name}  ({len(src)} chars)")
    except Exception as e:
        ok = False
        print(f"FAIL {name}: {e}")
sys.exit(0 if ok else 1)
