import heapq
import threading
from functools import total_ordering
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(__file__))
from model import Task

@total_ordering
class PriorityTask:
    def __init__(self, task):
        self.task = task
    
    def __lt__(self, other):
        # Rule 1: Non-retry tasks before retry tasks (retries get lower priority)
        if self.task.is_retry() != other.task.is_retry():
            return not self.task.is_retry()  # Non-retries (False) come before retries (True)
        
        # Rule 2: paid before free
        if self.task.user_tier != other.task.user_tier:
            return self.task.user_tier == "paid" and other.task.user_tier == "free"
        
        # Rule 3: shorter processing time first
        if self.task.est_processing_time != other.task.est_processing_time:
            return self.task.est_processing_time < other.task.est_processing_time
        
        # Rule 4: older tasks first (prevent starvation)
        return self.task.enqueued_at < other.task.enqueued_at
    
    def __eq__(self, other):
        return (self.task.user_tier == other.task.user_tier and 
                self.task.est_processing_time == other.task.est_processing_time and
                self.task.enqueued_at == other.task.enqueued_at)

class TaskQueue:
    def __init__(self):
        self._heap = []
        self._lock = threading.Lock()
        self._tasks = {} 
    
    def add_task(self, task):
        with self._lock:
            heapq.heappush(self._heap, PriorityTask(task))
            self._tasks[task.id] = task
            print(f"Added {task} to queue (size: {len(self._heap)})")
            return len(self._heap)  
    
    def get_next_task(self):
        with self._lock:
            if not self._heap:
                return None
            
            priority_task = heapq.heappop(self._heap)
            task = priority_task.task
            print(f"Popped {task} from queue")
            return task
    
    def size(self):
        return len(self._heap)
    
    def is_empty(self):
        return len(self._heap) == 0






# Test function
def test_priority_ordering():
   
    print("Testing priority queue...")
    
    queue = TaskQueue()
    now = datetime.now()
    
    tasks = [
        Task("1", "free", 10, "long free task", now),
        Task("2", "paid", 5, "medium paid task", now),  
        Task("3", "free", 2, "quick free task", now),   
        Task("4", "paid", 8, "slow paid task", now + timedelta(seconds=1)),  
    ]
    
    for task in [tasks[0], tasks[2], tasks[1], tasks[3]]:
        queue.add_task(task)
    
    print("\nProcessing order (should be: paid-5s, paid-8s, free-2s, free-10s):")
    
    results = []
    while not queue.is_empty():
        task = queue.get_next_task()
        results.append(f"{task.user_tier}-{task.est_processing_time}s")
        print(f"  {task}")
    
    expected = ["paid-5s", "paid-8s", "free-2s", "free-10s"]
    if results == expected:
        print("===> Priority ordering works correctly!")
    else:
        print(f"===> Wrong order. Expected: {expected}, Got: {results}")

if __name__ == "__main__":
    test_priority_ordering()