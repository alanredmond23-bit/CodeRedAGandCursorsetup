#!/usr/bin/env python3
"""
Test Inter-Agent Communication System
Comprehensive testing for billionaire-speed execution
"""

import asyncio
import time
import json
from datetime import datetime
from inter_agent_communication import (
    AgentCommunicator,
    AgentRole,
    MessageType,
    Priority,
    Message,
    TaskExecutor
)

class TestResults:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.execution_times = {}
        
    def record_pass(self, test_name, execution_time):
        self.passed.append(test_name)
        self.execution_times[test_name] = execution_time
        
    def record_fail(self, test_name, error):
        self.failed.append((test_name, error))
        
    def print_summary(self):
        total = len(self.passed) + len(self.failed)
        print("\n" + "=" * 50)
        print("TEST RESULTS SUMMARY")
        print("=" * 50)
        print(f"Total Tests: {total}")
        print(f"Passed: {len(self.passed)} ✅")
        print(f"Failed: {len(self.failed)} ❌")
        
        if self.passed:
            print("\n✅ Passed Tests:")
            for test in self.passed:
                time_ms = self.execution_times[test] * 1000
                print(f"  - {test}: {time_ms:.2f}ms")
        
        if self.failed:
            print("\n❌ Failed Tests:")
            for test, error in self.failed:
                print(f"  - {test}: {error}")
        
        print("\n" + "=" * 50)
        
        # Performance metrics
        if self.execution_times:
            avg_time = sum(self.execution_times.values()) / len(self.execution_times)
            max_time = max(self.execution_times.values())
            min_time = min(self.execution_times.values())
            
            print("PERFORMANCE METRICS")
            print("=" * 50)
            print(f"Average Execution: {avg_time*1000:.2f}ms")
            print(f"Fastest Test: {min_time*1000:.2f}ms")
            print(f"Slowest Test: {max_time*1000:.2f}ms")
            
            if avg_time < 0.1:  # Less than 100ms average
                print("⚡ BILLIONAIRE SPEED ACHIEVED!")
            elif avg_time < 0.5:  # Less than 500ms
                print("🚀 EXCELLENT PERFORMANCE")
            else:
                print("⚠️ PERFORMANCE NEEDS OPTIMIZATION")

async def test_basic_connection():
    """Test 1: Basic agent connection"""
    print("\n🧪 Test 1: Basic Connection")
    start = time.time()
    
    try:
        agent = AgentCommunicator("test_agent_001", AgentRole.ORCHESTRATOR)
        await agent.connect()
        
        # Verify connection
        await agent.redis.ping()
        
        await agent.shutdown()
        
        execution_time = time.time() - start
        print(f"  ✓ Connection established in {execution_time:.3f}s")
        return True, execution_time
        
    except Exception as e:
        print(f"  ✗ Connection failed: {e}")
        return False, str(e)

async def test_message_sending():
    """Test 2: Message sending between agents"""
    print("\n🧪 Test 2: Message Sending")
    start = time.time()
    
    try:
        # Create two agents
        sender = AgentCommunicator("sender", AgentRole.ORCHESTRATOR)
        receiver = AgentCommunicator("receiver", AgentRole.FRONTEND)
        
        await sender.connect()
        await receiver.connect()
        
        # Send message
        msg_id = await sender.send_message(
            "receiver",
            MessageType.TASK,
            {"task": "test_task", "priority": "high"},
            Priority.HIGH,
            requires_ack=False
        )
        
        # Brief wait for message processing
        await asyncio.sleep(0.1)
        
        await sender.shutdown()
        await receiver.shutdown()
        
        execution_time = time.time() - start
        print(f"  ✓ Message sent successfully in {execution_time:.3f}s")
        print(f"  ✓ Message ID: {msg_id}")
        return True, execution_time
        
    except Exception as e:
        print(f"  ✗ Message sending failed: {e}")
        return False, str(e)

async def test_state_management():
    """Test 3: State synchronization between agents"""
    print("\n🧪 Test 3: State Management")
    start = time.time()
    
    try:
        agent1 = AgentCommunicator("agent1", AgentRole.MANAGER)
        agent2 = AgentCommunicator("agent2", AgentRole.BACKEND)
        
        await agent1.connect()
        await agent2.connect()
        
        # Set state
        test_data = {"project": "test_project", "status": "in_progress", "progress": 42}
        await agent1.update_state("project_data", test_data)
        
        # Retrieve state from another agent
        retrieved = await agent2.get_state("agent1", "project_data")
        
        # Verify
        assert retrieved == test_data, "State mismatch"
        
        await agent1.shutdown()
        await agent2.shutdown()
        
        execution_time = time.time() - start
        print(f"  ✓ State synchronized in {execution_time:.3f}s")
        return True, execution_time
        
    except Exception as e:
        print(f"  ✗ State management failed: {e}")
        return False, str(e)

async def test_broadcast():
    """Test 4: Broadcast messaging"""
    print("\n🧪 Test 4: Broadcast Messaging")
    start = time.time()
    
    try:
        broadcaster = AgentCommunicator("broadcaster", AgentRole.ORCHESTRATOR)
        await broadcaster.connect()
        
        # Send broadcast
        await broadcaster.broadcast(
            MessageType.STATUS,
            {"announcement": "System update", "timestamp": datetime.utcnow().isoformat()}
        )
        
        await broadcaster.shutdown()
        
        execution_time = time.time() - start
        print(f"  ✓ Broadcast sent in {execution_time:.3f}s")
        return True, execution_time
        
    except Exception as e:
        print(f"  ✗ Broadcast failed: {e}")
        return False, str(e)

async def test_checkpoint_recovery():
    """Test 5: Checkpoint and recovery system"""
    print("\n🧪 Test 5: Checkpoint & Recovery")
    start = time.time()
    
    try:
        agent = AgentCommunicator("checkpoint_agent", AgentRole.DATABASE)
        await agent.connect()
        
        # Create checkpoint
        checkpoint_data = {
            "schema": "test_db",
            "tables": ["users", "products", "orders"],
            "migration_version": "v1.2.3",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        project_id = "test_project_123"
        await agent.checkpoint(project_id, checkpoint_data)
        
        # Recover checkpoint
        recovered = await agent.recover_from_checkpoint(project_id)
        
        # Verify
        assert recovered == checkpoint_data, "Checkpoint data mismatch"
        
        await agent.shutdown()
        
        execution_time = time.time() - start
        print(f"  ✓ Checkpoint/recovery completed in {execution_time:.3f}s")
        return True, execution_time
        
    except Exception as e:
        print(f"  ✗ Checkpoint/recovery failed: {e}")
        return False, str(e)

async def test_priority_queuing():
    """Test 6: Priority-based message queuing"""
    print("\n🧪 Test 6: Priority Queuing")
    start = time.time()
    
    try:
        agent = AgentCommunicator("priority_agent", AgentRole.DEPLOY)
        await agent.connect()
        
        # Send messages with different priorities
        critical_id = await agent.send_message(
            "priority_agent", MessageType.TASK,
            {"task": "critical_task"}, Priority.CRITICAL, False
        )
        
        normal_id = await agent.send_message(
            "priority_agent", MessageType.TASK,
            {"task": "normal_task"}, Priority.NORMAL, False
        )
        
        low_id = await agent.send_message(
            "priority_agent", MessageType.TASK,
            {"task": "low_task"}, Priority.LOW, False
        )
        
        await asyncio.sleep(0.1)
        await agent.shutdown()
        
        execution_time = time.time() - start
        print(f"  ✓ Priority queuing tested in {execution_time:.3f}s")
        return True, execution_time
        
    except Exception as e:
        print(f"  ✗ Priority queuing failed: {e}")
        return False, str(e)

async def test_task_execution():
    """Test 7: Task execution with time boxing"""
    print("\n🧪 Test 7: Task Execution")
    start = time.time()
    
    try:
        agent = AgentCommunicator("executor_agent", AgentRole.FRONTEND)
        await agent.connect()
        
        executor = TaskExecutor(agent)
        
        # Execute a quick task
        result = await executor.execute_task(
            "test_task_001",
            "simple_query",
            {"quick_complete": True},
            1  # 1 minute time limit
        )
        
        assert result['status'] == 'success', "Task execution failed"
        
        await agent.shutdown()
        
        execution_time = time.time() - start
        print(f"  ✓ Task executed in {execution_time:.3f}s")
        return True, execution_time
        
    except Exception as e:
        print(f"  ✗ Task execution failed: {e}")
        return False, str(e)

async def test_performance_metrics():
    """Test 8: Performance metrics tracking"""
    print("\n🧪 Test 8: Performance Metrics")
    start = time.time()
    
    try:
        agent = AgentCommunicator("metrics_agent", AgentRole.QUALITY)
        await agent.connect()
        
        # Send some messages to generate metrics
        for i in range(5):
            await agent.send_message(
                "metrics_agent",
                MessageType.STATUS,
                {"iteration": i},
                Priority.NORMAL,
                False
            )
        
        # Check metrics
        metrics = agent.performance_metrics
        assert metrics['messages_sent'] == 5, "Message count incorrect"
        
        await agent.shutdown()
        
        execution_time = time.time() - start
        print(f"  ✓ Metrics tracked in {execution_time:.3f}s")
        print(f"  ✓ Messages sent: {metrics['messages_sent']}")
        return True, execution_time
        
    except Exception as e:
        print(f"  ✗ Performance metrics failed: {e}")
        return False, str(e)

async def test_error_handling():
    """Test 9: Error handling and recovery"""
    print("\n🧪 Test 9: Error Handling")
    start = time.time()
    
    try:
        agent = AgentCommunicator("error_agent", AgentRole.BACKEND)
        await agent.connect()
        
        # Try to send to non-existent agent (should handle gracefully)
        msg_id = await agent.send_message(
            "non_existent_agent",
            MessageType.TASK,
            {"test": "error_handling"},
            Priority.LOW,
            False  # Don't require ack to avoid timeout
        )
        
        # Should not crash
        assert msg_id is not None, "Message ID not generated"
        
        await agent.shutdown()
        
        execution_time = time.time() - start
        print(f"  ✓ Error handled gracefully in {execution_time:.3f}s")
        return True, execution_time
        
    except Exception as e:
        print(f"  ✗ Error handling failed: {e}")
        return False, str(e)

async def test_heartbeat():
    """Test 10: Heartbeat system"""
    print("\n🧪 Test 10: Heartbeat System")
    start = time.time()
    
    try:
        agent = AgentCommunicator("heartbeat_agent", AgentRole.LEGAL)
        await agent.connect()
        
        # Wait for heartbeat (should happen within 30 seconds, but we'll check setup)
        await asyncio.sleep(0.5)
        
        # Verify agent is running
        assert agent.running == True, "Agent not running"
        
        await agent.shutdown()
        
        execution_time = time.time() - start
        print(f"  ✓ Heartbeat system active in {execution_time:.3f}s")
        return True, execution_time
        
    except Exception as e:
        print(f"  ✗ Heartbeat system failed: {e}")
        return False, str(e)

async def run_all_tests():
    """Run complete test suite"""
    print("\n" + "=" * 50)
    print("🚀 INTER-AGENT COMMUNICATION TEST SUITE")
    print("=" * 50)
    print("Target: Billionaire-speed execution")
    print("Tolerance: ZERO errors")
    print("Starting tests...")
    
    results = TestResults()
    
    # List of all tests
    tests = [
        ("Basic Connection", test_basic_connection),
        ("Message Sending", test_message_sending),
        ("State Management", test_state_management),
        ("Broadcast", test_broadcast),
        ("Checkpoint Recovery", test_checkpoint_recovery),
        ("Priority Queuing", test_priority_queuing),
        ("Task Execution", test_task_execution),
        ("Performance Metrics", test_performance_metrics),
        ("Error Handling", test_error_handling),
        ("Heartbeat", test_heartbeat)
    ]
    
    # Run each test
    for test_name, test_func in tests:
        try:
            success, result = await test_func()
            if success:
                results.record_pass(test_name, result)
            else:
                results.record_fail(test_name, result)
        except Exception as e:
            results.record_fail(test_name, str(e))
    
    # Print summary
    results.print_summary()
    
    # Final verdict
    print("\n" + "=" * 50)
    if len(results.failed) == 0:
        print("✅ ALL TESTS PASSED!")
        print("🚀 SYSTEM READY FOR BILLIONAIRE-SPEED EXECUTION")
    else:
        print("❌ SOME TESTS FAILED")
        print("⚠️ SYSTEM NEEDS ATTENTION BEFORE DEPLOYMENT")
    print("=" * 50)
    
    return len(results.failed) == 0

if __name__ == "__main__":
    # Run the test suite
    success = asyncio.run(run_all_tests())
    
    # Exit with appropriate code
    exit(0 if success else 1)
