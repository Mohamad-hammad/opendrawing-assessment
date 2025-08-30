import grpc
from concurrent import futures
import sys
import os
from datetime import datetime
import uuid

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'proto'))

import task_pb2
import task_pb2_grpc

from model import Task
from priority_queue import TaskQueue

# Retry configuration
MAX_RETRIES = 3
FAILURE_SIMULATION_RATE = 0.3  # 30% failure rate for testing

class TaskDistributorService(task_pb2_grpc.TaskDistributorServicer):
    def __init__(self):
        self.task_queue = TaskQueue()
        self.completed_tasks = {}  # Store completed task info
        self.active_tasks = {}  # Store tasks being processed (task_id -> Task object)
        print("server==> TaskDistributorService initialized with priority queue and retry mechanism")
    
    def Ping(self, request, context):
        response_message = f"Pong! Received: {request.message}"
        timestamp = datetime.now().isoformat()
        
        print(f"server ==> Received ping: {request.message}")
        
        return task_pb2.PingResponse(
            message=response_message,
            timestamp=timestamp
        )
    
    def SubmitTask(self, request, context):
        try:
            # Validate user tier
            if request.user_tier not in ["paid", "free"]:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details("user_tier must be 'paid' or 'free'")
                return task_pb2.SubmitTaskResponse()
            
            # Create task using your existing Task model
            task = Task(
                id=str(uuid.uuid4()),
                user_tier=request.user_tier,
                est_processing_time=request.est_processing_time,
                data=request.data,
                enqueued_at=datetime.now()
            )
            
            # Add to queue
            queue_position = self.task_queue.add_task(task)
            
            print(f"server ==> Task submitted: {task} at position {queue_position}")
            
            return task_pb2.SubmitTaskResponse(
                task_id=task.id,
                status="enqueued",
                queue_position=queue_position
            )
            
        except Exception as e:
            print(f"[SERVER] Error submitting task: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            return task_pb2.SubmitTaskResponse()
    def FetchTask(self, request, context):
      
        try:
            agent_id = request.agent_id
            
            # Get highest priority task from queue
            task = self.task_queue.get_next_task()
            
            if task is None:
                # No tasks available
                print(f"server ==> Agent {agent_id} requested task - queue empty")
                return task_pb2.FetchTaskResponse(has_task=False)
            
            # Mark task as assigned to this agent
            task.assigned_agent = agent_id
            
            # Store task for potential retry
            self.active_tasks[task.id] = task
            
            print(f"server ==> Agent {agent_id} fetched task: {task}")
            
            return task_pb2.FetchTaskResponse(
                has_task=True,
                task_id=task.id,
                user_tier=task.user_tier,
                est_processing_time=task.est_processing_time,
                data=task.data
            )
            
        except Exception as e:
            print(f"server ==> Error fetching task: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            return task_pb2.FetchTaskResponse(has_task=False)

    def CompleteTask(self, request, context):
        try:
            task_id = request.task_id
            agent_id = request.agent_id
            success = request.success
            result = request.result
            
            # Get the original task from active tasks
            original_task = self.active_tasks.get(task_id)
            
            if success:
                # Task completed successfully
                print(f"server ==> Task {task_id[:8]} completed successfully by {agent_id}")
                print(f"server ==> Result: {result}")
                
                # Store in completed tasks
                self.completed_tasks[task_id] = {
                    'agent_id': agent_id,
                    'success': True,
                    'result': result,
                    'completed_at': datetime.now(),
                    'retry_count': original_task.retry_count if original_task else 0
                }
                
                # Clean up active tasks
                if task_id in self.active_tasks:
                    del self.active_tasks[task_id]
                
                message = "Task completed successfully"
                
            else:
                # Task failed - check if we should retry
                print(f"server ==> Task {task_id[:8]} failed by {agent_id}")
                print(f"server ==> Error: {result}")
                
                if original_task and original_task.retry_count < MAX_RETRIES:
                    # Retry the task
                    message = self._retry_task(original_task, result)
                else:
                    # Max retries reached or task not found
                    message = self._handle_final_failure(task_id, result, original_task)
                    
                    # Clean up active tasks
                    if task_id in self.active_tasks:
                        del self.active_tasks[task_id]
            
            return task_pb2.CompleteTaskResponse(
                acknowledged=True,
                message=message
            )
            
        except Exception as e:
            print(f"server ==> Error handling completion: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return task_pb2.CompleteTaskResponse(
                acknowledged=False,
                message=f"Error: {str(e)}"
            )
    
    def _retry_task(self, task, error_message):
        """Retry a failed task by incrementing retry count and re-adding to queue"""
        task.increment_retry()
        
        print(f"server ==> Retrying task {task.id[:8]} (attempt {task.retry_count + 1}/{MAX_RETRIES + 1})")
        print(f"server ==> Previous error: {error_message}")
        
        # Re-add to queue for immediate retry (lower priority due to is_retry() = True)
        queue_position = self.task_queue.add_task(task)
        
        return f"Task failed, retrying (attempt {task.retry_count + 1}/{MAX_RETRIES + 1})"
    
    def _handle_final_failure(self, task_id, error_message, original_task):
        """Handle a task that has exceeded maximum retry attempts"""
        retry_count = original_task.retry_count if original_task else 0
        
        print(f"server ==> Task {task_id[:8]} PERMANENTLY FAILED after {retry_count + 1} attempts")
        print(f"server ==> Final error: {error_message}")
        
        # Store in completed tasks as permanently failed
        self.completed_tasks[task_id] = {
            'agent_id': 'N/A',
            'success': False,
            'result': f"PERMANENT FAILURE after {retry_count + 1} attempts: {error_message}",
            'completed_at': datetime.now(),
            'retry_count': retry_count
        }
        
        return f"Task permanently failed after {retry_count + 1} attempts"


def serve():
    print("server ==> Starting Task Distributor server...")
    
    # Create gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # Add our service
    task_pb2_grpc.add_TaskDistributorServicer_to_server(
        TaskDistributorService(), server
    )
    
    # Listen on port 50051
    server.add_insecure_port('[::]:50051')
    
    # Start server
    server.start()
    print("server ==> Task Distributor server started on port 50051")
    print("server ==> Ready to accept task submissions and fetch requests!")
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\nserver ==> Shutting down...")
        server.stop(0)

if __name__ == '__main__':
    serve()