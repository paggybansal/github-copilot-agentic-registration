"""Selenium browser automation tests for the registration flow (T11).

Covers the minimum end-to-end scenario (happy-path registration) and the
recommended additional scenario (mismatched passwords), per the
``python-test-standards`` skill. Both use explicit ``WebDriverWait`` waits
and stable element IDs -- never ``time.sleep``. Passwords are never
printed, logged, or captured in screenshots.
"""

from __future__ import annotations

import uuid

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

EXPLICIT_WAIT_SECONDS = 10

VALID_FULL_NAME = "New User"
VALID_PASSWORD = "Example123"  # noqa: S105
MISMATCHED_PASSWORD = "Different123"  # noqa: S105


def _unique_email() -> str:
    """Return a unique fictional email so UI test runs never collide."""
    return f"ui.user.{uuid.uuid4().hex[:12]}@example.test"


@pytest.mark.ui
def test_register_valid_submission_shows_registration_successful(driver, live_server):
    # Arrange
    driver.get(f"{live_server}/register")
    wait = WebDriverWait(driver, EXPLICIT_WAIT_SECONDS)
    wait.until(ec.visibility_of_element_located((By.ID, "full_name")))
    wait.until(ec.visibility_of_element_located((By.ID, "email")))
    wait.until(ec.visibility_of_element_located((By.ID, "password")))
    wait.until(ec.visibility_of_element_located((By.ID, "confirm_password")))

    # Act
    driver.find_element(By.ID, "full_name").send_keys(VALID_FULL_NAME)
    driver.find_element(By.ID, "email").send_keys(_unique_email())
    driver.find_element(By.ID, "password").send_keys(VALID_PASSWORD)
    driver.find_element(By.ID, "confirm_password").send_keys(VALID_PASSWORD)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    # Assert
    success_heading = wait.until(
        ec.visibility_of_element_located((By.ID, "success-message"))
    )
    assert success_heading.text == "Registration successful"


@pytest.mark.ui
def test_register_mismatched_passwords_shows_error_and_clears_password_fields(
    driver, live_server
):
    # Arrange
    driver.get(f"{live_server}/register")
    wait = WebDriverWait(driver, EXPLICIT_WAIT_SECONDS)
    wait.until(ec.visibility_of_element_located((By.ID, "full_name")))

    # Act
    driver.find_element(By.ID, "full_name").send_keys(VALID_FULL_NAME)
    driver.find_element(By.ID, "email").send_keys(_unique_email())
    driver.find_element(By.ID, "password").send_keys(VALID_PASSWORD)
    driver.find_element(By.ID, "confirm_password").send_keys(MISMATCHED_PASSWORD)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    # Assert
    error_item = wait.until(
        ec.visibility_of_element_located((By.CSS_SELECTOR, "#confirm_password-errors li"))
    )
    assert error_item.text == "Passwords do not match"

    password_field = driver.find_element(By.ID, "password")
    confirm_password_field = driver.find_element(By.ID, "confirm_password")
    assert password_field.get_attribute("value") == ""
    assert confirm_password_field.get_attribute("value") == ""
