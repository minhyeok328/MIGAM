from django.apps import apps
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from backend.apps.discovery.demo import seed_demo


ARTWORKS_URL = "/api/internal/v1/artworks/"


class ArtworkSourcePendingTests(TestCase):
    def test_unapproved_real_sources_have_an_explicit_empty_state(self):
        response = self.client.get(ARTWORKS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "total": 0, "page": 1, "page_size": 24, "has_more": False,
            "results": [], "availability": "SOURCE_PENDING",
        })


@override_settings(MIGAM_DEMO_MODE=True)
class ArtworkDemoAPITests(TestCase):
    def setUp(self):
        seed_demo()

    def artwork_model(self):
        return apps.get_model("catalog", "Artwork")

    def feature_model(self):
        return apps.get_model("catalog", "ArtworkFeatureAssertion")

    def first_artwork(self):
        return self.artwork_model().objects.order_by("pk").first()

    def detail_url(self, artwork=None):
        return f"{ARTWORKS_URL}{(artwork or self.first_artwork()).pk}/"

    def test_keyless_demo_has_four_fictional_rows_and_no_image_urls(self):
        response = self.client.get(ARTWORKS_URL)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["availability"], "DEMO")
        self.assertEqual(body["total"], 4)
        for row in body["results"]:
            self.assertIn("가상", row["title"])
            self.assertTrue(row["is_demo"])
            self.assertEqual(row["eligibility"], "DEMO")
            self.assertEqual(row["source"]["source_id"], "fictional-demo-only")
            self.assertEqual(row["media"], {
                "status": "HIDDEN", "media_url": None,
                "page_url": None, "credit_line": None,
            })
            self.assertNotIn("payload", row)

    def test_metadata_filters_and_pages_are_bounded_and_stable(self):
        first = self.client.get(ARTWORKS_URL, {"page_size": 2}).json()
        second = self.client.get(ARTWORKS_URL, {"page_size": 2, "page": 2}).json()
        self.assertTrue(first["has_more"])
        self.assertFalse(second["has_more"])
        self.assertEqual(len({row["id"] for row in first["results"] + second["results"]}), 4)
        self.assertEqual(self.client.get(ARTWORKS_URL, {"page": 3, "page_size": 2}).json()["results"], [])
        painting = self.client.get(ARTWORKS_URL, {"media_group": "PAINTING"}).json()
        self.assertEqual(painting["total"], 2)
        self.assertEqual(self.client.get(ARTWORKS_URL, {"q": "푸른"}).json()["total"], 1)
        institution = first["results"][0]["collection_institution"]["id"]
        collection = self.client.get(ARTWORKS_URL, {"institution_id": institution}).json()
        self.assertEqual(collection["total"], 2)
        self.assertTrue(all(row["collection_institution"]["id"] == institution for row in collection["results"]))

    def test_invalid_filters_are_rejected_without_echoing_raw_queries(self):
        for query in ({"page_size": 25}, {"page": 0}, {"q": "x" * 101},
                      {"institution_id": -1}, {"media_group": "INVENTED"},
                      {"q": ["one", "two"]}, {"unknown": "raw-private-query"}):
            with self.subTest(query=query):
                response = self.client.get(ARTWORKS_URL, query)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json()["error"]["code"], "INVALID_ARTWORK_QUERY")
                self.assertNotIn("raw-private-query", response.content.decode())

    def test_disabling_demo_hides_list_and_detail_without_deleting_rows(self):
        url = self.detail_url()
        with override_settings(MIGAM_DEMO_MODE=False):
            self.assertEqual(self.client.get(ARTWORKS_URL).json()["results"], [])
            self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.artwork_model().objects.count(), 4)

    def test_default_unverified_or_forged_verified_rows_are_never_published(self):
        self.assertEqual(self.artwork_model()().eligibility, "UNVERIFIED")
        row = self.first_artwork()
        self.artwork_model().objects.filter(pk=row.pk).update(eligibility="VERIFIED", is_demo=False)
        self.assertEqual(self.client.get(self.detail_url(row)).status_code, 404)
        with override_settings(MIGAM_DEMO_MODE=False):
            self.assertEqual(self.client.get(self.detail_url(row)).status_code, 404)
        self.assertEqual(self.client.get(ARTWORKS_URL).json()["total"], 3)

    def test_current_source_identity_and_safe_url_are_rechecked_at_read_time(self):
        row = self.first_artwork()
        self.artwork_model().objects.filter(pk=row.pk).update(official_url="javascript:alert(1)")
        self.assertEqual(self.client.get(self.detail_url(row)).status_code, 404)
        other = self.artwork_model().objects.order_by("pk")[1]
        self.artwork_model().objects.filter(pk=other.pk).update(source_artwork_id="wrong-official-id")
        self.assertEqual(self.client.get(self.detail_url(other)).status_code, 404)

    def test_detail_preserves_unknown_creator_and_culture_instead_of_inferring(self):
        row = self.artwork_model().objects.get(creator_state="UNKNOWN")
        body = self.client.get(self.detail_url(row)).json()["artwork"]
        self.assertEqual(body["creator"], {"name": "작자 미상 · 가상", "official_id": None, "state": "UNKNOWN"})
        self.assertEqual(body["cultural_context"], {"state": "UNKNOWN", "value": None, "is_korean": None})

    def test_detail_contains_only_current_server_evidence_and_no_inferred_exhibition(self):
        row = self.first_artwork()
        response = self.client.get(self.detail_url(row))
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["exhibition_links"], {"state": "UNCONFIRMED", "exhibitions": []})
        self.assertEqual({(f["axis"], f["value"]) for f in body["artwork"]["features"]}, {
            ("MEDIA_GROUP", "PAINTING"), ("MOOD", "CALM"),
        })
        for feature in body["artwork"]["features"]:
            self.assertEqual(feature["source"]["source_record_id"], row.source_artwork_id)
        self.assertNotIn("payload", response.content.decode())

    def test_stale_feature_evidence_is_not_returned_or_used_for_filtering(self):
        row = self.first_artwork()
        other = self.artwork_model().objects.order_by("pk")[1]
        self.feature_model().objects.filter(artwork=row).update(source_record=other.source_record)
        self.assertEqual(self.client.get(self.detail_url(row)).json()["artwork"]["features"], [])
        self.assertEqual(self.client.get(ARTWORKS_URL, {"media_group": "PAINTING"}).json()["total"], 1)

    def test_same_creator_requires_official_identity_not_only_matching_name(self):
        row = self.first_artwork()
        related = self.client.get(self.detail_url(row)).json()["similar_artworks"]
        creator_match = [item for item in related if "SAME_CREATOR" in item["reasons"]]
        self.assertEqual(len(creator_match), 1)
        counterpart = self.artwork_model().objects.get(pk=creator_match[0]["artwork"]["id"])
        self.assertEqual(counterpart.creator_name, row.creator_name)
        self.artwork_model().objects.filter(pk=counterpart.pk).update(creator_official_id="")
        after = self.client.get(self.detail_url(row)).json()["similar_artworks"]
        self.assertFalse(any("SAME_CREATOR" in item["reasons"] for item in after))

    def test_model_rejects_mismatched_provenance_and_unknown_creator_with_identity(self):
        row = self.first_artwork()
        row.creator_state = "UNKNOWN"
        with self.assertRaises(ValidationError):
            row.save()
        row.refresh_from_db()
        row.source_artwork_id = "not-source-identity"
        with self.assertRaises(ValidationError):
            row.save()

    def test_mutations_and_unknown_artwork_ids_are_not_available(self):
        self.assertEqual(self.client.post(ARTWORKS_URL, {}).status_code, 405)
        self.assertEqual(self.client.post(self.detail_url(), {}).status_code, 405)
        response = self.client.get(f"{ARTWORKS_URL}999999/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "NOT_FOUND")
