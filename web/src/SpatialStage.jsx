import React,{useEffect,useRef} from "react";
import * as THREE from "three";
import {OrbitControls} from "three/examples/jsm/controls/OrbitControls.js";

const COLORS={plane_01:0x3b82f6,plane_02:0xf59e0b,plane_03:0x64748b,plane_04:0xec4899,plane_05:0x8b5cf6,plane_06:0x10b981};

export default function SpatialStage({payload,onSelect}){
  const host=useRef(null);
  useEffect(()=>{
    const el=host.current;
    const scene=new THREE.Scene(); scene.background=new THREE.Color(0x090d14);
    const camera=new THREE.PerspectiveCamera(45,1,.1,100); camera.position.set(18,12,18);
    const renderer=new THREE.WebGLRenderer({antialias:true}); renderer.setPixelRatio(Math.min(devicePixelRatio,2)); el.appendChild(renderer.domElement);
    const controls=new OrbitControls(camera,renderer.domElement); controls.target.set(0,0,0); controls.enableDamping=true;

    const box=new THREE.Box3(new THREE.Vector3(-10,-5,-10),new THREE.Vector3(10,5,10));
    scene.add(new THREE.Box3Helper(box,0x334155));
    for(const [y,color] of [[5,0x059669],[0,0x475569],[-5,0xdc2626]]){
      const g=new THREE.PlaneGeometry(20,20),m=new THREE.MeshBasicMaterial({color,transparent:true,opacity:y===0?.12:.06,side:THREE.DoubleSide,depthWrite:false});
      const mesh=new THREE.Mesh(g,m); mesh.rotation.x=-Math.PI/2; mesh.position.y=y; scene.add(mesh);
    }
    scene.add(new THREE.AxesHelper(11));

    const objects=[];
    for(const edge of payload.graph_connection_rays||[]){
      const pts=[edge.source_coordinates,edge.target_coordinates].map(p=>new THREE.Vector3(p.x,p.y,p.z));
      const geo=new THREE.BufferGeometry().setFromPoints(pts);
      scene.add(new THREE.Line(geo,new THREE.LineBasicMaterial({color:0xcbd5e1,transparent:true,opacity:.22})));
    }
    for(const ray of payload.binding_rays||[]){
      const pts=[ray.from,ray.to].map(p=>new THREE.Vector3(p.x,p.y,p.z));
      const geo=new THREE.BufferGeometry().setFromPoints(pts);
      const mat=new THREE.LineDashedMaterial({color:0x94a3b8,transparent:true,opacity:.20,dashSize:.25,gapSize:.18});
      const line=new THREE.Line(geo,mat); if(ray.binding_class==="TRANSFERABLE_BIND")line.computeLineDistances(); scene.add(line);
    }

    for(const atom of payload.spatial_atoms_projection||[]){
      const radius=atom.binding_class==="DIRECT_BIND"?.18:atom.binding_class==="TRANSFERABLE_BIND"?.14:.10;
      const geo=new THREE.SphereGeometry(radius,16,12);
      const mat=new THREE.MeshBasicMaterial({color:COLORS[atom.plane_id]||0x94a3b8,transparent:true,opacity:atom.binding_class==="NON_BIND"?.3:1});
      const mesh=new THREE.Mesh(geo,mat); mesh.position.set(atom.x,atom.y,atom.z); mesh.userData.atom=atom;
      if(atom.polarity_zone==="FLOOR"){const ring=new THREE.Mesh(new THREE.RingGeometry(radius*1.25,radius*1.55,20),new THREE.MeshBasicMaterial({color:0xff6b6b,side:THREE.DoubleSide}));ring.position.copy(mesh.position);ring.lookAt(camera.position);scene.add(ring)}
      scene.add(mesh); objects.push(mesh);
    }

    const raycaster=new THREE.Raycaster(),mouse=new THREE.Vector2();
    function click(e){const r=renderer.domElement.getBoundingClientRect();mouse.x=((e.clientX-r.left)/r.width)*2-1;mouse.y=-((e.clientY-r.top)/r.height)*2+1;raycaster.setFromCamera(mouse,camera);const hit=raycaster.intersectObjects(objects,false)[0];if(hit)onSelect(hit.object.userData.atom)}
    renderer.domElement.addEventListener("click",click);

    function resize(){const w=el.clientWidth,h=el.clientHeight;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix()}
    const ro=new ResizeObserver(resize);ro.observe(el);resize();
    let id; function frame(){controls.update();renderer.render(scene,camera);id=requestAnimationFrame(frame)}frame();

    return()=>{cancelAnimationFrame(id);ro.disconnect();renderer.domElement.removeEventListener("click",click);controls.dispose();renderer.dispose();el.replaceChildren();};
  },[payload,onSelect]);
  return <div ref={host} className="three-host"/>;
}
