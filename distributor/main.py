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

class TaskDistributorService(task_pb2_grpc.TaskDistributorServicer):
    def __init__(self):
        self.task_queue = TaskQueue()
        print("server==> TaskDistributorService initialized with priority queue")
    
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
    print("server ==> Ready to accept task submissions!")
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\nserver ==> Shutting down...")
        server.stop(0)

if __name__ == '__main__':
    serve()