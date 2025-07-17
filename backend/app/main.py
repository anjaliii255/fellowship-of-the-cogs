from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.models.agent import Agent as AgentPydantic
from app.models.repair_ticket import RepairTicket
from app.services.planner import plan_agents
from app.services.workflow import generate_receipt, langchain_simulate_workflow
from app.services.contracts import generate_privacy_contract
from pydantic import BaseModel
from typing import List
import uuid
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

app = FastAPI(title="Fellowship of the Cogs: Agent API")

# CORS (for React frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB setup
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
client = MongoClient(MONGO_URL)
db = client["fellowship"]
agents_collection = db["agents"]

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
    return {"status": "ok"}

@app.get("/agents")
def get_agents():
    agents = list(agents_collection.find({}, {"_id": 0}))
    return agents

@app.post("/agents/register")
def register_agent(agent: AgentPydantic):
    agent_dict = agent.dict()
    if not agent_dict.get("id"):
        agent_dict["id"] = str(uuid.uuid4())
    agents_collection.insert_one(agent_dict)
    return {"message": "Agent registered successfully", "agent": agent_dict}

@app.post("/ticket/create")
def create_ticket(ticket: RepairTicket):
    return {"message": "Ticket created", "ticket": ticket}

@app.post("/ticket/plan")
def plan(ticket: RepairTicket):
    selected_agents = plan_agents(ticket)
    return {
        "workflow_agents": [a.dict() for a in selected_agents],
        "total_cost": sum(a.cost_per_task for a in selected_agents)
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
