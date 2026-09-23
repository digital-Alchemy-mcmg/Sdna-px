import React,{useState} from "react";
import SpatialStage from "./SpatialStage.jsx";

export default function App(){
  const [payload,setPayload]=useState(null);
  const [selected,setSelected]=useState(null);
  const [error,setError]=useState("");
  async function load(e){
    const f=e.target.files?.[0]; if(!f)return;
    try{
      const p=JSON.parse(await f.text());
      if(p.contract_version!=="MARA_LAYOUT_PAYLOAD_v1") throw new Error("Expected MARA_LAYOUT_PAYLOAD_v1");
      setPayload(p); setSelected(null); setError("");
    }catch(err){setError(String(err.message||err)); setPayload(null);}
  }
  const counts=payload?.spatial_configuration?.counts;
  return <main>
    <header>
      <div><strong>Spatial DNA</strong><span>Passive Observer</span></div>
      <label>Load projection<input type="file" accept=".json,application/json" onChange={load}/></label>
    </header>
    <section className="grid">
      <div className="stage">
        {payload?<SpatialStage payload={payload} onSelect={setSelected}/>:<div className="empty">Load a MARA projection packet.</div>}
      </div>
      <aside>
        <h2>Run receipt</h2>
        {error&&<pre className="error">{error}</pre>}
        {payload&&<>
          <dl>
            <dt>Job</dt><dd>{payload.metadata?.target_job_id}</dd>
            <dt>Strategy</dt><dd>{payload.strategy_lock?.strategy_id||payload.strategy_id}</dd>
            <dt>Atoms</dt><dd>{counts?.total_atoms_evaluated}</dd>
            <dt>Direct</dt><dd>{counts?.direct_bind_count}</dd>
            <dt>Transfer</dt><dd>{counts?.transferable_bind_count}</dd>
            <dt>Non-bind</dt><dd>{counts?.non_bind_count}</dd>
          </dl>
          <code>{payload.run_fingerprint_sha256}</code>
        </>}
        <h2>Selected atom</h2>
        <pre>{selected?JSON.stringify(selected,null,2):"None"}</pre>
      </aside>
    </section>
  </main>
}
