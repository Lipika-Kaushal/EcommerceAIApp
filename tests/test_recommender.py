import unittest

from recommender import build_recommendations


PRODUCTS = [
    {"id": 1, "name": "Laptop", "price": 50000},
    {"id": 2, "name": "Mobile", "price": 20000},
    {"id": 3, "name": "Keyboard", "price": 1000},
    {"id": 4, "name": "Mouse", "price": 500},
    {"id": 5, "name": "Smartwatch", "price": 8000},
    {"id": 6, "name": "Camera", "price": 35000},
    {"id": 7, "name": "Tablet", "price": 28000},
]
PURCHASES = [
    {"customer_id": "shopper-1", "product_id": 1},
    {"customer_id": "shopper-1", "product_id": 4},
    {"customer_id": "shopper-2", "product_id": 1},
    {"customer_id": "shopper-2", "product_id": 3},
    {"customer_id": "shopper-2", "product_id": 5},
    {"customer_id": "shopper-2", "product_id": 6},
    {"customer_id": "shopper-3", "product_id": 2},
    {"customer_id": "shopper-3", "product_id": 3},
    {"customer_id": "shopper-4", "product_id": 2},
    {"customer_id": "shopper-4", "product_id": 3},
    {"customer_id": "shopper-4", "product_id": 5},
    {"customer_id": "shopper-4", "product_id": 7},
]


class RecommendationTests(unittest.TestCase):
    def test_personalizes_to_cart_interests_and_excludes_them(self):
        results = build_recommendations(PRODUCTS, [1, 4], PURCHASES)

        self.assertEqual(results[0]["name"], "Keyboard")
        self.assertNotIn(1, [item["id"] for item in results])
        self.assertIn("Laptop", results[0]["reason"])

    def test_recommends_related_new_catalog_products(self):
        results = build_recommendations(PRODUCTS, [5], PURCHASES)

        product_ids = [item["id"] for item in results]
        self.assertIn(6, product_ids)
        self.assertIn(7, product_ids)
        self.assertNotIn(5, product_ids)

    def test_uses_popularity_for_a_new_shopper(self):
        results = build_recommendations(PRODUCTS, [], PURCHASES)

        self.assertEqual(results[0]["name"], "Keyboard")
        self.assertIn("Popular", results[0]["reason"])

    def test_handles_an_empty_order_history(self):
        results = build_recommendations(PRODUCTS, [], [])

        self.assertEqual(results[0]["name"], "Laptop")
        self.assertEqual(results[0]["reason"], "A great place to start")

    def test_returns_no_more_than_the_requested_limit(self):
        results = build_recommendations(PRODUCTS, [1], PURCHASES, limit=1)

        self.assertEqual(len(results), 1)


if __name__ == "__main__":
    unittest.main()
