import React, { useState, useEffect } from "react";
import axios from "axios";

export default function FeedbackForm() {
  const [agents, setAgents] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState("");
  const [rating, setRating] = useState(0.8);
  const [comment, setComment] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => {
    axios.get("http://127.0.0.1:8000/agents").then(res => {
      setAgents(res.data);
      if (res.data.length > 0) setSelectedAgent(res.data[0].id);
    });
  }, []);

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
      <br /><br />
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
          <h4>Result:</h4>
          <pre style={{ background: "#f4f4f4", padding: 12, borderRadius: 8 }}>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </form>
  );
} 