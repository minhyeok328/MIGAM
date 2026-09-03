from importlib import import_module, util

from django.test import TestCase, override_settings

from backend.apps.catalog.models import Exhibition, Institution


class IsolatedDiscoveryDemoTests(TestCase):
    def runner(self):
        self.assertIsNotNone(util.find_spec("backend.apps.discovery.demo"))
        return import_module("backend.apps.discovery.demo")

    def test_seed_refuses_non_demo_settings_without_writing(self):
        module = self.runner()
        with override_settings(MIGAM_DEMO_MODE=False):
            with self.assertRaises(RuntimeError):
                module.seed_demo()
        self.assertEqual(Institution.objects.count(), 0)

    @override_settings(MIGAM_DEMO_MODE=True)
    def test_demo_uses_actual_search_and_recommendation_with_hard_conditions(self):
        module = self.runner()
        module.seed_demo()
        result = self.client.get("/api/internal/v1/search/", {"q": "고요"})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["results"][0]["title"], "고요의 형태")
        result = self.client.post(
            "/api/internal/v1/recommendations/",
            {"max_budget_krw": 0}, content_type="application/json",
        )
        self.assertEqual(result.status_code, 200)
        self.assertTrue(result.json()["recommendations"])
        self.assertTrue(result.json()["needs_verification"])
        safety = self.client.post(
            "/api/internal/v1/recommendations/",
            {"required_accessibility": ["WHEELCHAIR_ACCESS"], "avoided_sensory": ["FLASHING_LIGHTS"]},
            content_type="application/json",
        ).json()
        self.assertTrue(safety["recommendations"])
        self.assertEqual(safety["needs_verification"], [])
        absent = self.client.post(
            "/api/internal/v1/recommendations/",
            {"region": {"area": "제주"}}, content_type="application/json",
        ).json()
        self.assertEqual(absent["candidate_count"], 0)
        count = Exhibition.objects.count()
        with self.assertRaises(RuntimeError):
            module.seed_demo()
        self.assertEqual(Exhibition.objects.count(), count)
