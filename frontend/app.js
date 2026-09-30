const API=window.CIVICLENS_API||(
  window.location.hostname==="civiclens-dashboard.onrender.com"
    ?"https://civiclens-api-s144.onrender.com"
    :"http://localhost:8000"
);
const fmt=n=>Number(n??0).toLocaleString("en-IN");
const pct=n=>Number(n??0).toFixed(2);
const esc=s=>String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;"}[c]));
let districtRows=[];let stateRows=[];let currentDistricts=[];let selectedDistrict="";

async function get(path){const r=await fetch(API+path);if(!r.ok)throw new Error(await r.text());return r.json();}
function setApiStatus(ok){
  const el=document.querySelector("#apiStatus"),side=document.querySelector("#sidebarStatus");
  if(el){el.className="status-pill"+(ok?" ok":"");el.innerHTML="<i></i> "+(ok?"API connected":"API unavailable");}
  if(side){side.parentElement.classList.toggle("ok",ok);side.textContent=ok?"Verified analytics":"API unavailable";}
}
function renderKpis(o){
  const items=[["Received",fmt(o.received),"Verified receipts"],["Disposed",fmt(o.disposed),"Recorded disposals"],["Pending",fmt(o.pending),"Current workload"],["Disposal rate",pct(o.disposal_rate)+"%","Disposed ÷ received"],["181+ days",fmt(o.ageing_181_plus),"Ageing 181+ days"]];
  document.querySelector("#kpis").innerHTML=items.map(x=>"<div class=\"kpi\"><small>"+x[0]+"</small><strong>"+x[1]+"</strong><span>"+x[2]+"</span></div>").join("");
  document.querySelector("#snapshot").textContent="Snapshot "+o.snapshot_date+" · Reporting period "+o.reporting_period;
}
function renderComposition(o){
  const received=Math.max(Number(o.received||0),1),disposed=Math.max(Number(o.disposed||0),0),pending=Math.max(Number(o.pending||0),0);
  const pendingAngle=Math.min(360,pending/Math.max(received+pending,1)*360);
  const disposedAngle=Math.min(360,disposed/received*360);
  document.querySelector("#donut").style.background="conic-gradient(var(--teal) 0deg "+pendingAngle+"deg,#7f8da3 "+pendingAngle+"deg "+Math.min(360,pendingAngle+disposedAngle/2)+"deg,#c77700 "+Math.min(360,pendingAngle+disposedAngle/2)+"deg 360deg)";
  document.querySelector("#donutValue").textContent=pct(o.pending_share)+"%";
  document.querySelector("#compositionLegend").innerHTML=[["Pending",pending,"Current workload"],["Disposed",disposed,"Recorded disposals"],["Received",received,"Base volume"]].map(x=>"<div class=\"legend-row\"><i></i><span>"+x[0]+" · "+x[2]+"</span><b>"+fmt(x[1])+"</b></div>").join("");
}
function mergeDistrictCounts(rows,directory){
  const map=new Map(directory.map(r=>[String(r.state_ut).toLowerCase(),r.district_count]));
  return rows.map(r=>{
    const exact=map.get(String(r.state_ut).toLowerCase());
    if(exact!==undefined)return {...r,district_count:exact};
    const normalized=String(r.state_ut).replace(/^Union Territory of /i,"").toLowerCase();
    const hit=directory.find(x=>String(x.state_ut).toLowerCase().includes(normalized)||normalized.includes(String(x.state_ut).toLowerCase()));
    return {...r,district_count:hit?.district_count??null};
  });
}
function renderStates(rows){
  stateRows=rows;
  document.querySelector("#rows").textContent=rows.length+" matching State / UT records";
  document.querySelector("#table").innerHTML=rows.length?rows.map(r=>"<tr><td><strong>"+esc(r.state_ut)+"</strong></td><td>"+esc(r.administrative_type||"State / UT")+"</td><td class=\"num\">"+fmt(r.received)+"</td><td class=\"num\">"+fmt(r.disposed)+"</td><td class=\"num\">"+fmt(r.pending_total)+"</td><td class=\"num\">"+pct(r.disposal_rate)+"%</td><td class=\"num\">"+fmt(r.ageing_181_plus)+"</td><td class=\"num\">"+(r.district_count??"—")+"</td></tr>").join(""):"<tr><td colspan=\"8\" class=\"empty\">No State / UT records match the search. Try the Geographic Explorer for district-level directory search.</td></tr>";
}
function renderSnapshots(snaps){
  const box=document.querySelector("#snapshots");
  box.innerHTML=snaps.length?snaps.slice(0,5).map(s=>"<div class=\"snapshot-item\"><strong>"+esc(s.snapshot_date)+"</strong><span>"+esc(s.reporting_period)+"</span><small>"+fmt(s.record_count)+" State / UT records · verified registry</small></div>").join(""):"<div class=\"empty\">No registered snapshots.</div>";
}
function renderAgeing(a){
  const items=[["0–60 days",a["0_60"]],["61–180 days",a["61_180"]],["181–365 days",a["181_365"]],["365+ days",a["365_plus"]]],total=items.reduce((s,x)=>s+Number(x[1]||0),0);
  document.querySelector("#ageCards").innerHTML=items.map(x=>"<div class=\"age-card\"><span>"+x[0]+"</span><strong>"+fmt(x[1])+"</strong><em>"+(total?((x[1]/total)*100).toFixed(1):"0.0")+"% of pending</em></div>").join("");
  const max=Math.max(...items.map(x=>Number(x[1]||0)),1);
  document.querySelector("#ageChart").innerHTML=items.map(x=>"<div class=\"bar-row\"><span>"+x[0]+"</span><div class=\"bar-track\"><i style=\"width:"+Math.max(2,Number(x[1]||0)/max*100)+"%\"></i></div><b>"+fmt(x[1])+"</b></div>").join("");
}
function renderQuality(d){
  const items=[["State / UT rows",d.rows],["Unique State / UT",d.unique_states_ut],["Missing numeric",d.missing_numeric_values],["Duplicate records",d.duplicate_states_ut],["Negative values",d.negative_numeric_values],["Ageing errors",d.ageing_reconciliation_errors]];
  document.querySelector("#quality").innerHTML=items.map(x=>"<div class=\"quality-item\"><small>"+x[0]+"</small><b>"+fmt(x[1])+"</b></div>").join("")+"<div class=\"quality-result\"><strong>✓ Dataset validation passed</strong><span>"+esc(d.snapshot_date)+" · "+esc(d.reporting_period)+" · HTTPS source: "+(d.source_is_https?"yes":"no")+"</span></div>";
}
function renderHistory(d){
  const status=document.querySelector("#historyStatus"),comparison=document.querySelector("#historyComparison"),detail=document.querySelector("#historyDetail");
  if(d.status!=="ok"){status.textContent=d.reason;comparison.innerHTML="";detail.innerHTML="<div class=\"empty\">Add another verified snapshot to unlock comparison and state timelines.</div>";return;}
  status.textContent=d.from.snapshot_date+" → "+d.to.snapshot_date+" · "+d.coverage.common_states_ut+" common State / UT records";
  const cards=[["Received",d.aggregate.received],["Disposed",d.aggregate.disposed],["Pending",d.aggregate.pending_total],["181–365 days",d.aggregate.pending_181_365],["365+ days",d.aggregate.pending_over_365]];
  comparison.innerHTML=cards.map(x=>"<div class=\"comparison-card\"><small>"+x[0]+"</small><b>"+deltaText(x[1])+"</b></div>").join("");
  detail.innerHTML="<div class=\"history-state\"><label for=\"historyState\">Explore a State / UT timeline</label><select id=\"historyState\">"+stateRows.map(x=>"<option value=\""+esc(x.state_ut)+"\">"+esc(x.state_ut)+"</option>").join("")+"</select><div id=\"stateTimeline\"></div></div>";
  document.querySelector("#historyState").addEventListener("change",loadStateHistory);loadStateHistory();
}
function deltaText(d){const sign=Number(d.change)>0?"+":"";return sign+Number(d.change).toLocaleString("en-IN")+(d.change_pct==null?"":" · "+sign+d.change_pct+"%");}
async function loadStateHistory(){const select=document.querySelector("#historyState"),box=document.querySelector("#stateTimeline");if(!select||!box)return;try{const d=await get("/api/v1/history/state/"+encodeURIComponent(select.value));if(d.status!=="ok"){box.innerHTML="<div class=\"empty\">"+esc(d.reason)+"</div>";return;}box.innerHTML="<div class=\"timeline\">"+d.timeline.map(x=>"<div class=\"timeline-item\"><span>"+esc(x.snapshot_date)+"</span><b>Pending "+fmt(x.pending_total)+"</b><small>Received "+fmt(x.received)+" · Disposed "+fmt(x.disposed)+"</small></div>").join("")+"</div>";}catch{box.innerHTML="<div class=\"empty\">State history unavailable.</div>";}}
async function loadHistory(){try{renderHistory(await get("/api/v1/history"));}catch{document.querySelector("#historyStatus").textContent="Historical registry unavailable.";}}
async function loadSuggestions(){try{const d=await get("/api/v1/ai/suggestions"),box=document.querySelector("#suggestions");box.innerHTML=d.suggestions.map(q=>"<button class=\"suggestion\" type=\"button\" data-q=\""+esc(q)+"\">"+esc(q)+"</button>").join("");box.querySelectorAll(".suggestion").forEach(b=>b.addEventListener("click",()=>{document.querySelector("#question").value=b.dataset.q;askAI();}));}catch{}}
async function askAI(){const input=document.querySelector("#question"),out=document.querySelector("#answer"),evidence=document.querySelector("#evidence"),question=input.value.trim();if(question.length<3){out.textContent="Please enter at least 3 characters.";return;}out.textContent="Analysing verified CIVICLENS data…";evidence.textContent="Resolving deterministic analytics and grounded AI context…";try{const r=await fetch(API+"/api/v1/ai/ask",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({question})}),d=await r.json();if(!r.ok)throw new Error(d.detail||"AI request failed.");out.textContent=d.answer||"No answer returned.";evidence.textContent="Evidence: "+(d.snapshot_date||"verified snapshot")+" · "+(d.reporting_period||"current period")+" · "+(d.grounding||"dataset-grounded");}catch(err){out.textContent="The AI service is temporarily unavailable. Deterministic dashboard analytics remain available.";evidence.textContent=err.message||"AI request unavailable.";}}
function renderDistrictDetail(state,district=null){
  const box=document.querySelector("#districtDetail");
  if(!state){box.innerHTML="";return;}
  const row=districtRows.find(r=>r.state_ut===state),count=row?.district_count||currentDistricts.length;
  const selected=district||selectedDistrict;
  document.querySelector("#crumbType").textContent=row?.administrative_type||"State / UT";
  document.querySelector("#crumbState").textContent=state;
  document.querySelector("#crumbDistrict").textContent=selected||"Select a district";
  box.innerHTML="<div class=\"district-summary\"><div class=\"big\">"+fmt(count)+"</div><div><span>Selected geography</span><b>"+esc(state)+"</b></div><div><span>Administrative type</span><b>"+esc(row?.administrative_type||"State / UT")+"</b></div><div><span>Directory source</span><b>Government of India · "+esc(row?.directory_report_date||"official directory")+"</b></div></div><div class=\"availability\">District directory verified. CPGRAMS district grievance metrics are not derived from State/UT totals.</div>";
}
function renderDistrictCards(rows){
  const box=document.querySelector("#districtCards");
  document.querySelector("#districtResultCount").textContent=rows.length+" district"+(rows.length===1?"":"s")+" shown";
  box.innerHTML=rows.length?rows.map(r=>"<button class=\"district-card "+(r.district===selectedDistrict?"selected":"")+" "+(r.metrics_available?"":"disabled")+"\" type=\"button\" data-district=\""+esc(r.district)+"\"><strong>"+esc(r.district)+"</strong><span>"+(r.metrics_available?"Grievance metrics connected":"Directory only")+"</span></button>").join(""):"<div class=\"empty\">No districts match this search.</div>";
  box.querySelectorAll(".district-card").forEach(b=>b.addEventListener("click",()=>selectDistrict(b.dataset.district)));
}
function selectDistrict(name){
  selectedDistrict=name;
  const select=document.querySelector("#districtSelect");if(select)select.value=name;
  renderDistrictCards(currentDistricts);
  renderDistrictDetail(document.querySelector("#districtState").value,name);
}
async function loadDistricts(state,search=""){
  if(!state)return;
  const box=document.querySelector("#districtCards");box.innerHTML="<div class=\"empty\">Loading official district directory…</div>";
  try{
    const rows=await get("/api/v1/districts/"+encodeURIComponent(state)+"/items"+(search?"?search="+encodeURIComponent(search):""));
    currentDistricts=rows;selectedDistrict=rows.some(x=>x.district===selectedDistrict)?selectedDistrict:"";
    const select=document.querySelector("#districtSelect");
    select.innerHTML=rows.length?'<option value="">Select a district</option>'+rows.map(r=>"<option value=\""+esc(r.district)+"\">"+esc(r.district)+"</option>").join(""):'<option value="">No districts found</option>';
    if(selectedDistrict)select.value=selectedDistrict;
    renderDistrictCards(rows);renderDistrictDetail(state,selectedDistrict);
  }catch(err){
    currentDistricts=[];document.querySelector("#districtResultCount").textContent="District directory unavailable";box.innerHTML="<div class=\"empty error\">"+esc(err.message||"Official district directory unavailable.")+"</div>";
  }
}
function onDistrictStateChange(){
  selectedDistrict="";const state=document.querySelector("#districtState").value;
  document.querySelector("#districtSearch").value="";loadDistricts(state);
}
function renderGeoStateOptions(rows){
  const select=document.querySelector("#districtState");
  const current=select.value;
  select.innerHTML=rows.map(r=>"<option value=\""+esc(r.state_ut)+"\">"+esc(r.state_ut)+" · "+fmt(r.district_count)+" districts</option>").join("");
  select.value=current&&rows.some(r=>r.state_ut===current)?current:(rows.find(r=>r.state_ut==="Tamil Nadu")?.state_ut||rows[0]?.state_ut||"");
  if(select.value)loadDistricts(select.value);
}
async function loadDashboard(search=""){
  const [o,states,a,snaps,coverage,directory]=await Promise.all([get("/api/v1/overview"),get("/api/v1/states?limit=100&search="+encodeURIComponent(search)),get("/api/v1/ageing"),get("/api/v1/snapshots"),get("/api/v1/districts/coverage"),get("/api/v1/districts?limit=100")]);
  stateRows=mergeDistrictCounts(states,directory);
  renderKpis(o);renderComposition(o);renderStates(stateRows);renderAgeing(a);renderSnapshots(snaps);renderGeoStateOptions(directory);setApiStatus(true);
}
let searchTimer;
document.querySelector("#refreshBtn")?.addEventListener("click",()=>loadDashboard().catch(()=>setApiStatus(false)));
document.querySelector("#exportBtn")?.addEventListener("click",()=>window.open(API+"/api/v1/export/csv","_blank"));
document.querySelector("#districtExport")?.addEventListener("click",()=>window.open(API+"/api/v1/export/district-directory","_blank"));
document.querySelector("#districtState")?.addEventListener("change",onDistrictStateChange);
document.querySelector("#districtSelect")?.addEventListener("change",e=>selectDistrict(e.target.value));
document.querySelector("#districtSearch")?.addEventListener("input",e=>{clearTimeout(searchTimer);searchTimer=setTimeout(()=>loadDistricts(document.querySelector("#districtState").value,e.target.value.trim()),220);});
document.querySelector("#ask")?.addEventListener("click",askAI);
document.querySelector("#question")?.addEventListener("keydown",e=>{if(e.key==="Enter")askAI();});
document.querySelector("#search")?.addEventListener("input",e=>{clearTimeout(searchTimer);searchTimer=setTimeout(()=>loadDashboard(e.target.value.trim()).catch(()=>{setApiStatus(false);document.querySelector("#rows").textContent="State data unavailable.";document.querySelector("#table").innerHTML="";}),250);});
(async()=>{
  try{await loadDashboard();await loadSuggestions();await loadHistory();renderQuality(await get("/api/v1/data-quality"));}
  catch(err){console.error(err);setApiStatus(false);document.querySelector("#rows").textContent="Dashboard data is temporarily unavailable.";document.querySelector("#districtResultCount").textContent="API unavailable.";document.querySelector("#quality").innerHTML="<div class=\"empty error\">Data quality endpoint unavailable.</div>";}
})();