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
Step definitions for Consul Backup with S3 Storage tests.

These steps test S3 storage integration:
- Backup exists in S3
- Backup removal from S3

Engineers can write feature files using these steps.
"""

import os

import pytest
from pytest_bdd import scenarios, then

# Import all scenarios from the feature file
scenarios("../features/backup_s3.feature")


# ============================================================================
# Constants
# ============================================================================

BACKUP_STORAGE_PATH = "/opt/consul/backup-storage"


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def s3_client():
    """Create S3 client if S3BackupLibrary is available."""
    try:
        from S3BackupLibrary import S3BackupLibrary
        return S3BackupLibrary(
            url=os.environ.get("S3_URL"),
            bucket=os.environ.get("S3_BUCKET"),
            key_id=os.environ.get("S3_KEY_ID"),
            key_secret=os.environ.get("S3_KEY_SECRET"),
            ssl_verify=False
        )
    except ImportError:
        pytest.skip("S3BackupLibrary not available")


# ============================================================================
# Then Steps
# ============================================================================

@then("backup should exist in S3 storage")
def backup_exists_in_s3(s3_client, test_context):
    """Verify backup exists in S3 storage."""
    backup_id = test_context["backup_id"]
    exists = s3_client.check_backup_exists(
        path=BACKUP_STORAGE_PATH,
        backup_id=backup_id
    )
    assert exists, f"Backup {backup_id} not found in S3"
    print(f"\n✅ Backup exists in S3: {backup_id}")


@then("granular backup should exist in S3 storage")
def granular_backup_exists_in_s3(s3_client, test_context):
    """Verify granular backup exists in S3 storage."""
    backup_id = test_context["backup_id"]
    exists = s3_client.check_backup_exists(
        path=f"{BACKUP_STORAGE_PATH}/granular",
        backup_id=backup_id
    )
    assert exists, f"Granular backup {backup_id} not found in S3"
    print(f"\n✅ Granular backup exists in S3: {backup_id}")


@then("backup should be removed from S3 storage")
def backup_removed_from_s3(s3_client, test_context):
    """Verify backup was removed from S3 storage."""
    backup_id = test_context["backup_id"]
    exists = s3_client.check_backup_exists(
        path=BACKUP_STORAGE_PATH,
        backup_id=backup_id
    )
    assert not exists, f"Backup {backup_id} still exists in S3"
    print(f"\n✅ Backup removed from S3: {backup_id}")


@then("granular backup should be removed from S3 storage")
def granular_backup_removed_from_s3(s3_client, test_context):
    """Verify granular backup was removed from S3 storage."""
    backup_id = test_context["backup_id"]
    exists = s3_client.check_backup_exists(
        path=f"{BACKUP_STORAGE_PATH}/granular",
        backup_id=backup_id
    )
    assert not exists, f"Granular backup {backup_id} still exists in S3"
    print(f"\n✅ Granular backup removed from S3: {backup_id}")


