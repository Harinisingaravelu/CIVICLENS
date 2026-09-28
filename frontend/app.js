const API = "http://localhost:8000";

const fmt = n => Number(n||0).toLocaleString("en-IN");

async function load(){
  const overview = await fetch(API+"/api/v1/overview").then(r=>r.json());
  const states = await fetch(API+"/api/v1/states").then(r=>r.json());

  document.querySelector("#kpis").innerHTML = [
    ["Received",fmt(overview.received)],
    ["Disposed",fmt(overview.disposed)],
    ["Pending",fmt(overview.pending)],
    ["Disposal rate",(overview.disposal_rate||0)+"%"]
  ].map(([label,value])=>`<div class="card"><small>${label}</small><div class="value">${value}</div></div>`).join("");

  document.querySelector("#rows").textContent = states.length+" records";
  document.querySelector("#table").innerHTML = states.map(r=>`
    <tr><td>${r.state_ut||""}</td><td>${fmt(r.received)}</td><td>${fmt(r.disposed)}</td><td>${fmt(r.pending_total)}</td></tr>
  `).join("");
}
load().catch(err=>console.error("CIVICLENS API unavailable",err));
