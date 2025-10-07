:root{  
  --bg:#0f1320; --card:#141a2b; --ink:#e9eefc; --muted:#9db0d6; --accent:#67e8f9;  
  --spring:#66d36e; --summer:#ffd166; --autumn:#ff8a5b; --winter:#7aa2ff;  
}  
@media (prefers-color-scheme: light){  
  :root{ --bg:#f7f9ff; --card:#ffffff; --ink:#0e162b; --muted:#5a6a8a; --accent:#2563eb; }  
}  
* { box-sizing: border-box; }  
html,body{ height: 100%; }  
body{  
  margin:0; background:var(--bg); color:var(--ink);  
  font: 14px/1.5 system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, "Helvetica Neue", Arial;  
}  
header{  
  padding:16px clamp(16px,3vw,32px);  
  border-bottom:1px solid rgba(255,255,255,.08);  
  display:flex; gap:16px; align-items:center; flex-wrap:wrap; justify-content:space-between;  
}  
.title h1{ margin:0; font-size: clamp(18px, 2.4vw, 28px); letter-spacing:.2px; }  
.subtitle{ color:var(--muted); font-size:13px; }  
.toolbar{ display:flex; gap:8px; align-items:center; flex-wrap:wrap; }  
.group{  
  background:var(--card);  
  border:1px solid rgba(255,255,255,.08);  
  padding:8px; border-radius:12px; display:flex; gap:8px; align-items:center; flex-wrap:wrap;  
}  
label.chk{  
  display:flex; align-items:center; gap:6px; font-weight:600; padding:4px 8px; border-radius:8px; cursor:pointer;  
  border:1px solid transparent;  
}  
label.chk input{ accent-color: var(--accent); }  
label[data-szn="winter"]{ background: rgba(122,162,255,.12); border-color: rgba(122,162,255,.24); }  
label[data-szn="spring"]{ background: rgba(102,211,110,.12); border-color: rgba(102,211,110,.24); }  
label[data-szn="summer"]{ background: rgba(255,209,102,.12); border-color: rgba(255,209,102,.24); }  
label[data-szn="autumn"]{ background: rgba(255,138,91,.12); border-color: rgba(255,138,91,.24); }  
button{  
  background:var(--accent); color:#00121f; border:0; font-weight:700; padding:10px 14px; border-radius:10px; cursor:pointer;  
}  
button.ghost{ background:transparent; color:var(--ink); border:1px solid rgba(255,255,255,.18); }  
main{ padding:18px clamp(16px,3vw,32px); display:grid; gap:16px; }  
.canvas{  
  background:var(--card); border:1px solid rgba(255,255,255,.08); border-radius:16px;  
  padding:16px;  
}  
#chart{ overflow:auto; }  
.legend{  
  display:flex; gap:10px; flex-wrap:wrap; color:var(--muted); font-size:13px;  
}  
.legend .dot{ width:10px; height:10px; border-radius:50%; display:inline-block; margin-right:6px; }  
.kpi{  
  display:grid; grid-template-columns: repeat(auto-fit,minmax(180px,1fr)); gap:12px;  
}  
.card{  
  background:var(--card); border:1px solid rgba(255,255,255,.08); border-radius:12px; padding:12px;  
}  
.card h3{ margin:4px 0 6px; font-size:14px; }  
.small{ color:var(--muted); font-size:12px; }  
footer{ padding:20px clamp(16px,3vw,32px); color:var(--muted); }  
.tip{ color:var(--muted); font-style:italic; }  
