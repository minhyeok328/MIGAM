# TP-005 Explainable Recommendation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a stateless internal recommendation API that preserves every required visit condition, ranks only eligible current/upcoming exhibitions, and returns evidence-backed qualitative reasons without exposing numeric scores.

**Architecture:** `discovery` owns a versioned feature projection and a `RecommendationService` protocol. The ORM service reads canonical `catalog` records in one transaction, resolves visit evidence conservatively, applies hard filters before scoring, reranks deterministically for diversity/exploration, and hands IDs plus traces to a presenter that reloads canonical source/media data. DRF validates a bounded one-request payload and OpenAPI remains the HTTP source of truth.

**Tech Stack:** Python 3.11+, Django 5.2, Django REST Framework 3.18, SQLite, OpenAPI 3.1, Django `TestCase`.

**Spec:** `docs/07-execution/task-packets/TP-005-explainable-recommendation.md`

## Global Constraints

- Work only on `main`; do not create a branch or worktree.
- Do not add an account, server user profile, recommendation-result model, request logging, analytics, external package, API key, `.env`, or network call.
- Candidate admission is `CURRENT | UPCOMING`, `VERIFIED`, `FRESH | STALE`, current official SourceRecord present, and no open SourceConflict.
- Required `UNKNOWN` never passes; accessibility/sensory unknown never enters either result group.
- Numeric scores and percentage-like values never cross the API boundary.
- Every feature reason must correspond to a current evidence-backed assertion and a positive score contribution.
- Artwork, Creator, OperatingSchedule/closure handling, map/location coordinates, generated TypeScript/Zod, and frontend work remain out of scope.
- Use `apply_patch` for changes and test-first RED/GREEN cycles for production behavior.

---

### Task 1: Feature projection model and evidence-safe writer

**Files:**
- Modify: `backend/apps/discovery/models.py`
- Create: `backend/apps/discovery/features.py`
- Create: `backend/apps/discovery/migrations/0002_content_feature_snapshot.py`
- Create: `tests/discovery/test_content_features.py`

**Interfaces:**
- Produces: `ContentFeatureSnapshot(exhibition, schema_version, is_current, created_at)`.
- Produces: `ContentFeatureAssertion(snapshot, axis, value, evidence_kind, source_record, rule_version)`.
- Produces: `FeatureAssertionInput(axis: str, value: str, evidence_kind: str, source_record: SourceRecord, rule_version: str = "")`.
- Produces: `record_content_feature_snapshot(*, exhibition: Exhibition, assertions: Iterable[FeatureAssertionInput], schema_version: str = FEATURE_SCHEMA_VERSION) -> ContentFeatureSnapshot`.

- [x] **Step 1: Write failing model/service tests**

  Add tests proving that a new snapshot becomes the sole current row, the former row remains history, duplicate axis/value assertions are rejected, invalid feature codes are rejected, direct and derived evidence requirements differ, and a SourceRecord from another institution is rejected. The production mutation each test catches is respectively: missing partial uniqueness, destructive overwrite, absent uniqueness/validation, absent evidence-mode validation, or missing institution-boundary validation.

- [x] **Step 2: Run the feature tests and verify RED**

  Run: `uv run --project backend python backend/manage.py test tests.discovery.test_content_features --verbosity 2`

  Expected: import/model failures because the snapshot and writer do not exist.

- [x] **Step 3: Implement the minimal models and writer**

  Use these stable enums:

  ```python
  class Axis(models.TextChoices):
      MEDIA_GROUP = "MEDIA_GROUP", "Media group"
      MEDIA_DETAIL = "MEDIA_DETAIL", "Media detail"
      THEME = "THEME", "Theme"
      MOOD = "MOOD", "Mood"
      EXPERIENCE = "EXPERIENCE", "Experience"
      SPACE_TYPE = "SPACE_TYPE", "Space type"
      EVENT_FORMAT = "EVENT_FORMAT", "Event format"

  class EvidenceKind(models.TextChoices):
      DIRECT = "DIRECT", "Direct"
      DERIVED = "DERIVED", "Derived"
  ```

  Apply `^[A-Z0-9][A-Z0-9_:-]{0,63}$` to `value`. Require SourceRecord for every assertion; require nonblank `rule_version` only for `DERIVED`; reject it for `DIRECT`. In `record_content_feature_snapshot`, lock current snapshots, mark them non-current, create and validate the new snapshot/assertions, and keep the whole transition atomic.

- [x] **Step 4: Create the migration and verify GREEN**

  Run: `uv run --project backend python backend/manage.py makemigrations discovery`

  Run: `uv run --project backend python backend/manage.py test tests.discovery.test_content_features --verbosity 2`

  Expected: all content-feature tests pass.

### Task 2: Conservative visit-evidence resolver

**Files:**
- Create: `backend/apps/discovery/visit_conditions.py`
- Create: `tests/discovery/test_visit_conditions.py`

**Interfaces:**
- Produces: `EvidenceState = CONFIRMED | UNKNOWN | CONFLICT`.
- Produces immutable `ResolvedPrice`, `ResolvedReservation`, `ResolvedDuration`, and `ResolvedThreeStateFact` values.
- Produces: `VisitEvidenceResolver.resolve(exhibition: Exhibition) -> ResolvedVisitEvidence`.
- Consumes the exhibition's current `ExhibitionSourceLink.latest_source_record_id` values and prefetched exhibition/institution-scoped visit rows.

- [x] **Step 1: Write failing resolver tests**

  Isolate adult standard price, reservation, duration, accessibility, and sensory behavior. Prove that current exhibition-source evidence wins over institution fallback, an old exhibition row outside current source links is ignored, equal-priority disagreements become `CONFLICT`, missing/explicit unknown stays `UNKNOWN`, and confirmed negative differs from unknown.

- [x] **Step 2: Run and verify RED**

  Run: `uv run --project backend python backend/manage.py test tests.discovery.test_visit_conditions --verbosity 2`

  Expected: import failure for the resolver.

- [x] **Step 3: Implement the resolver without guessing**

  Resolve each semantic key independently. Prefer exhibition rows whose SourceRecord is one of the exhibition's latest linked records. If none exist, use institution rows at the greatest `verified_at` precedence and retain all rows tied at that timestamp for conflict detection. Collapse equivalent values; two different values at the selected precedence become `CONFLICT`. For price, only `STANDARD + ADULT + is_standard_adult_admission` is eligible and the conservative payable amount is `amount_max` when present, otherwise `amount_min`, with free equal to zero.

- [x] **Step 4: Run and verify GREEN**

  Run: `uv run --project backend python backend/manage.py test tests.discovery.test_visit_conditions --verbosity 2`

  Expected: all resolver tests pass.

### Task 3: Candidate gate and hard filters

**Files:**
- Create: `backend/apps/discovery/recommendation.py`
- Create: `tests/discovery/test_recommendation_service.py`

**Interfaces:**
- Produces request dataclasses `RegionFilter`, `VisitDateRange`, `ReservationPreference`, `DurationPreference`, `FeaturePreference`, and `RecommendationQuery`.
- Produces `RecommendationReason`, `RecommendationHit`, and `RecommendationResult`.
- Produces `RecommendationService(Protocol).recommend(query: RecommendationQuery) -> RecommendationResult`.
- Produces `ORMRecommendationService` and `get_recommendation_service()`.

- [x] **Step 1: Write candidate-gate RED tests**

  Prove that ended/canceled/unknown lifecycle, non-VERIFIED, UNVERIFIED, missing latest source, and open SourceConflict records never appear. Prove FRESH and STALE records can appear, IDs are unique, and an empty eligible pool returns empty tuples without fabricated rows.

- [x] **Step 2: Run and verify RED**

  Run: `uv run --project backend python backend/manage.py test tests.discovery.test_recommendation_service --verbosity 2`

  Expected: import failure because the service does not exist.

- [x] **Step 3: Implement candidate loading and query validation**

  Load canonical exhibitions with `select_related("institution")` and bounded prefetches for latest source links, current feature snapshots/assertions, and visit evidence. Validate limit `1..24`, paired visit dates, ordered dates, region district dependency, nonnegative integer budget, unique bounded lists, legal enums, and duration bounds in the service as a second boundary behind DRF.

- [x] **Step 4: Add hard-filter RED tests**

  Cover exact area/district, inclusive date overlap, adult standard budget at zero/equal/over boundary, required accessibility positive/negative/unknown, avoided sensory negative/positive/unknown, required reservation match/mismatch/unknown, and required duration containment/mismatch/unknown. Name the production branch each test would break.

- [x] **Step 5: Implement hard filtering and verification split**

  Apply all known constraints before scoring. Known mismatch is excluded. Unknown/conflict price/reservation/duration may enter `needs_verification` only when all other hard conditions pass. Unknown/conflict accessibility or sensory is excluded from both arrays.

- [x] **Step 6: Run and verify GREEN**

  Run: `uv run --project backend python backend/manage.py test tests.discovery.test_recommendation_service --verbosity 2`

  Expected: candidate and hard-filter tests pass.

### Task 4: Deterministic scoring, diversity, exploration, and reasons

**Files:**
- Modify: `backend/apps/discovery/recommendation.py`
- Modify: `tests/discovery/test_recommendation_service.py`

**Interfaces:**
- Consumes only current `ContentFeatureAssertion` rows, explicit preferred features, liked exhibition feature snapshots, liked institution IDs, and preferred reservation/duration.
- Produces `algorithm_version = "p0-recommendation-1.0.0"`, qualitative match level, at most three trace-backed reasons, and at most one exploration hit.

- [x] **Step 1: Write scoring/reason RED tests**

  Test cold start FRESH-before-STALE, explicit feature match, ended liked-exhibition feature transfer without recommending the ended exhibition, weak institution interest, preferred reservation/duration match, soft unknown neutrality, stable ID tie-break, same-input reproducibility, and no numeric score field on public hit objects.

- [x] **Step 2: Implement minimal scoring and contribution trace**

  Keep weights and thresholds as module constants. Store internal contributions as axis/value/code/weight, sort them deterministically, map the sum to `VERY_CLOSE | GOOD_MATCH | SOME_MATCH | GENERAL`, and generate text only from positive contributions. Use a factual freshness/visit-condition reason when there is no personal contribution.

- [x] **Step 3: Write diversity/exploration RED tests**

  Build at least seven hard-filter-passing candidates. Prove repeated institutions and primary media are reduced when near-score alternatives exist, a six-item response contains at most one connected exploration hit, the exploration hit shares one user feature and has one novel feature, and no random/filler item appears when no connection exists.

- [x] **Step 4: Implement deterministic reranking**

  Greedily choose the highest `raw_score - institution_repeat_penalty - primary_media_repeat_penalty`, using raw ordering and exhibition ID as tie-breaks. When `limit >= 6`, reserve only the last slot for the highest hard-filter-passing connected-and-novel candidate outside the first five; otherwise omit exploration.

- [x] **Step 5: Run and verify GREEN**

  Run: `uv run --project backend python backend/manage.py test tests.discovery.test_recommendation_service --verbosity 2`

  Expected: all recommendation service tests pass with deterministic order and reasons.

### Task 5: Canonical presenter and internal recommendation API

**Files:**
- Modify: `backend/apps/discovery/presenters.py`
- Create: `backend/apps/discovery/recommendation_presenters.py`
- Create: `backend/apps/discovery/recommendation_views.py`
- Modify: `backend/config/urls.py`
- Create: `tests/discovery/test_recommendation_api.py`

**Interfaces:**
- Refactor `present_exhibitions_by_id(ordered_ids: Iterable[int]) -> list[dict[str, object]]` from the existing private search presenter without changing the search response.
- Produces `present_recommendation_result(result: RecommendationResult) -> dict[str, object]`.
- Produces `InternalRecommendationView.post()` at `/api/internal/v1/recommendations/`.

- [x] **Step 1: Write API RED tests**

  Test minimal `{}` cold-start request, a complete required/preferred request, exact top-level/result keys, default six/max 24, zero-result `200`, invalid enums/date/range/duplicate/oversized lists `400`, and canonical source/media reload. Assert no `score`, percentage, raw payload, forbidden media URL, lifecycle health, or request persistence appears.

- [x] **Step 2: Run and verify RED**

  Run: `uv run --project backend python backend/manage.py test tests.discovery.test_recommendation_api --verbosity 2`

  Expected: route or import failure.

- [x] **Step 3: Implement DRF serializers, view, route, and presenter reuse**

  Keep authentication/permission empty like internal search. Convert nested validated data to immutable query dataclasses. Wrap service execution plus canonical presentation in one `transaction.atomic()` block. Return `INVALID_RECOMMENDATION_REQUEST` with Korean message and field details for serializer/service validation failures.

- [x] **Step 4: Run API and search regression tests**

  Run: `uv run --project backend python backend/manage.py test tests.discovery.test_recommendation_api tests.discovery.test_search_api --verbosity 2`

  Expected: both API suites pass and search JSON remains unchanged.

### Task 6: OpenAPI contract and documentation evidence

**Files:**
- Modify: `openapi/internal-v1.yaml`
- Modify: `tests/discovery/test_openapi_contract.py`
- Modify: `README.md`
- Modify: `docs/00-index.md`
- Modify: `docs/06-quality/acceptance-criteria.md`
- Modify: `docs/06-quality/test-plan.md`
- Modify: `docs/07-execution/implementation-readiness.md`
- Modify: `docs/07-execution/task-packets/TP-005-explainable-recommendation.md`

**Interfaces:**
- OpenAPI operation: `recommendExhibitions`.
- Error codes: existing search codes plus `INVALID_RECOMMENDATION_REQUEST`.
- Response schemas: `RecommendationResponse`, `ExhibitionRecommendation`, `RecommendationReason`, `VerificationCandidate` and nested request schemas.

- [x] **Step 1: Write OpenAPI RED tests**

  Assert the POST path, operation ID, request required shapes and enum/list limits, response required fields, absence of numeric score, and shared canonical exhibition/source/media schema references.

- [x] **Step 2: Run and verify RED**

  Run: `uv run --project backend python backend/manage.py test tests.discovery.test_openapi_contract --verbosity 2`

  Expected: failure because the recommendation path/schemas are absent.

- [x] **Step 3: Extend OpenAPI compatibly and update implementation evidence**

  Bump API info version to `1.1.0`, preserve `/search/`, and add recommendation request/response schemas with `additionalProperties: false`. Update current-state docs to mark TP-005 implemented while retaining Artwork/Creator, OperatingSchedule, frontend, and data-source feature backfill as explicit remaining work.

- [x] **Step 4: Run contract and focused discovery tests**

  Run: `uv run --project backend python backend/manage.py test tests.discovery --verbosity 1`

  Expected: all discovery tests pass.

### Task 7: Final verification and review

**Files:**
- Inspect every changed file and the complete diff; do not modify unrelated files.

- [x] **Step 1: Run proportional full verification**

  Run: `uv run --project backend python backend/manage.py test tests --verbosity 1`

  Run: `uv run --project backend python backend/manage.py makemigrations --check --dry-run`

  Run: `uv run --project backend python backend/manage.py check`

  Run: `uv lock --check --project backend`

  Run: `git diff --check`

- [x] **Step 2: Inspect diff against the independent architecture review**

  Review candidate admission, evidence precedence, all hard-filter unknown branches, reason/contribution consistency, privacy, OpenAPI drift, and search regressions. Fix every Critical/Important finding through a new failing regression test before code changes.

  The completed independent architecture review supplied the checklist; the final implementation diff was reviewed locally because repository rules do not allow assigning additional work to a completed agent or starting a second agent without prior approval.

- [x] **Step 3: Re-run only affected focused tests, then final full verification if code changed**

  Expected: clean output, no migration drift, and all tests passing.

- [x] **Step 4: Apply commit workflow when recording TP-005**

  Inspect every changed file, stage explicit logical groups, inspect cached diffs, and use scoped conventional English commit messages. Do not push TP-005 unless the user authorizes that additional push.
