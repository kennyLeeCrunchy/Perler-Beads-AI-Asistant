import unittest

from fastapi.testclient import TestClient

from app.api_main import app


class ApiOnlyAppTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_root_does_not_serve_legacy_browser_demo(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 404)

    def test_api_routes_remain_available(self):
        response = self.client.get("/api/palette", params={"brand": "Mard"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["brand"], "Mard")


if __name__ == "__main__":
    unittest.main()
