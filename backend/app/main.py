from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.models.agent import Agent
import json
import os
import uuid
from fastapi import Body
from fastapi.responses import JSONResponse
from app.models.repair_ticket import RepairTicket
from app.services.planner import plan_agents
from app.services.workflow import generate_receipt
from app.services.contracts import generate_privacy_contract
from app.services.workflow import langchain_simulate_workflow
from pydantic import BaseModel
from typing import List

app = FastAPI(title="Fellowship of the Cogs: Agent API")

# CORS (for React frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

AGENT_REGISTRY_FILE = os.path.join(os.path.dirname(__file__), "registry", "agent_registry.json")

def load_agents():
    with open(AGENT_REGISTRY_FILE, "r") as f:
        return json.load(f)

def save_agents(agents):
    with open(AGENT_REGISTRY_FILE, "w") as f:
        json.dump(agents, f, indent=2)

class AgentInput(BaseModel):
    agents: List[dict]

@app.get("/")
def root():
    return {"message": "Fellowship of the Cogs API is running!"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/agents")
def get_agents():
    return load_agents()

@app.post("/agents/register")
def register_agent(agent: Agent):
    agents = load_agents()
    agent_dict = agent.dict()
    if not agent_dict.get("id"):
        agent_dict["id"] = str(uuid.uuid4())
    # Blockchain: require public_key and wallet_address
    if not agent_dict.get("public_key"):
        raise HTTPException(status_code=400, detail="public_key is required for blockchain identity.")
    if not agent_dict.get("wallet_address"):
        # Optionally, generate a wallet address from public key (stub: use hash)
        from app.utils.hashing import hash_data
        agent_dict["wallet_address"] = hash_data(agent_dict["public_key"])[:16]
    agents.append(agent_dict)
    save_agents(agents)
    return {"message": "Agent registered successfully", "agent": agent_dict}

@app.post("/ticket/create")
def create_ticket(ticket: RepairTicket):
    # For now, just return it back
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
    # Normally we'd load the agent's private key securely
    from app.utils.blockchain import generate_keys
    priv, pub = generate_keys()
    log = generate_receipt(agent, task_data, priv)
    return {"logged": log}

@app.post("/workflow/simulate")
def workflow_simulate(ticket: RepairTicket, agent_input: AgentInput):
    from app.models.agent import Agent
    agent_objs = [Agent(**a) for a in agent_input.agents]
    logs = langchain_simulate_workflow(ticket, agent_objs)
    # Signature verification for each log entry
    from app.utils.hashing import verify_signature
    verified_logs = []
    for log in logs:
        data_str = f"{log['agent']}|{log['step']}|{log['timestamp']}"
        is_valid = verify_signature(data_str, log['signature'], log['contract'].get('public_key', ''))
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
    # Return a sample simulation report (dashboard-friendly)
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
