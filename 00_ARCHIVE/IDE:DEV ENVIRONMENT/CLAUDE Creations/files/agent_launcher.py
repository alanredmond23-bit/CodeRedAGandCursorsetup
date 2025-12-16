#!/usr/bin/env python3
"""
Agent Launcher - Billionaire-Speed Agent Initialization
Starts agents with proper roles, configurations, and monitoring
"""

import os
import sys
import asyncio
import logging
import signal
from datetime import datetime
from typing import Dict, Any, Optional
import json

from inter_agent_communication import (
    AgentCommunicator, 
    AgentRole, 
    TaskExecutor,
    MessageType,
    Priority,
    Message
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'/app/logs/agent_{datetime.now().strftime("%Y%m%d")}.log')
    ]
)
logger = logging.getLogger('agent_launcher')

class AgentLauncher:
    """
    Sophisticated agent launcher with full orchestration capabilities
    Implements billionaire-speed initialization and monitoring
    """
    
    def __init__(self):
        self.agent: Optional[AgentCommunicator] = None
        self.executor: Optional[TaskExecutor] = None
        self.agent_id = os.getenv('AGENT_ID', 'agent_001')
        self.agent_role_str = os.getenv('AGENT_ROLE', 'orchestrator')
        self.model = os.getenv('MODEL', 'claude-sonnet-4.5')
        self.running = False
        self.start_time = None
        self.task_count = 0
        self.error_count = 0
        
        # Map string roles to enums
        self.role_map = {
            'orchestrator': AgentRole.ORCHESTRATOR,
            'manager': AgentRole.MANAGER,
            'frontend': AgentRole.FRONTEND,
            'backend': AgentRole.BACKEND,
            'database': AgentRole.DATABASE,
            'deploy': AgentRole.DEPLOY,
            'quality': AgentRole.QUALITY,
            'legal': AgentRole.LEGAL,
            'data': AgentRole.DATA
        }
        
        self.role = self.role_map.get(self.agent_role_str, AgentRole.ORCHESTRATOR)
        
    async def initialize(self):
        """Initialize agent with all necessary configurations"""
        logger.info(f"Initializing agent {self.agent_id} with role {self.role.value}")
        
        try:
            # Create agent communicator
            self.agent = AgentCommunicator(self.agent_id, self.role)
            
            # Connect to Redis
            await self.agent.connect()
            
            # Create task executor
            self.executor = TaskExecutor(self.agent)
            
            # Register message handlers
            await self._register_handlers()
            
            # Set initial state
            await self.agent.update_state('status', 'initializing')
            await self.agent.update_state('model', self.model)
            await self.agent.update_state('started_at', datetime.utcnow().isoformat())
            
            self.running = True
            self.start_time = datetime.utcnow()
            
            logger.info(f"Agent {self.agent_id} initialized successfully")
            
            # Send ready signal
            await self.agent.send_message(
                "orchestrator",
                MessageType.STATUS,
                {
                    'status': 'ready',
                    'agent_id': self.agent_id,
                    'role': self.role.value,
                    'model': self.model,
                    'capabilities': self._get_capabilities()
                },
                Priority.HIGH
            )
            
            # Update state to ready
            await self.agent.update_state('status', 'ready')
            
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            raise
    
    async def _register_handlers(self):
        """Register message handlers based on agent role"""
        
        # Universal handlers
        self.agent.register_handler(MessageType.TASK, self._handle_task)
        self.agent.register_handler(MessageType.STATUS, self._handle_status)
        self.agent.register_handler(MessageType.ERROR, self._handle_error)
        
        # Role-specific handlers
        if self.role == AgentRole.ORCHESTRATOR:
            self.agent.register_handler(MessageType.RESULT, self._handle_result)
        elif self.role == AgentRole.MANAGER:
            self.agent.register_handler(MessageType.TASK, self._handle_manager_task)
        elif self.role in [AgentRole.FRONTEND, AgentRole.BACKEND, AgentRole.DATABASE]:
            self.agent.register_handler(MessageType.TASK, self._handle_worker_task)
        elif self.role == AgentRole.QUALITY:
            self.agent.register_handler(MessageType.RESULT, self._handle_quality_check)
        elif self.role == AgentRole.DEPLOY:
            self.agent.register_handler(MessageType.RESULT, self._handle_deployment)
    
    async def _handle_task(self, message: Message):
        """Universal task handler"""
        logger.info(f"Received task: {message.payload.get('task_id', 'unknown')}")
        self.task_count += 1
        
        try:
            # Update state
            await self.agent.update_state('current_task', message.payload.get('task_id'))
            await self.agent.update_state('status', 'working')
            
            # Execute task based on role
            result = await self._execute_task_by_role(message.payload)
            
            # Send result
            await self.agent.send_message(
                message.from_agent,
                MessageType.RESULT,
                {
                    'task_id': message.payload.get('task_id'),
                    'result': result,
                    'agent_id': self.agent_id,
                    'execution_time': result.get('execution_time', 0)
                }
            )
            
            # Update state
            await self.agent.update_state('status', 'ready')
            await self.agent.update_state('tasks_completed', self.task_count)
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            self.error_count += 1
            
            await self.agent.send_message(
                message.from_agent,
                MessageType.ERROR,
                {
                    'task_id': message.payload.get('task_id'),
                    'error': str(e),
                    'agent_id': self.agent_id
                },
                Priority.HIGH
            )
    
    async def _handle_status(self, message: Message):
        """Handle status update messages"""
        logger.info(f"Status update from {message.from_agent}: {message.payload.get('status')}")
        
        # Store status in shared state
        await self.agent.update_state(
            f"peer_status_{message.from_agent}",
            message.payload
        )
    
    async def _handle_error(self, message: Message):
        """Handle error messages"""
        logger.error(f"Error from {message.from_agent}: {message.payload.get('error')}")
        self.error_count += 1
        
        # Orchestrator should handle error recovery
        if self.role == AgentRole.ORCHESTRATOR:
            await self._initiate_error_recovery(message)
    
    async def _handle_result(self, message: Message):
        """Handle task results (Orchestrator only)"""
        logger.info(f"Result received for task {message.payload.get('task_id')}")
        
        # Process result based on task type
        task_id = message.payload.get('task_id')
        result = message.payload.get('result')
        
        # Update project state
        await self.agent.update_state(f"task_result_{task_id}", result)
        
        # Check if all tasks complete
        await self._check_project_completion()
    
    async def _handle_manager_task(self, message: Message):
        """Project Manager specific task handling"""
        project = message.payload.get('project')
        
        # Decompose project into tasks
        tasks = await self._decompose_project(project)
        
        # Assign tasks to workers
        for task in tasks:
            worker = await self._select_best_worker(task)
            await self.agent.send_message(
                worker,
                MessageType.TASK,
                task,
                Priority.NORMAL
            )
    
    async def _handle_worker_task(self, message: Message):
        """Worker agent specific task handling"""
        # Execute using TaskExecutor
        result = await self.executor.execute_task(
            message.payload.get('task_id'),
            message.payload.get('task_type'),
            message.payload,
            message.payload.get('time_limit', 30)
        )
        
        return result
    
    async def _handle_quality_check(self, message: Message):
        """Quality checker specific handling"""
        # Run quality checks
        checks = await self._run_quality_checks(message.payload)
        
        if checks['passed']:
            # Forward to deployment
            await self.agent.send_message(
                "deploy_automator",
                MessageType.TASK,
                message.payload,
                Priority.HIGH
            )
        else:
            # Send back for fixes
            await self.agent.send_message(
                message.from_agent,
                MessageType.ERROR,
                {
                    'task_id': message.payload.get('task_id'),
                    'quality_issues': checks['issues']
                },
                Priority.HIGH
            )
    
    async def _handle_deployment(self, message: Message):
        """Deployment agent specific handling"""
        # Deploy to production
        deployment_result = await self._deploy_to_production(message.payload)
        
        # Notify orchestrator
        await self.agent.send_message(
            "orchestrator_prime",
            MessageType.RESULT,
            {
                'deployment': deployment_result,
                'task_id': message.payload.get('task_id')
            },
            Priority.HIGH
        )
    
    async def _execute_task_by_role(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task based on agent role"""
        start_time = datetime.utcnow()
        
        # Simulate task execution based on role
        # In production, this would call actual implementation
        
        if self.role == AgentRole.FRONTEND:
            result = {
                'components_created': ['Dashboard.tsx', 'Login.tsx'],
                'tests_written': True,
                'styling_complete': True
            }
        elif self.role == AgentRole.BACKEND:
            result = {
                'endpoints_created': ['/api/users', '/api/auth'],
                'database_connected': True,
                'tests_passing': True
            }
        elif self.role == AgentRole.DATABASE:
            result = {
                'schema_created': True,
                'migrations_run': True,
                'indexes_optimized': True
            }
        else:
            result = {'status': 'completed', 'data': 'generic_result'}
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        result['execution_time'] = execution_time
        
        return result
    
    def _get_capabilities(self) -> list:
        """Get agent capabilities based on role"""
        capabilities_map = {
            AgentRole.ORCHESTRATOR: ['planning', 'coordination', 'monitoring'],
            AgentRole.MANAGER: ['task_decomposition', 'assignment', 'tracking'],
            AgentRole.FRONTEND: ['react', 'nextjs', 'tailwind', 'typescript'],
            AgentRole.BACKEND: ['api', 'authentication', 'database', 'microservices'],
            AgentRole.DATABASE: ['schema_design', 'optimization', 'migration'],
            AgentRole.DEPLOY: ['docker', 'kubernetes', 'vercel', 'monitoring'],
            AgentRole.QUALITY: ['testing', 'security', 'performance', 'review'],
            AgentRole.LEGAL: ['contract_analysis', 'compliance', 'documentation'],
            AgentRole.DATA: ['analytics', 'ml', 'etl', 'visualization']
        }
        
        return capabilities_map.get(self.role, [])
    
    async def _decompose_project(self, project: Dict[str, Any]) -> list:
        """Decompose project into tasks (Manager role)"""
        # Simplified task decomposition
        tasks = []
        
        if 'frontend' in project:
            tasks.append({
                'task_id': f"{project['id']}_frontend",
                'task_type': 'frontend_development',
                'requirements': project['frontend']
            })
        
        if 'backend' in project:
            tasks.append({
                'task_id': f"{project['id']}_backend",
                'task_type': 'backend_development',
                'requirements': project['backend']
            })
        
        if 'database' in project:
            tasks.append({
                'task_id': f"{project['id']}_database",
                'task_type': 'database_setup',
                'requirements': project['database']
            })
        
        return tasks
    
    async def _select_best_worker(self, task: Dict[str, Any]) -> str:
        """Select best worker for task (Manager role)"""
        task_type = task.get('task_type', '')
        
        worker_map = {
            'frontend_development': 'frontend_specialist',
            'backend_development': 'backend_engineer',
            'database_setup': 'database_specialist'
        }
        
        return worker_map.get(task_type, 'backend_engineer')
    
    async def _run_quality_checks(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Run quality checks (Quality role)"""
        # Simplified quality checking
        return {
            'passed': True,
            'test_coverage': 85,
            'security_score': 'A',
            'performance_score': 92,
            'issues': []
        }
    
    async def _deploy_to_production(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy to production (Deploy role)"""
        # Simplified deployment
        return {
            'status': 'deployed',
            'url': 'https://example.vercel.app',
            'version': '1.0.0',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def _check_project_completion(self):
        """Check if all project tasks are complete (Orchestrator)"""
        # Implementation would check all task states
        pass
    
    async def _initiate_error_recovery(self, error_message: Message):
        """Initiate error recovery procedures (Orchestrator)"""
        error = error_message.payload
        task_id = error.get('task_id')
        
        logger.warning(f"Initiating recovery for task {task_id}")
        
        # Retry task with different agent or approach
        # Implementation depends on error type
    
    async def run(self):
        """Main execution loop"""
        logger.info(f"Agent {self.agent_id} starting main loop")
        
        try:
            while self.running:
                await asyncio.sleep(1)
                
                # Periodic health check
                if int(datetime.utcnow().timestamp()) % 60 == 0:
                    await self._send_health_status()
                    
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
        finally:
            await self.shutdown()
    
    async def _send_health_status(self):
        """Send periodic health status"""
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        health_status = {
            'agent_id': self.agent_id,
            'role': self.role.value,
            'status': 'healthy',
            'uptime_seconds': uptime,
            'tasks_completed': self.task_count,
            'errors': self.error_count,
            'error_rate': self.error_count / max(self.task_count, 1),
            'performance_metrics': self.agent.performance_metrics
        }
        
        await self.agent.broadcast(
            MessageType.HEARTBEAT,
            health_status,
            Priority.LOW
        )
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info(f"Shutting down agent {self.agent_id}")
        
        self.running = False
        
        if self.agent:
            # Send shutdown notification
            await self.agent.send_message(
                "orchestrator",
                MessageType.STATUS,
                {
                    'status': 'shutting_down',
                    'agent_id': self.agent_id,
                    'tasks_completed': self.task_count,
                    'errors': self.error_count
                },
                Priority.HIGH
            )
            
            # Clean shutdown
            await self.agent.shutdown()

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}")
    sys.exit(0)

async def main():
    """Main entry point"""
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and initialize launcher
    launcher = AgentLauncher()
    
    try:
        await launcher.initialize()
        await launcher.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Print startup banner
    print("=" * 50)
    print("🚀 AGENT LAUNCHER")
    print("Billionaire-Speed Execution System")
    print("=" * 50)
    print(f"Agent ID: {os.getenv('AGENT_ID', 'agent_001')}")
    print(f"Role: {os.getenv('AGENT_ROLE', 'orchestrator')}")
    print(f"Model: {os.getenv('MODEL', 'claude-sonnet-4.5')}")
    print("=" * 50)
    
    # Run the agent
    asyncio.run(main())
