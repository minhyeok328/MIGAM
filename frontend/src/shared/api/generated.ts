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
        /** 조건과 명시적 취향에 맞는 전시 추천 */
        post: operations["recommendExhibitions"];
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
        RecommendationRequest: {
            region?: components["schemas"]["RecommendationRegion"];
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
}
