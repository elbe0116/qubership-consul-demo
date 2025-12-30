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
Step definitions for Consul High Availability tests.

These steps test cluster resilience:
- Large value handling
- Leader failover
- Cluster recovery

Engineers can write feature files using these steps.
"""

import os
import time

import pytest
from pytest_bdd import scenarios, given, when, then, parsers

# Import all scenarios from the feature file
scenarios("../features/ha.feature")


# ============================================================================
# Given Steps
# ============================================================================

@given("I have extremely large value from file")
def load_large_value(test_context):
    """Load extremely large value from file."""
    file_path = os.path.join(os.path.dirname(__file__), "..", "data", "extremely_big_value.txt")
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            test_context["large_value"] = f.read()
    else:
        # Generate large value if file doesn't exist
        test_context["large_value"] = "x" * (512 * 1024 + 1)  # > 512KB
    print(f"\n📦 Large value size: {len(test_context['large_value'])} bytes")


# ============================================================================
# When Steps
# ============================================================================

@when("I try to put large value using HTTP request")
def put_large_value(consul, test_context):
    """Try to store large value using HTTP request."""
    folder = "test_folder"
    key = f"{folder}/{test_context['test_key']}"
    response = consul.put_data_using_request(key, test_context["large_value"])
    test_context["response"] = response
    test_context["folder_key"] = key
    print(f"\n📤 PUT large value response: {response.status_code}")


@when("I put normal value using HTTP request")
def put_normal_value(consul, test_context):
    """Store normal value using HTTP request."""
    response = consul.put_data_using_request(
        test_context["folder_key"],
        test_context["test_value"]
    )
    test_context["response"] = response
    print(f"\n📤 PUT normal value response: {response.status_code}")


@when("I perform CRUD operations successfully")
def perform_crud_operations(consul, test_context):
    """Perform basic CRUD operations to verify cluster health."""
    # Create
    consul.put_data(test_context["test_key"], test_context["test_value"])
    # Read
    value = consul.get_data(test_context["test_key"])
    assert value.decode() == test_context["test_value"]
    # Update
    consul.put_data(test_context["test_key"], test_context["updated_value"])
    value = consul.get_data(test_context["test_key"])
    assert value.decode() == test_context["updated_value"]
    # Delete
    consul.delete_data(test_context["test_key"])
    print("\n✅ CRUD operations completed successfully")


@when("I delete leader pod")
def delete_leader_pod(platform, consul_config, test_context):
    """Delete the current leader pod."""
    leader_ip = test_context["leader_ip"]
    platform.delete_pod_by_pod_ip(leader_ip, consul_config["namespace"])
    print(f"\n🗑️ Deleted leader pod with IP: {leader_ip}")


@when("I wait for leader reelection")
def wait_for_leader_reelection(consul, test_context):
    """Wait for new leader to be elected."""
    max_retries = 10
    retry_interval = 5
    
    for i in range(max_retries):
        try:
            new_leader = consul.get_leader()
            if new_leader and new_leader != test_context["leader_old"]:
                test_context["leader_new"] = new_leader
                print(f"\n✅ New leader elected: {new_leader}")
                return
        except Exception:
            pass
        print(f"\n⏳ Waiting for leader... ({i+1}/{max_retries})")
        time.sleep(retry_interval)
    
    pytest.fail("Leader reelection timeout")


# ============================================================================
# Then Steps
# ============================================================================

@then(parsers.parse("response status code should be {code:d}"))
def response_status_code(test_context, code: int):
    """Verify HTTP response status code."""
    actual = test_context["response"].status_code
    assert actual == code, f"Expected status {code}, got {actual}"


@then("I can read the stored value")
def can_read_stored_value(consul, test_context):
    """Verify value can be read."""
    value = consul.get_data(test_context["folder_key"])
    assert value.decode() == test_context["test_value"]
    print(f"\n📖 Read value: {value.decode()}")


@then("I cleanup the test data")
def cleanup_test_data(consul, test_context):
    """Delete test data."""
    consul.delete_data(test_context["folder_key"])
    print(f"\n🗑️ Cleaned up: {test_context['folder_key']}")


@then("new leader should be elected")
def new_leader_elected(consul, test_context):
    """Verify new leader was elected."""
    peers = consul.get_list_peers()
    is_reelected = consul.is_leader_reelected(
        test_context["leader_new"],
        test_context["leader_old"],
        peers
    )
    assert is_reelected, "New leader was not properly elected"
    print(f"\n✅ Leader reelection confirmed: {test_context['leader_new']}")


@then("CRUD operations should work after failover")
def crud_works_after_failover(consul, test_context):
    """Verify CRUD operations work after failover."""
    # Wait a bit for cluster stabilization
    time.sleep(15)
    
    # Perform CRUD
    consul.put_data(test_context["test_key"], test_context["test_value"])
    value = consul.get_data(test_context["test_key"])
    assert value.decode() == test_context["test_value"]
    consul.delete_data(test_context["test_key"])
    print("\n✅ CRUD operations work after failover")


