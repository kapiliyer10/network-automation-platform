from typing import Any


def summarize_results(
    results: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    """Summarize per-device validation results."""

    summary = {}

    for device_name, device_results in results.items():
        drift_results = [
            result
            for result in device_results
            if result["status"] == "DRIFT"
        ]

        summary[device_name] = {
            "status": "DRIFT" if drift_results else "PASS",
            "total": len(device_results),
            "passed": sum(
                result["status"] == "PASS"
                for result in device_results
            ),
            "drifted": len(drift_results),
        }

    overall_status = (
        "DRIFT"
        if any(
            device["status"] == "DRIFT"
            for device in summary.values()
        )
        else "PASS"
    )

    return {
        "devices": summary,
        "overall_status": overall_status,
    }
