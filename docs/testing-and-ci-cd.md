# Testing and CI/CD

## 1. Test Strategy

The project uses pytest for application-level tests and live network-integration tests.

Run application / non-integration tests:

```bash
pytest -q --ignore=tests/integration
```

Run live integration tests:

```bash
pytest -q tests/integration
```

Run the complete suite:

```bash
pytest -q
```

The integration tests use the Containerlab SR Linux environment and validate live NETCONF behavior, including configuration round trips.

Documented coverage areas include:

- Inventory loading
- Docker endpoint resolution
- gNMI client operations
- Device state discovery
- Desired-state loading and validation
- State comparison and drift detection
- CLI configuration rendering
- NETCONF configuration rendering and application
- Workflow execution and reporting
- FastAPI endpoints

## 2. Latest Verified Test Result

The latest verified local full-suite run recorded during this update was:

```text
102 passed in 96.56s
```

This run was executed with Containerlab `0.75.0` and includes the Docker resolver unit tests and live-container checks against R1, R2, and R3. An earlier Docker-hosted validation run recorded `100 passed in 87.47s`.

The CI workflow is now pinned to Containerlab `0.83.0`; its result remains to be verified by GitHub Actions.

Test counts and duration can change as code, dependencies, and the lab environment evolve. These are recorded results, not guarantees for every future run.

## 3. GitHub Actions Workflow

The workflow is:

```text
.github/workflows/ci.yml
```

It runs on pushes to `main` and pull requests targeting `main`.

The pipeline performs these steps:

1. Check out the repository.
2. Install Containerlab.
3. Prepare the expected repository path for the lab scripts.
4. Set up Python 3.12 and install requirements.
5. Start the Containerlab network.
6. Wait for OSPF convergence.
7. Run `python -m compileall src scripts` as a Python compile check.
8. Run non-integration pytest tests and write JUnit XML results.
9. Run live integration pytest tests and write JUnit XML results.
10. Build the Docker image.
11. Stop the network lab even when earlier steps fail.
12. Upload the JUnit XML files as workflow artifacts.

The OSPF readiness step is intended to prevent live integration tests from starting before the expected routing neighbors reach the Full state.

## 4. Result Artifacts

The workflow uploads:

```text
test-results.xml
integration-test-results.xml
```

These are JUnit XML result files. The workflow shown in the current repository does not itself publish an HTML test report.
