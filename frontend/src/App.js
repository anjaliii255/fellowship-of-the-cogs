import React, { useState } from "react";
import TicketForm from "./components/TicketForm";

function App() {
  const [results, setResults] = useState(null);

  return (
    <div style={{ fontFamily: 'Segoe UI, Arial, sans-serif', background: '#f6f8fa', minHeight: '100vh' }}>
      <header style={{ background: '#22223b', color: '#fff', padding: '1.5rem 0', textAlign: 'center', marginBottom: 32 }}>
        <h1 style={{ margin: 0, fontWeight: 700, letterSpacing: 1 }}>Fellowship of the Cogs</h1>
        <p style={{ margin: 0, fontSize: 18 }}>Find the best repair vendors worldwide, powered by AI</p>
      </header>
      <TicketForm onResults={setResults} />
      {results && (
        <div style={{ maxWidth: 700, margin: "2rem auto", background: "#fff", borderRadius: 8, boxShadow: "0 2px 8px #0001", padding: 24 }}>
          <h3 style={{ marginTop: 0 }}>Best Vendors:</h3>
          {results.workflow_agents && results.workflow_agents.length > 0 ? (
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {results.workflow_agents.map((agent, idx) => (
                <li key={idx} style={{ marginBottom: 18, borderBottom: '1px solid #eee', paddingBottom: 12 }}>
                  <strong>{agent.name}</strong> <span style={{ color: '#888' }}>({agent.location})</span><br />
                  <span>Capabilities: {agent.capabilities && agent.capabilities.join(', ')}</span><br />
                  <span>Trust Score: {agent.trust_score || 'N/A'}</span>
                </li>
              ))}
            </ul>
          ) : (
            <pre style={{ background: "#f4f4f4", padding: 16, borderRadius: 8 }}>
              {JSON.stringify(results, null, 2)}
            </pre>
          )}
          {results.total_cost !== undefined && (
            <div style={{ marginTop: 16, fontWeight: 500 }}>
              <span>Total Cost: </span>
              <span style={{ color: '#2a9d8f' }}>{results.total_cost}</span>
            </div>
          )}
        </div>
      )}
      <footer style={{ textAlign: 'center', color: '#888', marginTop: 48, padding: 24 }}>
        &copy; {new Date().getFullYear()} Fellowship of the Cogs
      </footer>
    </div>
  );
}

export default App;
