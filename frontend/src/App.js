import React, { useState } from "react";
import TicketForm from "./components/TicketForm";
import FeedbackForm from "./components/FeedbackForm";
import AgentGraph from "./components/AgentGraph";

function App() {
  const [results, setResults] = useState(null);

  return (
    <div style={{ fontFamily: 'Segoe UI, Arial, sans-serif', background: '#f6f8fa', minHeight: '100vh' }}>
      <header style={{ background: '#22223b', color: '#fff', padding: '1.5rem 0', textAlign: 'center', marginBottom: 32 }}>
        <h1 style={{ margin: 0, fontWeight: 700, letterSpacing: 1 }}>Fellowship of the Cogs</h1>
        <p style={{ margin: 0, fontSize: 18 }}>Find the best repair vendors worldwide, powered by AI</p>
      </header>
      {/* <CapabilitySheetUpload /> */}
      <TicketForm onResults={setResults} />
      {results && (
        <>
          <h3 style={{ marginTop: 0, textAlign: 'center' }}>Best Vendors:</h3>
          {results.workflow_agents && results.workflow_agents.length > 0 ? (
            <ul style={{ listStyle: 'none', padding: 0, maxWidth: 700, margin: '0 auto 2rem auto' }}>
              {results.workflow_agents.map((agent, idx) => (
                <li key={idx} style={{ marginBottom: 18, borderBottom: '1px solid #eee', paddingBottom: 12 }}>
                  <strong>{agent.name}</strong> <span style={{ color: '#888' }}>({agent.location})</span><br />
                  <span>Type: {agent.type || 'N/A'}</span><br />
                  <span>Capabilities: {agent.capabilities && agent.capabilities.join(', ')}</span><br />
                  <span>Trust Score: {agent.trust_score || 'N/A'}</span><br />
                  <span>Reviews: {agent.reviews || 0}</span><br />
                  {agent.phone && (<span>Phone: {agent.phone}<br /></span>)}
                  {agent.website && (<span>Website: <a href={agent.website} target="_blank" rel="noopener noreferrer">{agent.website}</a><br /></span>)}
                  {agent.description && (<span>Description: {agent.description}<br /></span>)}
                  {agent.hours && (<span>Hours: {agent.hours}<br /></span>)}
                </li>
              ))}
            </ul>
          ) : (
            <pre style={{ background: "#f4f4f4", padding: 16, borderRadius: 8, maxWidth: 700, margin: '0 auto 2rem auto' }}>
              {JSON.stringify(results, null, 2)}
            </pre>
          )}
          {results.total_cost !== undefined && (
            <div style={{ marginTop: 16, fontWeight: 500, textAlign: 'center' }}>
              <span>Total Cost: </span>
              <span style={{ color: '#2a9d8f' }}>{results.total_cost}</span>
            </div>
          )}
        </>
      )}
      {/* Always show AgentGraph if fellowship_graph exists */}
      {results && results.fellowship_graph && <AgentGraph fellowship_graph={results.fellowship_graph} />}
      <FeedbackForm />
      <footer style={{ textAlign: 'center', color: '#888', marginTop: 48, padding: 24 }}>
        &copy; {new Date().getFullYear()} Fellowship of the Cogs
      </footer>
    </div>
  );
}

export default App;
