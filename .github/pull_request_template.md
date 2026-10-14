## Summary
<!-- Two or three sentences describing what was built and why. -->

## Changes Made
<!-- Every file or component added or modified, with the reason. -->

## Test Evidence
<!-- pytest, coverage, Selenium, lint, audit and CI evidence. -->

## Known Limitations
<!-- Deferred findings, environmental limits and out-of-scope behavior. -->

## Reviewer Checklist

- [ ] Correctness matches the approved requirements
- [ ] Passwords are hashed and never displayed or logged
- [ ] SQL statements are parameterized
- [ ] Submitted HTML or JavaScript cannot execute
- [ ] CSRF protection is enabled for the real UI
- [ ] Duplicate email is handled case-insensitively
- [ ] Validation and database failures are safe
- [ ] Happy paths and negative paths are tested
- [ ] Selenium registration flow passes
- [ ] Coverage meets the approved target
- [ ] Ruff passes
- [ ] Dependency audit reviewed
- [ ] All SDLC artifacts are present
- [ ] No secrets or local database files are committed