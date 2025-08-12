# Example: Network Level Security Implementation
import ipaddress
import time
from typing import Set, Dict
import threading
import ssl

class NetworkSecurityManager:
    def __init__(self):
        self.allowed_ips: Set[str] = set()
        self.blocked_ips: Set[str] = set()
        self.rate_limits: Dict[str, Dict] = {}
        self.connection_counts: Dict[str, int] = {}
        self.max_connections_per_ip = 10
        self.rate_limit_window = 60  # 1 minute
        self.max_requests_per_window = 100
        self.lock = threading.Lock()
    
    def add_allowed_ip(self, ip_address: str):
        """Adds an allowed IP address."""
        try:
            ipaddress.ip_address(ip_address)
            self.allowed_ips.add(ip_address)
        except ValueError:
            raise ValueError(f"Invalid IP address: {ip_address}")
    
    def block_ip(self, ip_address: str, duration: int = 3600):
        """Blocks an IP address."""
        self.blocked_ips.add(ip_address)
        # Automatically unblock after a certain duration (in a real scenario, a separate scheduler would be used)
        threading.Timer(duration, lambda: self.blocked_ips.discard(ip_address)).start()
    
    def is_connection_allowed(self, ip_address: str) -> bool:
        """Checks if a connection is allowed."""
        with self.lock:
            # Check for blocked IPs
            if ip_address in self.blocked_ips:
                return False
            
            # Check if an allow list exists
            if self.allowed_ips and ip_address not in self.allowed_ips:
                return False
            
            # Check connection limit
            current_connections = self.connection_counts.get(ip_address, 0)
            if current_connections >= self.max_connections_per_ip:
                return False
            
            # Check request rate limit
            if not self._check_rate_limit(ip_address):
                return False
            
            return True
    
    def register_connection(self, ip_address: str):
        """Registers a new connection."""
        with self.lock:
            self.connection_counts[ip_address] = self.connection_counts.get(ip_address, 0) + 1
    
    def unregister_connection(self, ip_address: str):
        """Unregisters a connection."""
        with self.lock:
            if ip_address in self.connection_counts:
                self.connection_counts[ip_address] -= 1
                if self.connection_counts[ip_address] <= 0:
                    del self.connection_counts[ip_address]

    def _check_rate_limit(self, ip_address: str) -> bool:
        """Checks the request rate limit."""
        current_time = time.time()
        
        if ip_address not in self.rate_limits:
            self.rate_limits[ip_address] = {
                'requests': [],
                'window_start': current_time
            }
        
        rate_limit_data = self.rate_limits[ip_address]
        
        # Reset window
        if current_time - rate_limit_data['window_start'] >= self.rate_limit_window:
            rate_limit_data['requests'] = []
            rate_limit_data['window_start'] = current_time
        
        # Check the number of requests in the current window
        if len(rate_limit_data['requests']) >= self.max_requests_per_window:
            return False
        
        # Record request
        rate_limit_data['requests'].append(current_time)
        return True

class SecureAgentServer:
    """Note: This class is for demonstration and would require a running async server to be fully utilized."""
    def __init__(self, port: int = 8080):
        self.port = port
        self.security_manager = NetworkSecurityManager()
        self.ssl_context = self._create_ssl_context()
    
    def _create_ssl_context(self):
        """Creates an SSL/TLS context."""
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        # In a real scenario, specify the certificate file path
        # context.load_cert_chain('server.crt', 'server.key')
        
        # Set strong encryption
        context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        
        return context
    
    async def handle_connection(self, request, client_ip: str):
        """Handles a secure connection."""
        # Security check
        if not self.security_manager.is_connection_allowed(client_ip):
            return {'error': 'Connection denied', 'status': 403}
        
        try:
            # Register connection
            self.security_manager.register_connection(client_ip)
            
            # Process request
            response = await self.process_request(request)
            
            return response
            
        except Exception as e:
            # Log security event
            self._log_security_event(client_ip, f"Request processing error: {e}")
            return {'error': 'Internal server error', 'status': 500}
        
        finally:
            # Unregister connection
            self.security_manager.unregister_connection(client_ip)
    
    def _log_security_event(self, ip_address: str, event: str):
        """Logs a security event."""
        log_entry = {
            'timestamp': time.time(),
            'ip_address': ip_address,
            'event': event,
            'severity': 'WARNING'
        }
        # In a real scenario, send to a security logging system
        print(f"Security Event: {log_entry}")

if __name__ == "__main__":
    manager = NetworkSecurityManager()
    manager.max_requests_per_window = 5
    manager.rate_limit_window = 2 # seconds for demo

    print("--- NetworkSecurityManager Demo ---")

    # 1. Test Allowed IPs
    print("\n1. Testing Allowed IPs...")
    manager.add_allowed_ip("192.168.1.100")
    print(f"Connection from 192.168.1.100: {'Allowed' if manager.is_connection_allowed('192.168.1.100') else 'Denied'}")
    print(f"Connection from 192.168.1.101: {'Allowed' if manager.is_connection_allowed('192.168.1.101') else 'Denied'}")
    manager.allowed_ips.clear() # Clear for next tests

    # 2. Test Blocked IPs
    print("\n2. Testing Blocked IPs...")
    manager.block_ip("10.0.0.5", duration=3)
    print(f"Connection from 10.0.0.5: {'Allowed' if manager.is_connection_allowed('10.0.0.5') else 'Denied'}")

    # 3. Test Rate Limiting
    print("\n3. Testing Rate Limiting...")
    test_ip = "203.0.113.42"
    for i in range(7):
        allowed = manager.is_connection_allowed(test_ip)
        print(f"Request {i+1} from {test_ip}: {'Allowed' if allowed else 'Denied'}")
        if not allowed:
            print("   (Rate limit likely exceeded)")

    print("   Waiting for rate limit window to reset...")
    time.sleep(3)
    print(f"Request after waiting from {test_ip}: {'Allowed' if manager.is_connection_allowed(test_ip) else 'Denied'}")

    # 4. Test unblocking after duration
    print("\n4. Testing IP unblocking...")
    time.sleep(3)
    print(f"Connection from 10.0.0.5 (after 3s): {'Allowed' if manager.is_connection_allowed('10.0.0.5') else 'Denied'}")
