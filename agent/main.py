import grpc
import time
import sys
import os

# Add proto directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'proto'))

import task_pb2
import task_pb2_grpc

class TaskAgent:
    def __init__(self, agent_id):
        self.agent_id = agent_id
        self.channel = grpc.insecure_channel('localhost:50051')
        self.stub = task_pb2_grpc.TaskDistributorStub(self.channel)
        print(f"[AGENT-{agent_id}] Connected to distributor")
    
    def start(self):
        """Start polling for tasks every 2 seconds"""
        print(f"[AGENT-{self.agent_id}] Starting to poll for tasks...")
        
        try:
            while True:
                task = self._get_task()
                
                if task:
                    self._process_task(task)
                else:
                    print(f"[AGENT-{self.agent_id}] No tasks available")
                
                time.sleep(2)  # Poll every 2 seconds
                
        except KeyboardInterrupt:
            print(f"\n[AGENT-{self.agent_id}] Stopping...")
            self.channel.close()
    
    def _get_task(self):
        """Get next task from distributor"""
        try:
            response = self.stub.FetchTask(
                task_pb2.FetchTaskRequest(agent_id=self.agent_id)
            )
            
            if response.has_task:
                print(f"[AGENT-{self.agent_id}] Got task: {response.user_tier}-{response.est_processing_time}s")
                return response
            return None
            
        except Exception as e:
            print(f"[AGENT-{self.agent_id}] Error getting task: {e}")
            return None
    
    def _process_task(self, task):
        print(f"[AGENT-{self.agent_id}] Processing: {task.data}")
        print(f"[AGENT-{self.agent_id}] Working for {task.est_processing_time} seconds...")
        
        # Simulate work
        time.sleep(task.est_processing_time)
        
        print(f"[AGENT-{self.agent_id}] Completed task!")
        print()

def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py <agent_id>")
        print("Example: python main.py agent-a")
        sys.exit(1)
    
    agent_id = sys.argv[1]
    agent = TaskAgent(agent_id)
    agent.start()

if __name__ == '__main__':
    main()