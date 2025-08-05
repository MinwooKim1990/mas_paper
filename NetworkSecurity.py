# 예시: 네트워크 레벨 보안 구현
import ipaddress
import time
from typing import Set, Dict
import threading

class NetworkSecurityManager:
    def __init__(self):
        self.allowed_ips: Set[str] = set()
        self.blocked_ips: Set[str] = set()
        self.rate_limits: Dict[str, Dict] = {}
        self.connection_counts: Dict[str, int] = {}
        self.max_connections_per_ip = 10
        self.rate_limit_window = 60  # 1분
        self.max_requests_per_window = 100
        self.lock = threading.Lock()
    
    def add_allowed_ip(self, ip_address: str):
        """허용된 IP 주소 추가"""
        try:
            ipaddress.ip_address(ip_address)
            self.allowed_ips.add(ip_address)
        except ValueError:
            raise ValueError(f"Invalid IP address: {ip_address}")
    
    def block_ip(self, ip_address: str, duration: int = 3600):
        """IP 주소 차단"""
        self.blocked_ips.add(ip_address)
        # 일정 시간 후 자동 해제 (실제로는 별도 스케줄러 사용)
        threading.Timer(duration, lambda: self.blocked_ips.discard(ip_address)).start()
    
    def is_connection_allowed(self, ip_address: str) -> bool:
        """연결 허용 여부 확인"""
        with self.lock:
            # 차단된 IP 확인
            if ip_address in self.blocked_ips:
                return False
            
            # 허용 목록이 있는 경우 확인
            if self.allowed_ips and ip_address not in self.allowed_ips:
                return False
            
            # 연결 수 제한 확인
            current_connections = self.connection_counts.get(ip_address, 0)
            if current_connections >= self.max_connections_per_ip:
                return False
            
            # 요청 속도 제한 확인
            if not self._check_rate_limit(ip_address):
                return False
            
            return True
    
    def register_connection(self, ip_address: str):
        """새 연결 등록"""
        with self.lock:
            self.connection_counts[ip_address] = self.connection_counts.get(ip_address, 0) + 1
    
    def unregister_connection(self, ip_address: str):
        """연결 해제"""
        with self.lock:
            if ip_address in self.connection_counts:
                self.connection_counts[ip_address] -= 1
                if self.connection_counts[ip_address] <= 0:
                    del self.connection_counts[ip_address]
    def _check_rate_limit(self, ip_address: str) -> bool:
        """요청 속도 제한 확인"""
        current_time = time.time()
        
        if ip_address not in self.rate_limits:
            self.rate_limits[ip_address] = {
                'requests': [],
                'window_start': current_time
            }
        
        rate_limit_data = self.rate_limits[ip_address]
        
        # 윈도우 초기화
        if current_time - rate_limit_data['window_start'] >= self.rate_limit_window:
            rate_limit_data['requests'] = []
            rate_limit_data['window_start'] = current_time
        
        # 현재 윈도우 내 요청 수 확인
        if len(rate_limit_data['requests']) >= self.max_requests_per_window:
            return False
        
        # 요청 기록
        rate_limit_data['requests'].append(current_time)
        return True

class SecureAgentServer:
    def __init__(self, port: int = 8080):
        self.port = port
        self.security_manager = NetworkSecurityManager()
        self.ssl_context = self._create_ssl_context()
    
    def _create_ssl_context(self):
        """SSL/TLS 컨텍스트 생성"""
        import ssl
        
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        # 실제로는 인증서 파일 경로 지정
        # context.load_cert_chain('server.crt', 'server.key')
        
        # 강력한 암호화 설정
        context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        
        return context
    
    async def handle_connection(self, request, client_ip: str):
        """안전한 연결 처리"""
        # 보안 검사
        if not self.security_manager.is_connection_allowed(client_ip):
            return {'error': 'Connection denied', 'status': 403}
        
        try:
            # 연결 등록
            self.security_manager.register_connection(client_ip)
            
            # 요청 처리
            response = await self.process_request(request)
            
            return response
            
        except Exception as e:
            # 보안 이벤트 로깅
            self._log_security_event(client_ip, f"Request processing error: {e}")
            return {'error': 'Internal server error', 'status': 500}
        
        finally:
            # 연결 해제
            self.security_manager.unregister_connection(client_ip)
    
    def _log_security_event(self, ip_address: str, event: str):
        """보안 이벤트 로깅"""
        log_entry = {
            'timestamp': time.time(),
            'ip_address': ip_address,
            'event': event,
            'severity': 'WARNING'
        }
        # 실제로는 보안 로그 시스템에 전송
        print(f"Security Event: {log_entry}")