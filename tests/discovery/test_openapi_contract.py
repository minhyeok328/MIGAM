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
