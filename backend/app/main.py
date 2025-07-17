import logging
from fastapi import FastAPI, HTTPException, Body, Request, status, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from app.models.agent import Agent as AgentPydantic
from app.models.repair_ticket import RepairTicket
from app.services.planner import plan_agents
from app.services.workflow import generate_receipt, langchain_simulate_workflow
from app.services.contracts import generate_privacy_contract
from pydantic import BaseModel, Field, ValidationError
from typing import List
import uuid
from pymongo import MongoClient, errors as mongo_errors
import os
from dotenv import load_dotenv
import csv
import io
import json
import tempfile
from fpdf import FPDF

# Load environment variables from .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fellowship")

app = FastAPI(title="Fellowship of the Cogs: Agent API")

# Robust CORS (for React/frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Type", "Authorization", "X-Requested-With", "Access-Control-Allow-Origin", "Access-Control-Allow-Credentials"]
)

# MongoDB setup
MONGO_URL = os.environ.get("MONGO_URL", "mongodb+srv://gargkunal369:U1RsL0VSkgKq5kg4@cluster0.qm6ze7u.mongodb.net/")
try:
    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    db = client["fellowship"]
    agents_collection = db["agents"]
    # Test connection
    client.server_info()
except mongo_errors.ServerSelectionTimeoutError as e:
    logger.error(f"Could not connect to MongoDB: {e}")
    raise RuntimeError("MongoDB connection failed")

class AgentRegisterInput(BaseModel):
    name: str
    company: str
    location: str
    jurisdiction: List[str]
    capabilities: List[str]
    skills: List[str]
    cost_per_task: float
    currency: str
    access_type: str
    trust_score: float = Field(..., ge=0, le=1)
    is_ai: bool
    wallet_address: str
    openid_token: str
    public_key: str
    public_key_pem: str

class FeedbackInput(BaseModel):
    agent_id: str
    rating: float = Field(..., ge=0, le=1)
    comment: str = ""

class AgentInput(BaseModel):
    agents: List[dict]

class WorkflowSimulateInput(BaseModel):
    ticket: RepairTicket
    agents: List[dict]

@app.get("/")
def root():
    return {"message": "Fellowship of the Cogs API is running!"}

@app.get("/health")
def health_check():
    try:
        client.server_info()
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "detail": str(e)})

@app.get("/agents")
def get_agents():
    try:
        agents = list(agents_collection.find({}, {"_id": 0}))
        return agents
    except Exception as e:
        logger.error(f"Error fetching agents: {e}")
        raise HTTPException(status_code=500, detail="Database error fetching agents")

@app.post("/agents/register")
def register_agent(agent: AgentRegisterInput):
    try:
        agent_dict = agent.dict()
        if not agent_dict.get("id"):
            agent_dict["id"] = str(uuid.uuid4())
        # Prevent duplicate agent name
        if agents_collection.find_one({"name": agent_dict["name"]}):
            raise HTTPException(status_code=409, detail="Agent with this name already exists")
        agents_collection.insert_one(agent_dict)
        logger.info(f"Registered agent: {agent_dict['name']}")
        return {"message": "Agent registered successfully", "agent": agent_dict}
    except ValidationError as ve:
        logger.error(f"Validation error: {ve}")
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        logger.error(f"Error registering agent: {e}")
        raise HTTPException(status_code=500, detail="Database error registering agent")

@app.post("/ticket/create")
def create_ticket(ticket: RepairTicket):
    return {"message": "Ticket created", "ticket": ticket}

@app.post("/ticket/plan")
def plan(ticket: RepairTicket):
    agents, graph = plan_agents(ticket)
    return {
        "workflow_agents": [a.dict() for a in agents],
        "total_cost": sum(a.cost_per_task for a in agents),
        "fellowship_graph": graph
    }

@app.post("/workflow/log")
def log_handoff(ticket_id: str, agent: str, task_data: str):
    from app.utils.blockchain import generate_keys
    priv, pub = generate_keys()
    log = generate_receipt(agent, task_data, priv)
    return {"logged": log}

@app.post("/workflow/simulate")
def workflow_simulate(input: WorkflowSimulateInput):
    from app.models.agent import Agent as AgentPydantic
    agent_objs = [AgentPydantic(**a) for a in input.agents]
    logs = langchain_simulate_workflow(input.ticket, agent_objs)
    from app.utils.hashing import verify_signature
    verified_logs = []
    for log in logs:
        data_str = f"{log['agent']}|{log['step']}|{log['timestamp']}"
        public_key = log['contract'].get('public_key', '')
        if "KEY" in public_key or "PUBLIC KEY" in public_key:
            is_valid = "skipped (mock key)"
        else:
            try:
                is_valid = verify_signature(data_str, log['signature'], public_key)
            except Exception as e:
                is_valid = f"error: {str(e)}"
        log['signature_valid'] = is_valid
        verified_logs.append(log)
    return {"workflow_log": verified_logs}

@app.post("/privacy/contract")
def privacy_contract(
    agent_id: str = Body(...),
    permitted_fields: list = Body(...),
    data_jurisdiction: str = Body(...),
    expiry_hours: int = Body(48),
    policy: str = Body("")
):
    contract = generate_privacy_contract(agent_id, permitted_fields, data_jurisdiction, expiry_hours, policy)
    return {"privacy_contract": contract}

@app.post("/agents/feedback")
def agent_feedback(feedback: FeedbackInput):
    try:
        agent_id = feedback.agent_id
        rating = feedback.rating
        comment = feedback.comment
        agent = agents_collection.find_one({"id": agent_id})
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        # Exponential Moving Average (EMA) for trust_score
        alpha = 0.3  # learning rate, can be tuned
        old_score = agent.get("trust_score", 0.0)
        new_score = round((1 - alpha) * old_score + alpha * rating, 2)
        # Store feedback history (append to array)
        feedback_history = agent.get("feedback_history", [])
        feedback_history.append({"rating": rating, "comment": comment})
        agents_collection.update_one(
            {"id": agent_id},
            {"$set": {"trust_score": new_score, "feedback_history": feedback_history}}
        )
        logger.info(f"Feedback for agent {agent_id}: rating={rating}, new_score={new_score}")
        return {
            "message": "Trust score updated (EMA)",
            "new_trust_score": new_score,
            "feedback_count": len(feedback_history),
            "recent_feedback": feedback_history[-3:]
        }
    except ValidationError as ve:
        logger.error(f"Validation error: {ve}")
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        logger.error(f"Error in feedback: {e}")
        raise HTTPException(status_code=500, detail="Database error updating feedback")

@app.post("/agents/upload_capability_sheet")
def upload_capability_sheet(file: UploadFile = File(...)):
    content = file.file.read()
    filename = file.filename.lower()
    agents = []
    try:
        if filename.endswith('.csv'):
            decoded = content.decode('utf-8')
            reader = csv.DictReader(io.StringIO(decoded))
            for row in reader:
                # Convert lists from CSV string (e.g., "[a, b]") to Python list
                for k in ["jurisdiction", "capabilities", "skills", "data_needs"]:
                    if k in row and isinstance(row[k], str):
                        row[k] = [x.strip() for x in row[k].strip('[]').split(',') if x.strip()]
                row["id"] = str(uuid.uuid4())
                agents.append(row)
        elif filename.endswith('.json'):
            data = json.loads(content)
            if isinstance(data, dict):
                agents = [data]
            elif isinstance(data, list):
                agents = data
            for agent in agents:
                agent["id"] = str(uuid.uuid4())
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type. Use CSV or JSON.")
        # Store in MongoDB
        for agent in agents:
            agents_collection.insert_one(agent)
        return {"message": f"Registered {len(agents)} agents.", "agents": [a["name"] for a in agents]}
    except Exception as e:
        logger.error(f"Error uploading capability sheet: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process file: {e}")

@app.get("/simulation/report")
def simulation_report():
    report = {
        "ticket_id": "ticket-1001",
        "mttr_hours": 5.2,
        "csat_score": 4.8,
        "fraud_risk": 0.01,
        "carbon_footprint_kg": 2.3,
        "agent_hops": [
            {
                "agent_id": "agent-003",
                "role": "diagnosis",
                "timestamp": "2024-06-01T10:10:00Z",
                "signature": "mock-signature-hop1"
            },
            {
                "agent_id": "agent-002",
                "role": "logistics",
                "timestamp": "2024-06-01T11:00:00Z",
                "signature": "mock-signature-hop2"
            },
            {
                "agent_id": "agent-001",
                "role": "repair",
                "timestamp": "2024-06-01T13:00:00Z",
                "signature": "mock-signature-hop3"
            },
            {
                "agent_id": "agent-004",
                "role": "billing",
                "timestamp": "2024-06-01T15:00:00Z",
                "signature": "mock-signature-hop4"
            }
        ]
    }
    return JSONResponse(content=report)

@app.get("/audit_log/{ticket_id}")
def audit_log(ticket_id: str):
    # For demo: reconstruct a fake ticket and call plan_agents
    # In production, you would fetch the real ticket from DB
    from app.models.repair_ticket import RepairTicket
    # Minimal fake ticket for audit (customize as needed)
    ticket = RepairTicket(
        ticket_id=ticket_id,
        customer_location="Global",
        issue="Demo audit log for ticket",
        max_budget=1000,
        max_days=3,
        required_capabilities=[],
        data_constraints=["Global"],
        max_hops=4
    )
    _, graph = plan_agents(ticket)
    return graph

@app.get("/audit_log_pdf/{ticket_id}")
def audit_log_pdf(ticket_id: str):
    from app.models.repair_ticket import RepairTicket
    from fpdf import FPDF
    import os
    # Minimal fake ticket for audit (customize as needed)
    ticket = RepairTicket(
        ticket_id=ticket_id,
        customer_location="Global",
        issue="Demo audit log for ticket",
        max_budget=1000,
        max_days=3,
        required_capabilities=[],
        data_constraints=["Global"],
        max_hops=4
    )
    _, graph = plan_agents(ticket)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.cell(0, 10, f"Audit Log for Ticket: {ticket_id}", ln=True, align="C")
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 8, f"Policy/Fraud Flags: {len(graph.get('policy_flags', []))}", ln=True)
    for flag in graph.get('policy_flags', []):
        pdf.set_text_color(200,0,0)
        pdf.multi_cell(0, 7, f"[WARNING] {flag}")
    pdf.set_text_color(0,0,0)
    pdf.ln(2)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, "Workflow Nodes:", ln=True)
    pdf.set_font("Arial", size=10)
    for node in graph.get('nodes', []):
        pdf.cell(0, 7, f"Role: {node['role']} | Agent: {node['name']} | ID: {node['id']}", ln=True)
        pdf.cell(0, 7, f"  Step ID: {node['step_id']} | Signature: {node['signature'][:16]}...", ln=True)
        contract = node.get('data_contract', {})
        pdf.cell(0, 7, f"  Regulations: {', '.join(contract.get('applicable_regulations', []))}", ln=True)
        pdf.cell(0, 7, f"  Permitted Fields: {', '.join(contract.get('permitted_fields', []))}", ln=True)
        pdf.ln(1)
    pdf.ln(2)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, "Workflow Edges:", ln=True)
    pdf.set_font("Arial", size=10)
    for edge in graph.get('edges', []):
        pdf.cell(0, 7, f"From: {edge['from']} -> To: {edge['to']} | Handoff: {edge['handoff']}", ln=True)
        pdf.cell(0, 7, f"  Step ID: {edge['step_id']} | Signature: {edge['signature'][:16]}...", ln=True)
        pdf.ln(1)
    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        pdf.output(tmp.name)
        tmp_path = tmp.name
    return FileResponse(tmp_path, filename=f"audit_log_{ticket_id}.pdf", media_type="application/pdf")
