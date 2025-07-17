import React, { useState } from "react";
import axios from "axios";

// Simple keyword extraction (can be replaced with NLP)
const extractCapabilities = (description) => {
  const keywords = [
    { key: "repair", caps: ["repair"] },
    { key: "diagnosis", caps: ["diagnosis"] },
    { key: "install", caps: ["installation"] },
    { key: "cooling", caps: ["cooling_analysis"] },
    { key: "fraud", caps: ["fraud_detection"] },
    { key: "logistics", caps: ["logistics", "part_delivery"] },
    // Add more as needed
  ];
  let caps = [];
  for (const { key, caps: c } of keywords) {
    if (description.toLowerCase().includes(key)) {
      caps = [...caps, ...c];
    }
  }
  return caps.length ? caps : ["repair"];
};

const locations = [
  "India", "EU", "USA", "Japan", "LATAM", "Asia", "Germany", "Brazil", "Global"
];

export default function TicketForm({ onResults }) {
  const [location, setLocation] = useState("Global");
  const [budget, setBudget] = useState(500);
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    const required_capabilities = extractCapabilities(description);
    const payload = {
      ticket_id: "ticket-" + Date.now(),
      customer_location: location,
      issue: description,
      max_budget: budget,
      max_days: 3,
      required_capabilities,
      data_constraints: [location],
      max_hops: 2
    };
    try {
      const res = await axios.post("http://127.0.0.1:8000/ticket/plan", payload);
      onResults(res.data);
    } catch (err) {
      alert("Error fetching agents: " + (err.response?.data?.detail || err.message));
    }
    setLoading(false);
  };

  return (
    <form onSubmit={handleSubmit} style={{ maxWidth: 500, margin: "2rem auto", padding: 24, border: "1px solid #eee", borderRadius: 8, background: "#fafbfc" }}>
      <h2>Request a Repair</h2>
      <label>
        Location:
        <select value={location} onChange={e => setLocation(e.target.value)} style={{ marginLeft: 8 }}>
          {locations.map(loc => <option key={loc} value={loc}>{loc}</option>)}
        </select>
      </label>
      <br /><br />
      <label>
        Max Budget: <span style={{ fontWeight: "bold" }}>{budget}</span>
        <input
          type="range"
          min={50}
          max={2000}
          step={10}
          value={budget}
          onChange={e => setBudget(Number(e.target.value))}
          style={{ width: "100%" }}
        />
      </label>
      <br /><br />
      <label>
        Problem Description:
        <textarea
          value={description}
          onChange={e => setDescription(e.target.value)}
          rows={4}
          style={{ width: "100%", marginTop: 8 }}
          placeholder="Describe your issue (e.g., fridge not cooling, need installation, etc.)"
        />
      </label>
      <br />
      <button type="submit" disabled={loading} style={{ marginTop: 16, padding: "8px 24px", fontWeight: "bold" }}>
        {loading ? "Finding Vendors..." : "Find Vendors"}
      </button>
    </form>
  );
}
