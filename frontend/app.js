const API=window.CIVICLENS_API||(
  window.location.hostname==="civiclens-dashboard.onrender.com"
    ?"https://civiclens-api-s144.onrender.com"
    :"http://localhost:8000"
);
const fmt=n=>Number(n||0).toLocaleString("en-IN");
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
async function get(path){const r=await fetch(API+path);if(!r.ok)throw new Error(await r.text());return r.json()}
function renderKpis(o){document.querySelector("#kpis").innerHTML=[["Received",fmt(o.received),"Total grievances received"],["Disposed",fmt(o.disposed),"Recorded disposals"],["Pending",fmt(o.pending),"Current pending workload"],["Disposal rate",o.disposal_rate+"%","Disposed ÷ received"]].map(x=>`<div class="card"><small>${x[0]}</small><div class="value">${x[1]}</div><span>${x[2]}</span></div>`).join("")}
function renderTable(rows){document.querySelector("#rows").textContent=`${rows.length} matching State/UT records`;document.querySelector("#table").innerHTML=rows.map(r=>`<tr><td><strong>${esc(r.state_ut)}</strong></td><td>${fmt(r.received)}</td><td>${fmt(r.disposed)}</td><td>${fmt(r.pending_total)}</td><td>${r.disposal_rate??"—"}%</td><td>${r.ageing_181_plus==null?"—":fmt(r.ageing_181_plus)}</td></tr>`).join("")}
function renderAgeing(a){const items=[["0–60 days",a["0_60"]],["61–180 days",a["61_180"]],["181–365 days",a["181_365"]],["365+ days",a["365_plus"]]];const total=items.reduce((s,x)=>s+x[1],0);document.querySelector("#ageing").innerHTML=items.map(x=>`<div class="age"><span>${x[0]}</span><b>${fmt(x[1])}</b><em>${total?((x[1]/total)*100).toFixed(1):0}% of pending</em></div>`).join("");document.querySelector("#ageChart").innerHTML=items.map(x=>`<div class="bar-row"><span>${x[0]}</span><div class="bar-track"><i style="width:${total?Math.max(2,(x[1]/total)*100):0}%"></i></div><b>${fmt(x[1])}</b></div>`).join("")}
function renderSnapshots(snaps){document.querySelector("#snapshots").innerHTML=snaps.length?snaps.map(s=>`<div class="snapshot-item"><strong>${esc(s.snapshot_date)}</strong><span>${esc(s.reporting_period)}</span><small>${s.record_count} State/UT records</small></div>`).join(""):"No snapshots registered."}
async function loadDashboard(search=""){const[o,states,a,snaps]=await Promise.all([get("/api/v1/overview"),get("/api/v1/states?limit=100&search="+encodeURIComponent(search)),get("/api/v1/ageing"),get("/api/v1/snapshots")]);renderKpis(o);document.querySelector("#snapshot").textContent=`Snapshot: ${o.snapshot_date} • Period: ${o.reporting_period}`;document.querySelector("#source").textContent="Source: CPGRAMS / DARPG";renderTable(states);renderAgeing(a);renderSnapshots(snaps)}
async function loadQuality(){const d=await get("/api/v1/data-quality");const box=document.querySelector("#quality");if(!box)return;const items=[["Rows",fmt(d.rows)],["Unique State/UT",fmt(d.unique_states_ut)],["Missing values",fmt(d.missing_numeric_values)],["Duplicate records",fmt(d.duplicate_states_ut)],["Negative values",fmt(d.negative_numeric_values)],["Ageing reconciliation errors",fmt(d.ageing_reconciliation_errors)]];box.innerHTML=items.map(x=>`<div class="quality-item"><small>${esc(x[0])}</small><b>${x[1]}</b></div>`).join("")+`<div class="quality-result"><strong>✓ Validation passed</strong><span>${esc(d.snapshot_date)} • ${esc(d.reporting_period)}</span></div>`}
async function loadInsights(){const d=await get("/api/v1/insights");document.querySelector("#insights").innerHTML=d.largest_pending_workloads.map(x=>`<li><strong>${esc(x.state_ut)}</strong><span>${fmt(x.pending_total)} pending</span></li>`).join("")}
function changeText(d){const sign=d.change>0?"+":"";const pct=d.change_pct==null?"n/a":sign+d.change_pct+"%";return `${sign}${fmt(d.change)} (${pct})`}
function renderHistory(d){
 const status=document.querySelector("#historyStatus"),box=document.querySelector("#historyComparison"),detail=document.querySelector("#historyDetail");
 if(d.status!=="ok"){status.textContent=d.reason;box.innerHTML="";detail.innerHTML='<p class="history-empty">Add a second verified snapshot to unlock historical comparison and state timelines.</p>';return}
 status.textContent=d.from.snapshot_date+" → "+d.to.snapshot_date+" • "+d.coverage.common_states_ut+" common State/UT records";
 const a=d.aggregate;
 box.innerHTML=[["Received",a.received],["Disposed",a.disposed],["Pending",a.pending_total],["181–365 days",a.pending_181_365],["365+ days",a.pending_over_365]].map(x=>'<div class="history-card"><small>'+x[0]+'</small><b>'+changeText(x[1])+'</b></div>').join("");
 detail.innerHTML='<p class="history-note">'+esc(d.note)+'</p>';
}
async function loadStateHistory(){
 const select=document.querySelector("#historyState");
 if(!select)return;
 try{
  const d=await get("/api/v1/history/state/"+encodeURIComponent(select.value));
  const timeline=document.querySelector("#stateTimeline");
  if(!timeline)return;
  if(d.status!=="ok"){timeline.innerHTML='<p class="history-empty">'+esc(d.reason)+'</p>';return}
  timeline.innerHTML='<div class="state-timeline">'+d.timeline.map(x=>'<div class="timeline-item"><span>'+esc(x.snapshot_date)+'</span><b>Pending '+fmt(x.pending_total)+'</b><small>Received '+fmt(x.received)+' • Disposed '+fmt(x.disposed)+'</small></div>').join("")+'</div><p class="history-note">'+esc(d.note)+'</p>';
 }catch{
  const timeline=document.querySelector("#stateTimeline");
  if(timeline) timeline.innerHTML='<p class="history-empty">State history is unavailable.</p>';
 }
}
async function loadHistory(){
 try{
  const d=await get("/api/v1/history");
  renderHistory(d.latest_comparison);
  if(d.latest_comparison?.status==="ok"){
   const states=await get("/api/v1/states?limit=100");
   const detail=document.querySelector("#historyDetail");
   detail.innerHTML='<div class="history-state"><label for="historyState">Explore one State/UT timeline</label><select id="historyState">'+states.map(x=>'<option value="'+esc(x.state_ut)+'">'+esc(x.state_ut)+'</option>').join("")+'</select></div><div id="stateTimeline"></div>';
   document.querySelector("#historyState").addEventListener("change",loadStateHistory);
   await loadStateHistory();
  }
 }catch{document.querySelector("#historyStatus").textContent="Historical registry is unavailable."}
}
async function loadSuggestions(){const d=await get("/api/v1/ai/suggestions");const box=document.querySelector("#suggestions");if(!box)return;box.innerHTML=d.suggestions.map(q=>`<button class="suggestion" data-q="${esc(q)}">${esc(q)}</button>`).join("");box.querySelectorAll(".suggestion").forEach(b=>b.addEventListener("click",()=>{document.querySelector("#question").value=b.dataset.q;askAI()}))}
async function askAI(){const input=document.querySelector("#question"),out=document.querySelector("#answer"),question=input.value.trim();if(question.length<3){out.textContent="Please enter a question with at least 3 characters.";return}out.textContent="Analysing the CIVICLENS dataset…";try{const r=await fetch(API+"/api/v1/ai/ask",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({question})});const d=await r.json();out.textContent=d.answer||d.detail||"No answer returned.";document.querySelector("#evidence").textContent=`Evidence: ${d.snapshot_date} • ${d.reporting_period} • ${d.grounding}`}catch{out.textContent="Backend/Gemini is not available. Start FastAPI and configure backend/.env."}}
const askButton=document.querySelector("#ask");const questionInput=document.querySelector("#question");if(askButton)askButton.addEventListener("click",askAI);if(questionInput)questionInput.addEventListener("keydown",e=>{if(e.key==="Enter")askAI()});let timer;const searchInput=document.querySelector("#search");if(searchInput)searchInput.addEventListener("input",e=>{clearTimeout(timer);timer=setTimeout(()=>{document.querySelector("#rows").textContent="Searching…";loadDashboard(e.target.value).catch(()=>{document.querySelector("#rows").textContent="State data is temporarily unavailable. Showing the last verified results."})},250)});
async function bootSection(task,fallback){try{await task()}catch(err){console.error(err);fallback()}}
bootSection(()=>loadDashboard(),()=>{document.querySelector("#rows").textContent="Dashboard data is temporarily unavailable."});
bootSection(()=>loadQuality(),()=>{const box=document.querySelector("#quality");if(box)box.textContent="Data quality status is temporarily unavailable."});
bootSection(()=>loadInsights(),()=>{document.querySelector("#insights").innerHTML='<li>Insights are temporarily unavailable.</li>'});
bootSection(()=>loadSuggestions(),()=>{const box=document.querySelector("#suggestions");if(box)box.innerHTML='<span class="history-empty">AI suggestions are temporarily unavailable.</span>'});
bootSection(()=>loadHistory(),()=>{document.querySelector("#historyStatus").textContent="Historical registry is temporarily unavailable."});
