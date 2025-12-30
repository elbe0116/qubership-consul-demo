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

@backup @s3_storage
Feature: Consul Backup with S3 Storage
    As an engineer
    I want to verify backup to S3 storage
    So that I can ensure offsite backup works correctly

    Background:
        Given Consul cluster is available
        And backup daemon is available
        And S3 storage is configured
        And I have unique test key and value

    @backup @full_backup @full_backup_s3
    Scenario: Full backup and restore on S3 storage
        Given test data exists in Consul
        When I perform full backup
        Then backup should complete successfully
        And backup should exist in S3 storage
        When I delete test data from Consul
        And I restore from backup
        Then restore should complete successfully
        And test data should be recovered
        When I evict backup by ID
        Then backup should be removed from S3 storage

    @backup @granular_backup @granular_backup_s3
    Scenario: Granular backup and restore on S3 storage
        Given test data exists in Consul
        When I perform granular backup
        Then backup should complete successfully
        And granular backup should exist in S3 storage
        When I delete test data from Consul
        And I restore from backup
        Then restore should complete successfully
        And test data should be recovered
        When I evict backup by ID
        Then granular backup should be removed from S3 storage


