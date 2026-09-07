// Generated from openapi/internal-v1.yaml. Do not edit.
export interface paths {
    "/api/internal/v1/search/": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** 전시와 기관 검색 */
        get: operations["searchDiscovery"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/internal/v1/recommendations/": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * 조건과 명시적 취향에 맞는 전시 추천
         * @description exhibition_dates는 전시 기간의 경계 포함 겹침만 판정하며 실제 개관을 보장하지 않습니다. visit_dates는 공식 운영일 근거가 확인된 개관일을 요구합니다. 두 조건을 함께 보내면 교집합 안에 개관일이 있어야 하며 유효하지만 서로 겹치지 않는 기간은 빈 결과를 반환합니다.
         */
        post: operations["recommendExhibitions"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/internal/v1/exhibitions/{id}/": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * 출처와 방문 근거를 포함한 전시 상세
         * @description 검색 적격성 게이트를 통과한 전시만 반환합니다. 운영일은 Asia/Seoul의 오늘부터 종료일까지 해석하며 종료·취소 전시의 방문 가능성을 만들지 않습니다.
         */
        get: operations["getExhibitionDetail"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/internal/v1/institutions/{id}/": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** 기관 정보와 노출 가능한 전시 목록 */
        get: operations["getInstitutionDetail"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/internal/v1/artworks/": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * 작품 메타데이터 목록
         * @description 승인된 실제 작품 Source가 없어 일반 모드는 SOURCE_PENDING과 빈 목록을 반환합니다. 가상 작품은 명시적인 격리 데모 모드에서만 보입니다. 검색어를 저장하지 않으며 이미지 URL을 반환하지 않습니다.
         */
        get: operations["listArtworks"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/internal/v1/artworks/{id}/": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * 작품 근거와 확인된 유사 관계
         * @description 제작자·소장기관의 유사성은 출품 관계가 아닙니다. 공식 출품 관계 모델이 없으므로 exhibition_links는 UNCONFIRMED와 빈 배열입니다. 일반 모드의 미승인 데이터와 데모 행은 모두 404입니다.
         */
        get: operations["getArtworkDetail"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        ArtworkListResponse: {
            total: number;
            page: number;
            page_size: number;
            has_more: boolean;
            /** @enum {string} */
            availability: "DEMO" | "SOURCE_PENDING";
            results: components["schemas"]["ArtworkResult"][];
        };
        ArtworkResult: {
            /** @enum {string} */
            type: "ARTWORK";
            id: number;
            source_artwork_id: string;
            title: string;
            creator: components["schemas"]["ArtworkCreator"];
            production_year: string;
            medium: string;
            collection_institution: components["schemas"]["InstitutionReference"];
            cultural_context: components["schemas"]["ArtworkCulture"];
            /** Format: uri */
            official_url: string;
            /** Format: date-time */
            last_verified_at: string;
            /** @enum {string} */
            eligibility: "VERIFIED" | "DEMO";
            is_demo: boolean;
            source: components["schemas"]["SourceEvidence"];
            media: components["schemas"]["ArtworkHiddenMedia"];
            features: components["schemas"]["DetailFeature"][];
        };
        ArtworkCreator: {
            name: string;
            official_id: string | null;
            /** @enum {string} */
            state: "KNOWN" | "UNKNOWN";
        } & unknown;
        ArtworkCulture: {
            /** @enum {string} */
            state: "CONFIRMED" | "UNKNOWN";
            value: string | null;
            is_korean: boolean | null;
        } & unknown;
        ArtworkHiddenMedia: {
            /** @enum {string} */
            status: "HIDDEN";
            media_url: null;
            page_url: null;
            credit_line: null;
        };
        ArtworkDetailResponse: {
            artwork: components["schemas"]["ArtworkResult"];
            similar_artworks: components["schemas"]["SimilarArtwork"][];
            exhibition_links: {
                /** @enum {string} */
                state: "UNCONFIRMED";
                exhibitions: components["schemas"]["ExhibitionSearchResult"][];
            };
        };
        SimilarArtwork: {
            artwork: components["schemas"]["ArtworkResult"];
            reasons: ("SAME_CREATOR" | "SAME_COLLECTION")[];
        };
        ArtworkError: {
            error: {
                /** @enum {string} */
                code: "INVALID_ARTWORK_QUERY" | "NOT_FOUND";
                message: string;
                details: {
                    [key: string]: unknown;
                };
            };
        };
        ExhibitionDetailResponse: {
            exhibition: components["schemas"]["ExhibitionSearchResult"];
            content: components["schemas"]["ExhibitionContent"];
            visit_information: components["schemas"]["VisitInformation"];
            features: components["schemas"]["DetailFeature"][];
            operating_schedule: components["schemas"]["DetailOperatingSchedule"];
        };
        /** @description 공식 상세를 검토해 작성한 소개와 안내입니다. 현재 정본·원본이 바뀌거나 검토 유효기간이 지나면 null입니다. 관람 안내 문구는 추천용 확정 방문값과 구분합니다. */
        ExhibitionContent: {
            introduction: string;
            highlights: string[];
            visit_notes: components["schemas"]["ExhibitionVisitNote"][];
            /** Format: uri */
            official_url: string;
            source_owner: string;
            /** Format: date-time */
            reviewed_at: string;
            /** Format: date-time */
            expires_at: string;
        } | null;
        ExhibitionVisitNote: {
            /** @enum {string} */
            kind: "PRICE" | "HOURS" | "RESERVATION" | "AGE" | "LOCATION";
            text: string;
        };
        InstitutionDetailResponse: {
            institution: components["schemas"]["InstitutionSearchResult"];
            total: number;
            page: number;
            page_size: number;
            has_more: boolean;
            exhibitions: components["schemas"]["ExhibitionSearchResult"][];
        };
        DetailEvidence: {
            /** @enum {string} */
            scope: "EXHIBITION" | "INSTITUTION";
            /** Format: date-time */
            verified_at: string;
            source: components["schemas"]["SourceEvidence"];
        };
        /** @enum {string} */
        EvidenceState: "CONFIRMED" | "UNKNOWN" | "CONFLICT";
        VisitInformation: {
            price: components["schemas"]["DetailPrice"];
            reservation: components["schemas"]["DetailReservation"];
            duration: components["schemas"]["DetailDuration"];
            accessibility: components["schemas"]["DetailAccessibility"][];
            sensory: components["schemas"]["DetailSensory"][];
        };
        /** @description 일반 성인 기본 관람권의 확인된 비교 금액입니다. 공식 가격 범위가 있으면 상한을 쓰고 할인·단체권을 대신 쓰지 않습니다. 미확인·충돌 시 금액은 null입니다. */
        DetailPrice: {
            state: components["schemas"]["EvidenceState"];
            amount: number | null;
            currency: string | null;
            is_free: boolean | null;
            evidence: components["schemas"]["DetailEvidence"][];
        };
        DetailReservation: {
            state: components["schemas"]["EvidenceState"];
            /** @enum {string|null} */
            reservation_type: "NOT_REQUIRED" | "REQUIRED" | "RECOMMENDED" | "TIMED_ENTRY" | "ON_SITE" | "FIRST_COME" | "PROGRAM_ONLY" | null;
            official_urls: string[];
            guidance: string[];
            evidence: components["schemas"]["DetailEvidence"][];
        };
        DetailDuration: {
            state: components["schemas"]["EvidenceState"];
            minimum_minutes: number | null;
            maximum_minutes: number | null;
            evidence: components["schemas"]["DetailEvidence"][];
        };
        DetailAccessibility: {
            /** @enum {string} */
            kind: "WHEELCHAIR_ACCESS" | "MOBILITY_ACCESS" | "CAPTIONS" | "SIGN_LANGUAGE" | "AUDIO_DESCRIPTION" | "AGE_CONDITION";
            state: components["schemas"]["EvidenceState"];
            /** @enum {string|null} */
            value: "CONFIRMED_POSITIVE" | "CONFIRMED_NEGATIVE" | null;
            details: string[];
            evidence: components["schemas"]["DetailEvidence"][];
        };
        DetailSensory: {
            /** @enum {string} */
            kind: "LOUD_SOUND" | "SUDDEN_SOUND" | "FLASHING_LIGHTS" | "DARK_SPACE" | "NARROW_OR_ENCLOSED_SPACE";
            state: components["schemas"]["EvidenceState"];
            /** @enum {string|null} */
            value: "CONFIRMED_POSITIVE" | "CONFIRMED_NEGATIVE" | null;
            details: string[];
            evidence: components["schemas"]["DetailEvidence"][];
        };
        DetailFeature: {
            /** @enum {string} */
            axis: "MEDIA_GROUP" | "MEDIA_DETAIL" | "THEME" | "MOOD" | "EXPERIENCE" | "SPACE_TYPE" | "EVENT_FORMAT";
            value: string;
            /** @enum {string} */
            evidence_kind: "DIRECT" | "DERIVED";
            rule_version: string | null;
            source: components["schemas"]["SourceEvidence"];
        };
        DetailOperatingSchedule: {
            /** @enum {string} */
            state: "OPEN" | "CLOSED" | "UNKNOWN";
            visit_availability: components["schemas"]["VisitAvailability"];
            rules: components["schemas"]["DetailScheduleRule"][];
        };
        DetailScheduleRule: {
            /** @enum {string} */
            status: "CONFIRMED" | "UNKNOWN";
            /** @enum {string} */
            kind: "REGULAR" | "OVERRIDE";
            /** Format: date */
            effective_from: string;
            /** Format: date */
            effective_to: string;
            weekdays: number[];
            is_open: boolean | null;
            opens_at: string | null;
            closes_at: string | null;
            rule_version: string;
            evidence: components["schemas"]["DetailEvidence"];
        };
        DetailError: {
            error: {
                /** @enum {string} */
                code: "NOT_FOUND" | "INVALID_DETAIL_QUERY";
                message: string;
                details: {
                    [key: string]: unknown;
                };
            };
        };
        RecommendationRequest: {
            region?: components["schemas"]["RecommendationRegion"];
            exhibition_dates?: components["schemas"]["ExhibitionDateRange"];
            visit_dates?: components["schemas"]["VisitDateRange"];
            max_budget_krw?: number;
            required_accessibility?: ("WHEELCHAIR_ACCESS" | "MOBILITY_ACCESS" | "CAPTIONS" | "SIGN_LANGUAGE" | "AUDIO_DESCRIPTION" | "AGE_CONDITION")[];
            avoided_sensory?: ("LOUD_SOUND" | "SUDDEN_SOUND" | "FLASHING_LIGHTS" | "DARK_SPACE" | "NARROW_OR_ENCLOSED_SPACE")[];
            reservation?: components["schemas"]["ReservationPreferenceRequest"];
            duration?: components["schemas"]["DurationPreferenceRequest"];
            preferred_features?: components["schemas"]["FeaturePreference"][];
            liked_exhibition_ids?: number[];
            liked_institution_ids?: number[];
            /** @default 6 */
            limit?: number;
        };
        RecommendationRegion: {
            area: string;
            district?: string;
        };
        /** @description 공식 전시 기간과 경계를 포함해 하루 이상 겹치는 전시를 찾는 기간입니다. 개관일·휴관일·운영시간은 판정하지 않으며 이 조건만 사용하면 visit_availability는 null입니다. start는 end보다 늦을 수 없습니다. */
        ExhibitionDateRange: {
            /** Format: date */
            start: string;
            /** Format: date */
            end: string;
        };
        /** @description 공식 운영일 근거가 확인된 개관일이 하루 이상 있어야 하는 방문 기간입니다. exhibition_dates와 함께 사용하면 두 기간의 교집합에 적용합니다. start는 end보다 늦을 수 없습니다. */
        VisitDateRange: {
            /** Format: date */
            start: string;
            /** Format: date */
            end: string;
        };
        ReservationPreferenceRequest: {
            /** @enum {string} */
            mode: "REQUIRED" | "PREFERRED";
            types: ("NOT_REQUIRED" | "REQUIRED" | "RECOMMENDED" | "TIMED_ENTRY" | "ON_SITE" | "FIRST_COME" | "PROGRAM_ONLY")[];
        };
        DurationPreferenceRequest: {
            /** @enum {string} */
            mode: "REQUIRED" | "PREFERRED";
            minimum_minutes: number;
            maximum_minutes?: number;
        } | {
            /** @enum {string} */
            mode: "REQUIRED" | "PREFERRED";
            minimum_minutes?: number;
            maximum_minutes: number;
        };
        FeaturePreference: {
            /** @enum {string} */
            axis: "MEDIA_GROUP" | "MEDIA_DETAIL" | "THEME" | "MOOD" | "EXPERIENCE" | "SPACE_TYPE" | "EVENT_FORMAT";
            value: string;
        };
        RecommendationResponse: {
            algorithm_version: string;
            candidate_count: number;
            recommendations: components["schemas"]["ExhibitionRecommendation"][];
            needs_verification: components["schemas"]["VerificationCandidate"][];
        };
        /** @description First officially confirmed open day in the requested date range; not a reservation or seat availability guarantee. */
        VisitAvailability: {
            /** Format: date */
            first_open_date: string;
            opens_at: string;
            closes_at: string;
            /** Format: date-time */
            verified_at: string;
        } | null;
        ExhibitionRecommendation: {
            /** @enum {string} */
            type: "EXHIBITION";
            id: number;
            title: string;
            institution: components["schemas"]["InstitutionReference"];
            /** @enum {string} */
            lifecycle: "CURRENT" | "UPCOMING";
            /** Format: date */
            start_date: string;
            /** Format: date */
            end_date: string;
            venue: string;
            region: components["schemas"]["Region"];
            /** Format: uri */
            official_url: string;
            /** @enum {string} */
            freshness: "FRESH" | "STALE";
            /** @enum {string} */
            eligibility: "VERIFIED";
            /** Format: date-time */
            last_verified_at: string;
            source: components["schemas"]["SourceEvidence"];
            media: components["schemas"]["MediaPresentation"];
            /** @enum {string} */
            match_level: "VERY_CLOSE" | "GOOD_MATCH" | "SOME_MATCH" | "GENERAL" | "EXPLORATION";
            visit_availability?: components["schemas"]["VisitAvailability"];
            is_exploration: boolean;
            reasons: components["schemas"]["RecommendationReason"][];
        };
        VerificationCandidate: {
            /** @enum {string} */
            type: "EXHIBITION";
            id: number;
            title: string;
            institution: components["schemas"]["InstitutionReference"];
            /** @enum {string} */
            lifecycle: "CURRENT" | "UPCOMING";
            /** Format: date */
            start_date: string;
            /** Format: date */
            end_date: string;
            venue: string;
            region: components["schemas"]["Region"];
            /** Format: uri */
            official_url: string;
            /** @enum {string} */
            freshness: "FRESH" | "STALE";
            /** @enum {string} */
            eligibility: "VERIFIED";
            /** Format: date-time */
            last_verified_at: string;
            source: components["schemas"]["SourceEvidence"];
            media: components["schemas"]["MediaPresentation"];
            visit_availability?: components["schemas"]["VisitAvailability"];
            verification_reasons: ("PRICE_UNKNOWN" | "RESERVATION_UNKNOWN" | "DURATION_UNKNOWN")[];
        };
        RecommendationReason: {
            /** @enum {string} */
            code: "PREFERRED_FEATURE" | "LIKED_EXHIBITION_FEATURE" | "LIKED_INSTITUTION" | "PREFERRED_RESERVATION" | "PREFERRED_DURATION" | "FRESH_OFFICIAL_INFORMATION" | "OFFICIAL_INFORMATION" | "EXPLORATION_CONNECTION" | "EXPLORATION_NOVELTY";
            text: string;
            feature: components["schemas"]["FeaturePreference"] | null;
        };
        RecommendationError: {
            error: {
                /** @enum {string} */
                code: "INVALID_RECOMMENDATION_REQUEST";
                message: string;
                details: {
                    [key: string]: unknown;
                };
            };
        };
        SearchResponse: {
            total: number;
            page: number;
            page_size: number;
            has_more: boolean;
            results: (components["schemas"]["ExhibitionSearchResult"] | components["schemas"]["InstitutionSearchResult"])[];
        };
        ExhibitionSearchResult: {
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            type: "EXHIBITION";
            id: number;
            title: string;
            institution: components["schemas"]["InstitutionReference"];
            /** @enum {string} */
            lifecycle: "CURRENT" | "UPCOMING" | "ENDED" | "CANCELED";
            /** Format: date */
            start_date: string;
            /** Format: date */
            end_date: string;
            venue: string;
            region: components["schemas"]["Region"];
            /** Format: uri */
            official_url: string;
            /** @enum {string} */
            freshness: "FRESH" | "STALE";
            /** @enum {string} */
            eligibility: "VERIFIED";
            /** Format: date-time */
            last_verified_at: string;
            source: components["schemas"]["SourceEvidence"];
            media: components["schemas"]["MediaPresentation"];
        };
        InstitutionSearchResult: {
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            type: "INSTITUTION";
            id: number;
            name: string;
            region: components["schemas"]["Region"];
            searchable_exhibition_count: number;
        };
        InstitutionReference: {
            id: number;
            name: string;
        };
        Region: {
            area: string;
            district: string;
        };
        SourceEvidence: {
            source_id: string;
            source_record_id: string;
            source_owner: string;
            /** Format: date-time */
            last_seen_at: string;
        };
        MediaPresentation: {
            /** @enum {string} */
            status: "INLINE" | "LINK_ONLY" | "HIDDEN";
            /** Format: uri */
            media_url: string | null;
            /** Format: uri */
            page_url: string | null;
            credit_line: string | null;
        };
        SearchError: {
            error: {
                /** @enum {string} */
                code: "INVALID_SEARCH_QUERY" | "SEARCH_BACKEND_UNAVAILABLE";
                message: string;
                details: {
                    [key: string]: unknown;
                };
            };
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
    searchDiscovery: {
        parameters: {
            query?: {
                q?: string;
                type?: "EXHIBITION" | "INSTITUTION" | "ALL";
                lifecycle?: ("CURRENT" | "UPCOMING" | "ENDED" | "CANCELED")[];
                region_area?: string;
                region_district?: string;
                sort?: "RELEVANCE" | "LATEST_START" | "ENDING_SOON" | "UPCOMING_START";
                page?: number;
                page_size?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description 검색 성공. 결과가 없으면 results는 빈 배열입니다. */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SearchResponse"];
                };
            };
            /** @description 검색 조건 오류 */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SearchError"];
                };
            };
            /** @description SQLite FTS5 검색 백엔드 사용 불가 */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SearchError"];
                };
            };
        };
    };
    recommendExhibitions: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RecommendationRequest"];
            };
        };
        responses: {
            /** @description 추천 성공. 후보가 없으면 두 결과 배열은 비어 있습니다. */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RecommendationResponse"];
                };
            };
            /** @description 추천 조건 오류 */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RecommendationError"];
                };
            };
        };
    };
    getExhibitionDetail: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description 전시 상세 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ExhibitionDetailResponse"];
                };
            };
            /** @description 없거나 사용자에게 노출할 수 없는 전시 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DetailError"];
                };
            };
        };
    };
    getInstitutionDetail: {
        parameters: {
            query?: {
                page?: number;
                page_size?: number;
            };
            header?: never;
            path: {
                id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description 현재·예정·종료·취소 순서의 안전한 기관 전시 목록 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InstitutionDetailResponse"];
                };
            };
            /** @description 페이지 조건 오류 */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DetailError"];
                };
            };
            /** @description 없거나 노출 가능한 전시가 없는 기관 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DetailError"];
                };
            };
        };
    };
    listArtworks: {
        parameters: {
            query?: {
                q?: string;
                institution_id?: number;
                media_group?: "PAINTING" | "SCULPTURE" | "CRAFT" | "PHOTOGRAPHY" | "VIDEO" | "SOUND" | "INSTALLATION" | "PERFORMANCE" | "INTERACTIVE" | "MEDIA_ART" | "DESIGN" | "ARCHITECTURE";
                page?: number;
                page_size?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description 작품 목록 또는 출처 승인 대기 상태 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ArtworkListResponse"];
                };
            };
            /** @description 잘못된 검색·페이지 조건 또는 지원하지 않는·중복 조건 */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ArtworkError"];
                };
            };
        };
    };
    getArtworkDetail: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description 노출 가능한 작품 상세 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ArtworkDetailResponse"];
                };
            };
            /** @description 없거나 노출할 수 없는 작품 */
            404: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ArtworkError"];
                };
            };
        };
    };
}
