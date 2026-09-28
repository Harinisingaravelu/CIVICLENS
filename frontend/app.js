const API = window.CIVICLENS_API || "http://localhost:8000";
const fmt = n => Number(n || 0).toLocaleString("en-IN");
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

async function get(path) {
  const r = await fetch(API + path);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

function renderKpis(o) {
  document.querySelector("#kpis").innerHTML = [
    ["Received", fmt(o.received), "Total grievances received"],
    ["Disposed", fmt(o.disposed), "Recorded disposals"],
    ["Pending", fmt(o.pending), "Current pending workload"],
    ["Disposal rate", `${o.disposal_rate}%`, "Disposed ÷ received"]
  ].map(([label,value,note]) => `<div class="card"><small>${label}</small><div class="value">${value}</div><span>${note}</span></div>`).join("");
}

function renderTable(rows) {
  document.querySelector("#rows").textContent = `${rows.length} matching State/UT records`;
  document.querySelector("#table").innerHTML = rows.map(r => `
    <tr><td><strong>${esc(r.state_ut)}</strong></td><td>${fmt(r.received)}</td><td>${fmt(r.disposed)}</td><td>${fmt(r.pending_total)}</td><td>${r.disposal_rate ?? "—"}%</td><td>${r.ageing_181_plus == null ? "—" : fmt(r.ageing_181_plus)}</td></tr>`).join("");
}

function renderAgeing(a) {
  document.querySelector("#ageing").innerHTML = [
    ["0–60 days",a["0_60"]],["61–180 days",a["61_180"]],["181–365 days",a["181_365"]],["365+ days",a["365_plus"]]
  ].map(([label,value]) => `<div class="age"><span>${label}</span><b>${fmt(value)}</b></div>`).join("");
}

async function loadDashboard(search="") {
  const [o,states,ageing] = await Promise.all([get("/api/v1/overview"),get(`/api/v1/states?limit=100&search=${encodeURIComponent(search)}`),get("/api/v1/ageing")]);
  renderKpis(o);
  document.querySelector("#snapshot").textContent = `Official-source snapshot: ${o.snapshot_date} • Reporting period: ${o.reporting_period}`;
  renderTable(states);
  renderAgeing(ageing);
}

async function loadInsights() {
  const data = await get("/api/v1/insights");
  document.querySelector("#insights").innerHTML = data.largest_pending_workloads.map(x => `<li><strong>${esc(x.state_ut)}</strong><span>${fmt(x.pending_total)} pending</span></li>`).join("");
}

async function askAI() {
  const input=document.querySelector("#question"), out=document.querySelector("#answer"), question=input.value.trim();
  if(question.length<3){out.textContent="Please enter a question with at least 3 characters.";return;}
  out.textContent="Analysing the CIVICLENS dataset…";
  try{
    const r=await fetch(API+"/api/v1/ai/ask",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({question})});
    const data=await r.json(); out.textContent=data.answer||data.detail||"No answer returned.";
  }catch{out.textContent="Backend/Gemini is not available. Start FastAPI and configure backend/.env.";}
}
document.querySelector("#ask").addEventListener("click",askAI);
document.querySelector("#question").addEventListener("keydown",e=>{if(e.key==="Enter")askAI()});
document.querySelector("#search").addEventListener("input",e=>loadDashboard(e.target.value).catch(console.error));
Promise.all([loadDashboard(),loadInsights()]).catch(err=>{console.error(err);document.querySelector("#rows").textContent="API unavailable — start FastAPI";});
