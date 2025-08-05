from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseMemory
from typing import Dict, List, Any
import threading
import json
from datetime import datetime

class SharedBlackboard:
    """공유 블랙보드 시스템 - 여러 에이전트가 정보를 읽고 쓸 수 있는 중앙 저장소"""
    
    def __init__(self):
        self.data = {}
        self.lock = threading.Lock()
        self.subscribers = {}  # 특정 키에 대한 구독자들
        
    def write(self, key: str, value: Any, agent_id: str):
        """에이전트가 블랙보드에 정보 쓰기"""
        with self.lock:
            timestamp = datetime.now().isoformat()
            entry = {
                "value": value,
                "agent_id": agent_id,
                "timestamp": timestamp
            }
            
            if key not in self.data:
                self.data[key] = []
            self.data[key].append(entry)
            
            # 구독자들에게 알림
            if key in self.subscribers:
                for callback in self.subscribers[key]:
                    callback(key, entry)
    
    def read(self, key: str) -> List[Dict]:
        """특정 키의 모든 데이터 읽기"""
        with self.lock:
            return self.data.get(key, [])
    
    def read_latest(self, key: str) -> Dict:
        """특정 키의 최신 데이터 읽기"""
        with self.lock:
            entries = self.data.get(key, [])
            return entries[-1] if entries else None
    
    def subscribe(self, key: str, callback):
        """특정 키에 대한 변경사항 구독"""
        if key not in self.subscribers:
            self.subscribers[key] = []
        self.subscribers[key].append(callback)

# LangChain과 통합된 블랙보드 에이전트
from langchain.agents import Agent
from langchain.llms import OpenAI

class BlackboardAgent:
    def __init__(self, agent_id: str, blackboard: SharedBlackboard, llm):
        self.agent_id = agent_id
        self.blackboard = blackboard
        self.llm = llm
        self.memory = ConversationBufferMemory()
        
    def process_task(self, task: str, context_keys: List[str] = None):
        """작업 처리 - 블랙보드에서 컨텍스트 읽고 결과 쓰기"""
        
        # 블랙보드에서 관련 정보 수집
        context = ""
        if context_keys:
            for key in context_keys:
                data = self.blackboard.read_latest(key)
                if data:
                    context += f"{key}: {data['value']}\n"
        
        # LLM을 사용해 작업 처리
        prompt = f"""
        Task: {task}
        
        Available Context from Blackboard:
        {context}
        
        Please process this task and provide your response:
        """
        
        response = self.llm(prompt)
        
        # 결과를 블랙보드에 기록
        result_key = f"task_result_{self.agent_id}_{datetime.now().timestamp()}"
        self.blackboard.write(result_key, response, self.agent_id)
        
        return response
blackboard = SharedBlackboard()
llm = OpenAI(temperature=0.7)

# 여러 에이전트 생성
agent1 = BlackboardAgent("researcher", blackboard, llm)
agent2 = BlackboardAgent("writer", blackboard, llm)
agent3 = BlackboardAgent("reviewer", blackboard, llm)

# 협업 시나리오
# 1. 연구 에이전트가 정보 수집
research_result = agent1.process_task("Research about AI safety")
blackboard.write("research_data", research_result, "researcher")

# 2. 작가 에이전트가 연구 결과를 바탕으로 글 작성
article = agent2.process_task("Write an article about AI safety", ["research_data"])
blackboard.write("draft_article", article, "writer")

# 3. 리뷰어가 글을 검토
review = agent3.process_task("Review the draft article", ["draft_article"])
blackboard.write("review_feedback", review, "reviewer")