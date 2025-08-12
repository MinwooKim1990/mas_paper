# τ-Bench: 실시간 고객 상호작용 시뮬레이션
import asyncio
import random
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class TaskType(Enum):
    BOOKING = "booking"
    SEARCH = "search"
    SUPPORT = "support"
    PAYMENT = "payment"

@dataclass
class CustomerProfile:
    """고객 프로필 정의"""
    id: str
    preferences: Dict[str, Any]
    patience_level: float  # 0-1
    tech_savviness: float  # 0-1
    task_history: List[str]
    
class Customer:
    """동적 고객 시뮬레이션"""
    
    def __init__(self, profile: CustomerProfile):
        self.profile = profile
        self.current_task = None
        self.satisfaction = 0.5
        self.dialogue_history = []
        self.task_completed = False
        
    async def generate_request(self, context: Dict) -> str:
        """상황에 맞는 고객 요청 생성"""
        if not self.current_task:
            # 새 작업 시작
            self.current_task = random.choice(list(TaskType))
            templates = {
                TaskType.BOOKING: [
                    "I need to book a flight to {city}",
                    "Can you help me reserve a hotel in {city}?",
                    "I want to schedule an appointment"
                ],
                TaskType.SEARCH: [
                    "I'm looking for {item}",
                    "Can you find information about {topic}?",
                    "Show me options for {service}"
                ],
                TaskType.SUPPORT: [
                    "I'm having trouble with {issue}",
                    "My {service} isn't working",
                    "I need help with {problem}"
                ],
                TaskType.PAYMENT: [
                    "I want to pay my bill",
                    "How can I update my payment method?",
                    "I have a question about my invoice"
                ]
            }
            
            template = random.choice(templates[self.current_task])
            # 동적 파라미터 채우기
            request = self._fill_template(template, context)
        else:
            # 대화 계속
            request = self._generate_followup(context)
            
        self.dialogue_history.append(("customer", request))
        return request

    def _fill_template(self, template: str, context: Dict) -> str:
        """템플릿에 동적 값 채우기"""
        replacements = {
            "city": random.choice(["New York", "London", "Tokyo", "Paris"]),
            "item": random.choice(["laptop", "phone", "book", "shoes"]),
            "topic": random.choice(["AI", "climate", "health", "finance"]),
            "service": random.choice(["internet", "subscription", "delivery"]),
            "issue": random.choice(["login", "payment", "order", "account"]),
            "problem": random.choice(["refund", "cancellation", "update"])
        }
        
        for key, value in replacements.items():
            template = template.replace(f"{{{key}}}", value)
        return template
    
    def _generate_followup(self, context: Dict) -> str:
        """이전 대화 기반 후속 질문 생성"""
        last_response = context.get('last_response', '')
        
        if "more information" in last_response.lower():
            followups = [
                "Here's my order number: ORD-" + str(random.randint(10000, 99999)),
                "My email is customer@example.com",
                "I tried that already but it didn't work"
            ]
        elif "confirm" in last_response.lower():
            followups = [
                "Yes, that's correct",
                "No, actually I meant something else",
                "Can you show me other options?"
            ]
        else:
            followups = [
                "How long will this take?",
                "Is there another way to do this?",
                "I don't understand, can you explain?"
            ]
            
        return random.choice(followups)
    
    def evaluate_response(self, response: str, response_time: float) -> float:
        """에이전트 응답 평가"""
        score = 0.5  # 기본 점수
        
        # 응답 시간 평가
        if response_time < 1.0:
            score += 0.2
        elif response_time > 5.0:
            score -= 0.2 * self.profile.patience_level
        
        # 응답 품질 평가
        if len(response) > 20 and len(response) < 200:
            score += 0.1
        if any(word in response.lower() for word in ['sorry', 'apologize', 'understand']):
            score += 0.1
        if '?' in response:  # 명확성을 위한 질문
            score += 0.05
            
        # 작업 완료 확인
        completion_words = ['completed', 'done', 'confirmed', 'processed']
        if any(word in response.lower() for word in completion_words):
            self.task_completed = True
            score += 0.2
            
        self.satisfaction = max(0, min(1, self.satisfaction * 0.7 + score * 0.3))
        return score

class ToolExecutor:
    """도구 실행 시뮬레이터"""
    
    def __init__(self):
        self.tools = {
            'search_flights': self._search_flights,
            'book_reservation': self._book_reservation,
            'check_status': self._check_status,
            'process_payment': self._process_payment,
            'get_user_info': self._get_user_info
        }
        self.execution_history = []
        
    async def execute_tool(self, tool_name: str, params: Dict) -> Dict:
        """도구 실행 및 결과 반환"""
        start_time = time.time()
        
        if tool_name not in self.tools:
            result = {"error": f"Tool {tool_name} not found"}
        else:
            try:
                result = await self.tools[tool_name](params)
            except Exception as e:
                result = {"error": str(e)}
                
        execution_time = time.time() - start_time
        
        self.execution_history.append({
            'tool': tool_name,
            'params': params,
            'result': result,
            'execution_time': execution_time
        })
        
        return result
    
    async def _search_flights(self, params: Dict) -> Dict:
        """항공편 검색 시뮬레이션"""
        await asyncio.sleep(random.uniform(0.5, 1.5))  # API 호출 시뮬레이션
        
        return {
            'flights': [
                {'flight_no': f'FL{random.randint(100,999)}', 
                 'price': random.randint(200, 1000),
                 'departure': params.get('from', 'NYC'),
                 'arrival': params.get('to', 'LAX')}
                for _ in range(3)
            ]
        }
    
    async def _book_reservation(self, params: Dict) -> Dict:
        """예약 처리 시뮬레이션"""
        await asyncio.sleep(random.uniform(1.0, 2.0))
        
        if random.random() > 0.9:  # 10% 실패율
            return {'error': 'Booking failed - no availability'}
            
        return {
            'reservation_id': f'RES-{random.randint(100000, 999999)}',
            'status': 'confirmed'
        }

class SystemUnderTest:
    """테스트 대상 시스템 추상화"""
    
    def __init__(self, system_name: str):
        self.name = system_name
        self.metrics = {
            'response_times': [],
            'task_completion_rate': 0,
            'customer_satisfaction': [],
            'tool_usage': {},
            'error_rate': 0
        }
        
    async def process_request(self, request: str, context: Dict) -> str:
        """요청 처리 (실제 시스템 호출)"""
        # 실제 구현에서는 여기서 LLM/에이전트 시스템 호출
        # 예시로 간단한 응답 생성
        start_time = time.time()
        
        # 시뮬레이션된 처리
        await asyncio.sleep(random.uniform(0.5, 2.0))
        
        responses = [
            "I'll help you with that. Let me search for available options.",
            "I understand your request. Can you provide more information?",
            "I've processed your request. Here are the results...",
            "Your request has been completed successfully."
        ]
        
        response = random.choice(responses)
        response_time = time.time() - start_time
        
        self.metrics['response_times'].append(response_time)
        
        return response

class TauBenchEvaluator:
    """τ-Bench 평가 실행기"""
    
    def __init__(self, system: SystemUnderTest):
        self.system = system
        self.tool_executor = ToolExecutor()
        self.results = {
            'conversations': [],
            'aggregate_metrics': {}
        }
        
    async def run_evaluation(self, num_customers: int = 100, 
                           max_turns: int = 10) -> Dict:
        """평가 실행"""
        tasks = []
        
        for i in range(num_customers):
            profile = CustomerProfile(
                id=f"customer_{i}",
                preferences={'language': 'en', 'style': 'formal'},
                patience_level=random.uniform(0.3, 1.0),
                tech_savviness=random.uniform(0.2, 1.0),
                task_history=[]
            )
            
            task = self._evaluate_conversation(profile, max_turns)
            tasks.append(task)
            
        conversations = await asyncio.gather(*tasks)
        
        # 집계 메트릭 계산
        self._calculate_aggregate_metrics(conversations)
        
        return self.results