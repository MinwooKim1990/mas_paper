import asyncio
from queue import Queue, PriorityQueue
from enum import Enum
from dataclasses import dataclass
from typing import Optional
import uuid

class MessageType(Enum):
    REQUEST = "request"
    RESPONSE = "response"
    BROADCAST = "broadcast"
    TASK_ASSIGNMENT = "task_assignment"
@dataclass
class Message:
    id: str
    sender: str
    receiver: str  # "ALL"이면 브로드캐스트
    message_type: MessageType
    content: str
    priority: int = 1
    reply_to: Optional[str] = None
    
    def __lt__(self, other):
        return self.priority > other.priority  # 높은 우선순위가 먼저
class MessageBroker:
    """메시지 브로커 - 에이전트 간 비동기 메시지 전달"""
    def __init__(self):
        self.agent_queues = {}  # agent_id -> PriorityQueue
        self.message_history = {}
        
    def register_agent(self, agent_id: str):
        """새 에이전트 등록"""
        self.agent_queues[agent_id] = PriorityQueue()
        self.message_history[agent_id] = []
    def send_message(self, message: Message):
        """메시지 전송"""
        message.id = str(uuid.uuid4())
        if message.receiver == "ALL":
            # 브로드캐스트
            for agent_id in self.agent_queues:
                if agent_id != message.sender:
                    self.agent_queues[agent_id].put(message)
        else:
            # 특정 에이전트에게 전송
            if message.receiver in self.agent_queues:
                self.agent_queues[message.receiver].put(message)
        # 메시지 히스토리 저장
        if message.sender in self.message_history:
            self.message_history[message.sender].append(message)
    def receive_message(self, agent_id: str, timeout: int = 1) -> Optional[Message]:
        """메시지 수신 (논블로킹)"""
        try:
            if not self.agent_queues[agent_id].empty():
                return self.agent_queues[agent_id].get_nowait()
        except:
            pass
        return None
    
class MessageQueueAgent:
    def __init__(self, agent_id: str, broker: MessageBroker, llm):
        self.agent_id = agent_id
        self.broker = broker
        self.llm = llm
        self.running = False
        broker.register_agent(agent_id)
    async def start_listening(self):
        """메시지 수신 대기 시작"""
        self.running = True
        while self.running:
            message = self.broker.receive_message(self.agent_id)
            if message:
                await self.handle_message(message)
            await asyncio.sleep(0.1)  # CPU 사용량 조절
    async def handle_message(self, message: Message):
        """수신된 메시지 처리"""
        print(f"[{self.agent_id}] Received {message.message_type.value} from {message.sender}: {message.content}")
        if message.message_type == MessageType.REQUEST:
            # 요청에 대한 응답 생성
            response_content = await self.process_request(message.content)
            
            response = Message(
                id="",
                sender=self.agent_id,
                receiver=message.sender,
                message_type=MessageType.RESPONSE,
                content=response_content,
                reply_to=message.id
            )
            self.broker.send_message(response)
        elif message.message_type == MessageType.TASK_ASSIGNMENT:
            # 작업 할당 처리
            await self.execute_task(message.content)
    async def process_request(self, request: str) -> str:
        """LLM을 사용해 요청 처리"""
        prompt = f"""
        You are agent {self.agent_id}. 
        You received this request: {request}
        
        Please provide a helpful response:
        """
        return self.llm(prompt)
    async def execute_task(self, task: str):
        """할당된 작업 실행"""
        result = await self.process_request(f"Execute this task: {task}")
        
        # 작업 완료 브로드캐스트
        completion_message = Message(
            id="",
            sender=self.agent_id,
            receiver="ALL",
            message_type=MessageType.BROADCAST,
            content=f"Task completed: {task}. Result: {result}"
        )
        self.broker.send_message(completion_message)
    def send_request(self, target_agent: str, request: str, priority: int = 1):
        """다른 에이전트에게 요청 전송"""
        message = Message(
            id="",
            sender=self.agent_id,
            receiver=target_agent,
            message_type=MessageType.REQUEST,
            content=request,
            priority=priority
        )
        self.broker.send_message(message)

# 사용 예시
async def demo_message_queue():
    broker = MessageBroker()
    llm = OpenAI(temperature=0.7)   
    # 에이전트들 생성
    manager = MessageQueueAgent("manager", broker, llm)
    worker1 = MessageQueueAgent("worker1", broker, llm)
    worker2 = MessageQueueAgent("worker2", broker, llm)
    # 백그라운드에서 메시지 수신 시작
    tasks = [
        asyncio.create_task(manager.start_listening()),
        asyncio.create_task(worker1.start_listening()),
        asyncio.create_task(worker2.start_listening())
    ]
    # 작업 할당 시뮬레이션
    await asyncio.sleep(1)  # 시스템 초기화 대기
    # 매니저가 작업자들에게 작업 할당
    manager.send_request("worker1", "Analyze sales data for Q1", priority=2)
    manager.send_request("worker2", "Generate monthly report", priority=1)
    # 작업자들 간 협업
    worker1.send_request("worker2", "Can you provide customer feedback data?")
    await asyncio.sleep(5)  # 작업 처리 시간
    # 정리
    for task in tasks:
        task.cancel()