// ====== Config & Data ======  
const YEAR = new Date().getFullYear();  
const d = (y,m,day)=>`${y}-${String(m).padStart(2,'0')}-${String(day).padStart(2,'0')}`;  
  
const tasks = [  
  // Strategie & voorbereiding  
  { g:"Strategie & voorbereiding", l:"Plan & ontwerp", s:d(YEAR,1,10),  e:d(YEAR,1,11),  sz:"winter", m:["beginner","pro"], ms:true },  
  { g:"Strategie & voorbereiding", l:"Bodemstaal & pH", s:d(YEAR,1,15),  e:d(YEAR,2,15),  sz:"winter", m:["pro"] },  
  { g:"Strategie & voorbereiding", l:"Gereedschap slijpen & onderhoud", s:d(YEAR,1,10), e:d(YEAR,2,28), sz:"winter", m:["beginner","pro"] },  
  
  // Bomen & heesters  
  { g:"Bomen & heesters", l:"Wintersnoei bladverliezend", s:d(YEAR,1,10), e:d(YEAR,2,28), sz:"winter", m:["beginner","pro"] },  
  { g:"Bomen & heesters", l:"Aanplant hagen/bomen",      s:d(YEAR,3,1),  e:d(YEAR,4,15),  sz:"spring", m:["beginner","pro"] },  
  { g:"Bomen & heesters", l:"Eerste hagen-snoei (na 15 mei)", s:d(YEAR,5,20), e:d(YEAR,5,21), sz:"spring", m:["beginner","pro"], ms:true },  
  { g:"Bomen & heesters", l:"Tweede hagen-snoei (eind juli)", s:d(YEAR,7,25), e:d(YEAR,7,26), sz:"summer", m:["beginner","pro"], ms:true },  
  { g:"Bomen & heesters", l:"Vormsnoei nazomer/herfst",  s:d(YEAR,9,1),  e:d(YEAR,10,15), sz:"autumn", m:["pro"] },  
  
  // Gazon: aanleg & herstel  
  { g:"Gazon: aanleg & herstel", l:"Onkruid verwijderen",      s:d(YEAR,3,1),  e:d(YEAR,3,20), sz:"spring", m:["beginner","pro"] },  
  { g:"Gazon: aanleg & herstel", l:"Frezen/losmaken & egaliseren", s:d(YEAR,3,15), e:d(YEAR,4,5), sz:"spring", m:["beginner","pro"] },  
  { g:"Gazon: aanleg & herstel", l:"Zaaien (≥10 °C) of graszoden", s:d(YEAR,4,5),  e:d(YEAR,5,15), sz:"spring", m:["beginner","pro"] },  
  { g:"Gazon: aanleg & herstel", l:"Doorzaaien kale plekken",  s:d(YEAR,7,15), e:d(YEAR,8,31), sz:"summer", m:["pro"] },  
  { g:"Gazon: aanleg & herstel", l:"Verticuteren/Beluchten",   s:d(YEAR,9,1),  e:d(YEAR,9,30), sz:"autumn", m:["beginner","pro"] },  
  { g:"Gazon: aanleg & herstel", l:"Laatste maaibeurt",        s:d(YEAR,10,15),e:d(YEAR,10,16),sz:"autumn", m:["beginner","pro"], ms:true },  
  
  // Gazon: onderhoud  
  { g:"Gazon: onderhoud", l:"Maaien wekelijks", s:d(YEAR,5,1), e:d(YEAR,9,30), sz:"summer", m:["beginner","pro"] },  
  { g:"Gazon: onderhoud", l:"Water geven bij droogte", s:d(YEAR,6,1), e:d(YEAR,8,31), sz:"summer", m:["beginner","pro"] },  
  
  // Bemesting & bodem  
  { g:"Bemesting & bodem", l:"Voorjaarsbemesting", s:d(YEAR,3,25), e:d(YEAR,4,5),  sz:"spring", m:["beginner","pro"] },  
  { g:"Bemesting & bodem", l:"Zomerbijbemesting",  s:d(YEAR,6,15), e:d(YEAR,6,25), sz:"summer", m:["pro"] },  
  { g:"Bemesting & bodem", l:"Herfstbemesting (kali-rijk)", s:d(YEAR,9,20), e:d(YEAR,10,10), sz:"autumn", m:["beginner","pro"] },  
  { g:"Bemesting & bodem", l:"Kalk/compost indien nodig", s:d(YEAR,10,15), e:d(YEAR,11,15), sz:"autumn", m:["pro"] },  
  
  // Opschoning & winterklaar  
  { g:"Opschoning & winterklaar", l:"Bladruimen", s:d(YEAR,10,15), e:d(YEAR,11,30), sz:"autumn", m:["beginner","pro"] },  
  { g:"Opschoning & winterklaar", l:"Vorstgevoelige planten beschermen", s:d(YEAR,11,15), e:d(YEAR,12,10), sz:"winter", m:["beginner","pro"] },  
  { g:"Opschoning & winterklaar", l:"Winterrust & evaluatie", s:d(YEAR,12,1), e:d(YEAR,12,20), sz:"winter", m:["beginner","pro"] }  
];  
  
// ====== UI State ======  
let mode = "pro";  
const activeSeasons = new Set(["winter","spring","summer","autumn"]);  
  
// ====== Mermaid init ======  
mermaid.initialize({  
  startOnLoad: false,  
  theme: (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) ? 'default' : 'dark',  
  themeVariables: { fontSize: '14px' }  
});  
  
// ====== Render Helpers ======  
function toMermaid(){  
  const v = tasks.filter(t => activeSeasons.has(t.sz) && t.m.includes(mode));  
  const groups = [...new Set(v.map(t=>t.g))];  
  const out = ["gantt","  dateFormat  YYYY-MM-DD","  axisFormat  %b","  tickInterval 1month"];  
  groups.forEach(g=>{  
    out.push(`  section ${g}`);  
    v.filter(t=>t.g===g).forEach((t,i)=>{  
      out.push(`  ${t.l} :${t.ms?"milestone,":""} ${t.sz}_${i}, ${t.s}, ${t.e}`);  
    });  
  });  
  return { m: out.join("\n"), v };  
}  
  
function draw(){  
  const { m, v } = toMermaid();  
  const el = document.getElementById("chart");  
  el.textContent = m;  
  mermaid.run({ querySelector: "#chart" }).then(()=>{  
    // Recolor bars by season  
    const colors = { winter:"#7aa2ff", spring:"#66d36e", summer:"#ffd166", autumn:"#ff8a5b" };  
    const rects = el.querySelectorAll("rect.task");  
    const order = [];  
    const groups = [...new Set(v.map(t=>t.g))];  
    groups.forEach(g=> v.filter(t=>t.g===g).forEach(t=>order.push(t)));  
    rects.forEach((r,i)=>{  
      const t = order[i]; if(!t) return;  
      r.setAttribute('fill', colors[t.sz]);  
      r.setAttribute('stroke','rgba(0,0,0,.25)');  
    });  
    // KPI update  
    document.getElementById("kpiSeasons").textContent = `${activeSeasons.size}/4`;  
    document.getElementById("kpiMode").textContent = mode === "pro" ? "Pro" : "Beginner";  
  });  
}  
  
// ====== Events ======  
["winter","spring","summer","autumn"].forEach(s=>{  
  document.getElementById(`szn-${s}`).addEventListener("change",(e)=>{  
    e.target.checked ? activeSeasons.add(s) : activeSeasons.delete(s);  
    draw();  
  });  
});  
document.getElementById("btnBeginner").addEventListener("click", ()=>{ mode="beginner"; draw(); });  
document.getElementById("btnPro").addEventListener("click", ()=>{ mode="pro"; draw(); });  
  
document.getElementById("btnPNG").addEventListener("click", ()=>{  
  const svg = document.querySelector("#chart svg");  
  if(!svg){ alert("Grafiek nog niet gerenderd."); return; }  
  const xml = new XMLSerializer().serializeToString(svg);  
  const img = new Image();  
  img.onload = () => {  
    const c = document.createElement("canvas");  
    c.width = img.width; c.height = img.height;  
    const ctx = c.getContext("2d");  
    const bg = getComputedStyle(document.body).getPropertyValue('--bg') || "#ffffff";  
    ctx.fillStyle = bg; ctx.fillRect(0,0,c.width,c.height);  
    ctx.drawImage(img, 0, 0);  
    const a = document.createElement("a");  
    a.download = "tuinplanning_tijdlijn.png";  
    a.href = c.toDataURL("image/png");  
    a.click();  
  };  
  img.src = "data:image/svg+xml;base64," + btoa(unescape(encodeURIComponent(xml)));  
});  
  
// ====== Init ======  
draw();  
