from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseMemory
from typing import Dict, List, Any
import threading
import json
from datetime import datetime
import os

class SharedBlackboard:
    """A shared blackboard system - a central repository where multiple agents can read and write information."""
    
    def __init__(self):
        self.data = {}
        self.lock = threading.Lock()
        self.subscribers = {}  # Subscribers for specific keys
        
    def write(self, key: str, value: Any, agent_id: str):
        """An agent writes information to the blackboard."""
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
            
            # Notify subscribers
            if key in self.subscribers:
                for callback in self.subscribers[key]:
                    callback(key, entry)
    
    def read(self, key: str) -> List[Dict]:
        """Reads all data for a specific key."""
        with self.lock:
            return self.data.get(key, [])
    
    def read_latest(self, key: str) -> Dict:
        """Reads the latest data for a specific key."""
        with self.lock:
            entries = self.data.get(key, [])
            return entries[-1] if entries else None
    
    def subscribe(self, key: str, callback):
        """Subscribes to changes for a specific key."""
        if key not in self.subscribers:
            self.subscribers[key] = []
        self.subscribers[key].append(callback)

# Blackboard agent integrated with LangChain
from langchain.agents import Agent
from langchain_community.llms import OpenAI

class BlackboardAgent:
    def __init__(self, agent_id: str, blackboard: SharedBlackboard, llm):
        self.agent_id = agent_id
        self.blackboard = blackboard
        self.llm = llm
        self.memory = ConversationBufferMemory()
        
    def process_task(self, task: str, context_keys: List[str] = None):
        """Processes a task - reads context from the blackboard and writes the result."""
        
        # Collect relevant information from the blackboard
        context = ""
        if context_keys:
            for key in context_keys:
                data = self.blackboard.read_latest(key)
                if data:
                    context += f"{key}: {data['value']}\n"
        
        # Process the task using LLM
        prompt = f"""
        Task: {task}
        
        Available Context from Blackboard:
        {context}
        
        Please process this task and provide your response:
        """
        
        response = self.llm(prompt)
        
        # Write the result to the blackboard
        result_key = f"task_result_{self.agent_id}_{datetime.now().timestamp()}"
        self.blackboard.write(result_key, response, self.agent_id)
        
        return response

if __name__ == '__main__':
    # Check for OpenAI API key
    if "OPENAI_API_KEY" not in os.environ:
        print("Please set the OPENAI_API_KEY environment variable to run this demo.")
    else:
        blackboard = SharedBlackboard()
        llm = OpenAI(temperature=0.7)

        # Create multiple agents
        agent1 = BlackboardAgent("researcher", blackboard, llm)
        agent2 = BlackboardAgent("writer", blackboard, llm)
        agent3 = BlackboardAgent("reviewer", blackboard, llm)

        # Collaboration scenario
        # 1. Research agent collects information
        print("Researcher is researching AI safety...")
        research_result = agent1.process_task("Research about AI safety")
        blackboard.write("research_data", research_result, "researcher")
        print("Researcher has finished.")

        # 2. Writer agent writes an article based on the research results
        print("\nWriter is writing an article...")
        article = agent2.process_task("Write an article about AI safety", ["research_data"])
        blackboard.write("draft_article", article, "writer")
        print("Writer has finished.")

        # 3. Reviewer reviews the article
        print("\nReviewer is reviewing the article...")
        review = agent3.process_task("Review the draft article", ["draft_article"])
        blackboard.write("review_feedback", review, "reviewer")
        print("Reviewer has finished.")

        print("\n--- Final Results ---")
        print(f"Research Data: {blackboard.read_latest('research_data')['value']}")
        print(f"Draft Article: {blackboard.read_latest('draft_article')['value']}")
        print(f"Review Feedback: {blackboard.read_latest('review_feedback')['value']}")