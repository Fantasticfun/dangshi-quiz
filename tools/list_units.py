import sys, os, json, re
sys.stdout.reconfigure(encoding='utf-8')
BASE = r"C:\Users\13083\Desktop\dangshi-quiz"
src = open(os.path.join(BASE, "questions.js"), encoding="utf-8").read()
data = json.loads(re.search(r"window\.QUIZ_DATA\s*=\s*(?P<d>\{.*\});\s*$", src, re.S).group("d"))
for u in data["units"]:
    print(f'{u["chapter"]:>3} {u["no"]:>5}  {u["title"]}')
