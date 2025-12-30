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
Step definitions for Consul Prometheus Alerts tests.

These steps test monitoring alerts:
- ConsulDoesNotExist
- ConsulIsDegraded
- ConsulIsDown

Engineers can write feature files using these steps.
"""

import os
import time

import pytest
from pytest_bdd import scenarios, given, when, then, parsers

# Import all scenarios from the feature file
scenarios("../features/alerts.feature")


# ============================================================================
# Constants
# ============================================================================

ALERT_RETRY_TIME = 300  # 5 minutes
ALERT_RETRY_INTERVAL = 1  # seconds


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def monitoring():
    """Create MonitoringLibrary if available."""
    try:
        from MonitoringLibrary import MonitoringLibrary
        return MonitoringLibrary(
            host=os.environ.get("PROMETHEUS_URL"),
            username=os.environ.get("PROMETHEUS_USER"),
            password=os.environ.get("PROMETHEUS_PASSWORD"),
        )
    except ImportError:
        pytest.skip("MonitoringLibrary not available")


# ============================================================================
# When Steps
# ============================================================================

@when("I scale statefulset to 0 replicas")
def scale_to_zero(platform, consul_config, test_context):
    """Scale Consul StatefulSet to 0 replicas."""
    platform.set_replicas_for_stateful_set(
        consul_config["host"],
        consul_config["namespace"],
        replicas=0
    )
    print(f"\n⬇️ Scaled StatefulSet to 0 replicas")


@when("I scale statefulset back to original replicas")
def scale_back(platform, consul_config, test_context):
    """Scale Consul StatefulSet back to original replicas."""
    original = test_context.get("original_replicas", 3)
    platform.set_replicas_for_stateful_set(
        consul_config["host"],
        consul_config["namespace"],
        replicas=original
    )
    print(f"\n⬆️ Scaled StatefulSet back to {original} replicas")


@when("I delete leader pod")
def delete_leader(platform, consul, consul_config, test_context):
    """Delete the current leader pod."""
    leader = consul.get_leader()
    leader_ip = consul.delete_port(leader)
    platform.delete_pod_by_pod_ip(leader_ip, consul_config["namespace"])
    print(f"\n🗑️ Deleted leader pod: {leader_ip}")


@when("I delete all server pods")
def delete_all_pods(platform, consul, consul_config):
    """Delete all Consul server pods."""
    server_ips = consul.get_server_ips_list()
    for ip in server_ips:
        platform.delete_pod_by_pod_ip(ip, consul_config["namespace"])
        print(f"\n🗑️ Deleted server pod: {ip}")


# ============================================================================
# Then Steps
# ============================================================================

@then(parsers.parse('alert "{alert_name}" should become pending'))
def alert_becomes_pending(monitoring, consul_config, alert_name):
    """Wait for alert to become pending."""
    _wait_for_alert_status(monitoring, alert_name, consul_config["namespace"], "pending")
    print(f"\n⚠️ Alert {alert_name} is pending")


@then(parsers.parse('alert "{alert_name}" should become inactive'))
def alert_becomes_inactive(monitoring, consul_config, alert_name):
    """Wait for alert to become inactive."""
    _wait_for_alert_status(monitoring, alert_name, consul_config["namespace"], "inactive")
    print(f"\n✅ Alert {alert_name} is inactive")


@then(parsers.parse('alert "{alert_name}" should eventually become inactive'))
def alert_eventually_inactive(monitoring, consul_config, alert_name, consul):
    """Wait for alert to eventually become inactive (with leader check)."""
    # Also wait for leader to be available
    _wait_for_leader(consul)
    _wait_for_alert_status(monitoring, alert_name, consul_config["namespace"], "inactive")
    print(f"\n✅ Alert {alert_name} is inactive")


# ============================================================================
# Helper Functions
# ============================================================================

def _wait_for_alert_status(monitoring, alert_name, namespace, expected_status):
    """Wait for alert to reach expected status."""
    start_time = time.time()
    while time.time() - start_time < ALERT_RETRY_TIME:
        try:
            status = monitoring.get_alert_status(alert_name, namespace)
            if status == expected_status:
                return
        except Exception:
            pass
        time.sleep(ALERT_RETRY_INTERVAL)
    pytest.fail(f"Alert {alert_name} did not reach {expected_status} status in {ALERT_RETRY_TIME}s")


def _wait_for_leader(consul):
    """Wait for leader to be available."""
    start_time = time.time()
    while time.time() - start_time < ALERT_RETRY_TIME:
        if consul.check_leader_using_request():
            return
        time.sleep(ALERT_RETRY_INTERVAL)
    pytest.fail(f"Leader not available after {ALERT_RETRY_TIME}s")


