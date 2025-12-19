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
Step definitions for Consul CRUD operations.

These steps test Key-Value store functionality:
- Create (PUT)
- Read (GET)
- Update (PUT with existing key)
- Delete (DELETE)

Engineers can write feature files using these steps.
"""

from pytest_bdd import scenarios, when, then

# Import all scenarios from the feature file
scenarios("../features/crud.feature")


# ============================================================================
# When Steps - Simple Key Operations
# ============================================================================

@when("I add test data to Consul")
def add_test_data(consul, test_context):
    """Add test key-value to Consul."""
    result = consul.put_data(
        test_context["test_key"],
        test_context["test_value"]
    )
    test_context["put_result"] = result
    print(f"\n✅ Added: {test_context['test_key']} = {test_context['test_value']}")


@when("I read test data from Consul")
def read_test_data(consul, test_context):
    """Read test value from Consul."""
    value = consul.get_data(test_context["test_key"])
    test_context["read_value"] = value.decode() if isinstance(value, bytes) else value
    print(f"\n📖 Read: {test_context['test_key']} = {test_context['read_value']}")


@when("I update test data with new value")
def update_test_data(consul, test_context):
    """Update existing key with new value."""
    result = consul.put_data(
        test_context["test_key"],
        test_context["updated_value"]
    )
    test_context["put_result"] = result
    print(f"\n🔄 Updated: {test_context['test_key']} = {test_context['updated_value']}")


@when("I delete test data from Consul")
def delete_test_data(consul, test_context):
    """Delete test key from Consul."""
    result = consul.delete_data(test_context["test_key"])
    test_context["delete_result"] = result
    print(f"\n🗑️ Deleted: {test_context['test_key']}")


# ============================================================================
# When Steps - Path Key Operations
# ============================================================================

@when("I add test data under path to Consul")
def add_path_data(consul, test_context):
    """Add test key-value under path to Consul."""
    result = consul.put_data(
        test_context["path_test_key"],
        test_context["path_value"]
    )
    test_context["put_result"] = result
    print(f"\n✅ Added path: {test_context['path_test_key']} = {test_context['path_value']}")


@when("I read test data under path from Consul")
def read_path_data(consul, test_context):
    """Read test value under path from Consul."""
    value = consul.get_data(test_context["path_test_key"])
    test_context["read_path_value"] = value.decode() if isinstance(value, bytes) else value
    print(f"\n📖 Read path: {test_context['path_test_key']} = {test_context['read_path_value']}")


@when("I update test data under path with new value")
def update_path_data(consul, test_context):
    """Update existing path key with new value."""
    result = consul.put_data(
        test_context["path_test_key"],
        test_context["updated_path_value"]
    )
    test_context["put_result"] = result
    print(f"\n🔄 Updated path: {test_context['path_test_key']} = {test_context['updated_path_value']}")


@when("I delete test data under path from Consul")
def delete_path_data(consul, test_context):
    """Delete test path key from Consul."""
    result = consul.delete_data(test_context["path_test_key"])
    test_context["delete_result"] = result
    print(f"\n🗑️ Deleted path: {test_context['path_test_key']}")


# ============================================================================
# Then Steps - Simple Key Assertions
# ============================================================================

@then("data should be stored successfully")
def data_stored_successfully(test_context):
    """Verify data was stored."""
    assert test_context["put_result"] is True, "Failed to store data"


@then("data should match expected value")
def data_matches_expected(test_context):
    """Verify read value matches expected."""
    assert test_context["read_value"] == test_context["test_value"], \
        f"Expected {test_context['test_value']}, got {test_context['read_value']}"


@then("data should match updated value")
def data_matches_updated(test_context):
    """Verify read value matches updated value."""
    assert test_context["read_value"] == test_context["updated_value"], \
        f"Expected {test_context['updated_value']}, got {test_context['read_value']}"


@then("data should be deleted successfully")
def data_deleted_successfully(test_context):
    """Verify data was deleted."""
    assert test_context["delete_result"] is True, "Failed to delete data"


# ============================================================================
# Then Steps - Path Key Assertions
# ============================================================================

@then("data under path should be stored successfully")
def path_data_stored_successfully(test_context):
    """Verify path data was stored."""
    assert test_context["put_result"] is True, "Failed to store path data"


@then("data under path should match expected value")
def path_data_matches_expected(test_context):
    """Verify read path value matches expected."""
    assert test_context["read_path_value"] == test_context["path_value"], \
        f"Expected {test_context['path_value']}, got {test_context['read_path_value']}"


@then("data under path should match updated value")
def path_data_matches_updated(test_context):
    """Verify read path value matches updated value."""
    assert test_context["read_path_value"] == test_context["updated_path_value"], \
        f"Expected {test_context['updated_path_value']}, got {test_context['read_path_value']}"


@then("data under path should be deleted successfully")
def path_data_deleted_successfully(test_context):
    """Verify path data was deleted."""
    assert test_context["delete_result"] is True, "Failed to delete path data"

