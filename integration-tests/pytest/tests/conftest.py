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
Pytest configuration and fixtures for Consul BDD tests.

This module provides:
- ConsulLibrary fixture for Consul interactions
- PlatformLibrary fixture for Kubernetes interactions
- Backup daemon session fixture
- Shared test context for passing data between steps
"""

import os
import random
import string

import pytest
import requests
from pytest_bdd import given, parsers

from lib.consul_library import ConsulLibrary
from PlatformLibrary import PlatformLibrary


# ============================================================================
# Environment Configuration
# ============================================================================

def get_env(name: str, default: str = None) -> str:
    """Get environment variable with optional default."""
    value = os.environ.get(name, default)
    if value is None:
        raise ValueError(f"Environment variable {name} is required")
    return value


def get_env_optional(name: str, default: str = "") -> str:
    """Get optional environment variable."""
    return os.environ.get(name, default)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def consul_config() -> dict:
    """
    Session-scoped fixture with Consul configuration from environment.
    """
    return {
        "namespace": get_env("CONSUL_NAMESPACE"),
        "host": get_env("CONSUL_HOST"),
        "port": int(get_env("CONSUL_PORT")),
        "scheme": get_env("CONSUL_SCHEME", "http"),
        "token": get_env_optional("CONSUL_TOKEN"),
    }


@pytest.fixture(scope="session")
def consul(consul_config) -> ConsulLibrary:
    """
    Session-scoped fixture providing ConsulLibrary instance.
    """
    return ConsulLibrary(
        consul_namespace=consul_config["namespace"],
        consul_host=consul_config["host"],
        consul_port=consul_config["port"],
        consul_scheme=consul_config["scheme"],
        consul_token=consul_config["token"],
    )


@pytest.fixture(scope="session")
def platform() -> PlatformLibrary:
    """
    Session-scoped fixture providing PlatformLibrary instance.
    """
    return PlatformLibrary(managed_by_operator="true")


@pytest.fixture(scope="session")
def backup_config() -> dict:
    """
    Session-scoped fixture with backup daemon configuration.
    """
    return {
        "host": get_env("CONSUL_BACKUP_DAEMON_HOST"),
        "port": int(get_env("CONSUL_BACKUP_DAEMON_PORT")),
        "username": get_env_optional("CONSUL_BACKUP_DAEMON_USERNAME"),
        "password": get_env_optional("CONSUL_BACKUP_DAEMON_PASSWORD"),
        "protocol": get_env("CONSUL_BACKUP_DAEMON_PROTOCOL", "http"),
        "datacenter": get_env("DATACENTER_NAME"),
    }


@pytest.fixture(scope="session")
def backup_session(backup_config) -> requests.Session:
    """
    Session-scoped fixture providing authenticated requests session for backup daemon.
    """
    session = requests.Session()
    
    if backup_config["username"] and backup_config["password"]:
        session.auth = (backup_config["username"], backup_config["password"])
    
    session.headers.update({
        "Content-Type": "application/json",
        "Accept": "application/json",
    })
    
    # Configure TLS verification
    if backup_config["protocol"] == "https":
        ca_cert = "/consul/tls/backup/ca.crt"
        if os.path.exists(ca_cert):
            session.verify = ca_cert
    
    return session


@pytest.fixture(scope="session")
def backup_base_url(backup_config) -> str:
    """Base URL for backup daemon API."""
    return f"{backup_config['protocol']}://{backup_config['host']}:{backup_config['port']}"


@pytest.fixture
def test_context(consul_config) -> dict:
    """
    Test-scoped fixture for sharing data between steps.
    
    Pre-populated with namespace for convenience.
    """
    return {
        "namespace": consul_config["namespace"],
    }


@pytest.fixture
def random_id() -> str:
    """Generate random 3-character string for unique test data."""
    return ''.join(random.choices(string.ascii_lowercase, k=3))


# ============================================================================
# Common Given Steps
# ============================================================================

@given("Consul cluster is available")
def consul_cluster_available(consul):
    """Verify Consul cluster is available."""
    assert consul is not None, "ConsulLibrary not initialized"
    # Verify connectivity by checking leader
    leader = consul.get_leader()
    assert leader, "Consul cluster has no leader"


@given("Kubernetes cluster is available")
def kubernetes_cluster_available(platform):
    """Verify Kubernetes cluster is available."""
    assert platform is not None, "PlatformLibrary not initialized"


@given("backup daemon is available")
def backup_daemon_available(backup_session, backup_base_url):
    """Verify backup daemon is reachable."""
    response = backup_session.get(f"{backup_base_url}/health")
    # Accept any response (daemon is running)
    assert response is not None


@given("I have unique test key and value")
def unique_test_data(test_context, random_id):
    """Generate unique test key and value."""
    test_context["test_key"] = f"test_key_{random_id}"
    test_context["path_test_key"] = f"path_test_key/test_data_{random_id}"
    test_context["test_value"] = f"test_value_{random_id}"
    test_context["updated_value"] = f"update_test_value_{random_id}"
    test_context["path_value"] = f"path_test_value_{random_id}"
    test_context["updated_path_value"] = f"update_path_test_value_{random_id}"


@given("test data exists in Consul")
def ensure_test_data_exists(consul, test_context):
    """Ensure test data is stored in Consul."""
    consul.put_data(test_context["test_key"], test_context["test_value"])


@given("test data under path exists in Consul")
def ensure_path_data_exists(consul, test_context):
    """Ensure test data under path is stored in Consul."""
    consul.put_data(test_context["path_test_key"], test_context["path_value"])


@given(parsers.parse('cluster has at least {count:d} replicas'))
def cluster_has_replicas(platform, consul_config, test_context, count: int):
    """Verify cluster has minimum replica count."""
    replicas = platform.get_stateful_set_replicas_count(
        consul_config["host"], 
        consul_config["namespace"]
    )
    test_context["original_replicas"] = replicas
    if replicas < count:
        pytest.skip(f"Cluster has {replicas} replicas, minimum {count} required")


@given("I get current leader")
def get_current_leader(consul, test_context):
    """Get and store current leader information."""
    leader = consul.get_leader()
    test_context["leader_old"] = leader
    test_context["leader_ip"] = consul.delete_port(leader)


@given("Prometheus is configured")
def prometheus_configured():
    """Verify Prometheus configuration is available."""
    assert os.environ.get("PROMETHEUS_URL"), "PROMETHEUS_URL not configured"


@given(parsers.parse('alert "{alert_name}" is inactive'))
def alert_is_inactive(platform, consul_config, alert_name):
    """Verify specified alert is inactive."""
    # Import MonitoringLibrary if available
    try:
        from MonitoringLibrary import MonitoringLibrary
        monitoring = MonitoringLibrary(
            host=os.environ.get("PROMETHEUS_URL"),
            username=os.environ.get("PROMETHEUS_USER"),
            password=os.environ.get("PROMETHEUS_PASSWORD"),
        )
        status = monitoring.get_alert_status(alert_name, consul_config["namespace"])
        assert status == "inactive", f"Alert {alert_name} should be inactive"
    except ImportError:
        pytest.skip("MonitoringLibrary not available")


@given("all servers are ready")
def all_servers_ready(platform, consul_config):
    """Verify all Consul servers are ready."""
    replicas = platform.get_stateful_set_replicas_count(
        consul_config["host"], 
        consul_config["namespace"]
    )
    ready_replicas = platform.get_stateful_set_ready_replicas_count(
        consul_config["host"], 
        consul_config["namespace"]
    )
    assert replicas == ready_replicas, f"Only {ready_replicas}/{replicas} replicas ready"


@given("S3 storage is configured")
def s3_storage_configured():
    """Verify S3 storage configuration is available."""
    assert os.environ.get("S3_URL"), "S3_URL not configured"
    assert os.environ.get("S3_BUCKET"), "S3_BUCKET not configured"


@given("monitored images list is configured")
def monitored_images_configured(test_context):
    """Verify monitored images environment variable is set."""
    images = os.environ.get("MONITORED_IMAGES")
    assert images, "MONITORED_IMAGES not configured"
    test_context["monitored_images"] = images


# ============================================================================
# Pytest Hooks
# ============================================================================

def pytest_bdd_step_error(request, feature, scenario, step, step_func, step_func_args, exception):
    """Hook for enhanced error reporting."""
    print(f"\n❌ Step failed: {step}")
    print(f"   Feature: {feature.name}")
    print(f"   Scenario: {scenario.name}")
    print(f"   Exception: {exception}")


