# Example: Circuit Breaker Implementation
import time
import threading
from enum import Enum
from typing import Callable, Any
import random

class CircuitState(Enum):
    CLOSED = "closed"      # Normal state
    OPEN = "open"          # Tripped state
    HALF_OPEN = "half_open"  # Recovery state

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
        """Calls the function through the circuit breaker."""
        with self.lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.failure_count = 0
                else:
                    raise Exception("Circuit breaker is OPEN")
            
            try:
                result = func(*args, **kwargs)
                
                # Close the circuit on success
                if self.state == CircuitState.HALF_OPEN:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                
                return result
                
            except self.expected_exception as e:
                self._record_failure()
                raise e
    
    def _should_attempt_reset(self) -> bool:
        """Checks if a reset should be attempted."""
        return (self.last_failure_time and 
                time.time() - self.last_failure_time >= self.recovery_timeout)

    def _record_failure(self):
        """Records a failure."""
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
        """Adds a circuit breaker for a service."""
        self.circuit_breakers[service_name] = CircuitBreaker(**kwargs)
    
    def add_backup_service(self, primary_service: str, backup_service: str):
        """Registers a backup service."""
        self.backup_services[primary_service] = backup_service
    
    def call_service(self, service_name: str, service_func: Callable, *args, **kwargs):
        """Calls a service with fault tolerance."""
        try:
            if service_name in self.circuit_breakers:
                cb = self.circuit_breakers[service_name]
                return cb.call(service_func, *args, **kwargs)
            else:
                return service_func(*args, **kwargs)
                
        except Exception as e:
            # Try backup service
            if service_name in self.backup_services:
                backup_name = self.backup_services[service_name]
                print(f"Primary service {service_name} failed, trying backup {backup_name}")
                return self.call_backup_service(backup_name, *args, **kwargs)
            else:
                raise e
    
    def call_backup_service(self, backup_service: str, *args, **kwargs):
        """Calls a backup service."""
        # Implement backup service logic
        print(f"Executing backup service: {backup_service}")
        return {"status": "success", "source": "backup"}

if __name__ == "__main__":
    # A dummy service that can fail
    def potentially_failing_service():
        if random.random() < 0.6: # 60% chance of failure
            raise ValueError("Service failed")
        return "Success from primary service"

    agent = ResilientAgent("resilient_agent_007")

    # Configure a circuit breaker for the service
    agent.add_circuit_breaker(
        "failing_service",
        failure_threshold=2,
        recovery_timeout=5
    )

    # Configure a backup service
    agent.add_backup_service("failing_service", "backup_service_alpha")

    print("--- Demonstrating Circuit Breaker Pattern ---")

    for i in range(10):
        print(f"\n--- Call {i+1} ---")
        try:
            result = agent.call_service("failing_service", potentially_failing_service)
            print(f"Result: {result}")
        except Exception as e:
            print(f"Error: {e}")
            # Check the state of the circuit breaker
            cb = agent.circuit_breakers["failing_service"]
            print(f"Circuit breaker state: {cb.state.value}")

        time.sleep(1)

    print("\n--- Waiting for recovery timeout ---")
    time.sleep(5)

    print("\n--- Attempting call after recovery timeout ---")
    try:
        result = agent.call_service("failing_service", potentially_failing_service)
        print(f"Result: {result}")
        cb = agent.circuit_breakers["failing_service"]
        print(f"Circuit breaker state: {cb.state.value}")
    except Exception as e:
        print(f"Error: {e}")
        cb = agent.circuit_breakers["failing_service"]
        print(f"Circuit breaker state: {cb.state.value}")