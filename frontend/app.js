const API = "http://localhost:8000";
const fmt = n => Number(n||0).toLocaleString("en-IN");

async function get(path){ const r=await fetch(API+path); if(!r.ok) throw new Error(await r.text()); return r.json(); }

async function load(){
  const [o, states, ageing] = await Promise.all([
    get("/api/v1/overview"), get("/api/v1/states"), get("/api/v1/ageing")
  ]);

  document.querySelector("#kpis").innerHTML = [
    ["Received",fmt(o.received)],
    ["Disposed",fmt(o.disposed)],
    ["Pending",fmt(o.pending)],
    ["Disposal rate",(o.disposal_rate||0)+"%"]
  ].map(([label,value])=>`<div class="card"><small>${label}</small><div class="value">${value}</div></div>`).join("");

  document.querySelector("#rows").textContent =
    `${o.states_ut_count} State/UT records • Snapshot ${o.snapshot_date}`;

  document.querySelector("#table").innerHTML = states.map(r=>`
    <tr>
      <td><strong>${r.state_ut}</strong></td>
      <td>${fmt(r.received)}</td>
      <td>${fmt(r.disposed)}</td>
      <td>${fmt(r.pending_total)}</td>
      <td>${r.disposal_rate}%</td>
    </tr>`).join("");

  document.querySelector("#ageing").innerHTML = [
    ["0–60 days",ageing["0_60"]],["61–180 days",ageing["61_180"]],
    ["181–365 days",ageing["181_365"]],["365+ days",ageing["365_plus"]]
  ].map(([label,value])=>`<div class="age"><span>${label}</span><b>${fmt(value)}</b></div>`).join("");
}

async function askAI(){
  const input=document.querySelector("#question");
  const out=document.querySelector("#answer");
  const question=input.value.trim();
  if(!question) return;
  out.textContent="Analysing the CIVICLENS dataset…";
  try{
    const r=await fetch(API+"/api/v1/ai/ask",{
      method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({question})
    });
    const data=await r.json();
    out.textContent=data.answer || data.detail || "No answer returned.";
  }catch(e){ out.textContent="Backend/Gemini is not available. Start the FastAPI server and check GEMINI_API_KEY."; }
}

document.querySelector("#ask").addEventListener("click",askAI);
document.querySelector("#question").addEventListener("keydown",e=>{if(e.key==="Enter")askAI()});
load().catch(err=>{console.error(err); document.querySelector("#rows").textContent="API unavailable — start FastAPI";});
