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

@consul_images
Feature: Consul Image Verification
    As an engineer
    I want to verify deployed images match expected versions
    So that I can ensure correct versions are deployed

    Background:
        Given Kubernetes cluster is available
        And monitored images list is configured

    @consul_images
    Scenario: Verify hardcoded images match deployed versions
        When I check each monitored resource image
        Then all image tags should match expected versions

