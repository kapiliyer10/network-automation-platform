from src.reporting import summarize_results


def test_summarize_results():
    results = {
        "R1": [
            {"status": "PASS"},
            {"status": "PASS"},
        ],
        "R2": [
            {"status": "PASS"},
            {"status": "DRIFT"},
        ],
    }

    summary = summarize_results(results)

    assert summary == {
        "devices": {
            "R1": {
                "status": "PASS",
                "total": 2,
                "passed": 2,
                "drifted": 0,
            },
            "R2": {
                "status": "DRIFT",
                "total": 2,
                "passed": 1,
                "drifted": 1,
            },
        },
        "overall_status": "DRIFT",
    }
