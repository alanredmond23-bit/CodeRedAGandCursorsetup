"""
Inter-Agent Communication Layer
Redis-based message queue and state management for multi-agent orchestration
Billionaire-speed execution with zero tolerance for latency
"""

import redis
import json
import time
import asyncio
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from concurrent.futures import ThreadPoolExecutor
import traceback

# Configure logging - McKinsey grade, no fluff
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('AGENT_COMM')

# --- CONFIGURATION ---
REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'db': 0,
    'decode_responses': True,
    'socket_connect_timeout': 5,
    'socket_timeout': 5,
    'connection_pool_kwargs': {
        'max_connections': 50,
        'retry_on_timeout': True
    }
}

# Time limits - NO EXCEPTIONS
TIME_LIMITS = {
    '1min': 60,
    '5min': 300,
    '10min': 600,
    '30min': 1800,
    '1hour': 3600,
    '2hour_warning': 7200  # "Could fuck your day Alan"
}

# --- ENUMS ---
class AgentType(Enum):
    ORCHESTRATOR = "orchestrator"
    PROJECT_MANAGER = "project_manager"
    FRONTEND = "frontend"
    BACKEND = "backend"
    DATABASE = "database"
    DEPLOYMENT = "deployment"
    QUALITY = "quality"
    FINALIZER = "finalizer"

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    ERROR = "error"
    ABORTED = "aborted"

class ErrorLevel(Enum):
    WARNING = "warning"
    BLOCKING = "blocking"
    CRITICAL = "critical"

# --- DATA MODELS ---
@dataclass
class AgentMessage:
    """Standard message format for inter-agent communication"""
    agent_id: str
    agent_type: AgentType
    task_id: str
    project_id: str
    status: TaskStatus
    completion: int  # 0-100
    time_elapsed: int  # seconds
    time_estimate: int  # seconds
    dependencies: List[str]
    errors: List[Dict[str, Any]]
    output: Dict[str, Any]
    next_agent: Optional[str]
    timestamp: str
    
    def to_json(self) -> str:
        data = asdict(self)
        data['agent_type'] = self.agent_type.value
        data['status'] = self.status.value
        return json.dumps(data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'AgentMessage':
        data = json.loads(json_str)
        data['agent_type'] = AgentType(data['agent_type'])
        data['status'] = TaskStatus(data['status'])
        return cls(**data)

@dataclass
class TaskCheckpoint:
    """Checkpoint for task recovery and rollback"""
    task_id: str
    agent_id: str
    state: Dict[str, Any]
    timestamp: str
    completion: int
    
    def to_json(self) -> str:
        return json.dumps(asdict(self))
    
    @classmethod
    def from_json(cls, json_str: str) -> 'TaskCheckpoint':
        return cls(**json.loads(json_str))

# --- CORE COMMUNICATION LAYER ---
class InterAgentCommunicator:
    """
    High-performance inter-agent communication system
    Zero latency tolerance, billionaire-speed execution
    """
    
    def __init__(self, redis_config: Dict = None):
        self.config = redis_config or REDIS_CONFIG
        self.redis_client = redis.Redis(**self.config)
        self.pubsub = self.redis_client.pubsub()
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.callbacks: Dict[str, List[Callable]] = {}
        self._running = False
        
        # Test connection
        try:
            self.redis_client.ping()
            logger.info("✅ Redis connection established")
        except redis.ConnectionError:
            logger.error("❌ Redis connection failed - starting in local mode")
            raise
    
    # --- MESSAGE QUEUE OPERATIONS ---
    
    def send_message(self, message: AgentMessage) -> bool:
        """
        Send message to agent queue
        Returns success status
        """
        try:
            # Add to queue
            queue_key = f"queue:{message.next_agent}" if message.next_agent else "queue:orchestrator"
            self.redis_client.lpush(queue_key, message.to_json())
            
            # Publish notification
            channel = f"channel:{message.next_agent}" if message.next_agent else "channel:broadcast"
            self.redis_client.publish(channel, message.to_json())
            
            # Update state
            self._update_task_state(message)
            
            # Check time limits
            self._check_time_limits(message)
            
            logger.info(f"📤 Message sent: {message.agent_id} → {message.next_agent or 'broadcast'}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Message send failed: {str(e)}")
            return False
    
    def receive_message(self, agent_id: str, timeout: int = 1) -> Optional[AgentMessage]:
        """
        Receive message from agent queue (blocking with timeout)
        """
        try:
            queue_key = f"queue:{agent_id}"
            result = self.redis_client.brpop(queue_key, timeout=timeout)
            
            if result:
                _, message_json = result
                message = AgentMessage.from_json(message_json)
                logger.info(f"📥 Message received by {agent_id}")
                return message
            return None
            
        except Exception as e:
            logger.error(f"❌ Message receive failed: {str(e)}")
            return None
    
    def broadcast(self, message: Dict[str, Any]) -> bool:
        """
        Broadcast message to all agents
        """
        try:
            self.redis_client.publish("channel:broadcast", json.dumps(message))
            logger.info("📢 Broadcast sent to all agents")
            return True
        except Exception as e:
            logger.error(f"❌ Broadcast failed: {str(e)}")
            return False
    
    # --- STATE MANAGEMENT ---
    
    def get_task_state(self, project_id: str, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current task state
        """
        try:
            key = f"state:{project_id}:{task_id}"
            state_json = self.redis_client.get(key)
            return json.loads(state_json) if state_json else None
        except Exception as e:
            logger.error(f"❌ State retrieval failed: {str(e)}")
            return None
    
    def set_task_state(self, project_id: str, task_id: str, state: Dict[str, Any]) -> bool:
        """
        Set task state with TTL
        """
        try:
            key = f"state:{project_id}:{task_id}"
            state['updated'] = datetime.now().isoformat()
            self.redis_client.setex(
                key,
                timedelta(hours=24),  # 24 hour TTL
                json.dumps(state)
            )
            return True
        except Exception as e:
            logger.error(f"❌ State update failed: {str(e)}")
            return False
    
    def _update_task_state(self, message: AgentMessage):
        """
        Update task state based on message
        """
        state = {
            'task_id': message.task_id,
            'agent_id': message.agent_id,
            'status': message.status.value,
            'completion': message.completion,
            'time_elapsed': message.time_elapsed,
            'errors': message.errors,
            'output': message.output,
            'timestamp': message.timestamp
        }
        self.set_task_state(message.project_id, message.task_id, state)
    
    # --- CHECKPOINT & RECOVERY ---
    
    def create_checkpoint(self, project_id: str, checkpoint: TaskCheckpoint) -> bool:
        """
        Create checkpoint for rollback capability
        """
        try:
            # Store checkpoint
            key = f"checkpoint:{project_id}:{checkpoint.task_id}"
            self.redis_client.lpush(key, checkpoint.to_json())
            
            # Keep only last 3 checkpoints
            self.redis_client.ltrim(key, 0, 2)
            
            logger.info(f"💾 Checkpoint created: {checkpoint.task_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Checkpoint creation failed: {str(e)}")
            return False
    
    def get_checkpoint(self, project_id: str, task_id: str, index: int = 0) -> Optional[TaskCheckpoint]:
        """
        Get checkpoint (0 = most recent)
        """
        try:
            key = f"checkpoint:{project_id}:{task_id}"
            checkpoint_json = self.redis_client.lindex(key, index)
            return TaskCheckpoint.from_json(checkpoint_json) if checkpoint_json else None
        except Exception as e:
            logger.error(f"❌ Checkpoint retrieval failed: {str(e)}")
            return None
    
    def rollback_to_checkpoint(self, project_id: str, task_id: str, index: int = 0) -> bool:
        """
        Rollback task to checkpoint
        """
        try:
            checkpoint = self.get_checkpoint(project_id, task_id, index)
            if checkpoint:
                self.set_task_state(project_id, task_id, checkpoint.state)
                logger.info(f"⏮️ Rolled back to checkpoint: {checkpoint.timestamp}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Rollback failed: {str(e)}")
            return False
    
    # --- MONITORING & ALERTS ---
    
    def _check_time_limits(self, message: AgentMessage):
        """
        Check if task exceeds time limits
        """
        if message.time_elapsed > TIME_LIMITS['2hour_warning']:
            self._send_alert(
                level=ErrorLevel.CRITICAL,
                message=f"⚠️ TASK EXCEEDING 2 HOURS - Could fuck your day Alan! Task: {message.task_id}",
                task_id=message.task_id
            )
        elif message.time_elapsed > message.time_estimate * 1.5:
            self._send_alert(
                level=ErrorLevel.WARNING,
                message=f"⏰ Task running 50% over estimate: {message.task_id}",
                task_id=message.task_id
            )
    
    def _send_alert(self, level: ErrorLevel, message: str, task_id: str):
        """
        Send alert to monitoring channel
        """
        alert = {
            'level': level.value,
            'message': message,
            'task_id': task_id,
            'timestamp': datetime.now().isoformat()
        }
        self.redis_client.publish('channel:alerts', json.dumps(alert))
        logger.warning(f"🚨 Alert: {message}")
    
    def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """
        Get comprehensive project status
        """
        try:
            pattern = f"state:{project_id}:*"
            keys = self.redis_client.keys(pattern)
            
            tasks = []
            total_completion = 0
            blocked_count = 0
            error_count = 0
            
            for key in keys:
                state_json = self.redis_client.get(key)
                if state_json:
                    state = json.loads(state_json)
                    tasks.append(state)
                    total_completion += state.get('completion', 0)
                    if state.get('status') == TaskStatus.BLOCKED.value:
                        blocked_count += 1
                    elif state.get('status') == TaskStatus.ERROR.value:
                        error_count += 1
            
            return {
                'project_id': project_id,
                'total_tasks': len(tasks),
                'average_completion': total_completion / len(tasks) if tasks else 0,
                'blocked_tasks': blocked_count,
                'error_tasks': error_count,
                'tasks': tasks
            }
        except Exception as e:
            logger.error(f"❌ Project status failed: {str(e)}")
            return {}
    
    # --- SUBSCRIPTION & CALLBACKS ---
    
    def subscribe(self, channel: str, callback: Callable):
        """
        Subscribe to channel with callback
        """
        if channel not in self.callbacks:
            self.callbacks[channel] = []
        self.callbacks[channel].append(callback)
        self.pubsub.subscribe(channel)
        logger.info(f"📻 Subscribed to channel: {channel}")
    
    async def start_listening(self):
        """
        Start listening for messages (async)
        """
        self._running = True
        logger.info("🎧 Started listening for messages")
        
        while self._running:
            try:
                message = self.pubsub.get_message(timeout=0.1)
                if message and message['type'] == 'message':
                    channel = message['channel']
                    data = json.loads(message['data'])
                    
                    # Execute callbacks
                    if channel in self.callbacks:
                        for callback in self.callbacks[channel]:
                            self.executor.submit(callback, data)
                
                await asyncio.sleep(0.01)  # Prevent CPU spinning
                
            except Exception as e:
                logger.error(f"❌ Listening error: {str(e)}")
    
    def stop_listening(self):
        """
        Stop listening for messages
        """
        self._running = False
        self.pubsub.close()
        self.executor.shutdown(wait=True)
        logger.info("🛑 Stopped listening")
    
    # --- PERFORMANCE METRICS ---
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics
        """
        try:
            info = self.redis_client.info()
            return {
                'connected_clients': info.get('connected_clients', 0),
                'used_memory_human': info.get('used_memory_human', 'N/A'),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'instantaneous_ops_per_sec': info.get('instantaneous_ops_per_sec', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'hit_rate': (info.get('keyspace_hits', 0) / 
                           (info.get('keyspace_hits', 0) + info.get('keyspace_misses', 1))) * 100
            }
        except Exception as e:
            logger.error(f"❌ Metrics retrieval failed: {str(e)}")
            return {}
    
    # --- CLEANUP ---
    
    def cleanup_old_data(self, hours: int = 24):
        """
        Clean up old data older than specified hours
        """
        try:
            cutoff = datetime.now() - timedelta(hours=hours)
            
            # Clean old states
            for key in self.redis_client.keys("state:*"):
                state_json = self.redis_client.get(key)
                if state_json:
                    state = json.loads(state_json)
                    timestamp = datetime.fromisoformat(state.get('timestamp', datetime.now().isoformat()))
                    if timestamp < cutoff:
                        self.redis_client.delete(key)
            
            logger.info(f"🧹 Cleaned up data older than {hours} hours")
            return True
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {str(e)}")
            return False


# --- AGENT BASE CLASS ---
class BaseAgent:
    """
    Base class for all agents with communication capabilities
    """
    
    def __init__(self, agent_id: str, agent_type: AgentType, communicator: InterAgentCommunicator):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.comm = communicator
        self.current_task = None
        
    async def process_task(self, message: AgentMessage):
        """
        Process incoming task - override in subclasses
        """
        raise NotImplementedError("Subclasses must implement process_task")
    
    def send_progress(self, completion: int, output: Dict = None, next_agent: str = None):
        """
        Send progress update
        """
        if not self.current_task:
            return
        
        message = AgentMessage(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            task_id=self.current_task.task_id,
            project_id=self.current_task.project_id,
            status=TaskStatus.IN_PROGRESS if completion < 100 else TaskStatus.COMPLETED,
            completion=completion,
            time_elapsed=int(time.time() - self.start_time),
            time_estimate=self.current_task.time_estimate,
            dependencies=self.current_task.dependencies,
            errors=[],
            output=output or {},
            next_agent=next_agent,
            timestamp=datetime.now().isoformat()
        )
        
        self.comm.send_message(message)
    
    def report_error(self, error: str, level: ErrorLevel = ErrorLevel.WARNING):
        """
        Report error
        """
        if not self.current_task:
            return
        
        message = AgentMessage(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            task_id=self.current_task.task_id,
            project_id=self.current_task.project_id,
            status=TaskStatus.ERROR if level == ErrorLevel.CRITICAL else TaskStatus.IN_PROGRESS,
            completion=self.current_task.completion,
            time_elapsed=int(time.time() - self.start_time),
            time_estimate=self.current_task.time_estimate,
            dependencies=self.current_task.dependencies,
            errors=[{'error': error, 'level': level.value, 'timestamp': datetime.now().isoformat()}],
            output=self.current_task.output,
            next_agent=None,
            timestamp=datetime.now().isoformat()
        )
        
        self.comm.send_message(message)
    
    async def run(self):
        """
        Main agent loop
        """
        logger.info(f"🤖 {self.agent_id} started")
        
        while True:
            try:
                # Check for new messages
                message = self.comm.receive_message(self.agent_id, timeout=1)
                
                if message:
                    self.current_task = message
                    self.start_time = time.time()
                    
                    # Process task
                    await self.process_task(message)
                
                await asyncio.sleep(0.1)
                
            except KeyboardInterrupt:
                logger.info(f"🛑 {self.agent_id} stopped")
                break
            except Exception as e:
                logger.error(f"❌ {self.agent_id} error: {str(e)}")
                self.report_error(str(e), ErrorLevel.CRITICAL)


# --- EXAMPLE USAGE ---
async def main():
    """
    Example setup and usage
    """
    # Initialize communicator
    comm = InterAgentCommunicator()
    
    # Create sample message
    message = AgentMessage(
        agent_id="orchestrator_001",
        agent_type=AgentType.ORCHESTRATOR,
        task_id="task_123",
        project_id="project_abc",
        status=TaskStatus.PENDING,
        completion=0,
        time_elapsed=0,
        time_estimate=300,  # 5 minutes
        dependencies=[],
        errors=[],
        output={"instruction": "Create user dashboard"},
        next_agent="frontend_001",
        timestamp=datetime.now().isoformat()
    )
    
    # Send message
    comm.send_message(message)
    
    # Get project status
    status = comm.get_project_status("project_abc")
    print(f"Project Status: {json.dumps(status, indent=2)}")
    
    # Get metrics
    metrics = comm.get_metrics()
    print(f"Performance Metrics: {json.dumps(metrics, indent=2)}")
    
    # Example callback
    def alert_handler(data):
        print(f"🚨 ALERT RECEIVED: {data}")
    
    # Subscribe to alerts
    comm.subscribe('channel:alerts', alert_handler)
    
    # Start listening (in production, run in separate thread/process)
    await comm.start_listening()


if __name__ == "__main__":
    # Run example
    asyncio.run(main())
