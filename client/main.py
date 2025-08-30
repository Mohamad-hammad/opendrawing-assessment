import grpc
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'proto'))

import task_pb2
import task_pb2_grpc

def test_ping():
    print("Connecting to server...")
    
    channel = grpc.insecure_channel('localhost:50051')
    stub = task_pb2_grpc.TaskDistributorStub(channel)
    
    try:
        print("client ==> Sending ping...")
        response = stub.Ping(task_pb2.PingRequest(message="Hello from client!"))
        
        print(f"client ==> Received response:")
        print(f"  Message: {response.message}")
        print(f"  Timestamp: {response.timestamp}")
        print("client ==> Ping test successful!")
        
    except grpc.RpcError as e:
        print(f"client ==> gRPC Error: {e.code()} - {e.details()}")
    except Exception as e:
        print(f"client ==> Error: {str(e)}")
    finally:
        channel.close()

if __name__ == '__main__':
    test_ping()