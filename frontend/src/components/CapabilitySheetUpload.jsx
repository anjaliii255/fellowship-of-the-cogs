import React, { useState } from "react";
import axios from "axios";

const sampleCSV = `name,company,location,jurisdiction,capabilities,skills,cost_per_task,currency,access_type,trust_score,is_ai,wallet_address,openid_token,public_key,public_key_pem,data_needs
ThermoFix AI,FridgeMasters Inc.,Germany,"[EU]","[diagnosis,cooling_analysis]","[diagnosis,cooling_analysis]",250.0,EUR,API,0.92,True,0xthermofixai,openid-thermofixai,publickey-thermofixai,-----BEGIN PUBLIC KEY-----THERMOFIXAIKEY-----END PUBLIC KEY-----,"[EU,India]"
`;

export default function CapabilitySheetUpload() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleDownloadSample = () => {
    const blob = new Blob([sampleCSV], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "sample_agents.csv";
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setResult(null);
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    setResult(null);
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await axios.post("http://127.0.0.1:8000/agents/upload_capability_sheet", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      setResult(res.data);
    } catch (err) {
      setResult({ error: err.response?.data?.detail || err.message });
    }
    setLoading(false);
  };

  return (
    <div style={{ maxWidth: 500, margin: "2rem auto", padding: 24, border: "1px solid #eee", borderRadius: 8, background: "#fafbfc" }}>
      <h2>Upload Agent Capability Sheet</h2>
      <button type="button" onClick={handleDownloadSample} style={{ marginBottom: 16, padding: "6px 18px", fontWeight: "bold" }}>
        Download Sample CSV
      </button>
      <form onSubmit={handleUpload}>
        <input type="file" accept=".csv,.json" onChange={handleFileChange} />
        <button type="submit" disabled={loading || !file} style={{ marginLeft: 12, padding: "6px 18px", fontWeight: "bold" }}>
          {loading ? "Uploading..." : "Upload"}
        </button>
      </form>
      {result && (
        <div style={{ marginTop: 24 }}>
          <h4>Result:</h4>
          <pre style={{ background: "#f4f4f4", padding: 12, borderRadius: 8 }}>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
} 