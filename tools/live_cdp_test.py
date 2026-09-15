import sys, os, json, time, urllib.request, subprocess, socket
sys.stdout.reconfigure(encoding='utf-8')

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PROFILE = r"C:\Users\13083\Desktop\dangshi-quiz\build\cp-cdp"
URL = "https://fantasticfun.github.io/dangshi-quiz/"
PORT = 9333

import shutil
shutil.rmtree(PROFILE, ignore_errors=True)

proc = subprocess.Popen([
    CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
    "--proxy-server=http://127.0.0.1:7897",
    f"--remote-debugging-port={PORT}",
    f"--user-data-dir={PROFILE}",
    "--window-size=1280,900",
    URL,
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def wait_port(port, timeout=40):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except OSError:
            time.sleep(0.5)
    return False


def http_json(path):
    with urllib.request.urlopen(f"http://127.0.0.1:{PORT}{path}", timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


if not wait_port(PORT):
    print("CDP port never opened"); proc.kill(); sys.exit(1)

# find the page target
target = None
for _ in range(40):
    tabs = http_json("/json/list")
    for t in tabs:
        if t.get("type") == "page" and "dangshi-quiz" in t.get("url", ""):
            target = t; break
    if target: break
    time.sleep(0.5)
if not target:
    tabs = http_json("/json/list")
    print("no matching page; tabs:", [(t.get('type'), t.get('url')) for t in tabs])
    proc.kill(); sys.exit(1)
print("target:", target["url"])
ws_url = target["webSocketDebuggerUrl"]

# minimal websocket client (RFC6455) implemented by hand over a socket
import base64, hashlib, struct, os as _os

class WS:
    def __init__(self, url):
        from urllib.parse import urlparse
        u = urlparse(url)
        self.sock = socket.create_connection((u.hostname, u.port), timeout=30)
        key = base64.b64encode(_os.urandom(16)).decode()
        req = (f"GET {u.path} HTTP/1.1\r\nHost: {u.hostname}:{u.port}\r\n"
               "Upgrade: websocket\r\nConnection: Upgrade\r\n"
               f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n")
        self.sock.sendall(req.encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            buf += self.sock.recv(4096)
        assert b"101" in buf.split(b"\r\n")[0], buf[:200]
        self.buf = buf.split(b"\r\n\r\n", 1)[1]
        self.mid = 0

    def _recv_exact(self, n):
        while len(self.buf) < n:
            chunk = self.sock.recv(65536)
            if not chunk: raise EOFError
            self.buf += chunk
        out, self.buf = self.buf[:n], self.buf[n:]
        return out

    def send(self, obj):
        data = json.dumps(obj).encode()
        header = bytearray([0x81])
        mask = _os.urandom(4)
        ln = len(data)
        if ln < 126: header.append(0x80 | ln)
        elif ln < 65536: header.append(0x80 | 126); header += struct.pack(">H", ln)
        else: header.append(0x80 | 127); header += struct.pack(">Q", ln)
        header += mask
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
        self.sock.sendall(bytes(header) + masked)

    def recv(self):
        while True:
            b0, b1 = self._recv_exact(2)
            op = b0 & 0x0F
            ln = b1 & 0x7F
            if ln == 126: ln = struct.unpack(">H", self._recv_exact(2))[0]
            elif ln == 127: ln = struct.unpack(">Q", self._recv_exact(8))[0]
            payload = self._recv_exact(ln)
            if op == 1:
                return json.loads(payload.decode("utf-8"))
            if op == 8:
                raise EOFError("closed")

    def call(self, method, params=None, timeout=40):
        self.mid += 1
        mid = self.mid
        self.send({"id": mid, "method": method, "params": params or {}})
        t0 = time.time()
        while time.time() - t0 < timeout:
            msg = self.recv()
            if msg.get("id") == mid:
                return msg
        raise TimeoutError(method)


ws = WS(ws_url)
ws.call("Page.enable")
ws.call("Page.navigate", {"url": URL})
import time as _t
_t.sleep(9)
ws.call("Runtime.enable")

SCRIPT = r"""
(function(){
  var out = [];
  function log(s){ out.push(String(s)); }
  try {
    log('LIVE @ ' + location.href);
    log('title=' + document.title);
    log('hero=' + [].map.call(document.querySelectorAll('.stat-pill'), function(p){return p.textContent;}).join(' | '));
    log('chapters=' + document.querySelectorAll('.chapter').length + ' units=' + document.querySelectorAll('.unit').length);

    var rows = [].slice.call(document.querySelectorAll('.unit'));
    var row = rows.filter(function(u){
      return /6 题/.test(u.querySelector('.unit-meta').textContent); })[0] || rows[0];
    log('unit=' + row.querySelector('.unit-no').textContent + ' ' + row.querySelector('.unit-title').textContent
        + ' | ' + row.querySelector('.unit-meta').textContent);
    row.querySelector('.btn-primary').click();
    log('quiz=' + document.querySelector('#quizCounter').textContent);

    var answered=0, autoGraded=0, multiSubmitted=0, selfGraded=0, seen={}, steps=0;
    for (var i=0;i<10;i++){
      var badge = document.querySelector('.q-type');
      var ty = badge ? badge.textContent : '';
      var stem = document.querySelector('.q-stem');
      if (stem) seen[stem.textContent.slice(0,24)] = 1;
      var opts = [].slice.call(document.querySelectorAll('.opts .opt'));
      var jb = [].slice.call(document.querySelectorAll('.judge-opts .opt'));
      if (opts.length){
        if (ty === '多选题'){ opts.forEach(function(o){o.click();});
          var sb=document.querySelector('#btnSubmitMulti'); if(sb && !sb.disabled){sb.click(); multiSubmitted++;} }
        else { opts[0].click(); }
        answered++;
        if (document.querySelector('.verdict')) autoGraded++;
        var sg=[].slice.call(document.querySelectorAll('.self-grade .btn'));
        if (sg.length){ sg[0].click(); selfGraded++; }
      } else if (jb.length){
        jb[0].click(); answered++;
        var sg2=[].slice.call(document.querySelectorAll('.self-grade .btn'));
        if (sg2.length){ sg2[0].click(); selfGraded++; }
      }
      var nx=document.querySelector('#btnNext'); if(!nx) break;
      nx.click(); steps++;
      if (document.querySelector('#view-quiz').classList.contains('hidden')){ log('quiz ended after ' + steps + ' steps'); break; }
    }
    log('answered=' + answered + ' autoGraded=' + autoGraded + ' multiSubmitted=' + multiSubmitted + ' selfGraded=' + selfGraded);
    log('distinct stems walked=' + Object.keys(seen).length);
    log('hero after练习=' + [].map.call(document.querySelectorAll('.stat-pill'), function(p){return p.textContent;}).join(' | '));
    log('STORAGE=' + localStorage.getItem('dsq_stats_v1'));

    document.querySelector('#btnStats').click();
    log('stats=' + [].map.call(document.querySelectorAll('.stat-card'), function(c){return c.textContent;}).join(' | '));
    log('chapter rows=' + document.querySelectorAll('#statsBody tbody tr').length);
    document.querySelector('#btnWrong').click();
    var t=document.querySelector('#statsBody .page-title');
    log('wrongbook=' + (t?t.textContent:'-') + ' rows=' + document.querySelectorAll('#statsBody tbody tr').length);
    document.querySelector('#btnHome').click();
    var si=document.querySelector('#searchInput'); si.value='遵义会议';
    si.dispatchEvent(new Event('input'));
    return out.join('\n') + '\nPENDING_SEARCH';
  } catch(e){ return out.join('\n') + '\nEXCEPTION: ' + e.message + '\n' + e.stack; }
})()
"""

r = ws.call("Runtime.evaluate", {"expression": SCRIPT, "returnByValue": True, "awaitPromise": False})
val = r.get("result", {}).get("result", {}).get("value")
print(val)

time.sleep(1.5)
r2 = ws.call("Runtime.evaluate", {
    "expression": "document.querySelectorAll('.res-item').length + ' search-hits | storage=' + localStorage.getItem('dsq_stats_v1')",
    "returnByValue": True})
print("AFTER SEARCH:", r2.get("result", {}).get("result", {}).get("value"))

# reload to prove persistence
ws.call("Page.enable")
ws.call("Page.reload", {"ignoreCache": True})
time.sleep(6)
r3 = ws.call("Runtime.evaluate", {
    "expression": "document.title + ' || hero=' + [].map.call(document.querySelectorAll('.stat-pill'), function(p){return p.textContent;}).join(' | ') + ' || badge=' + document.querySelector('#wrongBadge').textContent",
    "returnByValue": True})
print("AFTER RELOAD:", r3.get("result", {}).get("result", {}).get("value"))

proc.kill()
