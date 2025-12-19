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

@alerts
Feature: Consul Prometheus Alerts
    As an engineer
    I want to verify Prometheus alerts work correctly
    So that I can ensure monitoring detects issues

    Background:
        Given Consul cluster is available
        And Prometheus is configured

    @alerts @consul_does_not_exist_alert
    Scenario: ConsulDoesNotExist alert triggers when cluster is down
        Given alert "ConsulDoesNotExistAlarm" is inactive
        And cluster has at least 3 replicas
        When I scale statefulset to 0 replicas
        Then alert "ConsulDoesNotExistAlarm" should become pending
        When I scale statefulset back to original replicas
        Then alert "ConsulDoesNotExistAlarm" should become inactive

    @alerts @consul_is_degraded_alert
    Scenario: ConsulIsDegraded alert triggers when leader is deleted
        Given alert "ConsulIsDegradedAlarm" is inactive
        And all servers are ready
        When I delete leader pod
        Then alert "ConsulIsDegradedAlarm" should become pending
        And alert "ConsulIsDegradedAlarm" should eventually become inactive

    @alerts @consul_is_down_alert
    Scenario: ConsulIsDown alert triggers when all pods are deleted
        Given alert "ConsulIsDownAlarm" is inactive
        And all servers are ready
        When I delete all server pods
        Then alert "ConsulIsDownAlarm" should become pending
        And alert "ConsulIsDownAlarm" should eventually become inactive

