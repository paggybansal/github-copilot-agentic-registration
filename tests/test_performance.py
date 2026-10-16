"""Performance test for GET /register (T10).

Verifies NFR-4: a GET request to ``/register`` returns a complete HTTP
response within 2.0 seconds median, measured over 5 requests via the Flask
test client, after one unmeasured warm-up request.

This measures server-side Flask-test-client response time only -- it does
not measure full browser rendering (DOM parsing, CSS, JS, network latency).
Full-browser timing is out of scope here and is not covered by any
Selenium test in this plan.
"""

from __future__ import annotations

import statistics
import time

import pytest

from registration_app.app import create_app
from registration_app.config import TestConfig

HTTP_OK = 200
MEASURED_REQUEST_COUNT = 5
MEDIAN_DURATION_LIMIT_SECONDS = 2.0


@pytest.fixture
def app(tmp_path):
    db_path = tmp_path / "registration.db"

    class PerfTestConfig(TestConfig):
        DATABASE_PATH = str(db_path)

    return create_app(config_class=PerfTestConfig)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.mark.performance
def test_get_register_median_response_time_under_threshold(client):
    """GET /register responds within a 2.0s median over 5 measured requests.

    One discarded warm-up request excludes import/first-request jitter
    (template compilation, module import caching, etc.) from the
    measurement, per NFR-4 and the approved architecture.
    """
    # Unmeasured warm-up request.
    warmup_response = client.get("/register")
    assert warmup_response.status_code == HTTP_OK

    durations = []
    for _ in range(MEASURED_REQUEST_COUNT):
        start = time.perf_counter()
        response = client.get("/register")
        elapsed = time.perf_counter() - start
        assert response.status_code == HTTP_OK
        durations.append(elapsed)

    median_duration = statistics.median(durations)

    print(f"Measured GET /register durations (s): {durations}")
    print(f"Median GET /register duration (s): {median_duration}")

    assert median_duration < MEDIAN_DURATION_LIMIT_SECONDS
