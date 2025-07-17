import hashlib
import time
from typing import Dict, Any
from app.utils.hashing import sign_data

def generate_contract(agent_id: str, ticket_id: str, data_shared: list, purpose: str, expiry_hours: int = 48, private_key: str = "") -> Dict[str, Any]:
    expiry_ts = int(time.time()) + expiry_hours * 3600
    contract = {
        'contract_id': f'contract-{agent_id[:4]}-{ticket_id[:4]}',
        'agent_id': agent_id,
        'ticket_id': ticket_id,
        'data_shared': data_shared,
        'purpose': purpose,
        'expiry': expiry_ts,
    }
    contract_str = str(contract)
    contract['hash'] = hashlib.sha256(contract_str.encode()).hexdigest()
    if private_key:
        contract['signature'] = sign_data(contract['hash'], private_key)
    else:
        contract['signature'] = 'mock-signature-' + agent_id[-3:]
    return contract

def generate_privacy_contract(agent_id: str, permitted_fields: list, data_jurisdiction: str, expiry_hours: int = 48, policy: str = "") -> Dict[str, Any]:
    expiry_ts = int(time.time()) + expiry_hours * 3600
    contract = {
        'contract_id': f'privacy-{agent_id[:6]}',
        'agent_id': agent_id,
        'permitted_fields': permitted_fields,
        'data_jurisdiction': data_jurisdiction,
        'expiry': expiry_ts,
        'policy': policy,
    }
    contract_str = str(contract)
    contract['policy_hash'] = hashlib.sha256(contract_str.encode()).hexdigest()
    return contract
