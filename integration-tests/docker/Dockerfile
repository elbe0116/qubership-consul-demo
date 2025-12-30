FROM ghcr.io/elbe0116/qubership-docker-integration-tests:PSUPATPOS-63

# Test output directory
ENV PYTEST_OUTPUT=/opt/pytest/output \
    PYTEST_HOME=/opt/pytest \
    SERVICE_CHECKER_SCRIPT=/opt/pytest/consul_pods_checker.py

# Custom resource status configuration
ENV STATUS_CUSTOM_RESOURCE_GROUP=apps
ENV STATUS_CUSTOM_RESOURCE_VERSION=v1
ENV STATUS_CUSTOM_RESOURCE_PLURAL=deployments
ENV STATUS_CUSTOM_RESOURCE_NAME=consul-integration-tests-runner

# Create directories
RUN mkdir -p ${PYTEST_OUTPUT} ${PYTEST_HOME}

WORKDIR ${PYTEST_HOME}

# Copy requirements and install dependencies
COPY integration-tests/docker/requirements.txt ${PYTEST_HOME}/requirements.txt
COPY integration-tests/docker/consul_pods_checker.py ${PYTEST_HOME}/consul_pods_checker.py

RUN set -x \
    && pip3 install -r ${PYTEST_HOME}/requirements.txt \
    && rm -rf /var/cache/apk/*

# Copy pytest tests
COPY integration-tests/pytest/pytest.ini ${PYTEST_HOME}/pytest.ini
COPY integration-tests/pytest/tests ${PYTEST_HOME}/tests

# Copy test data from robot (for HA tests)
COPY integration-tests/robot/tests/consul/ha/extremely_big_value.txt ${PYTEST_HOME}/tests/data/extremely_big_value.txt

# Upgrade all tools to avoid vulnerabilities
RUN set -x && apk add --update --no-cache apk-tools && apk upgrade --no-cache --available

USER 1000:0

EXPOSE 8080
VOLUME ["${PYTEST_OUTPUT}"]

# Default command - run pytest with Allure reporting
CMD ["pytest", "--tb=short", "-v", "--alluredir=/opt/pytest/output/allure-results"]
