# 예시: 보안 위협 분석 및 대응
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict
import logging

class ThreatLevel(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class SecurityThreat:
    threat_id: str
    description: str
    level: ThreatLevel
    affected_components: List[str]
    mitigation_strategies: List[str]

class SecurityThreatAnalyzer:
    def __init__(self):
        self.known_threats = {
            'message_tampering': SecurityThreat(
                threat_id='MSG_TAMPER_001',
                description='악의적인 에이전트가 메시지 내용을 변조',
                level=ThreatLevel.HIGH,
                affected_components=['communication', 'message_routing'],
                mitigation_strategies=['message_signing', 'encryption', 'integrity_check']
            ),
            'agent_impersonation': SecurityThreat(
                threat_id='AGENT_IMP_001',
                description='합법적 에이전트로 위장한 악의적 에이전트',
                level=ThreatLevel.CRITICAL,
                affected_components=['authentication', 'authorization'],
                mitigation_strategies=['mutual_authentication', 'certificate_validation']
            ),
            'resource_exhaustion': SecurityThreat(
                threat_id='RES_EXHAUST_001',
                description='시스템 자원을 고갈시키는 DoS 공격',
                level=ThreatLevel.HIGH,
                affected_components=['resource_management', 'message_processing'],
                mitigation_strategies=['rate_limiting', 'resource_quotas', 'circuit_breaker']
            ),
            'data_leakage': SecurityThreat(
                threat_id='DATA_LEAK_001',
                description='민감한 정보의 무단 노출',
                level=ThreatLevel.MEDIUM,
                affected_components=['data_storage', 'communication'],
                mitigation_strategies=['data_encryption', 'access_control', 'audit_logging']
            )
        }
        
        self.logger = logging.getLogger('security_analyzer')
    
    def assess_threat_level(self, system_components: List[str]) -> Dict[str, ThreatLevel]:
        """시스템 구성요소에 대한 위협 수준 평가"""
        threat_assessment = {}
        
        for threat_name, threat in self.known_threats.items():
            # 영향 받는 구성요소가 시스템에 포함되어 있는지 확인
            affected = any(component in system_components for component in threat.affected_components)
            
            if affected:
                threat_assessment[threat_name] = threat.level
                self.logger.warning(f"Threat detected: {threat.description}")
        
        return threat_assessment
    
    def recommend_mitigations(self, detected_threats: List[str]) -> List[str]:
        """감지된 위협에 대한 완화 전략 추천"""
        all_mitigations = set()
        
        for threat_name in detected_threats:
            if threat_name in self.known_threats:
                threat = self.known_threats[threat_name]
                all_mitigations.update(threat.mitigation_strategies)
        
        return list(all_mitigations)