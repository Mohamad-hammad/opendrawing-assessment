import grpc
from concurrent import futures
import sys
import os
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'proto'))

import task_pb2
import task_pb2_grpc

class TaskDistributorService(task_pb2_grpc.TaskDistributorServicer):
    
    def Ping(self, request, context):
        response_message = f"Pong! Received: {request.message}"
        timestamp = datetime.now().isoformat()
        
        print(f"server ==> Received ping: {request.message}")
        print(f"server ==> Sending pong: {response_message}")
        
        return task_pb2.PingResponse(
            message=response_message,
            timestamp=timestamp
        )

def serve():
    print("server ==> Starting ping server...")
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    task_pb2_grpc.add_TaskDistributorServicer_to_server(
        TaskDistributorService(), server
    )
    
    server.add_insecure_port('[::]:50051')
    
    server.start()
    print("server ==> Ping server started on port 50051")
    print("server ==> Waiting for ping requests..")
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\nserver ==> Shutting down...")
        server.stop(0)

if __name__ == '__main__':
    serve()