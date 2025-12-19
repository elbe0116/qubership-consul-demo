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

@ha
Feature: Consul High Availability
    As an engineer
    I want to verify Consul cluster resilience
    So that I can ensure the system survives failures

    Background:
        Given Consul cluster is available
        And I have unique test key and value

    @ha @exceeding_limit_size
    Scenario: Reject value exceeding size limit
        Given I have extremely large value from file
        When I try to put large value using HTTP request
        Then response status code should be 413
        When I put normal value using HTTP request
        Then response status code should be 200
        And I can read the stored value
        And I cleanup the test data

    @ha @leader_node_deleted
    Scenario: Cluster survives leader deletion
        Given cluster has at least 3 replicas
        And I get current leader
        When I perform CRUD operations successfully
        And I delete leader pod
        And I wait for leader reelection
        Then new leader should be elected
        And CRUD operations should work after failover

