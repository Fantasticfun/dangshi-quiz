/* ============================================================
   党史题库 · 刷题练习
   纯静态站点，无依赖，可直接以 file:// 打开
   ============================================================ */
(function () {
  'use strict';

  var DATA = (window.QUIZ_DATA || { units: [], questions: [] });
  var UNITS = DATA.units || [];
  var QUESTIONS = (DATA.questions || []).map(function (q, i) {
    return {
      id: 'q' + (i + 1),
      idx: i,
      unit: q.u,
      type: q.t,                 // single | multi | judge
      stem: q.q,
      options: q.o || null,      // array for single/multi, null for judge
      answer: q.a || ''          // '' when the source PDF carried no answer key
    };
  });

  var CHAPTER_TITLES = {
    0: '绪论 · 综合练习',
    1: '第一章 · 中国共产党的创建和投身大革命的洪流（一）',
    2: '第一章 · 中国共产党的创建和投身大革命的洪流（二）',
    3: '第二章 · 掀起土地革命的风暴（一）',
    4: '第二章 · 掀起土地革命的风暴（二）',
    5: '第三章 · 全民族抗日战争的中流砥柱（一）',
    6: '第三章 · 全民族抗日战争的中流砥柱（二）',
    7: '第四章 · 夺取新民主主义革命的全国性胜利',
    8: '第五章 · 中华人民共和国的成立和社会主义制度的建立',
    9: '第六章 · 社会主义建设的探索和曲折发展',
    10: '第七章 · 改革开放的起步与伟大转折',
    11: '第八章 · 改革开放的全面展开',
    12: '第九章 · 把中国特色社会主义推向 21 世纪',
    13: '第十章 · 建立社会主义市场经济体制',
    14: '第十一章 · 全面建设小康社会与推动科学发展',
    15: '第十二章 · 中国特色社会主义进入新时代'
  };
  var UNIT_TITLE = {};
  UNITS.forEach(function (u) { UNIT_TITLE[u.no] = u.title; });

  var TYPE_NAME = { single: '单选题', multi: '多选题', judge: '判断题' };
  var LETTERS = ['A', 'B', 'C', 'D', 'E', 'F'];

  /* ================= 存储层 ================= */
  var KEY = 'dsq_stats_v1';
  var KEY_THEME = 'dsq_theme_v1';
  var store = { stats: {} };

  function load() {
    try {
      var raw = localStorage.getItem(KEY);
      if (raw) store.stats = JSON.parse(raw) || {};
    } catch (e) { store.stats = {}; }
  }
  var saveTimer = null;
  function writeNow() {
    try { localStorage.setItem(KEY, JSON.stringify(store.stats)); } catch (e) {}
  }
  function save() {
    writeNow();                       // persist synchronously so no answer is ever lost
    if (saveTimer) clearTimeout(saveTimer);
    saveTimer = setTimeout(function () { saveTimer = null; writeNow(); }, 400);
  }
  function statOf(id) {
    var s = store.stats[id];
    if (!s) { s = { c: 0, w: 0, t: 0 }; store.stats[id] = s; }
    return s;
  }
  function record(id, correct) {
    var s = statOf(id);
    if (correct) s.c++; else s.w++;
    s.t = Date.now();
    save();
  }
  function resetAll() {
    store.stats = {};
    try { localStorage.removeItem(KEY); } catch (e) {}
  }

  /* ================= 工具 ================= */
  function $(sel) { return document.querySelector(sel); }
  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  function shuffle(a) {
    a = a.slice();
    for (var i = a.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var t = a[i]; a[i] = a[j]; a[j] = t;
    }
    return a;
  }
  function pct(c, w) {
    var n = c + w;
    return n ? Math.round((c / n) * 100) : 0;
  }
  function toast(msg) {
    var t = $('#toast');
    t.textContent = msg;
    t.classList.remove('hidden');
    clearTimeout(toast._t);
    toast._t = setTimeout(function () { t.classList.add('hidden'); }, 1800);
  }

  /* ================= 统计聚合 ================= */
  function unitAgg(unitNo) {
    var qs = QUESTIONS.filter(function (q) { return q.unit === unitNo; });
    var done = 0, right = 0, wrong = 0, wrongIds = [];
    qs.forEach(function (q) {
      var s = store.stats[q.id];
      if (!s || (s.c === 0 && s.w === 0)) return;
      done++;
      right += s.c; wrong += s.w;
      if (s.w > 0) wrongIds.push(q.id);
    });
    return { total: qs.length, done: done, right: right, wrong: wrong, wrongIds: wrongIds };
  }
  function chapterAgg(ch) {
    var units = UNITS.filter(function (u) { return u.chapter === ch; });
    var agg = { total: 0, done: 0, right: 0, wrong: 0, wrongIds: [] };
    units.forEach(function (u) {
      var a = unitAgg(u.no);
      agg.total += a.total; agg.done += a.done;
      agg.right += a.right; agg.wrong += a.wrong;
      agg.wrongIds = agg.wrongIds.concat(a.wrongIds);
    });
    return agg;
  }
  function globalAgg() {
    var agg = { total: QUESTIONS.length, done: 0, right: 0, wrong: 0, wrongIds: [] };
    QUESTIONS.forEach(function (q) {
      var s = store.stats[q.id];
      if (!s || (s.c === 0 && s.w === 0)) return;
      agg.done++;
      agg.right += s.c; agg.wrong += s.w;
      if (s.w > 0) agg.wrongIds.push(q.id);
    });
    return agg;
  }

  /* ================= 视图切换 ================= */
  var views = ['home', 'quiz', 'stats'];
  function show(name) {
    views.forEach(function (v) {
      $('#view-' + v).classList.toggle('hidden', v !== name);
    });
    window.scrollTo({ top: 0, behavior: 'instant' in window ? 'instant' : 'auto' });
  }

  /* ================= 首页 ================= */
  var openChapters = {};

  function renderHome() {
    var g = globalAgg();
    var hs = $('#heroStats');
    hs.innerHTML = '';
    [
      [QUESTIONS.length, '题库总题数'],
      [g.done, '已做题目'],
      [g.right, '累计答对'],
      [g.wrong, '累计答错'],
      [g.done ? pct(g.right, g.wrong) + '%' : '—', '正确率']
    ].forEach(function (pair) {
      var d = el('div', 'stat-pill');
      d.appendChild(el('b', null, String(pair[0])));
      d.appendChild(el('span', null, pair[1]));
      hs.appendChild(d);
    });

    var answered = QUESTIONS.filter(function (q) { return q.answer; }).length;
    $('#dataHint').textContent =
      '共 ' + QUESTIONS.length + ' 道题 · ' + UNITS.length + ' 个单元 · 其中 ' + answered +
      ' 道多选题在原始 PDF 中带有答案，可自动判分；其余题目请作答后对照解析自评。';

    renderTree('');
    $('#searchResults').classList.add('hidden');
    $('#unitTree').classList.remove('hidden');
    updateWrongBadge();
  }

  function matchFilter(q) {
    var onlyWrong = $('#onlyWrongFilter').checked;
    var onlyUnseen = $('#onlyUnseenFilter').checked;
    var s = store.stats[q.id] || { c: 0, w: 0 };
    if (onlyWrong && !(s.w > 0)) return false;
    if (onlyUnseen && (s.c > 0 || s.w > 0)) return false;
    return true;
  }

  function renderTree(keyword) {
    var tree = $('#unitTree');
    tree.innerHTML = '';
    var chapters = Object.keys(CHAPTER_TITLES).map(Number).sort(function (a, b) { return a - b; });
    var anyUnit = false;

    chapters.forEach(function (ch) {
      var units = UNITS.filter(function (u) { return u.chapter === ch; });
      var body = el('div', 'chapter-body');
      var unitCount = 0;

      units.forEach(function (u) {
        var qs = QUESTIONS.filter(function (q) {
          return q.unit === u.no && matchFilter(q);
        });
        if (!qs.length) return;
        unitCount++;
        anyUnit = true;

        var a = unitAgg(u.no);
        var row = el('div', 'unit');

        var no = el('span', 'unit-no', u.no);
        var title = el('span', 'unit-title', u.title);
        var meta = el('div', 'unit-meta');
        meta.appendChild(el('span', 'tag', qs.length + ' 题'));
        if (a.done) {
          meta.appendChild(el('span', 'tag ok', '✓ ' + a.right));
          if (a.wrong) meta.appendChild(el('span', 'tag bad', '✗ ' + a.wrong));
          meta.appendChild(el('span', 'rate', '正确率 ' + pct(a.right, a.wrong) + '%'));
        } else {
          meta.appendChild(el('span', 'tag', '未练习'));
        }

        var acts = el('div', 'unit-actions');
        var bAll = el('button', 'btn btn-sm btn-primary', '刷题');
        bAll.onclick = function () { startQuiz(qs.map(function (q) { return q.id; }), u.no + ' ' + u.title); };
        acts.appendChild(bAll);
        if (a.wrongIds.length) {
          var bW = el('button', 'btn btn-sm', '错题 ' + a.wrongIds.length);
          bW.onclick = function () {
            var ids = a.wrongIds.filter(function (id) {
              var q = QUESTIONS.find(function (x) { return x.id === id; });
              return q && matchFilter(q);
            });
            if (!ids.length) return toast('该单元没有符合条件的错题');
            startQuiz(ids, u.no + ' 错题重做');
          };
          acts.appendChild(bW);
        }

        row.appendChild(no); row.appendChild(title); row.appendChild(meta); row.appendChild(acts);
        body.appendChild(row);
      });

      if (!unitCount) return;

      var ca = chapterAgg(ch);
      var wrap = el('div', 'chapter' + (openChapters[ch] || keyword ? ' open' : ''));
      var head = el('div', 'chapter-head');
      head.appendChild(el('span', 'arrow', '▶'));
      head.appendChild(el('span', 'ch-title', CHAPTER_TITLES[ch]));
      var pm = el('div', 'progress-mini');
      var pi = el('i');
      pi.style.width = (ca.total ? Math.round((ca.done / ca.total) * 100) : 0) + '%';
      pm.appendChild(pi);
      head.appendChild(pm);
      head.appendChild(el('span', 'ch-count', ca.done + '/' + ca.total));
      head.onclick = function () {
        openChapters[ch] = !wrap.classList.contains('open');
        wrap.classList.toggle('open');
      };
      wrap.appendChild(head);
      wrap.appendChild(body);
      tree.appendChild(wrap);
    });

    if (!anyUnit) {
      tree.appendChild(el('div', 'empty', '没有符合条件的题目。试试调整筛选条件。'));
    }
  }

  function renderSearch(kw) {
    var box = $('#searchResults');
    var tree = $('#unitTree');
    kw = kw.trim();
    if (!kw) {
      box.classList.add('hidden');
      tree.classList.remove('hidden');
      renderTree('');
      return;
    }
    tree.classList.add('hidden');
    box.classList.remove('hidden');
    box.innerHTML = '';

    var hits = QUESTIONS.filter(function (q) {
      if (!matchFilter(q)) return false;
      if (q.stem.indexOf(kw) >= 0) return true;
      if (q.options) {
        for (var i = 0; i < q.options.length; i++) {
          if ((q.options[i] || '').indexOf(kw) >= 0) return true;
        }
      }
      return false;
    });

    if (!hits.length) {
      box.appendChild(el('div', 'empty', '没有找到包含「' + kw + '」的题目。'));
      return;
    }
    box.appendChild(el('div', 'hint', '找到 ' + hits.length + ' 道题 · 点击任意题目开始该题所在单元的练习'));
    hits.slice(0, 200).forEach(function (q) {
      var item = el('div', 'res-item');
      item.appendChild(el('div', 'res-unit', q.unit + ' ' + (UNIT_TITLE[q.unit] || '') + ' · ' + TYPE_NAME[q.type]));
      var d = el('div', 'res-q');
      d.innerHTML = highlight(q.stem, kw);
      item.appendChild(d);
      item.onclick = function () { startQuiz([q.id], '搜索练习：' + kw); };
      box.appendChild(item);
    });
    if (hits.length > 200) box.appendChild(el('div', 'hint', '仅显示前 200 条，请缩小关键词范围。'));
  }

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }
  function highlight(text, kw) {
    var t = esc(text);
    var k = esc(kw).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    try { return t.replace(new RegExp(k, 'gi'), function (m) { return '<mark>' + m + '</mark>'; }); }
    catch (e) { return t; }
  }

  /* ================= 刷题 ================= */
  var quiz = null;

  function startQuiz(ids, title) {
    var qs = ids.map(function (id) {
      return QUESTIONS.find(function (q) { return q.id === id; });
    }).filter(Boolean);
    if (!qs.length) return toast('没有可练习的题目');
    quiz = {
      title: title || '随机练习',
      list: qs,
      pos: 0,
      picked: {},        // id -> array of selected letters
      judged: {},        // id -> true/false result already recorded
      revealed: {}
    };
    $('#quizTitle').textContent = quiz.title;
    $('#btnQuick').textContent = '开始随机练习';
    show('quiz');
    renderQuestion();
  }

  function startRandom() {
    var pool = QUESTIONS.filter(matchFilter);
    if (!pool.length) return toast('没有符合条件的题目');
    var n = Math.min(pool.length, 20);
    var list = shuffle(pool).slice(0, n);
    startQuiz(list.map(function (q) { return q.id; }), '随机练习 · ' + n + ' 题');
  }

  function currentQ() { return quiz.list[quiz.pos]; }

  function renderQuestion() {
    var q = currentQ();
    if (!q) return;
    var card = $('#qCard');
    card.innerHTML = '';
    $('#qResult').innerHTML = '';

    $('#quizCounter').textContent = (quiz.pos + 1) + ' / ' + quiz.list.length;
    $('#progressBar').style.width = Math.round(((quiz.pos + 1) / quiz.list.length) * 100) + '%';

    var meta = el('div', 'q-meta');
    meta.appendChild(el('span', 'q-type ' + (q.type === 'multi' ? 'multi' : q.type === 'judge' ? 'judge' : ''),
      TYPE_NAME[q.type]));
    meta.appendChild(el('span', 'q-source', q.unit + ' ' + (UNIT_TITLE[q.unit] || '')));
    var s = store.stats[q.id];
    if (s && (s.c || s.w)) {
      meta.appendChild(el('span', 'q-badge ok', '对 ' + s.c));
      meta.appendChild(el('span', 'q-badge bad', '错 ' + s.w));
    }
    card.appendChild(meta);
    card.appendChild(el('p', 'q-stem', q.stem));

    var picked = quiz.picked[q.id] || [];
    var revealed = quiz.revealed[q.id];

    if (q.type === 'judge' || !q.options) {
      var jo = el('div', 'judge-opts');
      [['T', '正确'], ['F', '错误']].forEach(function (pair) {
        var b = el('button', 'opt');
        b.appendChild(el('span', 'opt-key', pair[0] === 'T' ? '✓' : '✗'));
        b.appendChild(el('span', 'opt-text', pair[1]));
        if (picked.indexOf(pair[0]) >= 0) b.classList.add('sel');
        b.onclick = function () { pick(q, pair[0], true); };
        jo.appendChild(b);
      });
      card.appendChild(jo);
    } else {
      var wrap = el('div', 'opts');
      q.options.forEach(function (text, i) {
        if (!text) return;
        var L = LETTERS[i];
        var b = el('button', 'opt');
        b.appendChild(el('span', 'opt-key', L));
        b.appendChild(el('span', 'opt-text', text));
        if (picked.indexOf(L) >= 0) b.classList.add('sel');
        if (revealed) markOption(b, L, q);
        // 只有带答案（多选题）才即时判分；单选题选完直接进入自评
        b.onclick = function () { pick(q, L, true); };
        wrap.appendChild(b);
      });
      card.appendChild(wrap);
    }

    $('#btnPrev').disabled = quiz.pos === 0;
    $('#btnNext').textContent = quiz.pos === quiz.list.length - 1 ? '完成练习' : '下一题';
    $('#btnReveal').classList.toggle('hidden', !!quiz.judged[q.id]);

    if (revealed) renderResult(q);
  }

  function markOption(btn, L, q) {
    btn.classList.add('locked');
    if (q.answer.indexOf(L) >= 0) btn.classList.add('correct');
    else if ((quiz.picked[q.id] || []).indexOf(L) >= 0) btn.classList.add('wrong');
  }

  function pick(q, L, autoSubmit) {
    if (quiz.revealed[q.id]) return;
    var picked = quiz.picked[q.id] || (quiz.picked[q.id] = []);
    if (q.type === 'multi') {
      var i = picked.indexOf(L);
      if (i >= 0) picked.splice(i, 1); else picked.push(L);
      renderQuestion();
      return;
    }
    quiz.picked[q.id] = [L];
    if (autoSubmit) grade(q);
    else renderQuestion();
  }

  /* 判分：PDF 中带答案的题目自动判分；其余题目由使用者自评 */
  function grade(q) {
    var picked = quiz.picked[q.id] || [];
    if (!picked.length) return;
    var revealed = true;
    quiz.revealed[q.id] = true;

    if (q.answer) {
      var ok = picked.slice().sort().join('') === q.answer.split('').sort().join('');
      if (!quiz.judged[q.id]) { record(q.id, ok); quiz.judged[q.id] = true; }
      renderQuestion();
      renderResult(q, ok);
    } else {
      renderQuestion();
      renderResult(q, null);
    }
  }

  function renderResult(q, autoOk) {
    var box = $('#qResult');
    box.innerHTML = '';
    var picked = quiz.picked[q.id] || [];
    var pickedText = picked.length ? picked.slice().sort().join('') : '未作答';

    if (q.answer) {
      var ok = (autoOk != null) ? autoOk
        : picked.slice().sort().join('') === q.answer.split('').sort().join('');
      var v = el('div', 'verdict ' + (ok ? 'ok' : 'bad'));
      v.innerHTML = ok
        ? '<strong>✓ 回答正确</strong>'
        : '<strong>✗ 回答错误</strong>';
      box.appendChild(v);

      var line = el('div', 'answer-line');
      line.innerHTML = '你的答案：<strong>' + esc(pickedText) + '</strong>　·　' +
        '题库答案：<strong>' + esc(q.answer) + '</strong>';
      box.appendChild(line);

      if (!ok && q.options) {
        var exp = el('div', 'answer-line');
        var parts = q.answer.split('').map(function (L) {
          var i = LETTERS.indexOf(L);
          return L + '. ' + (q.options[i] || '');
        });
        exp.innerHTML = '正确答案为：' + esc(parts.join('　'));
        box.appendChild(exp);
      }
    } else {
      var v2 = el('div', 'verdict info');
      v2.innerHTML = '原始 PDF 未收录本题答案。请对照资料判断，然后如实记录结果 —— 记录会累计到统计与错题本。';
      box.appendChild(v2);

      var line2 = el('div', 'answer-line');
      line2.innerHTML = '你的答案：<strong>' + esc(pickedText) + '</strong>';
      box.appendChild(line2);

      var sg = el('div', 'self-grade');
      sg.appendChild(el('span', null, '本题我答：'));
      var bOk = el('button', 'btn btn-sm', '✓ 对了');
      var bBad = el('button', 'btn btn-sm', '✗ 错了');
      var done = quiz.judged[q.id];
      bOk.disabled = !!done; bBad.disabled = !!done;
      bOk.onclick = function () { selfGrade(q, true); };
      bBad.onclick = function () { selfGrade(q, false); };
      sg.appendChild(bOk); sg.appendChild(bBad);
      if (quiz.judged[q.id]) sg.appendChild(el('span', null, '已记录'));
      box.appendChild(sg);
    }
  }

  function selfGrade(q, correct) {
    if (quiz.judged[q.id]) return;
    record(q.id, correct);
    quiz.judged[q.id] = true;
    toast(correct ? '已记为答对' : '已记为答错，已加入错题本');
    renderQuestion();
    renderResult(q, null);
    updateWrongBadge();
  }

  function nextQ() {
    if (quiz.pos >= quiz.list.length - 1) {
      var s = summaryOf(quiz.list);
      toast('练习完成：' + s.done + ' 题已记录，正确率 ' + (s.done ? pct(s.right, s.wrong) + '%' : '—'));
      show('home');
      renderHome();
      return;
    }
    quiz.pos++;
    renderQuestion();
  }

  function summaryOf(list) {
    var right = 0, wrong = 0, done = 0;
    list.forEach(function (q) {
      var s = store.stats[q.id];
      if (!s) return;
      if (s.c || s.w) done++;
      right += s.c; wrong += s.w;
    });
    return { right: right, wrong: wrong, done: done };
  }

  /* ================= 错题本 ================= */
  function openWrongBook() {
    var rows = [];
    QUESTIONS.forEach(function (q) {
      var s = store.stats[q.id];
      if (s && s.w > 0) rows.push({ q: q, s: s });
    });
    rows.sort(function (a, b) { return b.s.w - a.s.w || b.s.t - a.s.t; });

    var body = $('#statsBody');
    body.innerHTML = '';
    body.appendChild(el('h2', 'page-title', '错题本（' + rows.length + ' 题）'));
    if (!rows.length) {
      body.appendChild(el('div', 'empty', '还没有错题记录。开始刷题吧！'));
    } else {
      var bar = el('div', 'toolbar');
      var bAll = el('button', 'btn btn-primary btn-sm', '重做全部错题');
      bAll.onclick = function () {
        startQuiz(rows.map(function (r) { return r.q.id; }), '错题重做 · ' + rows.length + ' 题');
      };
      var bTop = el('button', 'btn btn-sm', '重做错得最多的 20 题');
      bTop.onclick = function () {
        var ids = rows.slice(0, 20).map(function (r) { return r.q.id; });
        startQuiz(ids, '高频错题 · ' + ids.length + ' 题');
      };
      bar.appendChild(bAll); bar.appendChild(bTop);
      body.appendChild(bar);

      var wrap = el('div', 'table-wrap');
      var t = el('table');
      var thead = el('thead');
      var htr = el('tr');
      ['单元', '题型', '题目', '错', '对'].forEach(function (h) { htr.appendChild(el('th', null, h)); });
      thead.appendChild(htr); t.appendChild(thead);
      var tb = el('tbody');
      rows.forEach(function (r) {
        var tr = el('tr');
        tr.appendChild(el('td', null, r.q.unit));
        tr.appendChild(el('td', null, TYPE_NAME[r.q.type]));
        var tdq = el('td');
        var a = el('a', null, r.q.stem.length > 42 ? r.q.stem.slice(0, 42) + '…' : r.q.stem);
        a.href = 'javascript:void(0)';
        a.onclick = function () { startQuiz([r.q.id], '错题重做'); };
        tdq.appendChild(a);
        tr.appendChild(tdq);
        tr.appendChild(el('td', 'num', String(r.s.w)));
        tr.appendChild(el('td', 'num', String(r.s.c)));
        tb.appendChild(tr);
      });
      t.appendChild(tb); wrap.appendChild(t); body.appendChild(wrap);
    }
    show('stats');
  }

  function updateWrongBadge() {
    var n = 0;
    QUESTIONS.forEach(function (q) {
      var s = store.stats[q.id];
      if (s && s.w > 0) n++;
    });
    var b = $('#wrongBadge');
    b.textContent = String(n);
    b.classList.toggle('hidden', n === 0);
  }

  /* ================= 统计页 ================= */
  function openStats() {
    var g = globalAgg();
    var body = $('#statsBody');
    body.innerHTML = '';
    body.appendChild(el('h2', 'page-title', '学习统计'));

    var grid = el('div', 'stat-grid');
    [
      [g.total, '题库总题数'],
      [g.done, '已练习题数'],
      [g.total - g.done, '未练习题数'],
      [g.right, '累计答对'],
      [g.wrong, '累计答错'],
      [g.done ? pct(g.right, g.wrong) + '%' : '—', '总体正确率']
    ].forEach(function (p) {
      var c = el('div', 'stat-card');
      c.appendChild(el('b', null, String(p[0])));
      c.appendChild(el('span', null, p[1]));
      grid.appendChild(c);
    });
    body.appendChild(grid);

    body.appendChild(el('h3', null, '分章统计'));
    var wrap = el('div', 'table-wrap');
    var t = el('table');
    var thead = el('thead'), htr = el('tr');
    ['编 / 章', '题数', '已做', '答对', '答错', '正确率'].forEach(function (h) { htr.appendChild(el('th', null, h)); });
    thead.appendChild(htr); t.appendChild(thead);
    var tb = el('tbody');
    Object.keys(CHAPTER_TITLES).map(Number).sort(function (a, b) { return a - b; }).forEach(function (ch) {
      var a = chapterAgg(ch);
      if (!a.total) return;
      var tr = el('tr');
      tr.appendChild(el('td', null, CHAPTER_TITLES[ch]));
      tr.appendChild(el('td', 'num', String(a.total)));
      tr.appendChild(el('td', 'num', String(a.done)));
      tr.appendChild(el('td', 'num', String(a.right)));
      tr.appendChild(el('td', 'num', String(a.wrong)));
      tr.appendChild(el('td', 'num', a.done ? pct(a.right, a.wrong) + '%' : '—'));
      tb.appendChild(tr);
    });
    t.appendChild(tb); wrap.appendChild(t); body.appendChild(wrap);

    body.appendChild(document.querySelector('.danger-zone'));
    show('stats');
  }

  /* ================= 事件绑定 ================= */
  function bind() {
    $('#btnHome').onclick = function () { show('home'); renderHome(); };
    $('#btnStats').onclick = openStats;
    $('#btnWrong').onclick = openWrongBook;
    $('#btnWrongHero').onclick = openWrongBook;
    $('#btnQuick').onclick = startRandom;
    $('#btnQuit').onclick = function () { show('home'); renderHome(); };
    $('#btnPrev').onclick = function () { if (quiz.pos > 0) { quiz.pos--; renderQuestion(); } };
    $('#btnNext').onclick = nextQ;
    $('#btnReveal').onclick = function () {
      var q = currentQ();
      if (!q) return;
      quiz.revealed[q.id] = true;
      if (!quiz.judged[q.id]) { record(q.id, false); quiz.judged[q.id] = true; }
      renderQuestion();
      renderResult(q, false);
      updateWrongBadge();
    };

    $('#btnExpandAll').onclick = function () {
      Object.keys(CHAPTER_TITLES).forEach(function (ch) { openChapters[ch] = true; });
      renderTree('');
    };
    $('#btnCollapseAll').onclick = function () {
      Object.keys(CHAPTER_TITLES).forEach(function (ch) { openChapters[ch] = false; });
      renderTree('');
    };

    var si = $('#searchInput');
    var st = null;
    si.oninput = function () {
      clearTimeout(st);
      st = setTimeout(function () { renderSearch(si.value); }, 160);
    };
    $('#onlyWrongFilter').onchange = function () { renderSearch(si.value); };
    $('#onlyUnseenFilter').onchange = function () { renderSearch(si.value); };

    $('#btnResetStats').onclick = function () {
      if (!confirm('确定要清空全部做题记录吗？此操作不可撤销。')) return;
      resetAll();
      toast('已清空全部记录');
      renderHome();
      show('home');
    };

    $('#btnTheme').onclick = function () {
      var cur = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', cur);
      try { localStorage.setItem(KEY_THEME, cur); } catch (e) {}
    };

    document.addEventListener('keydown', function (e) {
      if ($('#view-quiz').classList.contains('hidden')) return;
      if (e.target && /^(INPUT|TEXTAREA)$/.test(e.target.tagName)) return;
      var q = currentQ();
      if (!q) return;
      var k = e.key.toUpperCase();
      if (q.options && LETTERS.indexOf(k) >= 0 && LETTERS.indexOf(k) < q.options.length) {
        pick(q, k, q.type === 'single');
      } else if (q.type === 'judge' && (k === '1' || k === 'T')) {
        pick(q, 'T', true);
      } else if (q.type === 'judge' && (k === '2' || k === 'F')) {
        pick(q, 'F', true);
      } else if (e.key === 'Enter') {
        if (q.type === 'multi' && !quiz.revealed[q.id]) grade(q);
        else nextQ();
      } else if (e.key === 'ArrowRight') {
        nextQ();
      } else if (e.key === 'ArrowLeft') {
        if (quiz.pos > 0) { quiz.pos--; renderQuestion(); }
      }
    });

    // multi-choice submit button lives inside the result area
    document.addEventListener('click', function (e) {
      if (e.target && e.target.id === 'btnSubmitMulti') {
        var q = currentQ();
        if (q) grade(q);
      }
    });
  }

  /* multi 题需要在选项下方提供“提交答案” */
  var _origRender = renderQuestion;
  renderQuestion = function () {
    _origRender();
    var q = currentQ();
    if (!q || q.type !== 'multi' || quiz.revealed[q.id]) return;
    if ($('#qResult').children.length) return;
    var picked = quiz.picked[q.id] || [];
    var box = $('#qResult');
    var sg = el('div', 'self-grade');
    var b = el('button', 'btn btn-primary', '提交答案' + (picked.length ? '（' + picked.slice().sort().join('') + '）' : ''));
    b.id = 'btnSubmitMulti';
    b.disabled = !picked.length;
    sg.appendChild(b);
    box.appendChild(sg);
  };

  /* ================= 启动 ================= */
  function init() {
    try {
      var th = localStorage.getItem(KEY_THEME);
      if (th) document.documentElement.setAttribute('data-theme', th);
      else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        document.documentElement.setAttribute('data-theme', 'dark');
      }
    } catch (e) {}
    load();
    // make sure a pending write is never lost when the page goes away
    window.addEventListener('pagehide', writeNow);
    window.addEventListener('beforeunload', writeNow);
    document.addEventListener('visibilitychange', function () {
      if (document.visibilityState === 'hidden') writeNow();
    });
    bind();
    renderHome();
    show('home');
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
