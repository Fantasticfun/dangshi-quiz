import sys, os, shutil, json
sys.stdout.reconfigure(encoding='utf-8')
BASE = r"C:\Users\13083\Desktop\dangshi-quiz"
SITE = os.path.join(BASE, "site")
TEST = os.path.join(BASE, "build", "test")
os.makedirs(TEST, exist_ok=True)
for f in ("style.css", "app.js"):
    shutil.copy(os.path.join(SITE, f), os.path.join(TEST, f))

# all four questions live in ONE unit so navigation across the whole set is exercised
data = {
    "units": [
        {"no": "1.2", "title": "各种力量的艰难探索", "chapter": 1},
        {"no": "1.3", "title": "五四运动和马克思主义的传播", "chapter": 1},
    ],
    "questions": [
        {"u": "1.2", "t": "single", "q": "单选题：近代中国社会反帝反封建斗争的主力最初是",
         "o": ["学生", "农民", "地主", "工人"]},
        {"u": "1.2", "t": "multi", "q": "多选题：学党史要达到的目的，概括起来就是",
         "o": ["学史明理", "学史增信", "学史崇德", "学史力行"], "a": "ABCD"},
        {"u": "1.2", "t": "judge", "q": "判断题：没有中国共产党，就没有新中国。"},
        {"u": "1.2", "t": "single", "q": "单选题：第四题占位",
         "o": ["甲", "乙", "丙", "丁"]},
        {"u": "1.3", "t": "multi", "q": "多选题：另一个单元的题",
         "o": ["一", "二", "三", "四"], "a": "AB"},
    ],
}
open(os.path.join(TEST, "questions.js"), "w", encoding="utf-8").write(
    "window.QUIZ_DATA = " + json.dumps(data, ensure_ascii=False) + ";\n")
shutil.copy(os.path.join(SITE, "index.html"), os.path.join(TEST, "index.html"))
print("test data written")
