# 예시: 인간-에이전트 협업 시스템
from enum import Enum
from typing import Optional, Callable, Dict, Any
import asyncio

class InteractionMode(Enum):
    AUTONOMOUS = "autonomous"           # 완전 자율
    SUPERVISED = "supervised"          # 감독하에 실행
    COLLABORATIVE = "collaborative"    # 인간과 협업
    MANUAL_APPROVAL = "manual_approval" # 인간 승인 필요

class HumanApprovalRequired(Exception):
    """인간 승인이 필요한 경우 발생하는 예외"""
    def __init__(self, task_description: str, risk_level: str):
        self.task_description = task_description
        self.risk_level = risk_level
        super().__init__(f"Human approval required for: {task_description}")

class HumanInTheLoopAgent:
    def __init__(self, agent_id: str, interaction_mode: InteractionMode = InteractionMode.SUPERVISED):
        self.agent_id = agent_id
        self.interaction_mode = interaction_mode
        self.pending_approvals = {}
        self.human_feedback_history = []
        self.trust_score = 0.5  # 0-1 범위의 신뢰도
        
        # 위험도별 처리 방식
        self.risk_thresholds = {
            'low': 0.1,      # 낮은 위험: 자율 실행
            'medium': 0.5,   # 중간 위험: 로깅 후 실행
            'high': 0.8,     # 높은 위험: 인간 승인 필요
            'critical': 1.0  # 임계 위험: 항상 승인 필요
        }
    
    async def execute_task(self, task: Dict[str, Any]) -> Any:
        """작업 실행 (인간 개입 고려)"""
        # 위험도 평가
        risk_level = self._assess_risk(task)
        
        # 상호작용 모드와 위험도에 따른 처리
        if self._requires_human_approval(risk_level):
            return await self._request_human_approval(task, risk_level)
        elif self._requires_human_notification(risk_level):
            await self._notify_human(task, risk_level)
        
        # 작업 실행
        try:
            result = await self._execute_core_task(task)
            self._update_trust_score(True)
            return result
        except Exception as e:
            self._update_trust_score(False)
            await self._handle_execution_error(task, e)
            raise
    
    def _assess_risk(self, task: Dict[str, Any]) -> str:
        """작업의 위험도 평가"""
        # 작업 유형별 기본 위험도
        task_type = task.get('type', 'unknown')
        base_risk_scores = {
            'data_query': 0.1,
            'data_modification': 0.6,
            'system_command': 0.9,
            'external_api_call': 0.4,
            'file_operation': 0.5,
            'network_operation': 0.7
        }
        
        base_score = base_risk_scores.get(task_type, 0.5)
        
        # 추가 위험 요소 고려
        if task.get('affects_production', False):
            base_score += 0.3
        
        if task.get('irreversible', False):
            base_score += 0.2
        
        if task.get('affects_user_data', False):
            base_score += 0.2
        
        # 신뢰도에 따른 조정
        adjusted_score = base_score * (1.1 - self.trust_score)
        
        # 위험 수준 분류
        if adjusted_score >= 0.8:
            return 'critical'
        elif adjusted_score >= 0.6:
            return 'high'
        elif adjusted_score >= 0.3:
            return 'medium'
        else:
            return 'low'

    def _requires_human_approval(self, risk_level: str) -> bool:
        """인간 승인 필요 여부 확인"""
        if self.interaction_mode == InteractionMode.MANUAL_APPROVAL:
            return True
        elif self.interaction_mode == InteractionMode.AUTONOMOUS:
            return False
        else:  # SUPERVISED or COLLABORATIVE
            return risk_level in ['high', 'critical']
    
    def _requires_human_notification(self, risk_level: str) -> bool:
        """인간 알림 필요 여부 확인"""
        return (self.interaction_mode == InteractionMode.SUPERVISED and 
                risk_level in ['medium', 'high'])
    
    async def _request_human_approval(self, task: Dict[str, Any], risk_level: str) -> Any:
        """인간 승인 요청"""
        approval_id = f"approval_{int(time.time())}_{len(self.pending_approvals)}"
        
        approval_request = {
            'approval_id': approval_id,
            'agent_id': self.agent_id,
            'task': task,
            'risk_level': risk_level,
            'risk_factors': self._get_risk_factors(task),
            'estimated_impact': self._estimate_impact(task),
            'alternatives': self._suggest_alternatives(task),
            'timestamp': time.time()
        }
        
        self.pending_approvals[approval_id] = approval_request
        
        # 승인 요청 전송 (실제로는 UI/알림 시스템으로)
        await self._send_approval_request(approval_request)
        
        # 승인 대기
        return await self._wait_for_approval(approval_id)
    
    async def _notify_human(self, task: Dict[str, Any], risk_level: str):
        """인간에게 알림"""
        notification = {
            'type': 'task_notification',
            'agent_id': self.agent_id,
            'task': task,
            'risk_level': risk_level,
            'auto_executing': True,
            'timestamp': time.time()
        }
        
        # 알림 전송
        print(f"[NOTIFICATION] Agent {self.agent_id} executing {risk_level} risk task: {task.get('description', 'Unknown task')}")
    
    async def _execute_core_task(self, task: Dict[str, Any]) -> Any:
        """핵심 작업 실행"""
        # 실제 작업 로직 (예시)
        task_type = task.get('type')
        
        if task_type == 'data_query':
            return await self._execute_data_query(task)
        elif task_type == 'system_command':
            return await self._execute_system_command(task)
        else:
            # 일반 작업 처리
            await asyncio.sleep(1)  # 작업 실행 시뮬레이션
            return {'status': 'completed', 'result': f"Task {task.get('id')} completed"}
    
    def _update_trust_score(self, success: bool):
        """신뢰도 점수 업데이트"""
        if success:
            self.trust_score = min(1.0, self.trust_score + 0.05)
        else:
            self.trust_score = max(0.0, self.trust_score - 0.1)
    
    def receive_human_feedback(self, approval_id: str, approved: bool, feedback: str = None):
        """인간 피드백 수신"""
        if approval_id in self.pending_approvals:
            feedback_entry = {
                'approval_id': approval_id,
                'approved': approved,
                'feedback': feedback,
                'timestamp': time.time()
            }
            
            self.human_feedback_history.append(feedback_entry)
            
            # 승인 처리
            if approved:
                task = self.pending_approvals[approval_id]['task']
                # 승인된 작업 실행 스케줄링
                asyncio.create_task(self._execute_approved_task(approval_id))
            else:
                # 거부된 작업 처리
                self._handle_rejected_task(approval_id, feedback)

    async def _execute_approved_task(self, approval_id: str):
        """승인된 작업 실행"""
        approval_request = self.pending_approvals.pop(approval_id)
        task = approval_request['task']
        
        try:
            result = await self._execute_core_task(task)
            # 결과를 인간에게 보고
            await self._report_task_completion(approval_id, result)
        except Exception as e:
            await self._report_task_failure(approval_id, str(e))
    
    def _handle_rejected_task(self, approval_id: str, feedback: str):
        """거부된 작업 처리"""
        approval_request = self.pending_approvals.pop(approval_id)
        
        # 피드백을 학습에 활용
        self._learn_from_rejection(approval_request, feedback)
        
        print(f"Task rejected by human: {feedback}")
    
    def _learn_from_rejection(self, approval_request: Dict, feedback: str):
        """거부 사례로부터 학습"""
        # 간단한 학습 로직 (실제로는 더 복잡한 ML 모델 사용)
        task_type = approval_request['task'].get('type')
        risk_level = approval_request['risk_level']
        
        # 해당 유형의 작업에 대한 위험도 증가
        if hasattr(self, 'learned_risk_adjustments'):
            if task_type not in self.learned_risk_adjustments:
                self.learned_risk_adjustments[task_type] = 0.0
            self.learned_risk_adjustments[task_type] += 0.1
        else:
            self.learned_risk_adjustments = {task_type: 0.1}

class HumanAgentInterface:
    """인간-에이전트 인터페이스"""
    
    def __init__(self):
        self.active_agents = {}
        self.pending_requests = {}
        self.user_preferences = {}
    
    def register_agent(self, agent: HumanInTheLoopAgent):
        """에이전트 등록"""
        self.active_agents[agent.agent_id] = agent
    
    def set_user_preferences(self, user_id: str, preferences: Dict[str, Any]):
        """사용자 선호도 설정"""
        self.user_preferences[user_id] = preferences
    
    async def handle_approval_request(self, request: Dict[str, Any]):
        """승인 요청 처리"""
        request_id = request['approval_id']
        self.pending_requests[request_id] = request
        
        # UI에 승인 요청 표시
        await self._display_approval_request(request)
    
    def approve_request(self, request_id: str, user_id: str, feedback: str = None):
        """요청 승인"""
        if request_id in self.pending_requests:
            request = self.pending_requests[request_id]
            agent_id = request['agent_id']
            
            if agent_id in self.active_agents:
                agent = self.active_agents[agent_id]
                agent.receive_human_feedback(request_id, True, feedback)
                
                # 사용자 행동 학습
                self._learn_user_behavior(user_id, request, 'approved')

    def reject_request(self, request_id: str, user_id: str, reason: str):
        """요청 거부"""
        if request_id in self.pending_requests:
            request = self.pending_requests[request_id]
            agent_id = request['agent_id']
            
            if agent_id in self.active_agents:
                agent = self.active_agents[agent_id]
                agent.receive_human_feedback(request_id, False, reason)
                
                # 사용자 행동 학습
                self._learn_user_behavior(user_id, request, 'rejected')
    
    def _learn_user_behavior(self, user_id: str, request: Dict, decision: str):
        """사용자 행동 패턴 학습"""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {
                'approval_patterns': [],
                'risk_tolerance': 0.5
            }
        
        pattern = {
            'task_type': request['task']['type'],
            'risk_level': request['risk_level'],
            'decision': decision,
            'timestamp': time.time()
        }
        
        self.user_preferences[user_id]['approval_patterns'].append(pattern)
        
        # 위험 허용도 조정
        if decision == 'approved':
            risk_scores = {'low': 0.1, 'medium': 0.4, 'high': 0.7, 'critical': 0.9}
            approved_risk = risk_scores[request['risk_level']]
            current_tolerance = self.user_preferences[user_id]['risk_tolerance']
            
            # 점진적으로 위험 허용도 조정
            new_tolerance = (current_tolerance * 0.9) + (approved_risk * 0.1)
            self.user_preferences[user_id]['risk_tolerance'] = new_tolerance