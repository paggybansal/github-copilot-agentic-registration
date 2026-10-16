# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Repository scaffold for REG-1.
- Local user-story input replacing JIRA.
- Repository-wide GitHub Copilot instructions.
- REG-1 User Registration feature: `GET`/`POST /register` and `GET /register/success`
  routes, Full Name/Email/Password/Confirm Password form with CSRF protection
  (Flask-WTF), server-side validation and normalization, Werkzeug password hashing,
  and a SQLite-backed user repository enforcing case-insensitive email uniqueness.
- Unit, integration, security edge-case, performance (`@pytest.mark.performance`) and
  Selenium UI (`@pytest.mark.ui`) test suites for the registration feature.
- A dedicated `browser-tests` CI job (`.github/workflows/ci.yml`) that runs the headless
  Chrome Selenium UI tests on `ubuntu-latest` and uploads failure screenshots as a build
  artifact.

### Changed

- `README.md` updated with quick-start, testing and CI documentation for the completed
  registration feature.

### Security

- Passwords are hashed with Werkzeug's `generate_password_hash`/`check_password_hash`
  and are never logged, displayed, or stored in plain text.
- All SQL statements use parameterized queries; email uniqueness is enforced both at the
  application level and via a SQLite `UNIQUE` constraint.
- CSRF protection (Flask-WTF) is required on every registration POST request in the real
  application configuration.