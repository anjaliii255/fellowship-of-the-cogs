import requests
from app.models.repair_ticket import RepairTicket
from app.models.agent import Agent
import os

SERPAPI_KEY = "a968aa935374cedce17862752216921e741faa87f83f0826c52164bbfbc18ba2"

# Helper to search vendors using SerpAPI
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
    vendors = []
    for r in results:
        vendors.append({
            "name": r.get("title"),
            "company": r.get("title"),
            "location": r.get("address", location),
            "jurisdiction": [location],
            "capabilities": [query],
            "skills": [query],
            "cost_per_task": 0.0,  # No cost info from SerpAPI
            "currency": "INR",  # Default, can be improved
            "access_type": "API",
            "trust_score": float(r.get("rating", 0.8)),
            "is_ai": False,
            "wallet_address": "",
            "openid_token": "",
            "public_key": "",
            "public_key_pem": ""
        })
    return vendors

def plan_agents(ticket: RepairTicket):
    # Use SerpAPI to search for vendors
    query = " ".join(ticket.required_capabilities) + " repair"
    location = ticket.customer_location
    serp_vendors = search_vendors_serpapi(query, location)
    # Score and filter vendors
    selected = []
    for cap in ticket.required_capabilities:
        best = None
        for vendor in serp_vendors:
            if cap in vendor["capabilities"] and location in vendor["jurisdiction"]:
                # Use trust_score and other criteria
                if best is None or vendor["trust_score"] > best["trust_score"]:
                    best = vendor
        if best:
            selected.append(Agent(**best))
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
