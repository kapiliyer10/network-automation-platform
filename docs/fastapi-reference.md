# FastAPI Reference

## 1. Application

The FastAPI application is implemented in:

```text
src/api/main.py
```

Start it from the repository root:

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

FastAPI's interactive API documentation is available at `/docs` while the application is running.

## 2. Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/` | API root; returns an informational message |
| `GET` | `/devices` | List devices from inventory |
| `GET` | `/devices/{id}` | Retrieve a specific device |
| `GET` | `/devices/{id}/state` | Retrieve normalized device state |
| `POST` | `/devices/{id}/validate` | Validate a device against desired state |
| `POST` | `/devices/{id}/configure` | Reconcile a device with desired state |
| `GET` | `/drift` | Validate all devices and summarize drift |

## 3. Example Requests

```bash
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8000/devices
curl http://127.0.0.1:8000/devices/R1/state
curl -X POST http://127.0.0.1:8000/devices/R1/validate
curl -X POST http://127.0.0.1:8000/devices/R1/configure
curl http://127.0.0.1:8000/drift
```

## 4. Configuration Endpoint Behavior

The current `/devices/{id}/configure` endpoint performs desired-state reconciliation. It does not accept arbitrary user-supplied configuration in the request body.

The API delegates to the existing Python workflow and configuration modules rather than implementing a separate network-configuration path inside the API layer.
