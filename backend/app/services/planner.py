from app.models.agent import Agent
from app.models.repair_ticket import RepairTicket
import json
import os

AGENT_REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "..", "registry", "agent_registry.json")

def load_agents():
    with open(AGENT_REGISTRY_PATH, "r") as f:
        return [Agent(**a) for a in json.load(f)]

def plan_agents(ticket: RepairTicket):
    agents = load_agents()
    selected = []

    for cap in ticket.required_capabilities:
        best = None
        for agent in agents:
            if cap in agent.capabilities and ticket.customer_location in agent.jurisdiction:
                if agent.cost_per_task <= ticket.max_budget and agent.trust_score > 0.6:
                    if best is None or agent.trust_score > best.trust_score:
                        best = agent
        if best:
            selected.append(best)

    return selected

# Keep select_agents for compatibility
from typing import List, Dict, Any

def select_agents(agents: List[Agent], ticket: Dict[str, Any]) -> List[Agent]:
    # Stub: filter by jurisdiction, cost, trust, skills, and max hops
    filtered = [
        agent for agent in agents
        if ticket['data_jurisdiction'] in agent.jurisdiction
        and agent.cost_per_task <= ticket['budget_inr']
        and agent.trust_score >= 0.9
        and all(skill in agent.skills for skill in ticket.get('required_skills', []))
    ]
    return filtered[:ticket.get('max_hops', 4)]
