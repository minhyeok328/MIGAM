# Immersive Home and Discovery Route Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Follow superpowers:test-driven-development for every behavior change and superpowers:verification-before-completion before reporting success.

**Goal:** Replace the combined editorial/discovery screen with a quiet, full-screen MIGAM brand home at `/` and move the existing search/recommendation experience intact to `/discover`, using an original six-scene local film and rights-safe poster fallbacks.

**Architecture:** `App` performs a small pathname dispatch for the two fixed routes and an accessible not-found page; no router dependency or client-side history state is introduced. `HomePage` owns only local decorative media and links, while `DiscoveryPage` alone is wrapped in the existing query/Zustand providers. A link to `/discover#recommend` may select the recommendation tab, but no search term, filters, recommendation payload, or taste state leaves memory.

**Tech Stack:** React 19, TypeScript 5.9, Vite 8, Tailwind CSS 4, Radix Tabs/Dialog, Zustand, TanStack Query, Lucide React, Vitest, Testing Library, local WebP/MP4/WebM assets.

**Spec:** `docs/superpowers/specs/2026-09-04-immersive-home-discovery-split-design.md`

## Global Constraints

- Work directly on `main` as required by this repository; do not create a branch or worktree.
- Preserve all current in-scope uncommitted work and do not commit unless the user separately requests it.
- Update the authoritative UX, acceptance, traceability, task-packet, index, and frontend documentation before production code.
- Do not add a router, analytics, remote font, third-party runtime, new API, account, profile, browser persistence, or URL-encoded user input.
- Keep the existing discovery request, retry, stale-response, pagination, required-condition, media-rights, and text-fallback contracts unchanged.
- Treat every new home asset as decorative fictional brand imagery, never as an exhibition record or recommendation evidence.
- Keep exactly one `main` and one `h1` per route, a working skip link, visible focus, semantic links and controls, and a poster-only reduced-motion experience.
- Keep the superseded brown v1 sources and derivatives on disk, but remove every runtime reference to them.

---

### Task 1: Align the approved implementation contract

**Files:**
- Modify: `docs/07-execution/task-packets/TP-006-frontend-discovery.md`
- Modify: `docs/00-index.md`
- Modify: `docs/04-ux/screen-spec.md`
- Modify: `docs/06-quality/acceptance-criteria.md`
- Modify: `docs/06-quality/traceability-matrix.md`
- Modify: `frontend/README.md`
- Create or modify: `docs/04-ux/assets/home/README.md`

**Interfaces:**
- Consumes: approved split-route design and existing TP-006 discovery contract.
- Produces: an approved TP-006 revision defining `/`, `/discover`, `/discover#recommend`, local decorative media, accessibility fallbacks, and unchanged discovery data boundaries.

- [x] **Step 1: Rewrite TP-006 as the split-route task packet**

Raise it to `2.0.0`. Specify that `/` makes no API calls and contains the local film, statement, three visual chapters, and links; specify that `/discover` owns all existing discovery state and API behavior. Record the fixed non-sensitive `#recommend` exception and exclude actual taste tests, detail pages, and user persistence.

- [x] **Step 2: Synchronize the UX and quality documents**

Update the screen spec, acceptance criteria, and traceability rows so the route, accessible fallback, and API-zero home behavior are testable. Mark recommendations rendered on home as deferred rather than inventing home data.

- [x] **Step 3: Update the index, asset provenance, and local run guide**

Describe both routes, the six original fictional scenes, source/derivative locations, generated-image prompts, and the fact that v1 assets are retained but superseded.

- [x] **Step 4: Validate the documentation diff**

Run: `git diff --check -- docs/00-index.md docs/04-ux/screen-spec.md docs/06-quality/acceptance-criteria.md docs/06-quality/traceability-matrix.md docs/07-execution/task-packets/TP-006-frontend-discovery.md frontend/README.md docs/04-ux/assets/home/README.md`

Expected: exit 0 with no whitespace errors.

### Task 2: Create and verify the new home media

**Files:**
- Create: `docs/04-ux/assets/home/v2/source/migam-film-01-morning-gallery-source.png`
- Create: `docs/04-ux/assets/home/v2/source/migam-film-02-textile-walk-source.png`
- Create: `docs/04-ux/assets/home/v2/source/migam-film-03-material-study-source.png`
- Create: `docs/04-ux/assets/home/v2/source/migam-film-04-paused-gaze-source.png`
- Create: `docs/04-ux/assets/home/v2/source/migam-film-05-glass-corridor-source.png`
- Create: `docs/04-ux/assets/home/v2/source/migam-film-06-afterglow-source.png`
- Create: `frontend/public/assets/home/film/migam-film-01-morning-gallery-1920.webp`
- Create: `frontend/public/assets/home/film/migam-film-02-textile-walk-1920.webp`
- Create: `frontend/public/assets/home/film/migam-film-03-material-study-1920.webp`
- Create: `frontend/public/assets/home/film/migam-film-04-paused-gaze-1920.webp`
- Create: `frontend/public/assets/home/film/migam-film-05-glass-corridor-1920.webp`
- Create: `frontend/public/assets/home/film/migam-film-06-afterglow-1920.webp`
- Create: `frontend/public/assets/home/film/migam-home-poster-1920.webp`
- Create: `frontend/public/assets/home/film/migam-home-poster-960.webp`
- Create: `frontend/public/assets/home/film/migam-home-film-v1.mp4`
- Create: `frontend/public/assets/home/film/migam-home-film-v1.webm`

**Interfaces:**
- Consumes: six `photorealistic-natural` prompts sharing the approved warm-ivory, charcoal, limestone, muted blue-gray, pale-earth art direction.
- Produces: 16:9 stills, responsive poster derivatives, and an approximately 10–12 second silent loop with soft dissolves and 2–4% camera movement.

- [x] **Step 1: Generate six independent original scenes**

Use the built-in image generation tool once per scene. Require fictional back-view or small-scale visitors where applicable; prohibit real artworks, institutions, brands, readable signage, logos, watermarks, neon color, and advertising gloss.

- [x] **Step 2: Inspect every source before using it**

Open all six images at original detail. Reject and regenerate any frame with readable text, recognizable branding, anatomy defects, contradictory architecture, or color outside the approved subdued palette.

- [x] **Step 3: Produce 16:9 web derivatives**

Crop and resize each approved source to 1920×1080 WebP without stretching. Produce 1920×1080 and 960×540 versions of the first frame as the persistent poster.

- [x] **Step 4: Encode the silent loop**

Use a one-time local encoder outside runtime dependencies. Hold each frame for roughly two seconds, alternate subtle push/pan motion, and cross-dissolve for approximately 0.2 seconds. Encode H.264 MP4 with fast start and VP9 WebM when supported.

- [x] **Step 5: Verify media properties**

Inspect codecs, 1920×1080 dimensions, duration, lack of audio, and file sizes. Re-encode if the visual output is broken or unnecessarily large; keep the poster usable even if WebM is unavailable.

### Task 3: Lock route ownership and privacy behavior with failing tests

**Files:**
- Modify: `frontend/src/app/App.test.tsx`

**Interfaces:**
- Consumes: `App`, browser pathname/hash, real providers, and existing API fixtures.
- Produces: route-level tests that fail if the home mounts discovery, links point to the wrong destination, route semantics duplicate landmarks, or discovery behavior regresses.

- [x] **Step 1: Add a route-aware render helper**

Set `window.history` to a literal route before rendering and reset it after each test. Existing search and recommendation tests must render `/discover` explicitly.

- [x] **Step 2: Add the home ownership test**

Assert that `/` has exactly one `main` and `h1`, includes links with `href="/discover"` and `href="/discover#recommend"`, excludes the discovery tabs/searchbox, and performs zero API requests.

- [x] **Step 3: Add discovery and not-found route tests**

Assert that `/discover` includes its page `h1`, tabs and search form but no film home hero; an unknown pathname exposes links back to both valid routes.

- [x] **Step 4: Add the fragment initialization test**

Render `/discover#recommend`, assert the recommendation tab is selected, and confirm no search/filter/payload values were written to URL query, history state, localStorage, or sessionStorage.

- [x] **Step 5: Verify RED**

Run: `npm test -- src/app/App.test.tsx`

Expected: FAIL for the new route-specific assertions because `App` still renders the combined page.

### Task 4: Implement the minimal route boundary and separated discovery page

**Files:**
- Modify: `frontend/src/app/App.tsx`
- Modify: `frontend/src/app/providers.tsx`
- Modify: `frontend/src/app/SiteShell.tsx`
- Modify: `frontend/src/features/discovery/store.ts`
- Modify: `frontend/src/pages/DiscoveryPage.tsx`
- Create: `frontend/src/pages/HomePage.tsx`
- Create: `frontend/src/pages/NotFoundPage.tsx`

**Interfaces:**
- Produces: `createDiscoveryStore(initialTab?: 'search' | 'recommend')`, `Providers({ initialTab?, ... })`, `SiteShell({ currentPage, tone, demo?, children })`, and pathname dispatch in `App`.

- [x] **Step 1: Add the route dispatcher**

Map the normalized pathname `/` to `HomePage`, `/discover` to a provider-wrapped `DiscoveryPage`, and everything else to `NotFoundPage`. Use normal anchor navigation and do not add `pushState` listeners.

- [x] **Step 2: Initialize only the allowed tab fragment**

Pass `recommend` to the discovery store only when `window.location.hash === '#recommend'`; default to `search` for every other fragment.

- [x] **Step 3: Strip home presentation from discovery**

Give `DiscoveryPage` its own `main#main-content` and one descriptive `h1`. Keep the existing panels, data calls, cards, error states, and CTA behavior unchanged.

- [x] **Step 4: Verify GREEN**

Run: `npm test -- src/app/App.test.tsx`

Expected: all route and prior discovery tests pass except tests intentionally reserved for the unimplemented film behavior.

### Task 5: Specify and implement the accessible film boundary

**Files:**
- Modify: `frontend/src/app/App.test.tsx`
- Create: `frontend/src/features/home/HomeFilm.tsx`
- Modify: `frontend/src/pages/HomePage.tsx`

**Interfaces:**
- Produces: `HomeFilm()` rendering a decorative poster at all times and video only when `prefers-reduced-motion: reduce` is false.

- [x] **Step 1: Write the normal-motion failing test**

Assert a decorative video with `autoPlay`, `muted`, `loop`, `playsInline`, `preload="metadata"`, a WebM source, an MP4 source, and the approved poster path.

- [x] **Step 2: Write the reduced-motion failing test**

Stub `matchMedia('(prefers-reduced-motion: reduce)')` as matching, then assert no `video` exists while the decorative poster remains.

- [x] **Step 3: Verify RED**

Run: `npm test -- src/app/App.test.tsx`

Expected: FAIL because the film component does not exist.

- [x] **Step 4: Implement the film and HTML message layer**

Keep media `aria-hidden`, poster alternative text empty, and all meaningful `美感`, slogan, and CTA copy in HTML above the media. Do not use media playback events to reveal essential content.

- [x] **Step 5: Verify GREEN**

Run: `npm test -- src/app/App.test.tsx`

Expected: the film and all route tests pass.

### Task 6: Build the three visual chapters and quiet responsive system

**Files:**
- Delete: `frontend/src/features/home/HomeHero.tsx`
- Modify: `frontend/src/features/home/EditorialStatement.tsx`
- Create: `frontend/src/features/home/VisualChapters.tsx`
- Create: `frontend/src/features/home/HomeEntryCta.tsx`
- Modify: `frontend/src/pages/HomePage.tsx`
- Modify: `frontend/src/app/styles/home.css`
- Modify: `frontend/src/app/styles/shell.css`
- Modify: `frontend/src/app/styles/discovery.css`
- Modify: `frontend/src/app/styles/motion.css`

**Interfaces:**
- Consumes: approved local scene stills and existing shell/card styles.
- Produces: full-screen film, large statement, three full-width chapters, two route CTAs, soft-ink home chrome, paper discovery chrome, mobile poster priority, and no runtime references to v1 media.

- [x] **Step 1: Recompose the home in the approved order**

Render `film → statement → 공간의 온도 → 머무는 시선 → 재료의 감각 → entry CTA`. Use empty image alternatives because adjacent HTML carries the brand concept and no factual artwork is represented.

- [x] **Step 2: Replace the old color and card-like visual language**

Use warm ivory, ink/charcoal, limestone, muted blue-gray, and pale earth. Keep corners restrained, avoid pill decoration, and let the scene images and large Korean serif statements set the rhythm.

- [x] **Step 3: Implement desktop and mobile behavior**

At wide viewports, use near-full-bleed 16:9 chapters with alternating text alignment and generous vertical pauses. At narrow viewports, render the poster first, preserve text/CTA order, avoid horizontal overflow, and keep controls at least 44px high.

- [x] **Step 4: Keep motion optional and restrained**

Allow only existing short reveal/hover transitions outside the film. Under reduced motion, remove non-essential transitions and transforms as well as the video element.

- [x] **Step 5: Run the focused regression suite**

Run: `npm test -- src/app/App.test.tsx src/features/discovery/forms.test.ts src/shared/api/client.test.ts`

Expected: all selected tests pass with no warnings or unhandled requests.

### Task 7: Complete build, contract, and browser verification

**Files:**
- Verify: all modified documentation, frontend code, tests, and media assets.

**Interfaces:**
- Consumes: completed implementation.
- Produces: fresh automated and visual evidence for both routes and all fallbacks.

- [x] **Step 1: Run all frontend tests**

Run: `npm test`

Expected: every test passes.

- [x] **Step 2: Run build and repository checks**

Run: `npm run build`, `npm run api:check`, `npm run format:check`, and `git diff --check`.

Expected: each command exits 0.

- [x] **Step 3: Inspect media metadata**

Confirm both video dimensions and duration, confirm no audio stream, and record final file sizes. If WebM could not be produced, confirm MP4 plus poster fallback and document the limitation.

- [x] **Step 4: Inspect both routes in the browser**

At 1440px and 390px, check `/` and `/discover` for one `main`/`h1`, readable crops, header contrast, keyboard focus, responsive stacking, and horizontal overflow. Open `/discover` directly and verify `/discover#recommend` selects the recommendation tab.

- [x] **Step 5: Inspect failure and motion fallbacks**

Verify reduced-motion renders no video, a failed video leaves the poster visible, and the home causes zero `/api/` requests.

- [x] **Step 6: Record evidence and review the final diff**

Update TP-006 and the acceptance/traceability evidence fields with commands that actually passed, then run `git status --short`. Report any verification that could not be performed and its residual risk.
