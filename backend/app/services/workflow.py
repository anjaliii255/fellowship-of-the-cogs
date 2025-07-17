from datetime import datetime
from app.utils.blockchain import sign_data, generate_keys
from app.services.contracts import generate_privacy_contract

def generate_receipt(agent_name, task_data, private_key):
    data_str = f"{agent_name}|{task_data}|{datetime.utcnow().isoformat()}"
    signature = sign_data(private_key, data_str)
    return {
        "agent": agent_name,
        "data": task_data,
        "timestamp": datetime.utcnow().isoformat(),
        "signature": signature
    }

def langchain_simulate_workflow(ticket, agents):
    # Simulate Diagnoser -> LogisticBot -> RepairAgent
    steps = ["diagnosis", "logistics", "repair"]
    logs = []
    priv_keys = {}
    pub_keys = {}
    # Generate keys for each agent (mock)
    for agent in agents:
        priv, pub = generate_keys()
        priv_keys[agent.name] = priv
        pub_keys[agent.name] = pub
    for step, agent in zip(steps, agents):
        # Generate privacy contract for this step
        contract = generate_privacy_contract(
            agent_id=agent.name,
            permitted_fields=[step],
            data_jurisdiction=ticket.data_constraints[0] if ticket.data_constraints else "EU",
            expiry_hours=48,
            policy=f"Only {step} data allowed"
        )
        # Simulate agent signing the step
        data_str = f"{agent.name}|{step}|{datetime.utcnow().isoformat()}"
        signature = sign_data(priv_keys[agent.name], data_str)
        logs.append({
            "agent": agent.name,
            "step": step,
            "timestamp": datetime.utcnow().isoformat(),
            "contract": contract,
            "signature": signature
        })
    return logs 