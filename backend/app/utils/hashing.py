import hashlib
from Crypto.PublicKey import ECC
from Crypto.Signature import DSS
from Crypto.Hash import SHA256

def hash_data(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()

def mock_sign(data: str, key: str) -> str:
    # Simulate a digital signature
    return hash_data(data + key)[:16]

def generate_key_pair():
    key = ECC.generate(curve='P-256')
    private_key = key.export_key(format='PEM')
    public_key = key.public_key().export_key(format='PEM')
    return private_key, public_key

def sign_data(data: str, private_key_pem: str) -> str:
    key = ECC.import_key(private_key_pem)
    h = SHA256.new(data.encode())
    signer = DSS.new(key, 'fips-186-3')
    signature = signer.sign(h)
    return signature.hex()

def verify_signature(data: str, signature_hex: str, public_key_pem: str) -> bool:
    key = ECC.import_key(public_key_pem)
    h = SHA256.new(data.encode())
    verifier = DSS.new(key, 'fips-186-3')
    try:
        verifier.verify(h, bytes.fromhex(signature_hex))
        return True
    except ValueError:
        return False
