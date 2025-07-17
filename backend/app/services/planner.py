import requests
from app.models.repair_ticket import RepairTicket
from app.models.agent import Agent
import os
import re
from pymongo import MongoClient
import hashlib

SERPAPI_KEY = "a968aa935374cedce17862752216921e741faa87f83f0826c52164bbfbc18ba2"
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
client = MongoClient(MONGO_URL)
db = client["fellowship"]
agents_collection = db["agents"]

# List of known locations (expand as needed)
KNOWN_LOCATIONS = [
    "Delhi", "Mumbai", "Bangalore", "Chennai", "Kolkata", "Hyderabad", "Pune", "Ahmedabad", "Jaipur", "Lucknow",
    "India", "USA", "Japan", "LATAM", "Asia", "Germany", "Brazil", "Global", "Makati", "Taguig", "Quezon City", "San Juan", "Pasig", "Cainta", "Rizal", "Metro Manila", "Philippines"
]

WORKFLOW_ROLES = [
    {"role": "diagnosis", "capability": "diagnosis"},
    {"role": "logistics", "capability": "logistics"},
    {"role": "repair", "capability": "repair"},
    {"role": "billing", "capability": "billing"}
]

# Regulation mapping
REGULATION_MAP = {
    "EU": ["GDPR"],
    "Europe": ["GDPR"],
    "Germany": ["GDPR"],
    "France": ["GDPR"],
    "India": ["PDPB"],
    "Brazil": ["LGPD"],
    "USA": ["CCPA"],
    "California": ["CCPA"],
    "Global": [],
    # Add more as needed
}

# Regulation to permitted fields (example)
REGULATION_FIELDS = {
    "GDPR": ["name", "issue", "location"],
    "PDPB": ["name", "issue", "location", "company"],
    "LGPD": ["name", "issue", "location", "company"],
    "CCPA": ["name", "issue", "location", "company", "trust_score"],
}

# Helper to resolve regulations for a location

def resolve_regulations(location):
    regs = set()
    for loc, reglist in REGULATION_MAP.items():
        if loc.lower() in location.lower():
            regs.update(reglist)
    return list(regs)

# Helper to generate contract for a customer-agent pair

def generate_data_contract(customer_location, agent_location):
    customer_regs = resolve_regulations(customer_location)
    agent_regs = resolve_regulations(agent_location)
    all_regs = set(customer_regs) | set(agent_regs)
    permitted_fields = set()
    for reg in all_regs:
        permitted_fields.update(REGULATION_FIELDS.get(reg, []))
    # If no regulation, allow all fields (for demo)
    if not permitted_fields:
        permitted_fields = {"name", "issue", "location", "company", "trust_score", "cost_per_task"}
    contract = {
        "applicable_regulations": list(all_regs),
        "permitted_fields": list(permitted_fields),
        "expiry_hours": 48,
        "policy": "Data sharing must comply with all listed regulations. Only permitted fields may be shared."
    }
    return contract

def extract_appliance_and_issue(issue_text):
    appliances = [
        "washing machine", "fridge", "refrigerator", "laptop", "phone", "microwave", "tv", "air conditioner", "dishwasher", "oven", "stove", "computer", "mobile", "tablet"
    ]
    found_appliance = next((a for a in appliances if a in issue_text.lower()), "")
    issue_keywords = [
        "not working", "not cooling", "not spinning", "leaking", "broken", "no power", "no display", "not heating", "overheating", "no sound", "stuck", "error"
    ]
    found_issue = next((k for k in issue_keywords if k in issue_text.lower()), "")
    return found_appliance, found_issue

def extract_location(issue_text, fallback_location):
    for loc in KNOWN_LOCATIONS:
        if loc.lower() in issue_text.lower():
            return loc
    return fallback_location

def search_vendors_serpapi(query, location):
    params = {
        "engine": "google_local",
        "q": query,
        "location": location,
        "api_key": SERPAPI_KEY
    }
    response = requests.get("https://serpapi.com/search", params=params)
    data = response.json()
    results = data.get("local_results", [])
    return results

def get_registered_agents():
    return list(agents_collection.find({}, {"_id": 0}))

def select_best_agent(agents, capability, location, max_budget):
    # Try strict filtering first
    candidates = [
        a for a in agents
        if capability in [c.lower() for c in a.get("capabilities", [])]
        and (location in a.get("jurisdiction", []) or location.lower() in a.get("location", "").lower())
        and a.get("cost_per_task", 0) <= max_budget
        and a.get("trust_score", 0) >= 0.6
    ]
    if candidates:
        return max(candidates, key=lambda a: a.get("trust_score", 0))
    # Relax: ignore trust_score
    candidates = [
        a for a in agents
        if capability in [c.lower() for c in a.get("capabilities", [])]
        and (location in a.get("jurisdiction", []) or location.lower() in a.get("location", "").lower())
        and a.get("cost_per_task", 0) <= max_budget
    ]
    if candidates:
        return candidates[0]
    # Relax: ignore location
    candidates = [
        a for a in agents
        if capability in [c.lower() for c in a.get("capabilities", [])]
    ]
    if candidates:
        return candidates[0]
    # Relax: pick any agent
    if agents:
        return agents[0]
    # If no agents at all, return None
    return None

def extract_roles_from_ticket(ticket):
    # Use required_capabilities if present, else extract from issue
    if hasattr(ticket, 'required_capabilities') and ticket.required_capabilities:
        caps = ticket.required_capabilities
    else:
        # Simple NLP: extract keywords from issue
        issue = ticket.issue.lower()
        caps = []
        if 'diagnos' in issue:
            caps.append('diagnosis')
        if 'logistic' in issue or 'deliver' in issue:
            caps.append('logistics')
        if 'repair' in issue or 'fix' in issue:
            caps.append('repair')
        if 'bill' in issue or 'pay' in issue:
            caps.append('billing')
        if not caps:
            caps = ['repair']
    # Remove duplicates, preserve order
    seen = set()
    roles = []
    for cap in caps:
        if cap not in seen:
            roles.append(cap)
            seen.add(cap)
    # If only one or zero roles, use the default workflow chain for demo
    if len(roles) <= 1:
        roles = ['diagnosis', 'logistics', 'repair', 'billing']
    return roles

def build_fellowship_graph(ticket: RepairTicket):
    appliance, issue = extract_appliance_and_issue(ticket.issue)
    location = extract_location(ticket.issue, ticket.customer_location)
    agents = get_registered_agents()
    graph_nodes = []
    graph_edges = []
    prev_agent_id = None
    for step in WORKFLOW_ROLES:
        agent = select_best_agent(agents, step["capability"], location, ticket.max_budget)
        if agent:
            node = {
                "id": agent["id"],
                "name": agent["name"],
                "role": step["role"],
                "capability": step["capability"],
                "location": agent["location"],
                "trust_score": agent.get("trust_score", 0),
                "cost_per_task": agent.get("cost_per_task", 0)
            }
            graph_nodes.append(node)
            if prev_agent_id:
                graph_edges.append({"from": prev_agent_id, "to": agent["id"], "handoff": step["role"]})
            prev_agent_id = agent["id"]
    return {"nodes": graph_nodes, "edges": graph_edges}

def generate_mock_signature(agent_id, role, ticket_id):
    # For demo: hash of agent_id + role + ticket_id
    data = f"{agent_id}:{role}:{ticket_id}".encode()
    return hashlib.sha256(data).hexdigest()

def serpapi_result_to_agent(result, role):
    # Convert a SerpAPI local_result to an agent-like dict
    return {
        "id": result.get("place_id", result.get("title", "serpapi-"+role)),
        "name": result.get("title", "Vendor for "+role),
        "role": role,
        "capability": role,
        "location": result.get("address", "Unknown"),
        "trust_score": float(result.get("rating", 0.8))/5 if result.get("rating") else 0.8,
        "cost_per_task": 300.0,  # SerpAPI doesn't provide cost, use default
        "company": result.get("title", "Vendor"),
        "jurisdiction": ["Global"],
        "capabilities": [role],
        "skills": [role],
        "currency": "USD",
        "access_type": "api",
        "is_ai": False,
        "wallet_address": "serpapi",
        "openid_token": "serpapi",
        "public_key": "serpapi",
        "public_key_pem": "serpapi"
    }

# Main planner function for /ticket/plan

def plan_agents(ticket: RepairTicket):
    agents_in_db = get_registered_agents()
    required_roles = extract_roles_from_ticket(ticket)
    graph_nodes = []
    agent_objs = []
    used_ids = set()
    policy_flags = []
    prev_agent_id = None
    step_ids = set()
    for idx, role in enumerate(required_roles):
        # Try SerpAPI first
        serp_results = search_vendors_serpapi(role+" vendor", ticket.customer_location)
        agent = None
        if serp_results:
            agent = serpapi_result_to_agent(serp_results[0], role)
        else:
            # Fallback to local agent logic
            for policy_level in range(4):
                if policy_level == 0:
                    # Strict: all constraints
                    candidates = [
                        a for a in agents_in_db
                        if role in [c.lower() for c in a.get("capabilities", [])]
                        and (ticket.customer_location in a.get("jurisdiction", []) or ticket.customer_location.lower() in a.get("location", "").lower())
                        and a.get("cost_per_task", 0) <= ticket.max_budget
                        and a.get("trust_score", 0) >= 0.6
                    ]
                elif policy_level == 1:
                    # Relax trust
                    candidates = [
                        a for a in agents_in_db
                        if role in [c.lower() for c in a.get("capabilities", [])]
                        and (ticket.customer_location in a.get("jurisdiction", []) or ticket.customer_location.lower() in a.get("location", "").lower())
                        and a.get("cost_per_task", 0) <= ticket.max_budget
                    ]
                elif policy_level == 2:
                    # Relax location
                    candidates = [
                        a for a in agents_in_db
                        if role in [c.lower() for c in a.get("capabilities", [])]
                        and a.get("cost_per_task", 0) <= ticket.max_budget
                    ]
                else:
                    # Any agent with capability
                    candidates = [
                        a for a in agents_in_db
                        if role in [c.lower() for c in a.get("capabilities", [])]
                    ]
                if candidates:
                    agent = max(candidates, key=lambda a: a.get("trust_score", 0))
                    if policy_level > 0:
                        policy_flags.append(f"Policy relaxed for role '{role}' at level {policy_level}")
                    break
            if not agent:
                # Fallback: pick real agent with highest trust_score (even if not a match)
                if agents_in_db:
                    agent = max(agents_in_db, key=lambda a: a.get("trust_score", 0))
                    policy_flags.append(f"No matching agent for role '{role}', using real agent '{agent.get('id', 'unknown')}' as fallback")
                else:
                    # If no agents at all, use dummy
                    policy_flags.append(f"No agent found for role '{role}', using dummy agent")
                    agent = {
                        "id": role+"-dummy",
                        "name": role.capitalize()+" Agent",
                        "role": role,
                        "capability": role,
                        "location": "Global",
                        "trust_score": 0.8,
                        "cost_per_task": 200.0,
                        "company": "DemoCo",
                        "jurisdiction": ["Global"],
                        "capabilities": [role],
                        "skills": [role],
                        "currency": "USD",
                        "access_type": "api",
                        "is_ai": True,
                        "wallet_address": "0xDUMMY",
                        "openid_token": "demo",
                        "public_key": "demo",
                        "public_key_pem": "demo"
                    }
        # Generate data-sharing contract for this agent
        contract = generate_data_contract(ticket.customer_location, agent.get("location", "Global"))
        # Use real agent id and name for fallback, not dummy
        real_agent_id = agent.get("id", None)
        real_agent_name = agent.get("name", None)
        node_id = real_agent_id if real_agent_id else role+"-dummy"
        node_name = real_agent_name if real_agent_name else role.capitalize()+" Agent"
        # Generate provenance: step_id and mock signature
        step_id = f"{ticket.ticket_id}-{role}-{node_id}"
        if step_id in step_ids:
            policy_flags.append(f"Double-billing or duplicate step detected for {step_id}")
        step_ids.add(step_id)
        signature = generate_mock_signature(node_id, role, ticket.ticket_id)
        node = {
            "id": node_id,
            "name": node_name,
            "role": role,
            "capability": role,
            "location": agent.get("location", "Global"),
            "trust_score": agent.get("trust_score", 0.8),
            "cost_per_task": agent.get("cost_per_task", 200.0),
            "data_contract": contract,
            "step_id": step_id,
            "signature": signature,
            "agent_id": node_id
        }
        graph_nodes.append(node)
        if agent.get("id") not in used_ids:
            try:
                agent_objs.append(Agent(**agent))
            except Exception:
                pass
            used_ids.add(agent.get("id"))
        prev_agent_id = node_id
    # Build edges
    graph_edges = []
    for i in range(1, len(graph_nodes)):
        graph_edges.append({
            "from": graph_nodes[i-1]["id"],
            "to": graph_nodes[i]["id"],
            "handoff": graph_nodes[i]["role"],
            "step_id": graph_nodes[i]["step_id"],
            "signature": graph_nodes[i]["signature"],
            "agent_id": graph_nodes[i]["agent_id"]
        })
    graph = {"nodes": graph_nodes, "edges": graph_edges, "policy_flags": policy_flags}
    return agent_objs, graph

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
