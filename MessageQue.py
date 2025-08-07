import asyncio
from queue import Queue, PriorityQueue
from enum import Enum
from dataclasses import dataclass
from typing import Optional
import uuid
import os

class MessageType(Enum):
    REQUEST = "request"
    RESPONSE = "response"
    BROADCAST = "broadcast"
    TASK_ASSIGNMENT = "task_assignment"

@dataclass
class Message:
    id: str
    sender: str
    receiver: str  # "ALL" for broadcast
    message_type: MessageType
    content: str
    priority: int = 1
    reply_to: Optional[str] = None
    
    def __lt__(self, other):
        return self.priority > other.priority  # Higher priority comes first

class MessageBroker:
    """Message broker for asynchronous communication between agents."""
    def __init__(self):
        self.agent_queues = {}  # agent_id -> PriorityQueue
        self.message_history = {}
        
    def register_agent(self, agent_id: str):
        """Registers a new agent."""
        self.agent_queues[agent_id] = PriorityQueue()
        self.message_history[agent_id] = []

    def send_message(self, message: Message):
        """Sends a message."""
        message.id = str(uuid.uuid4())
        if message.receiver == "ALL":
            # Broadcast
            for agent_id in self.agent_queues:
                if agent_id != message.sender:
                    self.agent_queues[agent_id].put(message)
        else:
            # Send to a specific agent
            if message.receiver in self.agent_queues:
                self.agent_queues[message.receiver].put(message)

        # Save message history
        if message.sender in self.message_history:
            self.message_history[message.sender].append(message)

    def receive_message(self, agent_id: str, timeout: int = 1) -> Optional[Message]:
        """Receives a message (non-blocking)."""
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
        """Starts listening for messages."""
        self.running = True
        while self.running:
            message = self.broker.receive_message(self.agent_id)
            if message:
                await self.handle_message(message)
            await asyncio.sleep(0.1)  # Adjust CPU usage

    async def handle_message(self, message: Message):
        """Handles a received message."""
        print(f"[{self.agent_id}] Received {message.message_type.value} from {message.sender}: {message.content}")
        if message.message_type == MessageType.REQUEST:
            # Generate a response to the request
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
            # Handle task assignment
            await self.execute_task(message.content)

    async def process_request(self, request: str) -> str:
        """Processes a request using the LLM."""
        prompt = f"""
        You are agent {self.agent_id}. 
        You received this request: {request}
        
        Please provide a helpful response:
        """
        if hasattr(self.llm, 'invoke'):
             return self.llm.invoke(prompt)
        return self.llm(prompt)

    async def execute_task(self, task: str):
        """Executes an assigned task."""
        result = await self.process_request(f"Execute this task: {task}")
        
        # Broadcast task completion
        completion_message = Message(
            id="",
            sender=self.agent_id,
            receiver="ALL",
            message_type=MessageType.BROADCAST,
            content=f"Task completed: {task}. Result: {result}"
        )
        self.broker.send_message(completion_message)

    def send_request(self, target_agent: str, request: str, priority: int = 1):
        """Sends a request to another agent."""
        message = Message(
            id="",
            sender=self.agent_id,
            receiver=target_agent,
            message_type=MessageType.REQUEST,
            content=request,
            priority=priority
        )
        self.broker.send_message(message)

# Example Usage
if __name__ == "__main__":
    # Mock LLM for demonstration without API key
    class MockLLM:
        def __call__(self, prompt: str) -> str:
            return f"Mock response to: {prompt.strip()}"
        def invoke(self, prompt: str) -> str:
            return self.__call__(prompt)

    async def demo_message_queue():
        broker = MessageBroker()

        # Use MockLLM for the demo
        llm = MockLLM()
        print("--- Running Message Queue Demo with Mock LLM ---")

        # Uncomment the following lines to use OpenAI API
        # if "OPENAI_API_KEY" not in os.environ:
        #     print("Please set the OPENAI_API_KEY environment variable to run with OpenAI.")
        #     return
        # from langchain.llms import OpenAI
        # llm = OpenAI(temperature=0.7)
        # print("--- Running Message Queue Demo with OpenAI LLM ---")

        # Create agents
        manager = MessageQueueAgent("manager", broker, llm)
        worker1 = MessageQueueAgent("worker1", broker, llm)
        worker2 = MessageQueueAgent("worker2", broker, llm)

        # Start listening in the background
        tasks = [
            asyncio.create_task(manager.start_listening()),
            asyncio.create_task(worker1.start_listening()),
            asyncio.create_task(worker2.start_listening())
        ]

        # Simulate task assignment
        await asyncio.sleep(1)  # Wait for the system to initialize

        # Manager assigns tasks to workers
        print("\n--- Assigning Tasks ---")
        manager.send_request("worker1", "Analyze sales data for Q1", priority=2)
        manager.send_request("worker2", "Generate monthly report", priority=1)

        # Workers collaborate
        print("\n--- Worker Collaboration ---")
        worker1.send_request("worker2", "Can you provide customer feedback data?")

        await asyncio.sleep(2)  # Allow time for tasks to be processed

        # Clean up
        print("\n--- Shutting down ---")
        for task in tasks:
            task.cancel()

        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except asyncio.CancelledError:
            print("Tasks cancelled successfully.")

    asyncio.run(demo_message_queue())