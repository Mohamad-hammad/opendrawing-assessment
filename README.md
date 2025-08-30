# Task Distribution System

A distributed task processing system built with gRPC that manages task assignment between a distributor and multiple agents using a priority queue with retry mechanism.

## System Architecture

```
┌─────────────┐    gRPC     ┌─────────────────┐    gRPC     ┌─────────────┐
│   Client    │ ──────────► │   Distributor   │ ◄────────── │   Agent     │
│             │             │                 │             │             │
│ Submit Task │             │ Priority Queue  │             │ Process Task│
└─────────────┘             │ Retry Logic     │             └─────────────┘
                            └─────────────────┘
```

## Features

### Core Functionality
- **gRPC Communication**: Distributor and agents communicate via gRPC protocol
- **Priority Queue**: Tasks are processed based on priority rules
- **Multiple Agents**: Support for concurrent task processing by multiple agents
- **Task Retry**: Failed tasks are automatically retried up to 3 times

### Priority Rules (in order)
1. **Retry Status**: New tasks before retry attempts
2. **User Tier**: Paid users before free users  
3. **Processing Time**: Shorter tasks before longer tasks
4. **Queue Time**: Older tasks before newer tasks

### Retry Mechanism
- **Max Retries**: 3 attempts per task
- **Immediate Retry**: No delay between retry attempts
- **Lower Priority**: Retry tasks get lower priority than new tasks
- **Failure Simulation**: 30% failure rate for testing

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Generate Protos
```bash
py -m grpc_tools.protoc --proto_path=./proto --python_out=./proto --grpc_python_out=./proto ./proto/task.proto
```

### 3. Start the Distributor
```bash
cd distributor
python main.py
```

### 4. Start Agents (in separate terminals)
```bash
# Agent 1
cd agent
python main.py agent-1

# Agent 2  
cd agent
python main.py agent-2
```

### 4. Run Tests (submits tasks automatically)
```bash
cd client
python test_with_agent.py
```

## Components

### Distributor (`distributor/`)
- **`main.py`**: gRPC server handling task distribution
- **`priority_queue.py`**: Priority queue implementation with task ordering
- **`model.py`**: Task data model with retry support

### Agent (`agent/`)
- **`main.py`**: Worker agent that fetches and processes tasks

### Client (`client/`)
- **`main.py`**: Basic ping test
- **`test_with_agent.py`**: Main testing file - submits tasks and demonstrates workflow

### Protocol (`proto/`)
- **`task.proto`**: gRPC service definitions
- **`task_pb2.py`** & **`task_pb2_grpc.py`**: Generated gRPC code

## gRPC API

### TaskDistributor Service

#### `SubmitTask`
Submit a new task to the queue
```protobuf
rpc SubmitTask(SubmitTaskRequest) returns (SubmitTaskResponse);
```

#### `FetchTask` 
Agent requests next task from queue
```protobuf
rpc FetchTask(FetchTaskRequest) returns (FetchTaskResponse);
```

#### `CompleteTask`
Agent reports task completion (success/failure)
```protobuf
rpc CompleteTask(CompleteTaskRequest) returns (CompleteTaskResponse);
```

#### `Ping`
Health check endpoint
```protobuf
rpc Ping(PingRequest) returns (PingResponse);
```

## Task Model

```python
@dataclass
class Task:
    id: str                          # Unique task identifier
    user_tier: str                   # "paid" or "free"
    est_processing_time: int         # Processing time in seconds
    data: str                        # Task payload
    enqueued_at: datetime           # When task was submitted
    retry_count: int = 0            # Number of retry attempts
    assigned_agent: Optional[str]    # Currently assigned agent
```

## Configuration

### Retry Settings
```python
MAX_RETRIES = 3                     # Maximum retry attempts
FAILURE_RATE = 0.3                  # 30% failure rate for testing
```

### Server Settings
- **Port**: 50051 (default gRPC port)
- **Host**: localhost
- **Polling Interval**: 2 seconds (agent polling)

## Testing

### Main Test
```bash
cd client
python test_with_agent.py
```
- Automatically submits various tasks and demonstrates the complete workflow with priority ordering and retry mechanism.


## Example Usage

### Expected Processing Order
Given these submitted tasks:
1. `free-10s` (long free task)
2. `paid-5s` (medium paid task)  
3. `free-2s` (quick free task)
4. `paid-3s` (quick paid task)

Processing order will be:
1. `paid-3s` (paid + shortest)
2. `paid-5s` (paid + medium)  
3. `free-2s` (free + shortest)
4. `free-10s` (free + longest)
