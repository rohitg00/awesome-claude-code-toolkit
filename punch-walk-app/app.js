const $ = (s) => document.querySelector(s);
const items = [{ notes: [], photos: [], status: "pending" }];
let current = 0, seconds = 0, heading = 0, recording = false, recorder;
const parties = ["Architect", "Owner", "End-user", "Engineer", "Special inspector", "Internal PM / Super"];

function item() { return items[current]; }
function refresh() {
  $("#counter").textContent = String(current).padStart(2, "0");
  $("#noteCount").textContent = item().notes.length ? `${item().notes.length} NOTE${item().notes.length > 1 ? "S" : ""}` : "ADD DETAIL";
  $("#photoCount").textContent = `${item().photos.length} PHOTO${item().photos.length === 1 ? "" : "S"}`;
}
function move(delta) { current = Math.max(0, current + delta); while (items.length <= current) items.push({notes:[], photos:[], status:"pending"}); refresh(); }
$("#prevItem").onclick = () => move(-1); $("#nextItem").onclick = () => move(1);
$("#counter").onclick = () => { const n = prompt("Go to item number", current); if (/^\d+$/.test(n)) { current = +n; while(items.length <= current) move(1); refresh(); } };

$("#drawingInput").onchange = (e) => { if (!e.target.files[0]) return; $("#startWalk").disabled = false; $("#drawing").style.backgroundImage += `,url(${URL.createObjectURL(e.target.files[0])})`; };
$("#startWalk").onclick = () => { $("#setup").classList.remove("open"); startSensors(); };
function startSensors() {
  if (navigator.geolocation) navigator.geolocation.watchPosition(async p => {
    $("#accuracy").textContent = `GPS · ±${Math.round(p.coords.accuracy)} FT`;
    $("#locationDot").style.left = `${Math.sin(p.coords.longitude * 1000) * 12}px`;
    $("#locationDot").style.top = `${Math.cos(p.coords.latitude * 1000) * 12}px`;
  }, () => $("#accuracy").textContent = "GPS UNAVAILABLE", {enableHighAccuracy:true});
  const orient = e => { heading = e.webkitCompassHeading || (360 - (e.alpha || 0)); $("#locationDot i").style.transform = `rotate(${heading}deg)`; };
  if (typeof DeviceOrientationEvent !== "undefined" && DeviceOrientationEvent.requestPermission) DeviceOrientationEvent.requestPermission().then(x => x === "granted" && addEventListener("deviceorientation", orient)); else addEventListener("deviceorientation", orient);
}
setInterval(() => { seconds++; $("#timer").textContent = `${String(seconds/60|0).padStart(2,"0")}:${String(seconds%60).padStart(2,"0")}`; }, 1000);
$("#noteBtn").onclick = () => { $("#noteItem").textContent = String(current).padStart(2,"0"); $("#noteText").value = item().notes.join("\n"); $("#noteDialog").showModal(); };
$("#saveNote").onclick = () => { item().notes = $("#noteText").value.trim() ? [$("#noteText").value.trim()] : []; setTimeout(refresh); };
$("#cameraBtn").onclick = () => { if(recording) toggleRecord(); $("#cameraInput").click(); };
$("#cameraInput").onchange = e => { item().photos.push(...[...e.target.files].map(f => ({name:f.name,url:URL.createObjectURL(f)}))); refresh(); };
async function toggleRecord() { if (!recording) { try { const stream=await navigator.mediaDevices.getUserMedia({audio:true}); recorder=new MediaRecorder(stream); recorder.start(); recording=true; } catch { alert("Microphone access is required to record audio."); } } else { recorder?.stop(); recorder?.stream.getTracks().forEach(t=>t.stop()); recording=false; } $("#recordBtn").classList.toggle("active",recording); $("#recordBtn b").textContent=recording?"LIVE":"REC"; }
$("#recordBtn").onclick = toggleRecord;
$("#stopBtn").onclick = () => { if(recording) toggleRecord(); renderSummary(); $("#summaryDialog").showModal(); };
$("#resumeBtn").onclick = () => $("#summaryDialog").close();
function renderSummary(){ $("#summaryList").innerHTML=items.map((x,i)=>`<div class="summary-item"><span>${String(i).padStart(2,"0")}</span><div><b>${x.notes[0]||"Untitled item"}</b><p>${x.photos.length} photos · GPS tagged · ${Math.round(heading)}°</p></div><button onclick="editItem(${i})">Edit</button></div>`).join(""); }
window.editItem = i => { current=i; refresh(); $("#summaryDialog").close(); $("#noteBtn").click(); };
$("#completeBtn").onclick = () => { $("#summaryDialog").close(); $("#detailsDialog").showModal(); };
$("#parties").innerHTML=parties.map(p=>`<label class="check"><input type="checkbox" value="${p}">${p}</label>`).join("");
$("#detailsForm").onsubmit = e => { e.preventDefault(); $("#detailsDialog").close(); generateReport(); };
function generateReport(){ $("#app").hidden=true; $("#report").hidden=false; $("#reportProject").textContent=$("#projectName").value; $("#reportMeta").textContent=`${$("#projectAddress").value} · ${new Date().toLocaleDateString("en-US",{dateStyle:"long"})}`; $("#reportItems").innerHTML=items.map((x,i)=>`<article class="report-card"><h3>${String(i).padStart(2,"0")}</h3><div><h3>${x.notes[0]||"Punch item"}</h3><p>${x.photos.length} attached photo${x.photos.length===1?"":"s"} · Location verified</p></div><div class="status" data-i="${i}">${["pending","ready for review","accepted"].map(s=>`<button class="${x.status===s?"active":""}" data-status="${s}">${s.toUpperCase()}</button>`).join("")}</div></article>`).join(""); document.querySelectorAll(".status button").forEach(b=>b.onclick=()=>{const i=+b.parentElement.dataset.i;items[i].status=b.dataset.status;b.parentElement.querySelectorAll("button").forEach(x=>x.classList.toggle("active",x===b));$("#ownerBtn").disabled=!items.every(x=>x.status==="accepted");}); }
$("#ownerBtn").onclick=()=>$("#emailDialog").showModal();
const canvas=$("#signature"), ctx=canvas.getContext("2d"); let drawing=false; const point=e=>{const r=canvas.getBoundingClientRect(),t=e.touches?.[0]||e;return[(t.clientX-r.left)*canvas.width/r.width,(t.clientY-r.top)*canvas.height/r.height]}; canvas.onpointerdown=e=>{drawing=true;ctx.beginPath();ctx.moveTo(...point(e))}; canvas.onpointermove=e=>{if(drawing){ctx.lineTo(...point(e));ctx.strokeStyle="#111";ctx.lineWidth=3;ctx.stroke()}}; canvas.onpointerup=()=>drawing=false;
refresh();
