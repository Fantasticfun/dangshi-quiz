import sys, re, html
sys.stdout.reconfigure(encoding='utf-8')
raw = open(r'C:\Users\13083\Desktop\dangshi-quiz\build\harness.log', encoding='utf-8', errors='replace').read()
m = re.search(r'<pre id="log">(.*?)</pre>', raw, re.S)
if m:
    print(html.unescape(m.group(1)))
else:
    print("NO LOG FOUND; dumping first 3000 chars:")
    print(raw[:3000])
