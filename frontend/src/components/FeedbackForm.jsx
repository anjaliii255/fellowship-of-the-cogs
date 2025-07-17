import React, { useState, useEffect } from "react";
import axios from "axios";

export default function FeedbackForm() {
  const [agents, setAgents] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState("");
  const [rating, setRating] = useState(0.8);
  const [comment, setComment] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [currentTrustScore, setCurrentTrustScore] = useState(null);
  const [recentFeedback, setRecentFeedback] = useState([]);

  useEffect(() => {
    axios.get("http://127.0.0.1:8000/agents").then(res => {
      setAgents(res.data);
      if (res.data.length > 0) setSelectedAgent(res.data[0].id);
    });
  }, []);

  useEffect(() => {
    if (selectedAgent && agents.length > 0) {
      const agent = agents.find(a => a.id === selectedAgent);
      setCurrentTrustScore(agent ? agent.trust_score : null);
      setRecentFeedback(agent && agent.feedback_history ? agent.feedback_history.slice(-3).reverse() : []);
    }
  }, [selectedAgent, agents]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    try {
      const payload = {
        agent_id: selectedAgent,
        rating: rating,
        comment: comment
      };
      const res = await axios.post("http://127.0.0.1:8000/agents/feedback", payload);
      setResult(res.data);
      // Update trust score and recent feedback after submission
      setCurrentTrustScore(res.data.new_trust_score);
      setRecentFeedback(res.data.recent_feedback ? res.data.recent_feedback.slice().reverse() : []);
      // Optionally, update the agent in the agents list
      setAgents(prev => prev.map(a => a.id === selectedAgent ? { ...a, trust_score: res.data.new_trust_score, feedback_history: [...(a.feedback_history || []), { rating, comment }] } : a));
    } catch (err) {
      setResult({ error: err.response?.data?.detail || err.message });
    }
    setLoading(false);
  };

  return (
    <form onSubmit={handleSubmit} style={{ maxWidth: 500, margin: "2rem auto", padding: 24, border: "1px solid #eee", borderRadius: 8, background: "#fafbfc" }}>
      <h2>Leave Feedback for a Vendor</h2>
      <label>
        Select Agent:
        <select value={selectedAgent} onChange={e => setSelectedAgent(e.target.value)} style={{ marginLeft: 8, width: '100%' }}>
          {agents.map(agent => (
            <option key={agent.id} value={agent.id}>{agent.name} ({agent.location})</option>
          ))}
        </select>
      </label>
      {currentTrustScore !== null && (
        <div style={{ margin: '8px 0', color: '#2a9d8f', fontWeight: 500 }}>
          Current Trust Score: <span style={{ fontFamily: 'monospace' }}>{currentTrustScore}</span>
        </div>
      )}
      <br />
      <label>
        Rating: <span style={{ fontWeight: "bold" }}>{rating}</span>
        <input
          type="range"
          min={0}
          max={1}
          step={0.01}
          value={rating}
          onChange={e => setRating(Number(e.target.value))}
          style={{ width: "100%" }}
        />
      </label>
      <br /><br />
      <label>
        Comment:
        <textarea
          value={comment}
          onChange={e => setComment(e.target.value)}
          rows={3}
          style={{ width: "100%", marginTop: 8 }}
          placeholder="Describe your experience..."
        />
      </label>
      <br />
      <button type="submit" disabled={loading || !selectedAgent} style={{ marginTop: 16, padding: "8px 24px", fontWeight: "bold" }}>
        {loading ? "Submitting..." : "Submit Feedback"}
      </button>
      {result && (
        <div style={{ marginTop: 24 }}>
          {result.error ? (
            <>
              <h4 style={{ color: 'red' }}>Error:</h4>
              <pre style={{ background: "#f4f4f4", padding: 12, borderRadius: 8 }}>{result.error}</pre>
            </>
          ) : (
            <>
              <h4>Feedback Submitted!</h4>
              <div style={{ color: '#2a9d8f', fontWeight: 500 }}>
                Updated Trust Score: <span style={{ fontFamily: 'monospace' }}>{result.new_trust_score}</span>
              </div>
              <div style={{ marginTop: 12 }}>
                <strong>Recent Feedback:</strong>
                <ul style={{ paddingLeft: 18 }}>
                  {recentFeedback.length === 0 && <li>No feedback yet.</li>}
                  {recentFeedback.map((fb, idx) => (
                    <li key={idx} style={{ marginBottom: 6 }}>
                      <span style={{ color: '#555' }}>Rating: <b>{fb.rating}</b></span><br />
                      <span style={{ color: '#888' }}>{fb.comment}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </>
          )}
        </div>
      )}
    </form>
  );
} 