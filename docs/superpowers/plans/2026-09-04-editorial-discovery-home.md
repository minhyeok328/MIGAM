# Editorial Discovery Home Implementation Plan

> **Superseded on 2026-09-04:** 홈과 탐색을 한 화면에 두는 이 계획은 `2026-09-04-immersive-home-discovery-route.md`로 대체한다.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the approved single discovery screen into an editorial MIGAM landing experience, integrate the three original decorative hero images, and preserve every existing search, recommendation, privacy, media-rights, and accessibility behavior.

**Architecture:** `DiscoveryPage` remains the only page and continues to own the existing Radix tabs and discovery state. A new `SiteShell` isolates global navigation and footer, while home-focused presentation components provide the hero, editorial statement, and closing CTA without duplicating API results. Search uses a compact catalog card and recommendations use an editorial card variant, both sharing the same rights-safe media and text fallback boundary.

**Tech Stack:** React 19, TypeScript 5.9, Vite 8, Tailwind CSS 4, Radix Tabs/Dialog, Lucide React, Vitest, Testing Library.

**Spec:** `docs/07-execution/task-packets/TP-006-frontend-discovery.md` and `docs/04-ux/design-reference.md`

## Global Constraints

- Keep a single discovery screen; do not add routes, detail pages, saved taste profiles, interest actions, comparison, external analytics, web fonts, or new APIs.
- Keep search and recommendation drafts in memory only and preserve all existing request, retry, paging, and stale-response behavior.
- Treat the generated hero files as decorative MIGAM brand imagery: use empty alternative text and never associate them with an exhibition, institution, or factual record.
- Request exhibition media only through the existing `INLINE` presentation contract; preserve `LINK_ONLY`, `HIDDEN`, and image-error text fallbacks.
- Keep one `<main>`, one page `<h1>`, the skip link, visible keyboard focus, semantic controls, and reduced-motion behavior.
- Use the existing warm paper/ink/accent palette and system Serif/Sans fallbacks; do not add a dependency.

---

### Task 1: Record the approved presentation extension

**Files:**
- Modify: `docs/07-execution/task-packets/TP-006-frontend-discovery.md`
- Modify: `docs/00-index.md`

**Interfaces:**
- Consumes: the existing TP-006 search/recommendation contract and the user's approved Houston-inspired editorial direction.
- Produces: an approved, narrow UI-only extension covering the shell, decorative hero media, card variants, and motion limits.

- [x] **Step 1: Amend TP-006 without expanding product behavior**

Add the same-screen editorial prelude, original decorative imagery, catalog/editorial presentation variants, CSS-only entrance motion, and responsive/fallback requirements. Keep home routes, detail APIs, actual taste tests, and unimplemented navigation excluded.

- [x] **Step 2: Update the document index version**

Raise TP-006 to the matching minor version and date in `docs/00-index.md`.

- [x] **Step 3: Validate documentation**

Run: `git diff --check -- docs/07-execution/task-packets/TP-006-frontend-discovery.md docs/00-index.md`

Expected: exit 0 with no whitespace errors.

### Task 2: Lock the new semantic experience with failing tests

**Files:**
- Modify: `frontend/src/app/App.test.tsx`

**Interfaces:**
- Consumes: `App`, the existing test API fixtures, and accessible DOM roles.
- Produces: behavioral coverage for the editorial shell, decorative media, and CTA-to-tab navigation.

- [x] **Step 1: Write the failing hero and shell test**

Add a test that asserts one `h1` named “당신의 감각으로, 전시를 발견하다.”, a navigation landmark, three decorative images with empty `alt`, and the current skip-link target.

- [x] **Step 2: Write the failing CTA navigation test**

Add a test that activates “조건으로 추천받기” from the hero and verifies the recommendation tab is selected without writing URL or browser storage state.

- [x] **Step 3: Verify the tests fail for missing UI**

Run: `npm test -- src/app/App.test.tsx`

Expected: FAIL because the new hero structure and CTA do not exist yet.

### Task 3: Extract the shell and editorial page sections

**Files:**
- Create: `frontend/src/app/SiteShell.tsx`
- Create: `frontend/src/features/home/HomeHero.tsx`
- Create: `frontend/src/features/home/EditorialStatement.tsx`
- Create: `frontend/src/shared/ui/SectionHeader.tsx`
- Modify: `frontend/src/pages/DiscoveryPage.tsx`

**Interfaces:**
- Consumes: `demo`, `state.tab`, and `state.setTab('search' | 'recommend')` from the existing provider.
- Produces: `SiteShell({ children, demo, onNavigate })`, `HomeHero({ onChoose })`, `EditorialStatement()`, and `SectionHeader({ eyebrow, title, aside? })`.

- [x] **Step 1: Implement the minimal semantic components**

Keep the wordmark and functional discovery navigation in `SiteShell`. Render the three generated images inside `<picture>` elements with `alt=""`, fixed dimensions, and no factual caption. Keep CTA copy as real links targeting `#discovery-tools` and switch the existing Radix tab through `onChoose`.

- [x] **Step 2: Recompose `DiscoveryPage`**

Render `SiteShell → HomeHero → EditorialStatement → discovery tabs → closing CTA`. Do not render API result items anywhere outside their existing tab panel.

- [x] **Step 3: Run the focused test**

Run: `npm test -- src/app/App.test.tsx`

Expected: the new tests and all prior discovery-flow tests pass.

### Task 4: Introduce editorial and catalog card variants

**Files:**
- Modify: `frontend/src/entities/ExhibitionCard.tsx`
- Modify: `frontend/src/features/discovery/SearchPanel.tsx`
- Modify: `frontend/src/features/discovery/RecommendationPanel.tsx`
- Modify: `frontend/src/app/App.test.tsx`

**Interfaces:**
- Consumes: unchanged `ExhibitionView`, `InstitutionView`, `media`, lifecycle, verification, and source fields.
- Produces: `ExhibitionCard({ item, index, demo, variant: 'catalog' | 'editorial' })` with a shared image-failure and text-fallback path.

- [x] **Step 1: Write a failing variant test**

Assert that search results use the catalog presentation marker and recommendation results use the editorial presentation marker while both still expose the same heading and source behavior.

- [x] **Step 2: Verify RED**

Run: `npm test -- src/app/App.test.tsx`

Expected: FAIL because cards do not yet expose variants.

- [x] **Step 3: Implement variants without changing data semantics**

Pass `variant="catalog"` from `SearchPanel` and `variant="editorial"` from both recommendation sections. Keep one shared media decision and do not invent metadata or recommendation reasons.

- [x] **Step 4: Verify GREEN**

Run: `npm test -- src/app/App.test.tsx`

Expected: all tests pass.

### Task 5: Split and implement the visual system

**Files:**
- Modify: `frontend/src/app/styles.css`
- Create: `frontend/src/app/styles/foundation.css`
- Create: `frontend/src/app/styles/shell.css`
- Create: `frontend/src/app/styles/home.css`
- Create: `frontend/src/app/styles/discovery.css`
- Create: `frontend/src/app/styles/cards.css`
- Create: `frontend/src/app/styles/motion.css`
- Consume: `frontend/public/assets/home/*.webp`

**Interfaces:**
- Consumes: the component class names and six responsive WebP files.
- Produces: a 1440px editorial layout, paper/ink section themes, asymmetric hero media, dense catalog results, recommendation mosaic rhythm, mobile single-column behavior, and reduced-motion overrides.

- [x] **Step 1: Make `styles.css` an ordered import entry point**

Load Tailwind first, then foundation, shell, home, discovery, cards, and motion styles.

- [x] **Step 2: Move existing rules by responsibility**

Preserve all form, dialog, feedback, card, focus, skip-link, and responsive behavior while relocating the rules. Avoid unrelated selector or copy changes.

- [x] **Step 3: Add the editorial layout and motion**

Use image-only radii of 12–16px, small 8–12px entrance travel, 180–400ms transitions, stable CTA text, and no perpetual animation. At mobile width show only the primary spatial image and keep text/CTA ordering intact.

- [x] **Step 4: Verify CSS compilation and component behavior**

Run: `npm test -- src/app/App.test.tsx && npm run build`

Expected: tests pass and the TypeScript/Vite build exits 0.

### Task 6: Final verification and visual inspection

**Files:**
- Verify: all modified frontend and documentation files

**Interfaces:**
- Consumes: the completed implementation.
- Produces: fresh evidence for behavior, formatting, build integrity, and responsive visual quality.

- [x] **Step 1: Run the directly relevant frontend checks**

Run: `npm test -- src/app/App.test.tsx src/features/discovery/forms.test.ts src/shared/api/client.test.ts`

Expected: all selected tests pass.

- [x] **Step 2: Run repository-required frontend checks**

Run: `npm run build && npm run format:check`

Expected: both commands exit 0.

- [x] **Step 3: Inspect desktop and mobile in the browser**

Run the existing Vite demo, inspect the page at desktop and narrow mobile widths, and verify semantic landmarks, image crops, focus visibility, one-column stacking, overflow, and reduced-motion behavior.

- [x] **Step 4: Check the final diff**

Run: `git diff --check` and `git status --short`.

Expected: no whitespace errors and only the intended docs, frontend code, tests, and generated assets are changed.
