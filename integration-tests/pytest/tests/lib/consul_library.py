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
Consul Library for pytest-bdd tests.

This module provides Consul client functionality for:
- Key-Value store operations (CRUD)
- Cluster status monitoring
- Leader election checks
- HTTP API interactions

Adapted from Robot Framework ConsulLibrary for pytest-bdd usage.
"""

import os
from typing import List, Optional

import consul
import requests


CA_CERT_PATH = '/consul/tls/ca/tls.crt'


class ConsulLibrary:
    """
    Client library for interacting with Consul cluster.
    
    This library wraps python-consul2 and provides methods for:
    - Key-Value store CRUD operations
    - Cluster health monitoring
    - Leader election and failover testing
    
    Example usage:
        consul_lib = ConsulLibrary(
            consul_namespace="consul",
            consul_host="consul-server",
            consul_port=8500,
            consul_scheme="http"
        )
        consul_lib.put_data("my-key", "my-value")
    """
    
    def __init__(
        self,
        consul_namespace: str,
        consul_host: str,
        consul_port: int,
        consul_scheme: str = "http",
        consul_token: Optional[str] = None
    ):
        """
        Initialize Consul client.
        
        Args:
            consul_namespace: Kubernetes namespace where Consul is deployed
            consul_host: Consul server hostname
            consul_port: Consul server port
            consul_scheme: Protocol (http or https)
            consul_token: ACL token for authentication
        """
        self.consul_namespace = consul_namespace
        self.consul_host = consul_host
        self.consul_port = consul_port
        self.consul_scheme = consul_scheme
        self.consul_token = consul_token
        self.consul_cafile = CA_CERT_PATH if os.path.exists(CA_CERT_PATH) else None
        
        self.connect = consul.Consul(
            self.consul_host,
            self.consul_port,
            token=self.consul_token,
            scheme=consul_scheme,
            verify=self.consul_cafile,
            timeout=10
        )

    # =========================================================================
    # Key-Value Store Operations
    # =========================================================================

    def put_data(self, key: str, value: str) -> bool:
        """
        Store a key-value pair in Consul KV store.
        
        Args:
            key: Key to store
            value: Value to associate with the key
            
        Returns:
            True if successful, False otherwise
        """
        return self.connect.kv.put(key=key, value=value)

    def get_data(self, key: str) -> bytes:
        """
        Retrieve value for a key from Consul KV store.
        
        Args:
            key: Key to retrieve
            
        Returns:
            Value stored under the key
            
        Raises:
            KeyError: If key doesn't exist
        """
        resp = self.connect.kv.get(key=key)
        data = resp[1]
        if data is None:
            raise KeyError(f"Key '{key}' not found in Consul")
        return data['Value']

    def delete_data(self, key: str, recurse: bool = None) -> bool:
        """
        Delete a key (or key prefix) from Consul KV store.
        
        Args:
            key: Key to delete
            recurse: If True, delete all keys under the prefix
            
        Returns:
            True if successful
        """
        return self.connect.kv.delete(key=key, recurse=recurse)

    # =========================================================================
    # Cluster Status Operations
    # =========================================================================

    def get_leader(self) -> str:
        """
        Get the current cluster leader address.
        
        Returns:
            Leader address in format "ip:port"
        """
        return self.connect.status.leader()

    def get_list_peers(self) -> List[str]:
        """
        Get list of all cluster peers (servers).
        
        Returns:
            List of peer addresses
        """
        return self.connect.status.peers()

    def get_server_ips_list(self) -> List[str]:
        """
        Get list of server IPs (without port).
        
        Returns:
            List of server IP addresses
        """
        return [self.delete_port(peer) for peer in self.get_list_peers()]

    @staticmethod
    def delete_port(pod_ip: str) -> str:
        """
        Remove port from address string.
        
        Args:
            pod_ip: Address with port (e.g., "10.0.0.1:8300")
            
        Returns:
            IP address without port
        """
        return pod_ip.replace(":8300", "")

    def is_leader_reelected(
        self, 
        leader_new: str, 
        leader_old: str, 
        pod_list: List[str]
    ) -> bool:
        """
        Check if a new leader was elected after failover.
        
        Args:
            leader_new: New leader address
            leader_old: Previous leader address
            pod_list: List of valid pod addresses
            
        Returns:
            True if new leader was elected from pod list
        """
        for pod in pod_list:
            if pod == leader_new and pod != leader_old:
                return True
        return False

    # =========================================================================
    # HTTP API Operations (for special cases)
    # =========================================================================

    def put_data_using_request(self, key: str, value: str) -> requests.Response:
        """
        Store data using direct HTTP request.
        
        This method is useful for testing edge cases like:
        - Large value handling
        - TLS errors
        - Response code verification
        
        Args:
            key: Key to store
            value: Value to store
            
        Returns:
            HTTP Response object
        """
        url = f'{self.consul_scheme}://{self.consul_host}:{self.consul_port}/v1/kv/{key}'
        headers = {'Authorization': f'Bearer {self.consul_token}'} if self.consul_token else {}
        response = requests.Response()
        
        try:
            response = requests.put(
                url, 
                data=value, 
                headers=headers, 
                verify=self.consul_cafile
            )
        except OSError:
            # Handle SSLEOFError for large PUT requests with TLS
            response.status_code = 413
            
        return response

    def check_leader_using_request(self) -> bool:
        """
        Check if leader is available using direct HTTP request.
        
        Returns:
            True if leader is responding
        """
        url = f'{self.consul_scheme}://{self.consul_host}:{self.consul_port}/v1/status/leader'
        try:
            leader_response = requests.get(url, verify=self.consul_cafile)
            return leader_response.status_code == 200 and str(leader_response.content) != ""
        except Exception:
            return False

