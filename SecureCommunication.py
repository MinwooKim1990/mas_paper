# Example: Secure Communication Between Agents
import hashlib
import hmac
import json
import time
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import secrets
from typing import Dict, List

class SecureCommunication:
    def __init__(self, shared_secret: str):
        # Generate an encryption key from the shared secret
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'agent_salt',
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(shared_secret.encode()))
        self.cipher = Fernet(key)
        self.shared_secret = shared_secret
    
    def encrypt_message(self, message: Dict) -> str:
        """Encrypts a message."""
        # Add a timestamp to prevent replay attacks
        message['timestamp'] = time.time()
        message['nonce'] = self.generate_nonce()
        
        # Encrypt after JSON serialization
        message_json = json.dumps(message, sort_keys=True)
        encrypted_data = self.cipher.encrypt(message_json.encode())
        
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    def decrypt_message(self, encrypted_message: str) -> Dict:
        """Decrypts a message."""
        try:
            # Decrypt after Base64 decoding
            encrypted_data = base64.urlsafe_b64decode(encrypted_message.encode())
            decrypted_data = self.cipher.decrypt(encrypted_data)
            
            message = json.loads(decrypted_data.decode())
            
            # Validate timestamp (only messages from the last 5 minutes are valid)
            if time.time() - message.get('timestamp', 0) > 300:
                raise ValueError("Message timestamp too old")
            
            return message
            
        except Exception as e:
            raise ValueError(f"Message decryption failed: {e}")
    
    def sign_message(self, message: Dict) -> str:
        """Digitally signs a message for integrity."""
        message_json = json.dumps(message, sort_keys=True)
        signature = hmac.new(
            self.shared_secret.encode(),
            message_json.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def verify_signature(self, message: Dict, signature: str) -> bool:
        """Verifies a digital signature."""
        expected_signature = self.sign_message(message)
        return hmac.compare_digest(expected_signature, signature)

    @staticmethod
    def generate_nonce() -> str:
        """Generates a nonce to prevent replay attacks."""
        return secrets.token_hex(16)

class AgentAuthenticator:
    def __init__(self):
        self.registered_agents = {}
        self.active_sessions = {}
        self.failed_attempts = {}
    
    def register_agent(self, agent_id: str, public_key: str, permissions: List[str]):
        """Registers an agent."""
        self.registered_agents[agent_id] = {
            'public_key': public_key,
            'permissions': permissions,
            'created_at': time.time(),
            'status': 'active'
        }
    
    def authenticate_agent(self, agent_id: str, challenge_response: str) -> bool:
        """Authenticates an agent."""
        if agent_id not in self.registered_agents:
            self.record_failed_attempt(agent_id)
            return False
        
        # Check the number of failed attempts
        if self.is_blocked(agent_id):
            return False
        
        # Challenge-response verification (in a real scenario, this would be more complex)
        expected_response = self.calculate_expected_response(agent_id)
        
        if challenge_response == expected_response:
            self.create_session(agent_id)
            self.clear_failed_attempts(agent_id)
            return True
        else:
            self.record_failed_attempt(agent_id)
            return False
    
    def is_blocked(self, agent_id: str) -> bool:
        """Checks if an agent is blocked."""
        if agent_id in self.failed_attempts:
            attempts = self.failed_attempts[agent_id]
            if attempts['count'] >= 5:  # Block after 5 failed attempts
                # Check block duration (1 hour)
                return time.time() - attempts['last_attempt'] < 3600
        return False
    
    def record_failed_attempt(self, agent_id: str):
        """Records a failed attempt."""
        if agent_id not in self.failed_attempts:
            self.failed_attempts[agent_id] = {'count': 0, 'last_attempt': 0}
        
        self.failed_attempts[agent_id]['count'] += 1
        self.failed_attempts[agent_id]['last_attempt'] = time.time()

    def calculate_expected_response(self, agent_id: str) -> str:
        """Calculates the expected challenge response (mock)."""
        # This is a mock implementation. In a real system, this would involve challenges.
        return f"response_for_{agent_id}"

    def create_session(self, agent_id: str):
        """Creates a session for an authenticated agent (mock)."""
        session_id = secrets.token_hex(32)
        self.active_sessions[agent_id] = {
            'session_id': session_id,
            'started_at': time.time()
        }
        print(f"Session created for agent {agent_id}.")

    def clear_failed_attempts(self, agent_id: str):
        """Clears failed attempt records for an agent."""
        if agent_id in self.failed_attempts:
            del self.failed_attempts[agent_id]

if __name__ == "__main__":
    # --- SecureCommunication Demo ---
    print("--- SecureCommunication Demo ---")
    shared_secret = "a_very_secret_key"
    comm = SecureCommunication(shared_secret)

    # Create a message
    original_message = {"from": "agent1", "to": "agent2", "content": "This is a secret message."}
    print(f"Original message: {original_message}")

    # Encrypt the message
    encrypted_msg = comm.encrypt_message(original_message)
    print(f"Encrypted message: {encrypted_msg}")

    # Decrypt the message
    try:
        decrypted_message = comm.decrypt_message(encrypted_msg)
        print(f"Decrypted message: {decrypted_message}")
        assert decrypted_message['content'] == original_message['content']
    except ValueError as e:
        print(f"Decryption failed: {e}")

    # Sign the message
    signature = comm.sign_message(original_message)
    print(f"Signature: {signature}")

    # Verify the signature
    is_valid = comm.verify_signature(original_message, signature)
    print(f"Signature verification: {'Valid' if is_valid else 'Invalid'}")

    # --- AgentAuthenticator Demo ---
    print("\n--- AgentAuthenticator Demo ---")
    auth = AgentAuthenticator()

    # Register an agent
    agent_id = "test_agent_001"
    auth.register_agent(agent_id, "pubkey_xyz", ["read", "write"])
    print(f"Agent {agent_id} registered.")

    # Successful authentication
    print("\nTesting successful authentication...")
    challenge_response = auth.calculate_expected_response(agent_id)
    is_authenticated = auth.authenticate_agent(agent_id, challenge_response)
    print(f"Authentication for {agent_id}: {'Success' if is_authenticated else 'Failed'}")

    # Failed authentication
    print("\nTesting failed authentication...")
    for i in range(6):
        is_authenticated = auth.authenticate_agent(agent_id, "wrong_response")
        print(f"Attempt {i+1}: Authentication for {agent_id}: {'Success' if is_authenticated else 'Failed'}")
        if auth.is_blocked(agent_id):
            print(f"Agent {agent_id} is now blocked.")
            break