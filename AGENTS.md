---
title: "미감 작업 규칙"
status: DRAFT
version: "0.1.0"
last_updated: "2026-08-29"
authoritative_for:
  - "저장소 내 문서·구현 작업의 공통 규칙"
  - "문서 우선순위와 변경·검증 절차"
related_documents:
  - "docs/00-governance/document-policy.md"
  - "docs/00-governance/decision-register.md"
  - "docs/01-product/project-brief.md"
  - "docs/01-product/prd-p0.md"
  - "docs/01-product/domain-rules.md"
  - "docs/05-engineering/system-architecture.md"
  - "docs/05-engineering/security-privacy.md"
  - "docs/05-engineering/api-guidelines.md"
  - "docs/07-execution/implementation-readiness.md"
---

# 미감 작업 규칙

## 문서 우선순위

상위에서 하위 순으로 최신 사용자 결정, Project Brief, P0 PRD, Domain·Data Source 규칙, Data·Recommendation 명세, UX·Engineering 명세, API 계약, Acceptance·Test 문서, 실행 준비도와 승인된 작업 패킷, 코드·주석을 따른다. 같은 주제의 충돌은 해당 영역의 권위 문서와 `docs/00-governance/document-policy.md`를 기준으로 해결한다. 모든 현재 문서는 `DRAFT`이며 구현 승인 권위가 아니다. 구현은 승인된 작업 패킷과 관련 기준을 함께 충족할 때만 시작한다.

## 변경 원칙

- 기능·계약·데이터·개인정보 변경 시 해당 영역의 소유 문서를 먼저 갱신한 뒤 코드와 테스트를 맞춘다.
- 일반 사용자 계정·로그인·서버 익명 프로필·장기 취향 프로필을 만들지 않는다.
- 추천 payload, 정확 좌표, 원문 검색어를 장기 로그·분석·프로필로 보존하지 않는다. 외부 행동 분석 도구를 추가하지 않는다.
- 필수 조건을 자동 완화하지 않으며, 출처·권리·최신성이 불명확한 정보를 사실이나 이미지로 노출하지 않는다.
- Django Admin은 staff 운영자 전용이다. P0 API는 내부 프론트엔드·챗봇 소비용이며 외부 공개 API는 OD-005 전까지 만들지 않는다.
- 데모 모드와 테스트는 외부 API 키 없이 실행되어야 한다.

## 작업·검증 규칙

- 파일 탐색과 텍스트 검색에는 우선 `rg`를 사용한다.
- 파일 변경은 `apply_patch`로 수행한다.
- 변경 범위에 맞는 테스트·린트·빌드·문서 링크 검증을 실행하고, 실행하지 못한 검증은 이유와 함께 보고한다.
- SearchService 뒤에 SQLite FTS5를 두고, Kakao 지도는 MapProvider 뒤에 둔다. OpenAPI를 정본으로 하며 생성 TypeScript와 경계 Zod 어댑터를 사용한다.
- 미확정 사항은 임의 표기로 구현하지 말고 OD-001~OD-007의 해당 결정에 연결한다.
- 후반 결정으로 폐기된 안은 `docs/00-governance/decision-register.md`의 `SUPERSEDED` 항목을 확인하고 다시 도입하지 않는다.

## 사용자 변경 보존

작업 트리에 이미 있는 변경은 사용자의 변경으로 간주한다. 요청 범위와 무관한 파일을 수정·되돌리거나 포맷하지 않는다. 같은 파일을 건드려야 할 때는 기존 변경을 읽고 최소 범위 패치로 보존한다. 충돌을 안전하게 해소할 수 없으면 구현을 멈추고 사용자 지시를 구한다.
