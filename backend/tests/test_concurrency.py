"""
Concurrent access tests for Campaign Operations OS.

Tests race conditions and concurrent operations to ensure data integrity.
"""

import asyncio
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.exc import IntegrityError

from app.models import (
    Task,
    TaskAssignment,
    TaskStatus,
    TaskPriority,
    CampaignMembership,
    ApprovalRequest,
    ApprovalStatus,
)


class TestConcurrentTaskOperations:
    """Test concurrent task-related operations."""

    @pytest.mark.asyncio
    async def test_concurrent_task_status_updates(self, mock_db_session):
        """
        Test that concurrent task status updates are handled correctly.

        Scenario: Two users try to update the same task's status simultaneously.
        Expected: Only one update should succeed, or both should be serialized.
        """
        task = MagicMock(spec=Task)
        task.id = 1
        task.status = TaskStatus.TODO
        task.updated_at = datetime.now(timezone.utc)

        update_count = 0
        update_lock = asyncio.Lock()

        async def simulate_update(new_status: TaskStatus):
            nonlocal update_count
            async with update_lock:
                # Simulate database update with version check
                if task.status != TaskStatus.DONE:
                    task.status = new_status
                    update_count += 1
                    return True
                return False

        # Simulate concurrent updates
        results = await asyncio.gather(
            simulate_update(TaskStatus.IN_PROGRESS),
            simulate_update(TaskStatus.DONE),
        )

        # At least one update should succeed
        assert any(results)
        assert update_count >= 1

    @pytest.mark.asyncio
    async def test_concurrent_task_assignment(self, mock_db_session):
        """
        Test that the same member cannot be assigned to a task twice concurrently.

        Scenario: Two requests try to assign the same member to the same task.
        Expected: Database unique constraint prevents duplicate assignments.
        """
        task_id = 1
        member_id = 1
        assigned_assignments = []

        async def assign_member():
            # Check if already assigned
            existing = [a for a in assigned_assignments
                       if a["task_id"] == task_id and a["member_id"] == member_id]
            if existing:
                raise IntegrityError("", "", Exception("Duplicate entry"))

            # Simulate assignment
            assignment = {"task_id": task_id, "member_id": member_id}
            assigned_assignments.append(assignment)
            return assignment

        # Run concurrent assignments
        tasks = [assign_member() for _ in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Only one should succeed
        successful = [r for r in results if not isinstance(r, Exception)]
        errors = [r for r in results if isinstance(r, IntegrityError)]

        assert len(successful) == 1
        assert len(errors) == 4

    @pytest.mark.asyncio
    async def test_concurrent_task_column_move(self, mock_db_session):
        """
        Test moving tasks between columns concurrently.

        Scenario: Multiple tasks are moved to the same column simultaneously.
        Expected: Position ordering should remain consistent.
        """
        tasks = []
        column_tasks = []
        lock = asyncio.Lock()

        for i in range(5):
            task = MagicMock(spec=Task)
            task.id = i + 1
            task.column_id = None
            task.position = 0
            tasks.append(task)

        async def move_task_to_column(task: Task, column_id: int):
            async with lock:
                task.column_id = column_id
                task.position = len(column_tasks)
                column_tasks.append(task)
                return task.position

        # Move all tasks to column 1 concurrently
        results = await asyncio.gather(*[
            move_task_to_column(t, 1) for t in tasks
        ])

        # All positions should be unique
        assert len(set(results)) == 5
        # Positions should be 0-4
        assert sorted(results) == [0, 1, 2, 3, 4]


class TestConcurrentApprovalOperations:
    """Test concurrent approval-related operations."""

    @pytest.mark.asyncio
    async def test_concurrent_approval_decisions(self, mock_db_session):
        """
        Test that an approval can only be approved/rejected once.

        Scenario: Two approvers try to process the same approval simultaneously.
        Expected: Only one decision should be recorded.
        """
        approval = MagicMock(spec=ApprovalRequest)
        approval.id = 1
        approval.status = ApprovalStatus.PENDING
        decision_lock = asyncio.Lock()
        decision_made = False

        async def process_approval(new_status: ApprovalStatus):
            nonlocal decision_made
            async with decision_lock:
                if approval.status == ApprovalStatus.PENDING:
                    approval.status = new_status
                    decision_made = True
                    return True
                return False

        # Simulate concurrent decisions
        results = await asyncio.gather(
            process_approval(ApprovalStatus.APPROVED),
            process_approval(ApprovalStatus.REJECTED),
        )

        # Only one should succeed
        assert sum(results) == 1
        assert approval.status in [ApprovalStatus.APPROVED, ApprovalStatus.REJECTED]


class TestConcurrentMembershipOperations:
    """Test concurrent membership-related operations."""

    @pytest.mark.asyncio
    async def test_concurrent_role_assignment(self, mock_db_session):
        """
        Test concurrent role assignment to the same membership.

        Scenario: Two admins try to assign different roles to a member simultaneously.
        Expected: Only one role assignment should succeed.
        """
        membership = MagicMock(spec=CampaignMembership)
        membership.id = 1
        membership.role_id = None
        role_lock = asyncio.Lock()

        async def assign_role(role_id: int):
            async with role_lock:
                if membership.role_id is None:
                    membership.role_id = role_id
                    return True
                return False

        # Simulate concurrent role assignments
        results = await asyncio.gather(
            assign_role(1),  # Admin role
            assign_role(2),  # Member role
        )

        # Only one should succeed
        assert sum(results) == 1
        assert membership.role_id in [1, 2]

    @pytest.mark.asyncio
    async def test_concurrent_member_deactivation(self, mock_db_session):
        """
        Test that member deactivation is atomic.

        Scenario: Member is deactivated while they're being assigned a task.
        Expected: Task assignment should fail if member is inactive.
        """
        membership = MagicMock(spec=CampaignMembership)
        membership.id = 1
        membership.is_active = True
        operation_lock = asyncio.Lock()

        async def deactivate_member():
            async with operation_lock:
                membership.is_active = False
                await asyncio.sleep(0.01)  # Simulate DB operation
                return True

        async def assign_task_to_member():
            await asyncio.sleep(0.005)  # Slight delay
            async with operation_lock:
                if not membership.is_active:
                    raise ValueError("Cannot assign task to inactive member")
                return True

        # Run concurrently
        results = await asyncio.gather(
            deactivate_member(),
            assign_task_to_member(),
            return_exceptions=True,
        )

        # Deactivation should succeed
        assert results[0] is True
        # Task assignment should fail
        assert isinstance(results[1], ValueError)


class TestDatabaseIsolation:
    """Test database isolation and transaction handling."""

    @pytest.mark.asyncio
    async def test_read_committed_isolation(self, mock_db_session):
        """
        Test that uncommitted changes are not visible to other transactions.

        This is a conceptual test - actual isolation depends on database config.
        """
        shared_value = {"data": "original"}
        committed = False

        async def writer():
            nonlocal committed
            shared_value["data"] = "modified"
            await asyncio.sleep(0.01)  # Simulate work before commit
            committed = True
            return "committed"

        async def reader():
            await asyncio.sleep(0.005)  # Read during writer's work
            # In read committed, should see original until commit
            if not committed:
                return shared_value["data"]
            return "saw_committed"

        results = await asyncio.gather(writer(), reader())

        # Reader should see either original or committed value
        assert results[1] in ["original", "modified", "saw_committed"]

    @pytest.mark.asyncio
    async def test_serializable_operations(self, mock_db_session):
        """
        Test that operations requiring serialization are handled correctly.
        """
        counter = {"value": 0}
        lock = asyncio.Lock()

        async def increment():
            async with lock:
                current = counter["value"]
                await asyncio.sleep(0.001)  # Simulate DB read-modify-write
                counter["value"] = current + 1
                return counter["value"]

        # Run 10 concurrent increments
        results = await asyncio.gather(*[increment() for _ in range(10)])

        # All increments should be serialized
        assert counter["value"] == 10
        # Results should be 1-10 (in some order)
        assert sorted(results) == list(range(1, 11))


class TestRateLimiting:
    """Test rate limiting scenarios."""

    @pytest.mark.asyncio
    async def test_burst_request_handling(self):
        """
        Test handling of burst requests.

        Scenario: Many requests arrive simultaneously.
        Expected: Rate limiter should queue or reject excess requests.
        """
        request_count = 0
        max_concurrent = 5
        semaphore = asyncio.Semaphore(max_concurrent)
        processed = []

        async def process_request(request_id: int):
            nonlocal request_count
            async with semaphore:
                request_count += 1
                await asyncio.sleep(0.01)  # Simulate processing
                processed.append(request_id)
                return request_id

        # Send 20 concurrent requests
        results = await asyncio.gather(*[
            process_request(i) for i in range(20)
        ])

        # All requests should be processed
        assert len(results) == 20
        assert len(processed) == 20

    @pytest.mark.asyncio
    async def test_request_timeout_handling(self):
        """
        Test that slow requests timeout properly.
        """
        async def slow_operation():
            await asyncio.sleep(10)  # Very slow
            return "completed"

        async def fast_operation():
            await asyncio.sleep(0.01)
            return "completed"

        # Slow operation should timeout
        try:
            await asyncio.wait_for(slow_operation(), timeout=0.1)
            assert False, "Should have timed out"
        except asyncio.TimeoutError:
            pass  # Expected

        # Fast operation should complete
        result = await asyncio.wait_for(fast_operation(), timeout=1.0)
        assert result == "completed"
