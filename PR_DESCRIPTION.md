## What type of PR is this? (check all applicable)

- [ ] Refactor
- [x] Feature
- [ ] Bug Fix
- [ ] Optimization
- [ ] Documentation Update

## Description

This PR implements S3 integration for ATP Storage in the Consul service, enabling automated upload of integration test results to AWS S3 or S3-compatible storage providers.

### Key Changes

**1. ATP Storage Configuration (`values.yaml`)**
- Added `atpStorage` configuration block with S3 provider settings
- Configurable parameters: `provider`, `serverUrl`, `serverUiUrl`, `bucket`, `region`, `username`, `password`
- Added `atpReportViewUiUrl` and `environmentName` for test result viewing

**2. Integration Test Deployment (`deployment.yaml`)**
- Added environment variables to pass ATP Storage configuration to test runner
- Environment variables: `ATP_STORAGE_PROVIDER`, `ATP_STORAGE_SERVER_URL`, `ATP_STORAGE_SERVER_UI_URL`, `ATP_STORAGE_BUCKET`, `ATP_STORAGE_REGION`, `ATP_STORAGE_USERNAME`, `ATP_STORAGE_PASSWORD`, `ATP_REPORT_VIEW_UI_URL`, `ATP_ENVIRONMENT_NAME`

**3. Dockerfile Security Enhancements**
- Updated base image to `ghcr.io/netcracker/qubership-docker-integration-tests:main` with S3 adapter scripts
- Added permission configuration for AWS EKS security policies (non-root user execution)
- Added comments explaining the necessity of root user switch for S3 integration scripts

**4. S3 Integration Features**
- Real-time test artifact upload using `inotifywait` and `s5cmd`
- Support for multiple S3 providers: `aws`, `minio`, `s3-compatible`
- Automatic organization of test results by environment and timestamp
- Upload includes: Robot Framework results (output.xml, log.html, report.html), screenshots, Allure reports

## Related Tickets & Documents

- Related Issue: PSUPATPOS-63

## QA Instructions, Screenshots, Recordings

### Prerequisites
- AWS EKS cluster with configured S3 access
- S3 bucket created (e.g., `qstp-consul`)
- AWS credentials with S3 write permissions

### Testing Steps
1. Deploy Consul service to AWS EKS using the GitHub Actions workflow
2. Configure ATP Storage parameters in workflow inputs:
   - `atp_storage_provider`: `aws`
   - `atp_storage_server_url`: S3 endpoint URL
   - `atp_storage_bucket`: your S3 bucket name
   - `atp_storage_region`: AWS region (e.g., `us-east-1`)
   - `atp_storage_username`: AWS access key ID
   - `atp_storage_password`: AWS secret access key
3. Run integration tests
4. Verify test results are uploaded to S3 bucket under path: `{bucket}/robot-output/{environment}/{timestamp}/`
5. Check that uploaded artifacts include: `output.xml`, `log.html`, `report.html`, screenshots, Allure reports

### Manual Testing Performed
- Deployed to AWS EKS cluster in `us-east-1` region
- Verified S3 upload functionality with `qstp-consul` bucket
- Confirmed real-time artifact upload during test execution
- Validated test result accessibility via ATP Report View UI

### Breaking Change checklist
- [x] Does it change any deployment parameters, logic of their working or rename them?
  - **Yes**: New ATP Storage parameters added to `values.yaml`. Existing deployments without these parameters will continue to work (tests run without S3 upload).
- [x] Did update from previous version tested with the same set of deployment parameters?
  - **Yes**: Backward compatible - if ATP Storage parameters are not provided, tests execute normally without S3 integration.

## Added/updated tests?

- [ ] Yes
- [x] No, and this is why: This PR adds infrastructure for test result storage. The existing integration tests continue to work as before, with the added capability of uploading results to S3 when configured. Manual testing was performed on AWS EKS to verify the S3 upload functionality.
- [ ] I need help with writing tests
