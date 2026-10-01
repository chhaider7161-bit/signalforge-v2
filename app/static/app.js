let expiry = 30;
const $ = id => document.getElementById(id);

async function loadAssets(){
  const res = await fetch("/api/assets");
  const assets = await res.json();
  $("asset").innerHTML = assets.map(a =>
    `<option value="${a.symbol}">${a.name}${a.otc ? " · OTC" : ""}</option>`
  ).join("");
}

async function loadHealth(){
  const res = await fetch("/health");
  const h = await res.json();
  const badge = $("statusBadge");
  const demo = !!h.demo_mode;
  badge.innerHTML = `<i></i> ${demo ? "DEMO" : "LIVE FEED"}`;
  badge.className = demo ? "live demo-badge" : "live";
  $("mode").textContent = demo
    ? "Synthetic test data • no automatic trading"
    : "External feed configured • signal-only";
}

document.querySelectorAll(".expiry button").forEach(b=>{
  b.onclick=()=>{
    document.querySelectorAll(".expiry button").forEach(x=>x.classList.remove("selected"));
    b.classList.add("selected");
    expiry=Number(b.dataset.exp);
  };
});

$("generate").onclick = async ()=>{
  const btn=$("generate");
  btn.disabled=true; btn.textContent="ANALYZING…";
  $("signal").classList.remove("empty");
  try{
    const res=await fetch("/api/signal",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({symbol:$("asset").value,expiry_seconds:expiry})});
    const s=await res.json();
    if(s.error){$("signal").textContent=s.error;return;}
    const cls=s.direction==="CALL"?"call":"put";
    $("signal").innerHTML=`
      <div class="signal-main">
        <div>
          <div class="direction ${cls}">${s.direction==="CALL"?"🟢 CALL / UP":"🔴 PUT / DOWN"}</div>
          <div class="meta">${s.asset_name} · ${s.expiry_seconds}s · Entry ${s.entry_price}<br>${s.reason||""}</div>
        </div>
        <div><div class="strength">${s.strength}%</div><div class="meta">model score</div></div>
      </div>`;
    await refresh();
  }catch(e){
    $("signal").textContent="Request failed. Check that the server is running.";
  }finally{
    btn.disabled=false; btn.textContent="GENERATE SIGNAL";
  }
};

function fmt(t){return t?new Date(t).toLocaleTimeString(): "—"}

async function refresh(){
  const [sr,hr]=await Promise.all([fetch("/api/stats"),fetch("/api/signals?limit=50")]);
  const s=await sr.json(), rows=await hr.json();
  $("winrate").textContent=s.win_rate.toFixed(2)+"%";
  $("total").textContent=s.total; $("wins").textContent=s.wins;
  $("losses").textContent=s.losses; $("pending").textContent=s.pending;
  $("history").innerHTML=rows.map(x=>{
    const dir=x.direction==="CALL"?"call":"put";
    const result=x.status==="WIN"?'<span class="win">WIN</span>':
      x.status==="LOSS"?'<span class="loss">LOSS</span>':'<span class="pending">PENDING</span>';
    return `<tr><td>${fmt(x.created_at)}</td><td>${x.asset_name}</td>
      <td class="${dir}">${x.direction}</td><td>${x.expiry_seconds}s</td>
      <td>${x.strength}%</td><td>${x.entry_price}</td><td>${result}</td></tr>`;
  }).join("");
}

loadAssets().catch(()=>{});
loadHealth().catch(()=>{});
refresh().catch(()=>{});
setInterval(()=>{refresh().catch(()=>{}); loadHealth().catch(()=>{});},2000);
