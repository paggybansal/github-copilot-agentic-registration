"""Selenium UI test fixtures (T11).

Starts the Flask application on a free local port with a temporary SQLite
database, waits for readiness, and yields a headless Chrome WebDriver to
UI tests. If Chrome or a compatible driver is unavailable in the current
environment, the ``driver`` fixture skips with an explicit reason rather
than crashing the whole suite.

Per the ``python-test-standards`` skill, the fixture: starts the Flask app
with a temporary database, waits until the server is ready, starts the
browser, yields control, quits the browser, stops the Flask server, and
removes temporary resources (the ``tmp_path_factory``-managed database
directory is cleaned up automatically by pytest).
"""

from __future__ import annotations

import socket
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Iterator
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from werkzeug.serving import BaseWSGIServer, make_server

from registration_app.app import create_app
from registration_app.config import TestConfig

SCREENSHOT_DIR = Path(__file__).resolve().parent.parent.parent / "screenshots"
READINESS_TIMEOUT_SECONDS = 10.0
READINESS_POLL_INTERVAL_SECONDS = 0.05


def _free_port() -> int:
    """Return a free local TCP port for the test Flask server to bind to."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_until_ready(url: str, timeout: float) -> None:
    """Poll ``url`` until it responds or raise once ``timeout`` elapses."""
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1):  # noqa: S310
                return
        except (urllib.error.URLError, ConnectionError) as exc:
            last_error = exc
            time.sleep(READINESS_POLL_INTERVAL_SECONDS)
    message = f"Flask UI test server did not become ready at {url}"
    raise RuntimeError(message) from last_error


@pytest.fixture(scope="module")
def live_server(tmp_path_factory: pytest.TempPathFactory) -> Iterator[str]:
    """Start the registration app with a temporary database on a free port."""
    db_path = tmp_path_factory.mktemp("ui-db") / "registration.db"

    class UiTestConfig(TestConfig):
        DATABASE_PATH = str(db_path)

    app = create_app(config_class=UiTestConfig)
    port = _free_port()
    server: BaseWSGIServer = make_server("127.0.0.1", port, app)

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    base_url = f"http://127.0.0.1:{port}"
    try:
        _wait_until_ready(f"{base_url}/register", READINESS_TIMEOUT_SECONDS)
        yield base_url
    finally:
        server.shutdown()
        thread.join(timeout=5)


@pytest.fixture
def driver() -> Iterator[webdriver.Chrome]:
    """Yield a headless Chrome WebDriver, skipping if unavailable."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,1024")

    try:
        chrome_driver = webdriver.Chrome(options=options)
    except WebDriverException as exc:
        pytest.skip(f"Chrome/ChromeDriver unavailable in this environment: {exc}")

    try:
        yield chrome_driver
    finally:
        chrome_driver.quit()


@pytest.fixture(autouse=True)
def _save_screenshot_on_failure(request: pytest.FixtureRequest):
    """Save a screenshot (never containing password values) on test failure."""
    yield
    report = getattr(request.node, "rep_call", None)
    if report is None or not report.failed:
        return
    driver_fixture = request.node.funcargs.get("driver")
    if driver_fixture is None:
        return
    SCREENSHOT_DIR.mkdir(exist_ok=True)
    safe_name = request.node.name.replace("/", "_").replace("::", "_")
    driver_fixture.save_screenshot(str(SCREENSHOT_DIR / f"{safe_name}.png"))


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    """Expose the test outcome to fixtures via ``item.rep_<when>`` attributes."""
    outcome = yield
    report = outcome.get_result()
    if call.when == "call":
        item.rep_call = report
