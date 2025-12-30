# Copyright 2024-2025 NetCracker Technology Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Step definitions for Consul Backup and Restore tests.

These steps test backup daemon functionality:
- Full backup and restore
- Granular backup and restore
- Backup eviction
- Authentication

Engineers can write feature files using these steps.
"""

import time

import pytest
import requests
from pytest_bdd import scenarios, given, when, then

# Import all scenarios from the feature file
scenarios("../features/backup.feature")


# ============================================================================
# Constants
# ============================================================================

BACKUP_TIMEOUT = 120  # seconds
BACKUP_INTERVAL = 10  # seconds
RESTORE_TIMEOUT = 120  # seconds
RESTORE_INTERVAL = 10  # seconds


# ============================================================================
# Given Steps
# ============================================================================

@given("unauthorized backup session")
def create_unauthorized_session(test_context, backup_base_url):
    """Create session without authentication."""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Accept": "application/json",
    })
    test_context["unauthorized_session"] = session
    test_context["backup_url"] = backup_base_url


# ============================================================================
# When Steps
# ============================================================================

@when("I perform full backup")
def perform_full_backup(backup_session, backup_base_url, test_context):
    """Trigger full backup and wait for completion."""
    response = backup_session.post(f"{backup_base_url}/backup")
    assert response.status_code == 200, f"Backup request failed: {response.status_code}"
    
    backup_id = response.text.strip('"')
    test_context["backup_id"] = backup_id
    print(f"\n📦 Full backup started: {backup_id}")
    
    # Wait for backup completion
    _wait_for_backup(backup_session, backup_base_url, backup_id, is_granular=False)


@when("I perform granular backup")
def perform_granular_backup(backup_session, backup_base_url, backup_config, test_context):
    """Trigger granular backup and wait for completion."""
    data = {"dbs": [backup_config["datacenter"]]}
    response = backup_session.post(f"{backup_base_url}/backup", json=data)
    assert response.status_code == 200, f"Backup request failed: {response.status_code}"
    
    backup_id = response.text.strip('"')
    test_context["backup_id"] = backup_id
    test_context["is_granular"] = True
    print(f"\n📦 Granular backup started: {backup_id}")
    
    # Wait for backup completion
    _wait_for_backup(backup_session, backup_base_url, backup_id, is_granular=True)


@when("I restore from backup")
def restore_from_backup(backup_session, backup_base_url, backup_config, test_context):
    """Restore from backup and wait for completion."""
    restore_data = {
        "vault": test_context["backup_id"],
        "dbs": [backup_config["datacenter"]],
        "skip_acl_recovery": "true"
    }
    response = backup_session.post(f"{backup_base_url}/restore", json=restore_data)
    assert response.status_code == 200, f"Restore request failed: {response.status_code}"
    
    task_id = response.text.strip('"')
    test_context["restore_task_id"] = task_id
    print(f"\n🔄 Restore started: {task_id}")
    
    # Wait for restore completion
    _wait_for_restore(backup_session, backup_base_url, task_id)


@when("I evict backup by ID")
def evict_backup(backup_session, backup_base_url, test_context):
    """Evict (delete) backup by ID."""
    backup_id = test_context["backup_id"]
    response = backup_session.post(f"{backup_base_url}/evict/{backup_id}")
    assert response.status_code == 200, f"Evict request failed: {response.status_code}"
    print(f"\n🗑️ Backup evicted: {backup_id}")


@when("I try to create backup without auth")
def backup_without_auth(test_context):
    """Try to create backup without authentication."""
    session = test_context["unauthorized_session"]
    url = test_context["backup_url"]
    response = session.post(f"{url}/backup")
    test_context["response"] = response


# ============================================================================
# Then Steps
# ============================================================================

@then("backup should complete successfully")
def backup_completed(test_context):
    """Verify backup completed."""
    assert "backup_id" in test_context, "Backup ID not found"
    print(f"\n✅ Backup completed: {test_context['backup_id']}")


@then("backup should be marked as granular")
def backup_is_granular(test_context):
    """Verify backup is marked as granular."""
    assert test_context.get("is_granular") is True, "Backup should be granular"


@then("restore should complete successfully")
def restore_completed(test_context):
    """Verify restore completed."""
    assert "restore_task_id" in test_context, "Restore task ID not found"
    print(f"\n✅ Restore completed: {test_context['restore_task_id']}")


@then("test data should be recovered")
def data_recovered(consul, test_context):
    """Verify test data was recovered after restore."""
    value = consul.get_data(test_context["test_key"])
    assert value.decode() == test_context["test_value"], \
        f"Expected {test_context['test_value']}, got {value.decode()}"
    print(f"\n✅ Data recovered: {test_context['test_key']} = {value.decode()}")
    
    # Cleanup
    consul.delete_data(test_context["test_key"])


@then("backup should be removed from list")
def backup_removed(backup_session, backup_base_url, test_context):
    """Verify backup was removed from list."""
    response = backup_session.get(f"{backup_base_url}/listbackups")
    assert test_context["backup_id"] not in response.text, \
        f"Backup {test_context['backup_id']} still in list"
    print(f"\n✅ Backup removed from list")


# ============================================================================
# Helper Functions
# ============================================================================

def _wait_for_backup(session, base_url, backup_id, is_granular):
    """Wait for backup to complete."""
    start_time = time.time()
    while time.time() - start_time < BACKUP_TIMEOUT:
        response = session.get(f"{base_url}/listbackups/{backup_id}")
        if response.status_code == 200:
            data = response.json()
            if not data.get("failed") and data.get("valid"):
                assert data.get("is_granular") == is_granular
                return
        time.sleep(BACKUP_INTERVAL)
    pytest.fail(f"Backup timeout after {BACKUP_TIMEOUT}s")


def _wait_for_restore(session, base_url, task_id):
    """Wait for restore to complete."""
    start_time = time.time()
    while time.time() - start_time < RESTORE_TIMEOUT:
        response = session.get(f"{base_url}/jobstatus/{task_id}")
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "Successful":
                return
        time.sleep(RESTORE_INTERVAL)
    pytest.fail(f"Restore timeout after {RESTORE_TIMEOUT}s")


