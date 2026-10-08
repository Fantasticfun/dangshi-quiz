# 党史题库 · 刷题练习

一个纯静态的党史知识刷题网站。题目取自《党史题库》PDF（扫描件，178 页），
经 OCR 提取与结构化整理后，按教材单元分类，支持**按单元自选刷题**并
**逐题记录正确 / 错误次数**。

**在线访问：** https://fantasticfun.github.io/dangshi-quiz/

---

## 功能

| 功能 | 说明 |
| --- | --- |
| 按单元分类刷题 | 按 16 个章节组、69 个单元归类，可自选任意单元开始练习 |
| 逐题记录对错 | 每道题分别累计答对 / 答错次数，实时写入浏览器本地存储 |
| 错题本 | 自动汇总做错过的题目，支持「重做全部错题」「重做错得最多的 20 题」 |
| 学习统计 | 总体正确率、已做 / 未做数量，以及分章正确率明细 |
| 三种题型 | 单选题、多选题、判断题；多选题自动判分 |
| 搜索与筛选 | 关键词搜索题干与选项，可筛选「只看做错过」「只看没做过」 |
| 随机练习 | 从符合筛选条件的题目中随机抽取 20 题 |
| 其他 | 深色模式、键盘快捷键、移动端适配、无需联网即可使用 |

## 使用

直接用浏览器打开 `index.html` 即可，**无需服务端、无需构建**。

若要本地起静态服务器：

```bash
python -m http.server 8000
# 访问 http://localhost:8000
```

### 快捷键

| 按键 | 作用 |
| --- | --- |
| `A` `B` `C` `D` | 选择选项（多选题可多选，再按 `Enter` 提交） |
| `1` / `T`、`2` / `F` | 判断题选「正确」/「错误」 |
| `Enter` | 提交多选题答案 / 进入下一题 |
| `←` `→` | 上一题 / 下一题 |

## 目录结构

```
index.html        页面结构（GitHub Pages 入口）
style.css         样式（含深色模式、移动端适配）
app.js            应用逻辑（刷题、判分、统计、错题本）
questions.js      题库数据
.nojekyll         关闭 Jekyll 处理
site/             与根目录相同的站点文件副本
tools/            题库提取与构建脚本
README.md
```

> 根目录文件是 GitHub Pages 直接发布的内容；`site/` 保留一份同样的副本，
> 便于本地直接打开 `site/index.html` 调试。修改时请同时更新两处，或只改一处后
> 用 `copy site\* .` 同步。

## 题库说明

- 共 **374 道题**，分布在 **69 个单元**中（16 个章节组）。
- 原始 PDF 中**只有多选题记录了答案**（形如「我的答案：ABCD」）。
- 为让单选题和判断题也能自动判分，这些题目的答案**依据中共党史知识补录**，
  在数据中标记为 `"ak": "kb"`，作答后界面会提示「本答案依据党史知识补录，请以教材为准」。
- 原件是扫描图，文字经 OCR 识别。已对常见识别错误做系统修正
  （如「战净」→「战争」、「戊成」→「戊戌」、「古由会议」→「古田会议」），
  但个别字词仍可能有误，请以教材为准。

## 数据结构

`questions.js` 导出：

```js
window.QUIZ_DATA = {
  units: [
    { no: "1.2", title: "各种力量的艰难探索", chapter: 1 },
    // ...
  ],
  questions: [
    { u: "1.2", t: "single", q: "题干……", o: ["A项", "B项", "C项", "D项"], a: "B", ak: "kb" },
    { u: "1.2", t: "multi",  q: "题干……", o: ["A项", "B项", "C项", "D项"], a: "ABCD" },
    { u: "1.3", t: "judge",  q: "题干……", a: "T" }
  ]
};
```

| 字段 | 含义 |
| --- | --- |
| `u` | 所属单元号，对应 `units[].no` |
| `t` | 题型：`single` 单选 / `multi` 多选 / `judge` 判断 |
| `q` | 题干 |
| `o` | 选项数组（判断题省略） |
| `a` | 答案：单选为单个字母，多选为多个字母，判断为 `T`/`F`；缺省表示无答案 |
| `ak` | 答案来源：`"kb"` 表示依据党史知识补录；缺省表示原件自带 |

学习记录保存在浏览器 `localStorage` 的 `dsq_stats_v1` 键：

```json
{ "q1": { "c": 3, "w": 1, "t": 1789486058510 } }
```

`c` = 答对次数，`w` = 答错次数，`t` = 最近作答时间戳。

## 重新生成题库

原始 PDF 是「一张 785 × 29219 像素的长图切成 178 页」，脚本按以下顺序处理：

```bash
python tools/render_all.py        # 1. 将 PDF 每页渲染为 PNG（pages/）
python tools/ocr_all.py           # 2. RapidOCR 识别每页文字（ocr/），约 7 分钟
python tools/parse6.py            # 3. 结构化解析 → build/questions_final.json
python tools/repair.py            # 4. 对选项缺失的题目做定点重新 OCR → questions_repaired.json
python tools/postfix2.py          # 5. 清理混入题干的选项 → questions_final3.json
python tools/postfix.py           # 6. 收紧题干与选项边界 → questions_final4.json
python tools/build_site_data2.py  # 7. 生成 questions.js（根目录与 site/）
python tools/finalize.py          # 8. 剔除仍不完整的题目，输出最终 questions.js
python tools/final_check.py       # 9. 数据完整性自检
```

依赖：

```bash
pip install pdfplumber opencv-python rapidocr-onnxruntime numpy Pillow esprima
```

校验脚本：

```bash
python tools/check_js.py          # JavaScript 语法检查
python tools/read_log.py          # 读取浏览器测试日志
python tools/make_final_test.py   # 生成浏览器端端到端测试页
```

## 浏览器端测试

`tools/make_final_test.py` 会生成一个页面，在真实浏览器里驱动整套流程
（展开单元 → 开始刷题 → 选择答案 → 自评 → 记录统计 → 错题本 → 搜索），
并用无头 Chrome 执行：

```bash
chrome --headless=new --allow-file-access-from-files \
       --virtual-time-budget=12000 --dump-dom build/final/final.html
```

## 许可

题库内容版权归原作者所有，本仓库仅作学习练习用途。
