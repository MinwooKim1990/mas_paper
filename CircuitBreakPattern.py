# 예시: 회로 차단기 구현
import time
import threading
from enum import Enum
from typing import Callable, Any

class CircuitState(Enum):
    CLOSED = "closed"      # 정상 상태
    OPEN = "open"          # 차단 상태
    HALF_OPEN = "half_open"  # 반개방 상태

class CircuitBreaker:
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 expected_exception: type = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        self.lock = threading.Lock()
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """회로 차단기를 통한 함수 호출"""
        with self.lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.failure_count = 0
                else:
                    raise Exception("Circuit breaker is OPEN")
            
            try:
                result = func(*args, **kwargs)
                
                # 성공 시 회로 닫기
                if self.state == CircuitState.HALF_OPEN:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                
                return result
                
            except self.expected_exception as e:
                self._record_failure()
                raise e
    
    def _should_attempt_reset(self) -> bool:
        """회로 재설정 시도 여부 확인"""
        return (self.last_failure_time and 
                time.time() - self.last_failure_time >= self.recovery_timeout)
    def _record_failure(self):
        """실패 기록"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

    @property
    def is_open(self) -> bool:
        return self.state == CircuitState.OPEN

class ResilientAgent:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.circuit_breakers = {}
        self.backup_services = {}
    
    def add_circuit_breaker(self, service_name: str, **kwargs):
        """서비스에 대한 회로 차단기 추가"""
        self.circuit_breakers[service_name] = CircuitBreaker(**kwargs)
    
    def add_backup_service(self, primary_service: str, backup_service: str):
        """백업 서비스 등록"""
        self.backup_services[primary_service] = backup_service
    
    def call_service(self, service_name: str, service_func: Callable, *args, **kwargs):
        """장애 내성을 가진 서비스 호출"""
        try:
            if service_name in self.circuit_breakers:
                cb = self.circuit_breakers[service_name]
                return cb.call(service_func, *args, **kwargs)
            else:
                return service_func(*args, **kwargs)
                
        except Exception as e:
            # 백업 서비스 시도
            if service_name in self.backup_services:
                backup_name = self.backup_services[service_name]
                print(f"Primary service {service_name} failed, trying backup {backup_name}")
                return self.call_backup_service(backup_name, *args, **kwargs)
            else:
                raise e
    
    def call_backup_service(self, backup_service: str, *args, **kwargs):
        """백업 서비스 호출"""
        # 백업 서비스 로직 구현
        print(f"Executing backup service: {backup_service}")
        return {"status": "success", "source": "backup"}