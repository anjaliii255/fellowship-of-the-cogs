from app.utils.hashing import verify_signature

def check_double_billing(agent_id: str, ticket_id: str, logs: list) -> bool:
    # Stub: return True if agent has already billed for this ticket
    return any(log['agent_id'] == agent_id and log['ticket_id'] == ticket_id for log in logs)

def check_impersonation(data: str, signature: str, public_key: str) -> bool:
    # Return True if signature is invalid (impersonation detected)
    return not verify_signature(data, signature, public_key)
