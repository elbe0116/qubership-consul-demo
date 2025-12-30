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

@backup
Feature: Consul Backup and Restore
    As an engineer
    I want to verify backup and restore functionality
    So that I can ensure data recovery works correctly

    Background:
        Given Consul cluster is available
        And backup daemon is available
        And I have unique test key and value

    @backup @full_backup
    Scenario: Full backup and restore
        Given test data exists in Consul
        When I perform full backup
        Then backup should complete successfully
        When I delete test data from Consul
        And I restore from backup
        Then restore should complete successfully
        And test data should be recovered

    @backup @granular_backup
    Scenario: Granular backup and restore
        Given test data exists in Consul
        When I perform granular backup
        Then backup should complete successfully
        And backup should be marked as granular
        When I delete test data from Consul
        And I restore from backup
        Then restore should complete successfully
        And test data should be recovered

    @backup @backup_eviction
    Scenario: Evict backup by ID
        When I perform full backup
        Then backup should complete successfully
        When I evict backup by ID
        Then backup should be removed from list

    @backup @unauthorized_access
    Scenario: Unauthorized access is rejected
        Given unauthorized backup session
        When I try to create backup without auth
        Then response status code should be 401


