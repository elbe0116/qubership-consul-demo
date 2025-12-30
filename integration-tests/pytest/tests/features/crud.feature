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

@crud
Feature: Consul Key-Value Store CRUD Operations
    As an engineer
    I want to verify Consul KV store operations
    So that I can ensure data storage works correctly

    Background:
        Given Consul cluster is available
        And I have unique test key and value

    @smoke @crud
    Scenario: Add data to Consul
        When I add test data to Consul
        Then data should be stored successfully

    @smoke @crud
    Scenario: Read data from Consul
        Given test data exists in Consul
        When I read test data from Consul
        Then data should match expected value

    @smoke @crud
    Scenario: Update data in Consul
        Given test data exists in Consul
        When I update test data with new value
        And I read test data from Consul
        Then data should match updated value

    @smoke @crud
    Scenario: Delete data from Consul
        Given test data exists in Consul
        When I delete test data from Consul
        Then data should be deleted successfully

    @smoke @crud
    Scenario: Create key under path
        When I add test data under path to Consul
        Then data under path should be stored successfully

    @smoke @crud
    Scenario: Read data under path
        Given test data under path exists in Consul
        When I read test data under path from Consul
        Then data under path should match expected value

    @smoke @crud
    Scenario: Update data under path
        Given test data under path exists in Consul
        When I update test data under path with new value
        And I read test data under path from Consul
        Then data under path should match updated value

    @smoke @crud
    Scenario: Delete data under path
        Given test data under path exists in Consul
        When I delete test data under path from Consul
        Then data under path should be deleted successfully


