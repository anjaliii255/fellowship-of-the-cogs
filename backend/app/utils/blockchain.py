from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.exceptions import InvalidSignature
import base64

def generate_keys():
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    return private_key, public_key

def sign_data(private_key, data: str):
    signature = private_key.sign(data.encode(), ec.ECDSA(hashes.SHA256()))
    return base64.b64encode(signature).decode()

def verify_signature(public_key, data: str, signature: str):
    try:
        decoded = base64.b64decode(signature.encode())
        public_key.verify(decoded, data.encode(), ec.ECDSA(hashes.SHA256()))
        return True
    except InvalidSignature:
        return False 