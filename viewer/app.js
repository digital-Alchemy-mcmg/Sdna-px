const canvas=document.getElementById("canvas"),ctx=canvas.getContext("2d");
const file=document.getElementById("file"),detail=document.getElementById("detail"),run=document.getElementById("run"),status=document.getElementById("status");
let payload=null,points=[],yaw=-0.65,pitch=0.42,drag=false,lastX=0,lastY=0,screenPoints=[];
const fallback={plane_01:"#3B82F6",plane_02:"#F59E0B",plane_03:"#64748B",plane_04:"#EC4899",plane_05:"#8B5CF6",plane_06:"#10B981"};
function resize(){const d=devicePixelRatio||1;canvas.width=Math.floor(canvas.clientWidth*d);canvas.height=Math.floor(canvas.clientHeight*d);ctx.setTransform(d,0,0,d,0,0);draw()}
new ResizeObserver(resize).observe(canvas);
function colorMap(){const map={...fallback};if(payload)for(const p of payload.spatial_configuration?.active_lateral_planes||[])map[p.plane_id]=p.color_hex||map[p.plane_id];return map}
function rotate(p){const cy=Math.cos(yaw),sy=Math.sin(yaw),cp=Math.cos(pitch),sp=Math.sin(pitch);const x=p.x*cy-p.z*sy,z1=p.x*sy+p.z*cy;const y=p.y*cp-z1*sp,z=p.y*sp+z1*cp;return{x,y,z}}
function project(p){const r=rotate(p),w=canvas.clientWidth,h=canvas.clientHeight,scale=Math.min(w,h)/28,depth=34+r.z,fac=34/depth;return{x:w/2+r.x*scale*fac,y:h/2-r.y*scale*fac,z:r.z,fac}}
function drawAxes(){const o=project({x:0,y:0,z:0});for(const [v,c] of [[{x:10,y:0,z:0},"#4a5c76"],[{x:0,y:5,z:0},"#4a5c76"],[{x:0,y:0,z:10},"#4a5c76"]]){const e=project(v);ctx.strokeStyle=c;ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(o.x,o.y);ctx.lineTo(e.x,e.y);ctx.stroke()}}
function draw(){const w=canvas.clientWidth,h=canvas.clientHeight;ctx.clearRect(0,0,w,h);ctx.fillStyle="#090d14";ctx.fillRect(0,0,w,h);drawAxes();if(!payload)return;const colors=colorMap(),origin=project({x:0,y:0,z:0});screenPoints=[];
const ordered=[...points].sort((a,b)=>rotate(a).z-rotate(b).z);
for(const a of ordered){const p=project(a);if(a.binding_class==="DIRECT_BIND"||a.binding_class==="TRANSFERABLE_BIND"){ctx.save();ctx.strokeStyle=(colors[a.plane_id]||"#93a4bb")+"66";ctx.lineWidth=a.binding_class==="DIRECT_BIND"?1.5:1;ctx.setLineDash(a.binding_class==="DIRECT_BIND"?[]:[5,5]);ctx.beginPath();ctx.moveTo(origin.x,origin.y);ctx.lineTo(p.x,p.y);ctx.stroke();ctx.restore()}}
for(const a of ordered){const p=project(a),r=Math.max(3,5*p.fac);ctx.beginPath();ctx.arc(p.x,p.y,r,0,Math.PI*2);ctx.fillStyle=colors[a.plane_id]||"#93a4bb";ctx.globalAlpha=a.binding_class==="NON_BIND"?.28:1;ctx.fill();ctx.globalAlpha=1;if(a.polarity_zone==="FLOOR"){ctx.strokeStyle="#ff6b6b";ctx.lineWidth=1.5;ctx.stroke()}screenPoints.push({a,x:p.x,y:p.y,r:r+5})}
status.textContent=`${points.length} atoms | ${payload.strategy_id||"derived strategy"} | fingerprint ${(payload.run_fingerprint_sha256||"").slice(0,12)}…`;
run.textContent=JSON.stringify({counts:payload.spatial_configuration?.counts,active_planes:payload.spatial_configuration?.active_lateral_planes,strategy_id:payload.strategy_id,fingerprint:payload.run_fingerprint_sha256},null,2)}
file.addEventListener("change",async()=>{const f=file.files[0];if(!f)return;try{payload=JSON.parse(await f.text());if(payload.contract_version!=="MARA_LAYOUT_PAYLOAD_v1")throw new Error("Not MARA_LAYOUT_PAYLOAD_v1");points=payload.spatial_atoms_projection||[];detail.textContent="None";draw()}catch(e){status.textContent=e.message}});
canvas.addEventListener("pointerdown",e=>{drag=true;lastX=e.clientX;lastY=e.clientY;canvas.setPointerCapture(e.pointerId)});
canvas.addEventListener("pointermove",e=>{if(!drag)return;yaw+=(e.clientX-lastX)*.008;pitch=Math.max(-1.25,Math.min(1.25,pitch+(e.clientY-lastY)*.008));lastX=e.clientX;lastY=e.clientY;draw()});
canvas.addEventListener("pointerup",()=>drag=false);
canvas.addEventListener("click",e=>{let best=null,bd=Infinity;for(const p of screenPoints){const d=Math.hypot(e.offsetX-p.x,e.offsetY-p.y);if(d<p.r&&d<bd){best=p;bd=d}}if(best)detail.textContent=JSON.stringify(best.a,null,2)});
resize();
