#!/usr/bin/env python3
"""
GEO Dataset Downloader + CSV Viewer — Single-file Flask App
Rode com: python app.py
Acesse  : http://localhost:5000
"""

import csv, io, json, os, queue, re, sys, threading, uuid, zipfile
from flask import Flask, Response, request, send_file, jsonify

missing = []
try:    import GEOparse
except: missing.append("GEOparse")
try:    import requests
except: missing.append("requests")

app  = Flask(__name__)
JOBS = {}


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN PAGE HTML
# ═══════════════════════════════════════════════════════════════════════════════
HTML = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>GEO Dataset Downloader</title>
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet"/>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0b0f14;--surf:#111820;--border:#1e2d3d;--border2:#243447;
  --accent:#00c8ff;--green:#00ff9d;--warn:#ffb347;--err:#ff5f5f;
  --text:#c8d8e8;--dim:#4a6278;--mono:'Space Mono',monospace;--sans:'DM Sans',sans-serif;
}
html,body{height:100%;background:var(--bg);color:var(--text);font-family:var(--sans);font-size:15px}
body::before{content:'';position:fixed;inset:0;
  background-image:linear-gradient(rgba(0,200,255,.03) 1px,transparent 1px),
                   linear-gradient(90deg,rgba(0,200,255,.03) 1px,transparent 1px);
  background-size:40px 40px;pointer-events:none;z-index:0}
.page{position:relative;z-index:1;min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:48px 20px 64px}
.header{text-align:center;margin-bottom:44px}
.badge{display:inline-block;font-family:var(--mono);font-size:11px;letter-spacing:.12em;text-transform:uppercase;
  color:var(--accent);border:1px solid var(--border2);border-radius:2px;padding:4px 10px;
  margin-bottom:18px;background:rgba(0,200,255,.05)}
h1{font-family:var(--mono);font-size:clamp(22px,4vw,38px);font-weight:700;color:#fff;line-height:1.1}
h1 span{color:var(--accent)}
.sub{margin-top:10px;color:var(--dim);font-size:13px;font-weight:300}
.card{width:100%;max-width:660px;background:var(--surf);border:1px solid var(--border);border-radius:6px;overflow:hidden}
.bar{display:flex;align-items:center;gap:6px;padding:10px 16px;background:rgba(0,0,0,.3);border-bottom:1px solid var(--border)}
.dot{width:10px;height:10px;border-radius:50%}.dr{background:#ff5f56}.dy{background:#ffbd2e}.dg{background:#27c93f}
.bar-lbl{font-family:var(--mono);font-size:11px;color:var(--dim);margin-left:8px;letter-spacing:.06em}
.prog-wrap{height:2px;background:var(--border);position:relative;overflow:hidden}
.prog{position:absolute;top:0;left:0;bottom:0;width:0;background:var(--accent);transition:width .4s}
.prog.spin{width:40%;animation:slide 1.4s ease-in-out infinite}
@keyframes slide{0%{left:-40%}100%{left:100%}}
.inp-sec{padding:26px 26px 22px;border-bottom:1px solid var(--border)}
label{display:block;font-family:var(--mono);font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--accent);margin-bottom:9px}
.row{display:flex;gap:10px}
input[type=text]{flex:1;background:var(--bg);border:1px solid var(--border2);border-radius:4px;color:#fff;
  font-family:var(--mono);font-size:15px;padding:12px 14px;outline:none;
  transition:border-color .2s,box-shadow .2s;letter-spacing:.04em}
input[type=text]::placeholder{color:var(--dim)}
input[type=text]:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(0,200,255,.1)}
input[type=text]:disabled{opacity:.5}
.btn{background:var(--accent);color:#000;border:none;border-radius:4px;
  font-family:var(--mono);font-size:13px;font-weight:700;letter-spacing:.06em;
  padding:12px 20px;cursor:pointer;transition:background .15s,transform .1s;white-space:nowrap}
.btn:hover:not(:disabled){background:#33d4ff}
.btn:active:not(:disabled){transform:scale(.97)}
.btn:disabled{opacity:.4;cursor:not-allowed}
.hint{margin-top:9px;font-size:12px;color:var(--dim)}
.hint code{font-family:var(--mono);color:var(--green);font-size:11px}
.err-banner{display:none;align-items:center;gap:9px;margin-top:13px;padding:9px 13px;
  background:rgba(255,95,95,.08);border:1px solid rgba(255,95,95,.3);border-radius:4px;
  color:var(--err);font-size:13px}
.err-banner.show{display:flex}
.log-sec{display:none}.log-sec.show{display:block}
.log-hdr{display:flex;align-items:center;justify-content:space-between;
  padding:9px 18px;border-bottom:1px solid var(--border);background:rgba(0,0,0,.2)}
.log-lbl{font-family:var(--mono);font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--dim)}
.pill{font-family:var(--mono);font-size:10px;padding:2px 8px;border-radius:20px;letter-spacing:.08em}
.pill.run{background:rgba(0,200,255,.12);color:var(--accent);border:1px solid rgba(0,200,255,.3)}
.pill.ok {background:rgba(0,255,157,.12);color:var(--green);border:1px solid rgba(0,255,157,.3)}
.pill.err{background:rgba(255,95,95,.12);color:var(--err);border:1px solid rgba(255,95,95,.3)}
#log{font-family:var(--mono);font-size:12px;line-height:1.85;padding:16px 18px;
  max-height:300px;overflow-y:auto;scrollbar-width:thin;scrollbar-color:var(--border2) transparent}
#log::-webkit-scrollbar{width:4px}
#log::-webkit-scrollbar-thumb{background:var(--border2);border-radius:2px}
.ll{display:block}.ls{color:var(--green)}.lw{color:var(--warn)}.le{color:var(--err)}
.cur::after{content:'█';animation:blink 1s step-end infinite;color:var(--accent);margin-left:3px}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0}}

/* ── Download + viewer buttons ── */
.dl-sec{display:none;padding:18px 26px 22px;border-top:1px solid var(--border);background:rgba(0,255,157,.02)}
.dl-sec.show{display:block}
.dl-top{display:flex;align-items:center;gap:14px;margin-bottom:14px}
.dl-icon{width:38px;height:38px;background:rgba(0,255,157,.1);border:1px solid rgba(0,255,157,.25);
  border-radius:6px;display:grid;place-items:center;flex-shrink:0;font-size:17px}
.dl-meta{flex:1}
.dl-meta strong{display:block;font-size:14px;color:#fff;font-weight:500}
.dl-meta span{font-size:12px;color:var(--dim)}
.btn-dl{background:var(--green);color:#000;text-decoration:none;border-radius:4px;
  font-family:var(--mono);font-size:12px;font-weight:700;letter-spacing:.06em;
  padding:10px 16px;transition:background .15s;white-space:nowrap;border:none;cursor:pointer}
.btn-dl:hover{background:#33ffb3}
.view-btns{display:flex;gap:8px;flex-wrap:wrap}
.btn-view{background:transparent;color:var(--accent);border:1px solid var(--border2);border-radius:4px;
  font-family:var(--mono);font-size:11px;letter-spacing:.06em;padding:7px 14px;cursor:pointer;
  transition:all .15s;display:flex;align-items:center;gap:6px}
.btn-view:hover{background:rgba(0,200,255,.08);border-color:var(--accent)}
.btn-view .tag{font-size:9px;background:rgba(0,200,255,.15);color:var(--accent);
  padding:1px 5px;border-radius:2px;letter-spacing:.06em}

footer{margin-top:36px;font-size:12px;color:var(--dim);text-align:center}
footer a{color:var(--dim)}
</style>
</head>
<body>
<div class="page">
  <div class="header">
    <div class="badge">NCBI · GEO · Bioinformatics</div>
    <h1>GEO<span>.</span>downloader</h1>
    <p class="sub">Baixe e visualize datasets do Gene Expression Omnibus direto no navegador</p>
  </div>
  <div class="card">
    <div class="bar">
      <span class="dot dr"></span><span class="dot dy"></span><span class="dot dg"></span>
      <span class="bar-lbl">geo_download.py — terminal</span>
    </div>
    <div class="prog-wrap"><div class="prog" id="prog"></div></div>
    <div class="inp-sec">
      <label for="acc">Código de acesso GEO</label>
      <div class="row">
        <input id="acc" type="text" placeholder="GSE5281" autocomplete="off" spellcheck="false" maxlength="20"/>
        <button class="btn" id="runBtn" onclick="go()">▶ Executar</button>
      </div>
      <p class="hint">Exemplos: <code>GSE5281</code> · <code>GSE48350</code> · <code>GSE175814</code></p>
      <div class="err-banner" id="eb"><span>⚠</span><span id="em"></span></div>
    </div>
    <div class="log-sec" id="ls">
      <div class="log-hdr">
        <span class="log-lbl">stdout</span>
        <span class="pill run" id="pill">● RUNNING</span>
      </div>
      <div id="log"></div>
    </div>

    <!-- Download + viewer panel -->
    <div class="dl-sec" id="ds">
      <div class="dl-top">
        <div class="dl-icon">📦</div>
        <div class="dl-meta">
          <strong id="dfn">dataset.zip</strong>
          <span>Expression matrix · Clinical metadata · Summary</span>
        </div>
        <a class="btn-dl" id="dla" href="#" download>↓ ZIP</a>
      </div>
      <div class="view-btns">
        <button class="btn-view" id="vExpr" onclick="openViewer('expression')">
          🔬 Visualizar Expressão <span class="tag">CSV</span>
        </button>
        <button class="btn-view" id="vClin" onclick="openViewer('clinical')">
          🧬 Visualizar Metadados <span class="tag">CSV</span>
        </button>
      </div>
    </div>
  </div>
  <footer><a href="https://www.ncbi.nlm.nih.gov/geo/" target="_blank">NCBI GEO</a> · Powered by GEOparse</footer>
</div>
<script>
let jid=null, es=null;
const $=id=>document.getElementById(id);
const acc=()=>$('acc').value.trim().toUpperCase();
$('acc').addEventListener('keydown',e=>{ if(e.key==='Enter') go(); });

function addLog(t){
  let c='';
  if(t.startsWith('  ✔')||t.startsWith('✔')) c='ls';
  else if(t.startsWith('  ⚠')) c='lw';
  else if(t.startsWith('  ✗')||t.startsWith('✗')) c='le';
  const prev=$('log').querySelector('.cur'); if(prev) prev.classList.remove('cur');
  const s=document.createElement('span'); s.className='ll '+c+' cur'; s.textContent=t;
  $('log').appendChild(s); $('log').appendChild(document.createElement('br'));
  $('log').scrollTop=$('log').scrollHeight;
}
function setP(st){
  const p=$('prog'); p.className='prog'; p.style.background=''; p.style.width='';
  if(st==='run') p.classList.add('spin');
  else if(st==='ok'){p.style.width='100%';p.style.background='var(--green)';}
  else if(st==='err'){p.style.width='100%';p.style.background='var(--err)';}
  else p.style.width='0';
}
function reset(){ $('runBtn').disabled=false; $('acc').disabled=false; }

async function go(){
  const a=acc(); if(!a){$('acc').focus();return;}
  $('eb').classList.remove('show'); $('log').innerHTML=''; $('ds').classList.remove('show');
  $('ls').classList.add('show'); $('pill').className='pill run'; $('pill').textContent='● RUNNING';
  $('runBtn').disabled=true; $('acc').disabled=true; setP('run');
  if(es){es.close();es=null;}
  let r;
  try{ r=await fetch('/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({accession:a})}); }
  catch(e){ $('em').textContent='Não foi possível conectar ao servidor.'; $('eb').classList.add('show'); reset(); setP(''); return; }
  const d=await r.json();
  if(!r.ok){ $('em').textContent=d.error||'Erro desconhecido.'; $('eb').classList.add('show'); $('ls').classList.remove('show'); reset(); setP(''); return; }
  jid=d.job_id;
  es=new EventSource('/stream/'+jid);
  es.onmessage=e=>{
    const m=JSON.parse(e.data);
    if(m.type==='log') addLog(m.msg);
    else if(m.type==='done'){
      es.close();
      const c=$('log').querySelector('.cur'); if(c) c.classList.remove('cur');
      $('pill').className='pill ok'; $('pill').textContent='✔ DONE'; setP('ok');
      $('dfn').textContent=a+'_dataset.zip'; $('dla').href='/download/'+m.job_id;
      $('ds').classList.add('show'); $('dla').click(); reset();
    } else if(m.type==='error'){
      es.close();
      const c=$('log').querySelector('.cur'); if(c) c.classList.remove('cur');
      $('pill').className='pill err'; $('pill').textContent='✗ ERROR'; setP('err'); reset();
    }
  };
  es.onerror=()=>{ if(es.readyState!==2) return; $('pill').className='pill err'; $('pill').textContent='✗ ERROR'; setP('err'); reset(); };
}

function openViewer(type){
  if(!jid) return;
  window.open('/viewer/'+jid+'/'+type, '_blank');
}
</script>
</body></html>"""


# ═══════════════════════════════════════════════════════════════════════════════
#  CSV VIEWER PAGE HTML
# ═══════════════════════════════════════════════════════════════════════════════
VIEWER_HTML = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>CSV Viewer — {title}</title>
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet"/>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#080c12;--surf:#0f1720;--surf2:#131e2c;--border:#1a2a3e;--border2:#1e3248;
  --accent:#00c8ff;--green:#00ff9d;--warn:#ffb347;--err:#ff5f5f;--purple:#b48eff;
  --text:#c8d8e8;--dim:#4a6278;--bright:#f0f8ff;
  --mono:'Space Mono',monospace;--sans:'DM Sans',sans-serif;
}
html,body{height:100%;background:var(--bg);color:var(--text);font-family:var(--sans);font-size:14px;overflow:hidden}
body::before{content:'';position:fixed;inset:0;
  background-image:linear-gradient(rgba(0,200,255,.025) 1px,transparent 1px),
                   linear-gradient(90deg,rgba(0,200,255,.025) 1px,transparent 1px);
  background-size:40px 40px;pointer-events:none;z-index:0}

/* ── Shell layout ── */
.shell{position:relative;z-index:1;display:flex;flex-direction:column;height:100vh}

/* ── Top bar ── */
.topbar{
  display:flex;align-items:center;gap:12px;
  padding:0 20px;height:52px;flex-shrink:0;
  background:var(--surf);border-bottom:1px solid var(--border);
}
.tb-dots{display:flex;gap:5px}
.dot{width:9px;height:9px;border-radius:50%}.dr{background:#ff5f56}.dy{background:#ffbd2e}.dg{background:#27c93f}
.tb-title{font-family:var(--mono);font-size:12px;color:var(--dim);letter-spacing:.04em;flex:1;text-align:center}
.tb-title strong{color:var(--accent)}
.tb-stats{font-family:var(--mono);font-size:10px;color:var(--dim);letter-spacing:.04em;white-space:nowrap}

/* ── Controls bar ── */
.controls{
  display:flex;align-items:center;gap:10px;flex-wrap:wrap;
  padding:10px 20px;background:var(--surf2);border-bottom:1px solid var(--border);flex-shrink:0;
}
.search-wrap{position:relative;flex:1;min-width:200px;max-width:380px}
.search-wrap input{
  width:100%;background:var(--bg);border:1px solid var(--border2);border-radius:4px;
  color:var(--bright);font-family:var(--mono);font-size:12px;
  padding:8px 12px 8px 32px;outline:none;
  transition:border-color .2s,box-shadow .2s;letter-spacing:.03em;
}
.search-wrap input:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(0,200,255,.08)}
.search-wrap input::placeholder{color:var(--dim);opacity:.7}
.search-icon{position:absolute;left:10px;top:50%;transform:translateY(-50%);color:var(--dim);font-size:13px;pointer-events:none}

.ctrl-sep{width:1px;height:22px;background:var(--border2);flex-shrink:0}

.page-info{font-family:var(--mono);font-size:11px;color:var(--dim);white-space:nowrap}
.page-info strong{color:var(--text)}

.btn-page{background:var(--surf);border:1px solid var(--border2);border-radius:3px;
  color:var(--text);font-family:var(--mono);font-size:12px;padding:5px 10px;cursor:pointer;
  transition:all .15s}
.btn-page:hover:not(:disabled){border-color:var(--accent);color:var(--accent)}
.btn-page:disabled{opacity:.35;cursor:not-allowed}

.rows-select{background:var(--bg);border:1px solid var(--border2);border-radius:3px;
  color:var(--text);font-family:var(--mono);font-size:11px;padding:5px 8px;outline:none;cursor:pointer}
.rows-select:focus{border-color:var(--accent)}

.freeze-btn{background:transparent;border:1px solid var(--border2);border-radius:3px;
  color:var(--dim);font-family:var(--mono);font-size:10px;letter-spacing:.05em;
  padding:5px 10px;cursor:pointer;transition:all .15s;text-transform:uppercase}
.freeze-btn.active{background:rgba(0,200,255,.1);border-color:var(--accent);color:var(--accent)}

.btn-dl-csv{background:transparent;border:1px solid rgba(0,255,157,.3);border-radius:3px;
  color:var(--green);font-family:var(--mono);font-size:10px;letter-spacing:.05em;
  padding:5px 10px;cursor:pointer;transition:all .15s;text-decoration:none;text-transform:uppercase}
.btn-dl-csv:hover{background:rgba(0,255,157,.08)}

/* ── Table area ── */
.table-wrap{flex:1;overflow:auto;position:relative;
  scrollbar-width:thin;scrollbar-color:var(--border2) transparent}
.table-wrap::-webkit-scrollbar{width:6px;height:6px}
.table-wrap::-webkit-scrollbar-thumb{background:var(--border2);border-radius:3px}

table{border-collapse:collapse;min-width:100%;font-size:12.5px}
thead{position:sticky;top:0;z-index:10}
thead tr{background:var(--surf)}

th{
  font-family:var(--mono);font-size:10px;font-weight:700;
  letter-spacing:.07em;text-transform:uppercase;color:var(--dim);
  padding:10px 14px;border-bottom:1px solid var(--border2);border-right:1px solid var(--border);
  white-space:nowrap;cursor:pointer;user-select:none;
  transition:background .15s,color .15s;
  position:relative;
}
th:hover{background:rgba(0,200,255,.06);color:var(--text)}
th.sort-asc::after{content:' ↑';color:var(--accent)}
th.sort-desc::after{content:' ↓';color:var(--accent)}
th.sort-asc,th.sort-desc{color:var(--accent)}

td{
  padding:8px 14px;border-bottom:1px solid rgba(26,42,62,.7);border-right:1px solid var(--border);
  white-space:nowrap;max-width:260px;overflow:hidden;text-overflow:ellipsis;
  font-family:var(--mono);font-size:11.5px;color:var(--text);
  transition:background .1s;
}
tbody tr:hover td{background:rgba(0,200,255,.04)}

/* Frozen first column */
.frozen th:first-child,
.frozen td:first-child{
  position:sticky;left:0;z-index:5;
  background:var(--surf);border-right:2px solid var(--accent) !important;
}
.frozen tbody tr:hover td:first-child{background:var(--surf2)}

/* Row number column */
td.rn,th.rn{color:var(--dim);font-size:10px;padding:8px 10px;min-width:44px;text-align:right}

/* Highlight search matches */
mark{background:rgba(0,200,255,.25);color:var(--bright);border-radius:2px;padding:0 1px}

/* ── Loading state ── */
.loading{display:flex;flex-direction:column;align-items:center;justify-content:center;
  height:100%;gap:16px;color:var(--dim);font-family:var(--mono);font-size:13px}
.spinner{width:32px;height:32px;border:2px solid var(--border2);border-top-color:var(--accent);
  border-radius:50%;animation:spin .8s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}

/* ── Footer ── */
.statusbar{
  padding:5px 20px;background:var(--surf);border-top:1px solid var(--border);flex-shrink:0;
  font-family:var(--mono);font-size:10px;color:var(--dim);display:flex;align-items:center;gap:16px;
  letter-spacing:.04em;
}
.statusbar span{display:flex;align-items:center;gap:5px}
.dot-ok{width:6px;height:6px;border-radius:50%;background:var(--green)}
</style>
</head>
<body>
<div class="shell">
  <!-- Top bar -->
  <div class="topbar">
    <div class="tb-dots"><span class="dot dr"></span><span class="dot dy"></span><span class="dot dg"></span></div>
    <div class="tb-title" id="tb-title">Carregando...</div>
    <div class="tb-stats" id="tb-stats"></div>
  </div>

  <!-- Controls -->
  <div class="controls">
    <div class="search-wrap">
      <span class="search-icon">⌕</span>
      <input id="searchInput" type="text" placeholder="Buscar em todas as colunas..." oninput="onSearch()"/>
    </div>
    <div class="ctrl-sep"></div>
    <select class="rows-select" id="pageSel" onchange="onPageSizeChange()">
      <option value="25">25 linhas</option>
      <option value="50" selected>50 linhas</option>
      <option value="100">100 linhas</option>
      <option value="250">250 linhas</option>
    </select>
    <button class="btn-page" id="btnPrev" onclick="prevPage()" disabled>← Anterior</button>
    <span class="page-info" id="pageInfo">—</span>
    <button class="btn-page" id="btnNext" onclick="nextPage()">Próxima →</button>
    <div class="ctrl-sep"></div>
    <button class="freeze-btn" id="freezeBtn" onclick="toggleFreeze()">⬛ Fixar col.1</button>
    <a class="btn-dl-csv" id="dlCsvBtn" href="#" download>↓ CSV</a>
  </div>

  <!-- Table -->
  <div class="table-wrap" id="tableWrap">
    <div class="loading"><div class="spinner"></div><span>Carregando dados...</span></div>
  </div>

  <!-- Status bar -->
  <div class="statusbar">
    <span><span class="dot-ok"></span> GEO Viewer</span>
    <span id="sb-file">—</span>
    <span id="sb-filter">—</span>
    <span id="sb-sort">Clique em coluna para ordenar</span>
  </div>
</div>

<script>
// ── State ──────────────────────────────────────────────────────────────────
let allRows=[], headers=[], filtered=[], sortCol=-1, sortDir=1;
let page=0, pageSize=50, frozen=false, query='';
const JID   = location.pathname.split('/')[2];
const CTYPE = location.pathname.split('/')[3];

// ── Init ───────────────────────────────────────────────────────────────────
(async()=>{
  const r = await fetch(`/csv/${JID}/${CTYPE}`);
  if(!r.ok){ document.getElementById('tableWrap').innerHTML='<div class="loading"><span>❌ Arquivo não disponível.</span></div>'; return; }
  const {headers:h, rows:rw, filename, accession} = await r.json();
  headers=h; allRows=rw;
  document.getElementById('tb-title').innerHTML = `<strong>${accession}</strong> — ${filename}`;
  document.getElementById('sb-file').textContent = filename;
  document.getElementById('dlCsvBtn').href = `/csv-raw/${JID}/${CTYPE}`;
  document.getElementById('dlCsvBtn').download = filename;
  document.title = `${accession} · ${CTYPE}`;
  applyFilter();
})();

// ── Filter & sort ──────────────────────────────────────────────────────────
function onSearch(){ query=document.getElementById('searchInput').value.toLowerCase(); page=0; applyFilter(); }
function onPageSizeChange(){ pageSize=+document.getElementById('pageSel').value; page=0; render(); }

function applyFilter(){
  if(!query){ filtered=allRows.slice(); }
  else{
    filtered=allRows.filter(r=>r.some(c=>(c||'').toLowerCase().includes(query)));
  }
  if(sortCol>=0) doSort(sortCol, false);
  else render();
}

function sortBy(col){
  if(sortCol===col) sortDir*=-1; else{sortCol=col;sortDir=1;}
  doSort(col, true);
}
function doSort(col, updateDir){
  const isNum = filtered.every(r=>r[col]===''||!isNaN(r[col]));
  filtered.sort((a,b)=>{
    let av=a[col]||'', bv=b[col]||'';
    if(isNum){av=parseFloat(av)||0;bv=parseFloat(bv)||0;}
    if(av<bv) return -sortDir; if(av>bv) return sortDir; return 0;
  });
  render();
}

function toggleFreeze(){ frozen=!frozen; document.getElementById('freezeBtn').classList.toggle('active',frozen); render(); }

// ── Render ─────────────────────────────────────────────────────────────────
function highlight(txt){
  if(!query||!txt) return escHtml(txt);
  const s=escHtml(txt), q=escHtml(query);
  return s.replace(new RegExp(q,'gi'),m=>`<mark>${m}</mark>`);
}
function escHtml(s){ return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

function render(){
  const total=filtered.length;
  const pages=Math.max(1,Math.ceil(total/pageSize));
  if(page>=pages) page=pages-1;
  const start=page*pageSize, end=Math.min(start+pageSize,total);
  const slice=filtered.slice(start,end);

  // Stats
  document.getElementById('tb-stats').textContent = `${total.toLocaleString()} linhas · ${headers.length} colunas`;
  document.getElementById('pageInfo').innerHTML = `<strong>${page+1}</strong>/${pages}`;
  document.getElementById('sb-filter').textContent = query ? `Filtro: "${query}" → ${total} resultados` : `${allRows.length.toLocaleString()} linhas totais`;
  document.getElementById('sb-sort').textContent = sortCol>=0 ? `Ordenado por: ${headers[sortCol]} ${sortDir>0?'↑':'↓'}` : 'Clique em coluna para ordenar';
  document.getElementById('btnPrev').disabled = page===0;
  document.getElementById('btnNext').disabled = page>=pages-1;

  // Build table
  let html=`<table class="${frozen?'frozen':''}"><thead><tr><th class="rn">#</th>`;
  headers.forEach((h,i)=>{
    let cls='';
    if(sortCol===i) cls=sortDir>0?'sort-asc':'sort-desc';
    html+=`<th class="${cls}" onclick="sortBy(${i})">${escHtml(h)}</th>`;
  });
  html+='</tr></thead><tbody>';
  slice.forEach((row,ri)=>{
    html+=`<tr><td class="rn">${start+ri+1}</td>`;
    row.forEach(cell=>{ html+=`<td title="${escHtml(cell)}">${highlight(cell)}</td>`; });
    html+='</tr>';
  });
  html+='</tbody></table>';
  document.getElementById('tableWrap').innerHTML=html;
}

function prevPage(){ if(page>0){page--;render();} }
function nextPage(){ const pages=Math.ceil(filtered.length/pageSize); if(page<pages-1){page++;render();} }

// keyboard shortcuts
document.addEventListener('keydown',e=>{
  if(e.target.tagName==='INPUT') return;
  if(e.key==='ArrowRight') nextPage();
  if(e.key==='ArrowLeft')  prevPage();
  if(e.key==='/')          { e.preventDefault(); document.getElementById('searchInput').focus(); }
});
</script>
</body></html>"""


# ═══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def validate(acc):
    a = acc.strip().upper()
    return a if re.match(r"^GSE\d+$", a) else None


def run_download(job_id, accession):
    job = JOBS[job_id]; q = job["log_queue"]
    def log(m): q.put({"type":"log","msg":m})
    try:
        log(f"▶ Iniciando download de {accession}...")
        log("  Conectando ao NCBI GEO...")
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            log("  Baixando arquivos do GEO (pode demorar alguns minutos)...")
            gse = GEOparse.get_GEO(geo=accession, destdir=tmp, silent=True)
            title    = gse.metadata.get("title",           ["N/A"])[0]
            summary  = gse.metadata.get("summary",         ["N/A"])[0]
            organism = gse.metadata.get("sample_organism", ["N/A"])[0]
            platform = gse.metadata.get("platform_id",     ["N/A"])[0]
            n        = len(gse.gsms)
            pubs     = gse.metadata.get("pubmed_id", [])
            log("  ✔ Dataset encontrado!")
            log(f"  Título     : {title}")
            log(f"  Organismo  : {organism}")
            log(f"  Plataforma : {platform}")
            log(f"  Amostras   : {n}")
            if pubs: log(f"  PubMed     : {', '.join(pubs)}")

            buf = io.BytesIO()
            expr_csv = None
            clin_csv = None

            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                # Expression
                try:
                    log("  Gerando tabela de expressão gênica...")
                    pivot = gse.pivot_samples("VALUE")
                    expr_csv = pivot.to_csv()
                    zf.writestr(f"{accession}/{accession}_expression.csv", expr_csv)
                    log(f"  ✔ Expressão: {len(pivot)} genes × {len(pivot.columns)} amostras")
                except Exception as e:
                    log(f"  ⚠ Expressão não disponível: {e}")

                # Clinical
                log("  Gerando metadados clínicos...")
                rows = []
                for nm, gsm in gse.gsms.items():
                    row = {"sample_id":nm,
                           "title":gsm.metadata.get("title",[""])[0],
                           "source":gsm.metadata.get("source_name_ch1",[""])[0],
                           "organism":gsm.metadata.get("organism_ch1",[""])[0]}
                    for ch in gsm.metadata.get("characteristics_ch1",[]):
                        if ":" in ch:
                            k,_,v = ch.partition(":")
                            row[k.strip().lower().replace(" ","_")] = v.strip()
                        else:
                            row[ch.strip().lower().replace(" ","_")] = ""
                    rows.append(row)
                if rows:
                    keys = list(dict.fromkeys(k for r in rows for k in r))
                    out  = io.StringIO()
                    w = csv.DictWriter(out, fieldnames=keys, extrasaction="ignore")
                    w.writeheader(); w.writerows(rows)
                    clin_csv = out.getvalue()
                    zf.writestr(f"{accession}/{accession}_clinical.csv", clin_csv)
                    log(f"  ✔ Metadados: {len(rows)} amostras")

                # Summary
                zf.writestr(f"{accession}/{accession}_summary.txt",
                    f"Accession: {accession}\nTítulo: {title}\nOrganismo: {organism}\n"
                    f"Plataforma: {platform}\nAmostras: {n}\n"
                    f"PubMed: {', '.join(pubs) if pubs else 'N/A'}\n\nResumo:\n{summary}\n")
                log("  ✔ Resumo gerado")

            buf.seek(0)
            job["zip"]       = buf.read()
            job["fname"]     = f"{accession}_dataset.zip"
            job["accession"] = accession
            job["expr_csv"]  = expr_csv
            job["clin_csv"]  = clin_csv
            job["status"]    = "done"
            log("✔ Concluído! Baixe o ZIP ou visualize os CSVs abaixo.")
            q.put({"type":"done","job_id":job_id})
    except Exception as e:
        job["status"]="error"; log(f"✗ Erro: {e}"); q.put({"type":"error","msg":str(e)})


def parse_csv_to_json(csv_text):
    """Parse CSV string → {headers, rows}"""
    reader = csv.reader(io.StringIO(csv_text))
    rows   = list(reader)
    if not rows:
        return {"headers":[], "rows":[]}
    return {"headers": rows[0], "rows": rows[1:]}


# ═══════════════════════════════════════════════════════════════════════════════
#  ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return HTML, 200, {"Content-Type": "text/html; charset=utf-8"}


@app.route("/start", methods=["POST"])
def start():
    data = request.get_json() or {}
    acc  = validate(data.get("accession",""))
    if not acc:
        return jsonify({"error":"Código GEO inválido. Use o formato GSExxxx (ex: GSE5281)."}), 400
    jid = str(uuid.uuid4())
    JOBS[jid] = {"status":"running","log_queue":queue.Queue(),
                 "zip":None,"fname":None,"accession":None,
                 "expr_csv":None,"clin_csv":None}
    threading.Thread(target=run_download, args=(jid,acc), daemon=True).start()
    return jsonify({"job_id":jid})


@app.route("/stream/<jid>")
def stream(jid):
    if jid not in JOBS:
        return jsonify({"error":"not found"}), 404
    def gen():
        q = JOBS[jid]["log_queue"]
        while True:
            try:
                msg = q.get(timeout=120)
                yield f"data: {json.dumps(msg)}\n\n"
                if msg["type"] in ("done","error"): break
            except queue.Empty:
                yield f"data: {json.dumps({'type':'ping'})}\n\n"
    return Response(gen(), mimetype="text/event-stream",
                    headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})


@app.route("/download/<jid>")
def download(jid):
    job = JOBS.get(jid)
    if not job or job["status"]!="done": return jsonify({"error":"não disponível"}), 404
    return send_file(io.BytesIO(job["zip"]), mimetype="application/zip",
                     as_attachment=True, download_name=job["fname"])


@app.route("/viewer/<jid>/<ctype>")
def viewer(jid, ctype):

    return VIEWER_HTML, 200, {"Content-Type": "text/html; charset=utf-8"}


@app.route("/csv/<jid>/<ctype>")
def csv_json(jid, ctype):
    """Return CSV as JSON for the viewer."""
    job = JOBS.get(jid)
    if not job or job["status"] != "done":
        return jsonify({"error":"não disponível"}), 404
    acc = job["accession"]
    if ctype == "expression":
        raw = job.get("expr_csv")
        fname = f"{acc}_expression.csv"
    elif ctype == "clinical":
        raw = job.get("clin_csv")
        fname = f"{acc}_clinical.csv"
    else:
        return jsonify({"error":"tipo inválido"}), 400
    if not raw:
        return jsonify({"error":"arquivo não gerado"}), 404
    data = parse_csv_to_json(raw)
    data["filename"]  = fname
    data["accession"] = acc
    return jsonify(data)


@app.route("/csv-raw/<jid>/<ctype>")
def csv_raw(jid, ctype):
    """Return raw CSV for download."""
    job = JOBS.get(jid)
    if not job or job["status"] != "done":
        return jsonify({"error":"não disponível"}), 404
    acc = job["accession"]
    if ctype == "expression":
        raw = job.get("expr_csv"); fname = f"{acc}_expression.csv"
    elif ctype == "clinical":
        raw = job.get("clin_csv"); fname = f"{acc}_clinical.csv"
    else:
        return jsonify({"error":"tipo inválido"}), 400
    if not raw:
        return jsonify({"error":"arquivo não gerado"}), 404
    return send_file(io.BytesIO(raw.encode("utf-8")), mimetype="text/csv",
                     as_attachment=True, download_name=fname)


# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if missing:
        print(f"\n[ERRO] Instale: pip install flask GEOparse requests\n"); sys.exit(1)
    print("\n  ✔ GEO Downloader + CSV Viewer → http://localhost:5000\n")
    app.run(debug=False, port=5000)
