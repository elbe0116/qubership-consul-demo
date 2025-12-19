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
Step definitions for Consul Image Verification tests.

These steps verify deployed container images match expected versions:
- Parse MONITORED_IMAGES environment variable
- Compare expected vs actual image tags

Engineers can write feature files using these steps.
"""

import os

import pytest
from pytest_bdd import scenarios, when, then

# Import all scenarios from the feature file
scenarios("../features/images.feature")


# ============================================================================
# Helper Functions
# ============================================================================

def get_image_tag(image: str) -> str:
    """
    Extract tag from image string.
    
    Args:
        image: Full image path (e.g., "registry/image:tag")
        
    Returns:
        Tag portion of image string
    """
    parts = image.split(":")
    if len(parts) > 1:
        # Handle registry:port/image:tag format
        return parts[-1]
    raise ValueError(f"Image has no tag: {image}")


# ============================================================================
# When Steps
# ============================================================================

@when("I check each monitored resource image")
def check_monitored_images(platform, consul_config, test_context):
    """
    Check each resource in MONITORED_IMAGES and compare tags.
    
    MONITORED_IMAGES format: "type name container_name expected_image,..."
    """
    monitored = test_context["monitored_images"].rstrip(",")
    resources = monitored.split(",")
    
    results = []
    for resource in resources:
        parts = resource.strip().split()
        if len(parts) != 4:
            print(f"\n⚠️ Invalid resource format: {resource}")
            continue
            
        resource_type, name, container_name, expected_image = parts
        
        try:
            actual_image = platform.get_resource_image(
                resource_type,
                name,
                consul_config["namespace"],
                container_name
            )
            
            expected_tag = get_image_tag(expected_image)
            actual_tag = get_image_tag(actual_image)
            
            results.append({
                "resource": f"{resource_type}/{name}",
                "container": container_name,
                "expected_tag": expected_tag,
                "actual_tag": actual_tag,
                "match": expected_tag == actual_tag
            })
            
            print(f"\n[COMPARE] {name}: Expected={expected_tag}, Actual={actual_tag}")
            
        except Exception as e:
            results.append({
                "resource": f"{resource_type}/{name}",
                "container": container_name,
                "error": str(e),
                "match": False
            })
            print(f"\n[ERROR] {name}: {e}")
    
    test_context["image_results"] = results


# ============================================================================
# Then Steps
# ============================================================================

@then("all image tags should match expected versions")
def all_images_match(test_context):
    """Verify all image tags match expected versions."""
    results = test_context.get("image_results", [])
    
    if not results:
        pytest.fail("No images were checked")
    
    mismatches = [r for r in results if not r.get("match")]
    
    if mismatches:
        error_msg = "Image tag mismatches:\n"
        for m in mismatches:
            if "error" in m:
                error_msg += f"  - {m['resource']}: {m['error']}\n"
            else:
                error_msg += f"  - {m['resource']}: expected {m['expected_tag']}, got {m['actual_tag']}\n"
        pytest.fail(error_msg)
    
    print(f"\n✅ All {len(results)} images match expected versions")

