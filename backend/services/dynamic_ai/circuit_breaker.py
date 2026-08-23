from loguru import logger
# backend/services/dynamic_ai/circuit_breaker.py
"""
Circuit Breaker Pattern Implementation
Prevents cascading failures by stopping calls to failing providers
"""

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional


class CircuitState(Enum):
    CLOSED = "closed"        # Normal operation - requests flow through
    OPEN = "open"            # Failing - requests are blocked
    HALF_OPEN = "half_open"  # Testing - one request allowed to test recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior"""
    failure_threshold: int = 3        # Failures before opening
    success_threshold: int = 2        # Successes in half-open to close
    timeout_seconds: float = 30.0     # How long to stay open before half-open
    half_open_max_calls: int = 1      # Max concurrent calls in half-open state


@dataclass
class CircuitStateInfo:
    """Current state of a circuit breaker"""
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    last_state_change: float = field(default_factory=time.time)
    total_blocked_requests: int = 0
    total_allowed_requests: int = 0


class CircuitBreakerManager:
    """
    Manages circuit breakers for all providers
    Prevents wasting time on known-failing services
    """
    
    def __init__(self, config: Optional[CircuitBreakerConfig] = None):
        self._config = config or CircuitBreakerConfig()
        self._circuits: Dict[str, CircuitStateInfo] = {}
        self._lock = asyncio.Lock()
    
    def get_circuit(self, provider_id: str) -> CircuitStateInfo:
        """Get or create circuit breaker for provider"""
        if provider_id not in self._circuits:
            self._circuits[provider_id] = CircuitStateInfo()
        return self._circuits[provider_id]
    
    async def is_available(self, provider_id: str) -> bool:
        """
        Check if request should be allowed through
        Updates state based on time and previous failures
        """
        circuit = self.get_circuit(provider_id)
        
        async with self._lock:
            current_time = time.time()
            
            if circuit.state == CircuitState.CLOSED:
                # Normal operation - allow through
                circuit.total_allowed_requests += 1
                return True
            
            elif circuit.state == CircuitState.OPEN:
                # Check if we should transition to half-open
                time_since_open = current_time - circuit.last_failure_time
                
                if time_since_open >= self._config.timeout_seconds:
                    # Time to test if recovered
                    circuit.state = CircuitState.HALF_OPEN
                    circuit.success_count = 0
                    circuit.last_state_change = current_time
                    logger.debug(f"🔓 Circuit for {provider_id} transitioning to HALF-OPEN (testing)")
                    return True
                else:
                    # Still in open state - block request
                    circuit.total_blocked_requests += 1
                    remaining = self._config.timeout_seconds - time_since_open
                    return False
            
            elif circuit.state == CircuitState.HALF_OPEN:
                # Allow limited requests through to test
                if circuit.success_count < self._config.half_open_max_calls:
                    circuit.total_allowed_requests += 1
                    return True
                else:
                    # Already testing - block additional
                    circuit.total_blocked_requests += 1
                    return False
        
        return True  # Default allow if lock fails
    
    async def record_success(self, provider_id: str):
        """Record successful request"""
        circuit = self.get_circuit(provider_id)
        
        async with self._lock:
            if circuit.state == CircuitState.HALF_OPEN:
                circuit.success_count += 1
                
                # Check if we should close the circuit
                if circuit.success_count >= self._config.success_threshold:
                    old_state = circuit.state
                    circuit.state = CircuitState.CLOSED
                    circuit.failure_count = 0
                    circuit.success_count = 0
                    circuit.last_state_change = time.time()
                    logger.debug(f"Circuit for {provider_id} CLOSED (recovered!)")
            
            elif circuit.state == CircuitState.CLOSED:
                # Reset failure count on success in closed state
                circuit.failure_count = 0
    
    async def record_failure(self, provider_id: str):
        """Record failed request"""
        circuit = self.get_circuit(provider_id)
        
        async with self._lock:
            circuit.failure_count += 1
            circuit.last_failure_time = time.time()
            
            if circuit.state == CircuitState.CLOSED:
                # Check if we should open the circuit
                if circuit.failure_count >= self._config.failure_threshold:
                    old_state = circuit.state
                    circuit.state = CircuitState.OPEN
                    circuit.last_state_change = time.time()
                    logger.debug(f"🔒 Circuit for {provider_id} OPENED ({circuit.failure_count} failures)")
            
            elif circuit.state == CircuitState.HALF_OPEN:
                # Failure in half-open - go back to open
                circuit.state = CircuitState.OPEN
                circuit.last_failure_time = time.time()
                circuit.last_state_change = time.time()
                logger.debug(f"🔒 Circuit for {provider_id} RE-OPENED (half-open test failed)")
    
    def get_all_circuit_states(self) -> Dict[str, dict]:
        """Get status of all circuit breakers"""
        states = {}
        for provider_id, circuit in self._circuits.items():
            states[provider_id] = {
                "state": circuit.state.value,
                "failure_count": circuit.failure_count,
                "success_count": circuit.success_count,
                "total_blocked": circuit.total_blocked_requests,
                "total_allowed": circuit.total_allowed_requests,
                "last_failure_time": circuit.last_failure_time,
                "last_state_change": circuit.last_state_change,
            }
        return states
    
    def reset_circuit(self, provider_id: str):
        """Manually reset a circuit breaker (force closed)"""
        if provider_id in self._circuits:
            self._circuits[provider_id] = CircuitStateInfo()
            logger.debug(f"🔄 Circuit for {provider_id} manually reset")
