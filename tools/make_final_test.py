import sys, os, shutil, json, re
sys.stdout.reconfigure(encoding='utf-8')
BASE = r"C:\Users\13083\Desktop\dangshi-quiz"
SITE = os.path.join(BASE, "site")
TEST = os.path.join(BASE, "build", "final")
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
  log('HERO: '+qa('.stat-pill').map(function(p){return p.textContent;}).join(' | '));
  log('chapters='+qa('.chapter').length+' units(all)='+qa('.unit').length);
  log('dataHint='+(q('#dataHint')?q('#dataHint').textContent:'-'));
  q('#btnExpandAll').click();
  log('units after expand='+qa('.unit').length);
  // start the biggest unit
  var rows=qa('.unit');
  log('first unit meta='+rows[0].querySelector('.unit-meta').textContent);
  rows[0].querySelector('.btn-primary').click();
  log('quiz counter='+q('#quizCounter').textContent);
  log('stem='+(q('.q-stem')?q('.q-stem').textContent.slice(0,40):'-'));
  var ty=q('.q-type')?q('.q-type').textContent:'-';
  log('type='+ty);
  log('option texts='+qa('.opts .opt, .judge-opts .opt').map(function(o){
      return o.textContent.replace(/\\s+/g,' ').slice(0,26);}).join(' || '));
  // answer it
  var opts=qa('.opts .opt');
  if(opts.length){ opts[0].click(); log('after pick: sel='+qa('.opt.sel').length+' verdict='+(q('.verdict')?q('.verdict').textContent.slice(0,10):'-')); }
  else { var jb=qa('.judge-opts .opt'); if(jb.length) jb[0].click(); }
  var sg=qa('.self-grade .btn');
  log('selfgrade buttons='+sg.length);
  if(sg.length) sg[1].click();   // record as WRONG
  log('stats='+localStorage.getItem('dsq_stats_v1'));
  log('wrongBadge='+q('#wrongBadge').textContent);
  // walk forward through 12 questions without error
  var seen={};
  for(var i=0;i<12;i++){
    q('#btnNext').click();
    if(!q('#view-quiz').classList.contains('hidden')){
      var st=q('.q-stem'); if(st) seen[st.textContent.slice(0,20)]=1;
    } else { log('quiz ended early at step '+i); break; }
  }
  log('distinct stems walked='+Object.keys(seen).length);
  // wrong book from the real dataset
  q('#btnWrong').click();
  log('wrongbook: '+(q('#statsBody .page-title')?q('#statsBody .page-title').textContent:'-')+' rows='+qa('#statsBody tbody tr').length);
  q('#btnStats').click();
  log('stats cards='+qa('.stat-card').map(function(c){return c.textContent;}).join(' | '));
  log('chapter rows='+qa('#statsBody tbody tr').length);
  q('#btnHome').click();
  q('#searchInput').value='毛泽东';
  q('#searchInput').dispatchEvent(new Event('input'));
  setTimeout(function(){
    log('search hits for 毛泽东='+qa('.res-item').length);
    log('DONE');
  },600);
 }catch(e){ log('EXCEPTION: '+e.message+' | '+e.stack); log('DONE'); }
}
</script></body></html>
"""
open(os.path.join(TEST, "final.html"), "w", encoding="utf-8").write(harness)
print("final harness written")
