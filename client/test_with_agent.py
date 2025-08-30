import grpc
import sys
import os
import time

# Add proto directory to path  
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'proto'))

import task_pb2
import task_pb2_grpc

def submit_task(user_tier, processing_time, data):
    channel = grpc.insecure_channel('localhost:50051')
    stub = task_pb2_grpc.TaskDistributorStub(channel)
    
    try:
        response = stub.SubmitTask(task_pb2.SubmitTaskRequest(
            user_tier=user_tier,
            est_processing_time=processing_time,
            data=data
        ))
        print(f"[CLIENT] 📤 Submitted {user_tier}-{processing_time}s: '{data}'")
        return response.task_id
    except Exception as e:
        print(f"[CLIENT] ❌ Error: {str(e)}")
        return None
    finally:
        channel.close()

def demo_agent_workflow():
    """Demo the complete workflow with agents"""
    print("=" * 70)
    print("AGENT WORKFLOW DEMO")
    print("Make sure you have agents running!")
    print("=" * 70)
    print()
    
    # Submit a variety of tasks to test priority and agent processing
    tasks = [
        ("paid", 1, "Quick paid task - VIP customer payment"),
        ("free", 3, "Free user report generation"), 
        ("paid", 2, "Paid user data export"),
        ("free", 1, "Quick free task - email validation"),
        ("paid", 4, "Complex paid analytics job"),
        ("free", 2, "Free user backup"),
    ]
    
    print("Submitting tasks for agents to process...")
    print("Watch the agent terminals to see them get processed!")
    print()
    
    for i, (tier, proc_time, desc) in enumerate(tasks, 1):
        print(f"{i}. Submitting {tier}-{proc_time}s task...")
        submit_task(tier, proc_time, desc)
        time.sleep(0.5)  # Small delay between submissions
    
    print()
    print("All tasks submitted!")
    print()
    print("Expected processing order by agents:")
    print("1. paid-1s (Quick paid task)")
    print("2. paid-2s (Paid user data export)")  
    print("3. paid-4s (Complex paid analytics)")
    print("4. free-1s (Quick free task)")
    print("5. free-2s (Free user backup)")
    print("6. free-3s (Free user report)")
    print()
    print("Check your agent terminals to verify this order!")

def submit_continuous_tasks():
    """Keep submitting tasks for testing"""
    print("=" * 50)
    print("CONTINUOUS TASK SUBMISSION")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    task_counter = 1
    
    try:
        while True:
            # Randomly choose task type
            import random
            tier = random.choice(["paid", "free"])
            time_needed = random.randint(1, 5)
            
            task_data = f"Task #{task_counter} - {tier} user operation"
            
            submit_task(tier, time_needed, task_data)
            task_counter += 1
            
            # Wait between submissions
            time.sleep(3)
            
    except KeyboardInterrupt:
        print("\n[CLIENT] Stopped submitting tasks")

def main():
    """Main menu for testing agents"""
    print("Agent Testing Client")
    print("1. Submit demo batch (6 tasks)")
    print("2. Submit continuous tasks")
    
    choice = input("Choose option (1 or 2): ").strip()
    
    if choice == "1":
        demo_agent_workflow()
    elif choice == "2":
        submit_continuous_tasks()
    else:
        print("Invalid choice")

if __name__ == '__main__':
    main()