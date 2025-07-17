import React, { useState } from "react";

const ROLE_COLORS = {
  diagnosis: "#457b9d",
  logistics: "#f4a261",
  repair: "#2a9d8f",
  billing: "#e76f51",
  default: "#bcbcbc"
};

function ModalBase({ children, onClose }) {
  return (
    <div className="modal-backdrop">
      <div className="modal-container">
        <button className="modal-close" onClick={onClose}>&times;</button>
        {children}
      </div>
    </div>
  );
}

function ContractModal({ contract, onClose }) {
  if (!contract) return null;
  return (
    <ModalBase onClose={onClose}>
      <h3 className="modal-title">Data Sharing Contract</h3>
      <p><strong>Applicable Regulations:</strong> {contract.applicable_regulations?.length ? contract.applicable_regulations.join(', ') : 'None'}</p>
      <p><strong>Permitted Fields:</strong> {contract.permitted_fields?.length ? contract.permitted_fields.join(', ') : 'All'}</p>
      <p><strong>Expiry (hours):</strong> {contract.expiry_hours}</p>
      <p><strong>Policy:</strong> {contract.policy}</p>
    </ModalBase>
  );
}

function ProvenanceModal({ provenance, onClose }) {
  if (!provenance) return null;
  const isValid = provenance.signature?.length === 64;
  return (
    <ModalBase onClose={onClose}>
      <h3 className="modal-title">Provenance Details</h3>
      <p><strong>Step ID:</strong> <code>{provenance.step_id}</code></p>
      <p><strong>Agent ID:</strong> <code>{provenance.agent_id}</code></p>
      <p>
        <strong>Signature:</strong> <code className="break-word">{provenance.signature}</code> 
        <span className={isValid ? 'valid' : 'invalid'}>{isValid ? '✔' : '✖'}</span>
      </p>
    </ModalBase>
  );
}

export default function AgentGraph({ fellowship_graph }) {
  const [hovered, setHovered] = useState(null);
  const [modalContract, setModalContract] = useState(null);
  const [modalProvenance, setModalProvenance] = useState(null);

  // Download audit log as JSON
  const handleDownloadAudit = async () => {
    if (!fellowship_graph.nodes || !fellowship_graph.nodes.length) return;
    const ticketId = fellowship_graph.nodes[0].step_id.split('-')[0];
    const res = await fetch(`http://127.0.0.1:8000/audit_log/${ticketId}`);
    const data = await res.json();
    const blob = new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit_log_${ticketId}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Download audit log as PDF
  const handleDownloadAuditPDF = async () => {
    if (!fellowship_graph.nodes || !fellowship_graph.nodes.length) return;
    const ticketId = fellowship_graph.nodes[0].step_id.split('-')[0];
    const res = await fetch(`http://127.0.0.1:8000/audit_log_pdf/${ticketId}`);
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit_log_${ticketId}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!fellowship_graph || !fellowship_graph.nodes || fellowship_graph.nodes.length === 0) {
    return <div style={{textAlign:'center', color:'#888'}}>No workflow graph to display.</div>;
  }
  const width = Math.max(700, 300 * fellowship_graph.nodes.length);
  const height = 450;
  const nodeRadius = 36;
  const nodeY = height / 2;
  const nodeSpacing = width / (fellowship_graph.nodes.length + 1);

  // Map node ids to x positions
  const nodePositions = fellowship_graph.nodes.reduce((acc, node, i) => {
    acc[node.id] = { x: nodeSpacing * (i + 1), y: nodeY };
    return acc;
  }, {});

  return (
    <div style={{margin: '4rem 0', textAlign:'center'}}>
      <div style={{marginBottom:12, display:'flex', justifyContent:'center', alignItems:'center', gap:16}}>
        <button onClick={handleDownloadAudit} style={{padding:'8px 18px', fontWeight:600, borderRadius:8, background:'#264653', color:'#fff', border:'none', boxShadow:'0 2px 8px #0001', cursor:'pointer', transition:'background 0.2s'}} onMouseOver={e=>e.target.style.background='#457b9d'} onMouseOut={e=>e.target.style.background='#264653'}>Download Audit Log</button>
        <button onClick={handleDownloadAuditPDF} style={{padding:'8px 18px', fontWeight:600, borderRadius:8, background:'#e76f51', color:'#fff', border:'none', boxShadow:'0 2px 8px #0001', cursor:'pointer', transition:'background 0.2s'}} onMouseOver={e=>e.target.style.background='#f4a261'} onMouseOut={e=>e.target.style.background='#e76f51'}>Download Audit Log (PDF)</button>
      </div>
      <h4 style={{marginBottom:20, color:'#22223b', fontWeight:700, letterSpacing:1}}>Workflow Visualization</h4>
      <svg width={width} height={height} style={{background:'linear-gradient(120deg,#f8fafc 60%,#e0e7ef 100%)', borderRadius:20, boxShadow:'0 4px 24px #0001', transition:'box-shadow 0.3s'}}>
        <defs>
          <radialGradient id="nodeGradient" cx="50%" cy="50%" r="80%">
            <stop offset="0%" stopColor="#fff" stopOpacity="0.9" />
            <stop offset="100%" stopColor="#e0e7ef" stopOpacity="0.7" />
          </radialGradient>
          <filter id="edgeShadow" x="-20%" y="-20%" width="200%" height="150%">
            <feDropShadow dx="0" dy="2" stdDeviation="2" floodColor="#888" floodOpacity="0.18" />
          </filter>
          <marker id="arrow" markerWidth="10" markerHeight="10" refX="10" refY="5" orient="auto" markerUnits="strokeWidth">
            <path d="M0,0 L10,5 L0,10" fill="#888" />
          </marker>
          <style>{`
            @keyframes dash {
              to { stroke-dashoffset: 16; }
            }
            .node-appear { animation: nodePop 0.5s cubic-bezier(.5,1.8,.5,1) both; }
            @keyframes nodePop { 0% { transform: scale(0.7); opacity:0; } 100% { transform: scale(1); opacity:1; } }
          `}</style>
        </defs>
        {/* Edges with animation and drop shadow */}
        {fellowship_graph.edges.map((edge, i) => {
          const from = nodePositions[edge.from];
          const to = nodePositions[edge.to];
          if (!from || !to) return null;
          // Button position: halfway between from and to, below the edge
          const btnX = (from.x + to.x) / 2 - 45;
          const btnY = from.y + 30;
          return (
            <g key={i}>
              <line x1={from.x} y1={from.y} x2={to.x} y2={to.y} stroke="#888" strokeWidth={3.5} markerEnd="url(#arrow)" style={{strokeDasharray: 8, animation: 'dash 1.2s linear infinite'}} filter="url(#edgeShadow)" />
              <text x={(from.x+to.x)/2} y={from.y-24} textAnchor="middle" fontSize={15} fill="#22223b" fontWeight="bold" style={{letterSpacing:0.2}}>{edge.handoff}</text>
              {/* Edge Provenance Button */}
              <foreignObject x={btnX} y={btnY} width={90} height={50}>
                <button onClick={() => setModalProvenance({step_id: edge.step_id, signature: edge.signature, agent_id: edge.agent_id, role: edge.handoff, ticket_id: edge.step_id.split('-')[0]})} style={{width:'100%', padding:'4px 0', fontSize:12, borderRadius:6, border:'1px solid #bbb', background:'#fff', color:'#457b9d', cursor:'pointer', boxShadow:'0 1px 4px #0001', marginTop:4, transition:'background 0.2s'}} onMouseOver={e=>e.target.style.background='#f4faff'} onMouseOut={e=>e.target.style.background='#fff'}>Edge Provenance</button>
              </foreignObject>
            </g>
          );
        })}
        {/* Nodes with gradient, pop-in, and zoom-on-hover */}
        {fellowship_graph.nodes.map((node, i) => {
          const color = ROLE_COLORS[node.role] || ROLE_COLORS.default;
          const isHovered = hovered === node.id;
          return (
            <g key={node.id} className="node-appear" style={{cursor:'pointer', transition:'transform 0.18s', transform: isHovered ? 'scale(1.08)' : 'scale(1)'}}
              onMouseEnter={() => setHovered(node.id)}
              onMouseLeave={() => setHovered(null)}>
              <circle cx={nodePositions[node.id].x} cy={nodePositions[node.id].y} r={nodeRadius} fill={`url(#nodeGradient)`} stroke={color} strokeWidth={4} style={{filter:'drop-shadow(0 2px 12px #0002)'}} />
              <circle cx={nodePositions[node.id].x} cy={nodePositions[node.id].y} r={nodeRadius-7} fill={color} stroke="none" />
              <text x={nodePositions[node.id].x} y={nodePositions[node.id].y-8} textAnchor="middle" fontWeight="bold" fontSize={18} fill="#fff" style={{textShadow:'0 2px 8px #0006', letterSpacing:0.2}}>{node.role}</text>
              <text x={nodePositions[node.id].x} y={nodePositions[node.id].y+20} textAnchor="middle" fontSize={14} fill="#e9ecef" style={{fontWeight:500}}>{node.name}</text>
              {/* Tooltip */}
              {isHovered && (
                <g>
                  <rect x={nodePositions[node.id].x-80} y={nodePositions[node.id].y-nodeRadius-70} width={200} height={60} rx={12} fill="#fff" stroke="#fff" />
                  <text x={nodePositions[node.id].x} y={nodePositions[node.id].y-nodeRadius-48} textAnchor="middle" fontSize={15} fontWeight="bold" fill="#222">{node.name}</text>
                  <text x={nodePositions[node.id].x} y={nodePositions[node.id].y-nodeRadius-28} textAnchor="middle" fontSize={13} fill="#555">Location: {node.location}</text>
                  <text x={nodePositions[node.id].x} y={nodePositions[node.id].y-nodeRadius-12} textAnchor="middle" fontSize={13} fill="#555">Trust: {node.trust_score}</text>
                  <text x={nodePositions[node.id].x} y={nodePositions[node.id].y+nodeRadius+28} textAnchor="middle" fontSize={13} fill="#555">Cost: {node.cost_per_task}</text>
                </g>
              )}
              {/* View Contract Button */}
              <foreignObject x={nodePositions[node.id].x-45} y={nodePositions[node.id].y+nodeRadius+8} width={90} height={50}>
                <button onClick={() => setModalContract(node.data_contract)} style={{width:'100%', padding:'4px 0', fontSize:12, borderRadius:6, border:'1px solid #bbb', background:'#fff', color:'#264653', cursor:'pointer', boxShadow:'0 1px 4px #0001', marginTop:10, transition:'background 0.2s'}} onMouseOver={e=>e.target.style.background='#f4faff'} onMouseOut={e=>e.target.style.background='#fff'}>View Contract</button>
              </foreignObject>
              {/* View Provenance Button */}
              <foreignObject x={nodePositions[node.id].x-45} y={nodePositions[node.id].y+nodeRadius+44} width={90} height={50}>
                <button onClick={() => setModalProvenance({step_id: node.step_id, signature: node.signature, agent_id: node.agent_id, role: node.role, ticket_id: node.step_id.split('-')[0]})} style={{width:'100%', padding:'4px 0', fontSize:12, borderRadius:6, border:'1px solid #bbb', background:'#fff', color:'#e76f51', cursor:'pointer', boxShadow:'0 1px 4px #0001', marginTop:4, transition:'background 0.2s'}} onMouseOver={e=>e.target.style.background='#fbeee7'} onMouseOut={e=>e.target.style.background='#fff'}>View Provenance</button>
              </foreignObject>
            </g>
          );
        })}
      </svg>
      <ContractModal contract={modalContract} onClose={() => setModalContract(null)} />
      <ProvenanceModal provenance={modalProvenance} onClose={() => setModalProvenance(null)} />
    </div>
  );
}