import sys, os, shutil, json
sys.stdout.reconfigure(encoding='utf-8')
BASE = r"C:\Users\13083\Desktop\dangshi-quiz"
SITE = BASE
TEST = os.path.join(BASE, "build", "finaltest")
shutil.rmtree(TEST, ignore_errors=True)
os.makedirs(TEST)
for f in ("style.css", "app.js", "questions.js", "index.html"):
    shutil.copy(os.path.join(SITE, f), os.path.join(TEST, f))

harness = """<!DOCTYPE html><html><head><meta charset="utf-8"></head>
<body><div id="mount"></div><pre id="log"></pre>
<script>
var LOG=[];
function log(s){LOG.push(s);document.getElementById('log').textContent=LOG.join('\\n');}
window.onerror=function(m,u,l,c){log('JSERROR: '+m+' @'+l+':'+c);};
fetch('index.html').then(function(r){return r.text();}).then(function(h){
  document.getElementById('mount').innerHTML=h;
  return ['questions.js','app.js'].reduce(function(p,s){
    return p.then(function(){return new Promise(function(res){
      var e=document.createElement('script');e.src=s;e.onload=res;
      e.onerror=function(){log('SCRIPT FAIL '+s);res();};document.body.appendChild(e);});});
  },Promise.resolve());
}).then(function(){setTimeout(main,400);});
function q(s){return document.querySelector(s);}
function qa(s){return Array.prototype.slice.call(document.querySelectorAll(s));}
function main(){
 try{
  log('title='+document.title);
  log('hero='+qa('.stat-pill').map(function(p){return p.textContent;}).join(' | '));
  log('chapters='+qa('.chapter').length+' units='+qa('.unit').length);
  log('hint='+(q('#dataHint')?q('#dataHint').textContent:'-'));
  var Q=window.QUIZ_DATA.questions;
  var withA=Q.filter(function(x){return x.a;}).length;
  var kb=Q.filter(function(x){return x.a&&x.ak==='kb';}).length;
  log('payload: '+Q.length+' questions, '+withA+' with answer, '+kb+' kb-sourced');
  // start a unit and answer 8 questions
  q('#btnExpandAll').click();
  var row=qa('.unit')[0];
  log('unit='+row.querySelector('.unit-no').textContent+' '+row.querySelector('.unit-meta').textContent);
  row.querySelector('.btn-primary').click();
  var answered=0, auto=0, self=0, seen={};
  for(var i=0;i<8;i++){
    var ty=q('.q-type')?q('.q-type').textContent:'';
    var st=q('.q-stem'); if(st) seen[st.textContent.slice(0,20)]=1;
    var opts=qa('.opts .opt'), jb=qa('.judge-opts .opt');
    if(opts.length){
      if(ty==='多选题'){ opts.forEach(function(o){o.click();});
        var sb=q('#btnSubmitMulti'); if(sb&&!sb.disabled) sb.click(); }
      else opts[0].click();
      answered++;
      if(q('.verdict')) auto++;
      var sg=qa('.self-grade .btn'); if(sg.length){ sg[0].click(); self++; }
    } else if(jb.length){
      jb[0].click(); answered++;
      var sg2=qa('.self-grade .btn'); if(sg2.length){ sg2[0].click(); self++; }
    }
    var nx=q('#btnNext'); if(!nx) break; nx.click();
    if(q('#view-quiz').classList.contains('hidden')){ log('quiz ended after '+(i+1)+' steps'); break; }
  }
  log('answered='+answered+' autoGraded='+auto+' selfGraded='+self);
  log('hero after='+qa('.stat-pill').map(function(p){return p.textContent;}).join(' | '));
  q('#btnStats').click();
  log('stats='+qa('.stat-card').map(function(c){return c.textContent;}).join(' | '));
  q('#btnWrong').click();
  log('wrongbook='+(q('#statsBody .page-title')?q('#statsBody .page-title').textContent:'-'));
  q('#btnHome').click();
  q('#searchInput').value='遵义会议';
  q('#searchInput').dispatchEvent(new Event('input'));
  setTimeout(function(){
    log('search hits='+qa('.res-item').length);
    log('DONE');
  },600);
 }catch(e){ log('EXCEPTION: '+e.message+' | '+e.stack); log('DONE'); }
}
</script></body></html>
"""
open(os.path.join(TEST, "final.html"), "w", encoding="utf-8").write(harness)
print("harness written to", TEST)
