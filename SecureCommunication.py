# 예시: 에이전트 간 암호화 통신
import hashlib
import hmac
import json
import time
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class SecureCommunication:
    def __init__(self, shared_secret: str):
        # 공유 비밀을 기반으로 암호화 키 생성
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
        """메시지 암호화"""
        # 타임스탬프 추가로 재전송 공격 방지
        message['timestamp'] = time.time()
        message['nonce'] = self.generate_nonce()
        
        # JSON 직렬화 후 암호화
        message_json = json.dumps(message, sort_keys=True)
        encrypted_data = self.cipher.encrypt(message_json.encode())
        
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    def decrypt_message(self, encrypted_message: str) -> Dict:
        """메시지 복호화"""
        try:
            # Base64 디코딩 후 복호화
            encrypted_data = base64.urlsafe_b64decode(encrypted_message.encode())
            decrypted_data = self.cipher.decrypt(encrypted_data)
            
            message = json.loads(decrypted_data.decode())
            
            # 타임스탬프 검증 (5분 이내 메시지만 유효)
            if time.time() - message.get('timestamp', 0) > 300:
                raise ValueError("Message timestamp too old")
            
            return message
            
        except Exception as e:
            raise ValueError(f"Message decryption failed: {e}")
    
    def sign_message(self, message: Dict) -> str:
        """메시지 무결성을 위한 디지털 서명"""
        message_json = json.dumps(message, sort_keys=True)
        signature = hmac.new(
            self.shared_secret.encode(),
            message_json.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def verify_signature(self, message: Dict, signature: str) -> bool:
        """디지털 서명 검증"""
        expected_signature = self.sign_message(message)
        return hmac.compare_digest(expected_signature, signature)
    @staticmethod
    def generate_nonce() -> str:
        """재전송 공격 방지를 위한 논스 생성"""
        import secrets
        return secrets.token_hex(16)

class AgentAuthenticator:
    def __init__(self):
        self.registered_agents = {}
        self.active_sessions = {}
        self.failed_attempts = {}
    
    def register_agent(self, agent_id: str, public_key: str, permissions: List[str]):
        """에이전트 등록"""
        self.registered_agents[agent_id] = {
            'public_key': public_key,
            'permissions': permissions,
            'created_at': time.time(),
            'status': 'active'
        }
    
    def authenticate_agent(self, agent_id: str, challenge_response: str) -> bool:
        """에이전트 인증"""
        if agent_id not in self.registered_agents:
            self.record_failed_attempt(agent_id)
            return False
        
        # 실패 시도 횟수 확인
        if self.is_blocked(agent_id):
            return False
        
        # 챌린지-응답 검증 (실제로는 더 복잡한 로직)
        expected_response = self.calculate_expected_response(agent_id)
        
        if challenge_response == expected_response:
            self.create_session(agent_id)
            self.clear_failed_attempts(agent_id)
            return True
        else:
            self.record_failed_attempt(agent_id)
            return False
    
    def is_blocked(self, agent_id: str) -> bool:
        """에이전트 차단 상태 확인"""
        if agent_id in self.failed_attempts:
            attempts = self.failed_attempts[agent_id]
            if attempts['count'] >= 5:  # 5회 실패 시 차단
                # 차단 시간 확인 (1시간)
                return time.time() - attempts['last_attempt'] < 3600
        return False
    
    def record_failed_attempt(self, agent_id: str):
        """실패 시도 기록"""
        if agent_id not in self.failed_attempts:
            self.failed_attempts[agent_id] = {'count': 0, 'last_attempt': 0}
        
        self.failed_attempts[agent_id]['count'] += 1
        self.failed_attempts[agent_id]['last_attempt'] = time.time()