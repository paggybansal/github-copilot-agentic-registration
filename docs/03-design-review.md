# Design Review — REG-1 User Registration

| Field | Value |
|---|---|
| Artifact | Design Review |
| SDLC Step | 3. Design Review |
| Source | `docs/01-requirements.md` (Approved), `docs/02-architecture.md` (Approved, Revision 1 applied) |
| Author Role | Design Reviewer (Copilot agent) |
| Commit | Pending before commit |
| Date | 2026-10-16 |
| Status | Approved with conditions |

## 1. Review Scope

An adversarial pre-code review of `docs/02-architecture.md` against `docs/01-requirements.md`,
using the ten required lenses: requirement coverage, password/secret handling, SQL injection
and database integrity, duplicate-email race conditions, CSRF protection, XSS and output
escaping, validation bypass and maximum input lengths, transaction rollback, testability
without external dependencies, and simplicity/unnecessary complexity. No production code was
written during this review.

## 2. Requirement-Coverage Matrix

| Requirement ID | Architecture component(s) | Coverage |
|---|---|---|
| FR-1 | Registration route, Templates | Covered |
| FR-2 | Registration route, Repository | Covered |
| FR-3 | Password hashing | Covered |
| FR-4 | Registration route, Templates | Covered |
| FR-5 | Validation, Registration route | Covered |
| FR-6 | Registration route | Covered |
| FR-7 | Validation | Covered |
| FR-8 | Validation | Covered |
| FR-9 | Validation | Covered |
| FR-10 | Repository | Covered (strengthened by DR-2) |
| FR-11 | Repository, Database lifecycle | Covered (strengthened by DR-2) |
| FR-12 | Validation | Covered |
| FR-13 | Validation | Covered (narrowed by DR-4) |
| FR-14 | Validation, Configuration | Covered (strengthened by DR-6) |
| FR-15 | Forms, Application factory, Templates | Covered (strengthened by DR-3) |
| FR-16 | Templates | Covered |
| NFR-1 | Application factory, Configuration | Covered |
| NFR-2 | Password hashing, Registration route, Configuration | Covered (strengthened by DR-1) |
| NFR-3 | Templates | Covered |
| NFR-4 | Registration route | Covered |
| NFR-5 | All components | Covered (strengthened by DR-5) |
| NFR-6 | Database lifecycle, test architecture | Covered |
| NFR-7 | Database lifecycle | Covered |
| NFR-8 | Test architecture | Covered |

No `Gap` or `Partial` entries remain after the corrections in Section 5.

## 3. Ranked Findings

| ID | Severity | Area | Finding | Evidence | Risk | Recommendation | Decision | Rationale |
|---|---|---|---|---|---|---|---|---|
| DR-1 | High | Password and secret handling | The original architecture deferred "logging format/destination" entirely (Section 12) without constraining *what* may be logged, and did not require `DEBUG=False`. A default Flask debug error page or an unconstrained exception log statement (e.g. `logging.exception(e)` on a `ValueError` raised with the raw form dict) could expose the submitted password or traceback to a response or log file. | `docs/02-architecture.md` (pre-correction) Section 12, Open Design Questions: "Logging format/destination ... is deferred to implementation." | A DB or validation exception could leak a plain-text password or internal path through a traceback page or log line, violating NFR-2 and SEC-6. | Require `DEBUG=False` in every non-test configuration; require that application-level exception handling log only the exception class name and a static safe message, never raw form data, exception args, the submitted password, or the CSRF token. | Accepted | This is a concrete, testable control (not a vague "be careful") and directly closes a gap the architecture itself flagged as unresolved. |
| DR-2 | High | Duplicate-email race conditions | `sqlite3.IntegrityError` is a subclass of `sqlite3.Error`. The original Section 6/9 wording said `repository.py` "catches `sqlite3.Error`" for the generic-failure path without specifying catch order relative to the uniqueness-constraint violation described separately in Section 6's "Email uniqueness" row. If implemented with a single broad `except sqlite3.Error`, a concurrent duplicate-insert race (two requests passing `email_exists()` simultaneously) would surface the generic "could not be completed" message instead of "An account with this email already exists" for the losing request, contradicting the architecture's own stated intent and FR-10. | `docs/02-architecture.md` (pre-correction) Section 6 ("a `sqlite3.IntegrityError` ... is caught ... and converted to duplicate-email outcome") vs. Section 9 EC-14 row ("caught `sqlite3.Error`") — the two sections did not establish a consistent except-clause order. | Under concurrent requests for the same email, the loser could receive a confusing generic database-failure message instead of the correct, already-specified duplicate-email message. | Specify explicitly that `repository.create_user()` must catch `sqlite3.IntegrityError` **before** the broader `sqlite3.Error`, routing it to the duplicate-email outcome; only a non-`IntegrityError` `sqlite3.Error` rolls back and raises `RepositoryError`. | Accepted | Exception-hierarchy ordering is a precise, code-level correction that removes the ambiguity without weakening any requirement. |
| DR-3 | High | CSRF protection | The architecture specified `CSRFProtect` and a `RegistrationForm` carrying a CSRF token, but the Templates component's responsibility list did not require the template to actually render the hidden CSRF field inside the `<form>` element. | `docs/02-architecture.md` (pre-correction) Component table, "Templates and static assets" row — listed rendering the form and escaping, but not the CSRF hidden field. | If `register.html` is implemented without `{{ form.hidden_tag() }}` / `{{ form.csrf_token }}`, every legitimate POST (including AC2's successful-registration path) would be rejected by `CSRFProtect`, a functional regression discovered only at integration-test time. | Add an explicit requirement to the Templates component and Section 6 security design that `register.html` must render the CSRF hidden field inside the form. | Accepted | Closes a concrete implementation gap that would otherwise break FR-15 and AC2 silently until tested. |
| DR-4 | Low | Validation bypass / scope control | The architecture's open design questions (pre-correction) stated full-name validation would reject Unicode categories `Cc` **and** `Cf` ("format characters"), but `docs/01-requirements.md` FR-13 only specifies rejecting "Unicode control characters" (category `Cc`). Adding `Cf` silently broadens validation behavior beyond what the human approved in Clarification 3, without an explicit decision record. | `docs/01-requirements.md` FR-13; `docs/02-architecture.md` (pre-correction) Section 12. | A legitimate full name containing a format character (e.g. a zero-width joiner used in some scripts) could be rejected by an unapproved rule, risking an unintended accessibility/internationalization regression that was explicitly called out as a concern in Clarification 3. | Narrow the architecture to reject only category `Cc`, exactly matching FR-13; do not add `Cf` without an explicit human decision. | Accepted | Governance rule: "Do not weaken a requirement" cuts both ways — the architecture must also not silently broaden one without approval. |
| DR-5 | Medium | Testability without external dependencies | The original Repository component description (`email_exists(normalized_email)`, `create_user(...)`) did not state how the module obtains its `sqlite3.Connection`. If implemented by importing and calling `get_db()` internally, repository unit tests (required by the Testing Strategy: "insert, lookup, duplicate constraint, commit, rollback...") would need a full Flask application/request context just to get a connection, adding unnecessary coupling and friction contrary to the "keep SQL access separate from templates and validation" and "small design" constraints. | `docs/02-architecture.md` (pre-correction) Component table, "Repository" row and Section 8. | Increased test setup complexity and tighter coupling between the repository and Flask, working against the 85% coverage target (NFR-5) and the architecture's own simplicity lens. | Change the Repository component signatures to accept an explicit `sqlite3.Connection` parameter (dependency injection) rather than calling `get_db()` internally. | Accepted | Straightforward signature change; makes the module trivially unit-testable against a bare `tmp_path` connection, consistent with NFR-5 and NFR-6. |
| DR-6 | Medium | Validation bypass and maximum input lengths | Length limits (100/254/128 characters) are enforced in `validation.py` only after Flask has fully parsed the request body into memory. The architecture did not configure any request-size ceiling, so an oversized POST body (e.g. several megabytes in a single field) would be fully buffered and parsed before being rejected by the character-count check, an avoidable resource-consumption risk. | `docs/02-architecture.md` (pre-correction) Section 7 ("Validation Strategy") and Configuration component — no `MAX_CONTENT_LENGTH` setting was specified. | A malicious or malformed oversized request could consume more memory/CPU than necessary before being rejected, an unnecessary amplification risk not excluded by any existing control. | Add `MAX_CONTENT_LENGTH` to `config.py` (for example 16 KB, well above the largest legitimate field combination) so Flask rejects oversized bodies with HTTP 413 before parsing reaches `validation.py`. | Accepted | Cheap, standard Flask control; the exact byte value is an implementation detail to confirm in Step 4/5, but the control itself is adopted now. |

Six findings are raised (within the maximum of eight). DR-1 addresses password leakage, DR-2
addresses duplicate registration under concurrent requests, and DR-3 addresses CSRF, satisfying
the three mandatory assessment areas.

## 4. Agreed Design Decisions (ADD-*)

| ID | Decision | Originating finding |
|---|---|---|
| ADD-1 | Production/non-test configuration always sets `DEBUG=False`; application-level error handling logs only exception class name and a static safe message, never raw form data, exception arguments, the submitted password, or the CSRF token. | DR-1 |
| ADD-2 | `repository.create_user()` catches `sqlite3.IntegrityError` before the broader `sqlite3.Error`; an `IntegrityError` on the email unique constraint always produces the duplicate-email outcome, never the generic database-failure message. | DR-2 |
| ADD-3 | `register.html` must render the CSRF hidden field (`{{ form.hidden_tag() }}` or `{{ form.csrf_token }}`) inside the registration `<form>` element. | DR-3 |
| ADD-4 | Full Name validation rejects only Unicode category `Cc` (control characters), exactly matching FR-13; no broader category is excluded without explicit human approval. | DR-4 |
| ADD-5 | `repository.email_exists()` and `repository.create_user()` accept an explicit `sqlite3.Connection` parameter; the repository module never calls `get_db()` internally. | DR-5 |
| ADD-6 | `config.py` sets `MAX_CONTENT_LENGTH` so Flask rejects oversized request bodies before they reach `validation.py`; the exact byte limit is confirmed during implementation. | DR-6 |

## 5. Changes Applied to Architecture

All six accepted corrections (ADD-1–ADD-6) were applied directly to `docs/02-architecture.md`:

- Section 2 (Component table): Configuration row now lists `DEBUG=False` and
  `MAX_CONTENT_LENGTH`; Repository row now specifies explicit `sqlite3.Connection` parameters;
  Templates row now requires the CSRF hidden field.
- Section 6 (Security Design): added "Debug/traceback safety" and "Request-size limiting" rows;
  updated "Database-error safety" row to specify `IntegrityError`-before-`Error` ordering and
  include it under FR-10/EC-12/EC-13 as well as FR-11/EC-14.
- Section 8 (Database and Transaction Lifecycle): updated the exception-handling bullet to the
  `IntegrityError`-then-`Error` order; added a bullet describing connection dependency
  injection into the repository functions.
- Section 9 (Error-Handling Strategy): EC-12/EC-13 row now also credits the `IntegrityError`
  backstop; EC-14 row now explicitly excludes `IntegrityError`.
- Section 12 (Open Design Questions): removed the unapproved `Cf` category extension; replaced
  with an explicit `Cc`-only scope statement referencing this review.
- Section 14 (Revision History): added, recording this review as the trigger for Revision 1.

`docs/02-architecture.md` Status remains `Approved` (Revision 1 applied, no re-approval gate
required for this class of correction since no requirement was weakened).

## 6. Residual Risks

- The exact byte value for `MAX_CONTENT_LENGTH` (ADD-6) is not yet fixed; an implementation
  task must choose and justify a specific value (e.g. 16 KB) against the sum of the approved
  maximum field lengths plus form overhead.
- The practical email-format regex (already an open item in the architecture) is not yet
  written; its exact behavior against edge-case addresses will only be confirmed by the
  required unit tests in Step 5/6.
- The architecture's connection-per-request model is appropriate for this story's expected
  load but is not designed for high-concurrency production traffic; this is accepted as
  out of scope per the story's non-functional expectations.

## 7. Deliberately Unpursued Review Areas

- Accessibility (WCAG) review of the rendered HTML — not an approved requirement for this
  story; not reviewed here.
- Load/stress testing beyond the single-request performance check in NFR-4 — out of scope per
  the approved requirements.
- Cross-browser compatibility beyond the approved "latest stable headless Chrome" — out of
  scope per Clarification 7.
- Deployment/production infrastructure review — explicitly out of scope per the user story.

## 8. Final Outcome

**Approved with conditions.**

Conditions: the implementer (Step 5) must apply ADD-1 through ADD-6 exactly as specified when
writing `config.py`, `repository.py`, `db.py`, and `register.html`, and the code reviewer
(Step 6) must verify each ADD is present in the implementation.

---

**Gate:** Approve step 3 and continue? (yes / changes needed)
