from pathlib import Path

from django.test import SimpleTestCase
import yaml


OPENAPI_PATH = Path(__file__).resolve().parents[2] / "openapi" / "internal-v1.yaml"


class InternalOpenAPIContractTests(SimpleTestCase):
    def setUp(self) -> None:
        self.assertTrue(OPENAPI_PATH.is_file(), "internal OpenAPI document is missing")
        self.document = yaml.safe_load(OPENAPI_PATH.read_text(encoding="utf-8"))

    def test_document_defines_internal_search_path_and_query_contract(self) -> None:
        self.assertEqual(self.document["openapi"], "3.1.0")
        operation = self.document["paths"]["/api/internal/v1/search/"]["get"]
        parameters = {item["name"]: item for item in operation["parameters"]}

        self.assertEqual(
            set(parameters),
            {
                "q",
                "type",
                "lifecycle",
                "region_area",
                "region_district",
                "sort",
                "page",
                "page_size",
            },
        )
        self.assertEqual(
            parameters["type"]["schema"]["enum"],
            ["EXHIBITION", "INSTITUTION", "ALL"],
        )
        self.assertEqual(
            parameters["lifecycle"]["schema"]["items"]["enum"],
            ["CURRENT", "UPCOMING", "ENDED", "CANCELED"],
        )
        self.assertTrue(parameters["lifecycle"]["explode"])
        self.assertEqual(
            parameters["sort"]["schema"]["enum"],
            ["RELEVANCE", "LATEST_START", "ENDING_SOON", "UPCOMING_START"],
        )
        self.assertEqual(parameters["page_size"]["schema"]["default"], 24)
        self.assertEqual(parameters["page_size"]["schema"]["maximum"], 24)
        self.assertEqual(set(operation["responses"]), {"200", "400", "503"})

    def test_response_schemas_require_discriminator_source_and_safe_media_fields(self) -> None:
        schemas = self.document["components"]["schemas"]

        self.assertEqual(
            set(schemas["SearchResponse"]["required"]),
            {"total", "page", "page_size", "has_more", "results"},
        )
        result_items = schemas["SearchResponse"]["properties"]["results"]["items"]
        self.assertEqual(
            result_items["oneOf"],
            [
                {"$ref": "#/components/schemas/ExhibitionSearchResult"},
                {"$ref": "#/components/schemas/InstitutionSearchResult"},
            ],
        )
        self.assertEqual(result_items["discriminator"]["propertyName"], "type")
        self.assertIn("source", schemas["ExhibitionSearchResult"]["required"])
        self.assertIn("media", schemas["ExhibitionSearchResult"]["required"])
        self.assertEqual(
            schemas["MediaPresentation"]["properties"]["status"]["enum"],
            ["INLINE", "LINK_ONLY", "HIDDEN"],
        )
        self.assertEqual(
            schemas["SearchError"]["properties"]["error"]["required"],
            ["code", "message", "details"],
        )

    def test_document_defines_recommendation_post_request_contract(self) -> None:
        self.assertEqual(self.document["info"]["version"], "1.1.1")
        operation = self.document["paths"][
            "/api/internal/v1/recommendations/"
        ]["post"]

        self.assertEqual(operation["operationId"], "recommendExhibitions")
        self.assertEqual(
            operation["requestBody"]["content"]["application/json"]["schema"],
            {"$ref": "#/components/schemas/RecommendationRequest"},
        )
        self.assertEqual(set(operation["responses"]), {"200", "400"})

        request = self.document["components"]["schemas"][
            "RecommendationRequest"
        ]
        self.assertFalse(request["additionalProperties"])
        self.assertEqual(
            set(request["properties"]),
            {
                "region",
                "visit_dates",
                "max_budget_krw",
                "required_accessibility",
                "avoided_sensory",
                "reservation",
                "duration",
                "preferred_features",
                "liked_exhibition_ids",
                "liked_institution_ids",
                "limit",
            },
        )
        self.assertEqual(request["properties"]["limit"]["default"], 6)
        self.assertEqual(request["properties"]["limit"]["maximum"], 24)
        for field in (
            "required_accessibility",
            "avoided_sensory",
            "preferred_features",
            "liked_exhibition_ids",
            "liked_institution_ids",
        ):
            self.assertEqual(request["properties"][field]["maxItems"], 100)
            self.assertTrue(request["properties"][field]["uniqueItems"])
        self.assertEqual(
            self.document["components"]["schemas"]["FeaturePreference"][
                "properties"
            ]["axis"]["enum"],
            [
                "MEDIA_GROUP",
                "MEDIA_DETAIL",
                "THEME",
                "MOOD",
                "EXPERIENCE",
                "SPACE_TYPE",
                "EVENT_FORMAT",
            ],
        )

    def test_recommendation_response_has_qualitative_trace_without_score(self) -> None:
        schemas = self.document["components"]["schemas"]
        response = schemas["RecommendationResponse"]
        self.assertEqual(
            set(response["required"]),
            {
                "algorithm_version",
                "candidate_count",
                "recommendations",
                "needs_verification",
            },
        )
        recommendation = schemas["ExhibitionRecommendation"]
        self.assertEqual(
            set(recommendation["required"]),
            {
                "type",
                "id",
                "title",
                "institution",
                "lifecycle",
                "start_date",
                "end_date",
                "venue",
                "region",
                "official_url",
                "freshness",
                "eligibility",
                "last_verified_at",
                "source",
                "media",
                "match_level",
                "is_exploration",
                "reasons",
            },
        )
        self.assertNotIn("score", recommendation["properties"])
        self.assertNotIn("percentage", recommendation["properties"])
        self.assertEqual(
            recommendation["properties"]["match_level"]["enum"],
            ["VERY_CLOSE", "GOOD_MATCH", "SOME_MATCH", "GENERAL", "EXPLORATION"],
        )
        self.assertEqual(recommendation["properties"]["reasons"]["minItems"], 1)
        self.assertEqual(recommendation["properties"]["reasons"]["maxItems"], 3)
        self.assertEqual(
            schemas["RecommendationReason"]["properties"]["code"]["enum"],
            [
                "PREFERRED_FEATURE",
                "LIKED_EXHIBITION_FEATURE",
                "LIKED_INSTITUTION",
                "PREFERRED_RESERVATION",
                "PREFERRED_DURATION",
                "FRESH_OFFICIAL_INFORMATION",
                "OFFICIAL_INFORMATION",
                "EXPLORATION_CONNECTION",
                "EXPLORATION_NOVELTY",
            ],
        )
        self.assertEqual(
            schemas["VerificationCandidate"]["properties"][
                "verification_reasons"
            ]["items"]["enum"],
            ["PRICE_UNKNOWN", "RESERVATION_UNKNOWN", "DURATION_UNKNOWN"],
        )
        self.assertEqual(
            schemas["RecommendationError"]["properties"]["error"][
                "properties"
            ]["code"]["enum"],
            ["INVALID_RECOMMENDATION_REQUEST"],
        )
