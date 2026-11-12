import sqlite3
import unittest

from recommender import get_recommendations


class RecommendationTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.executescript(
            """
            CREATE TABLE products (id INTEGER, name TEXT, price INTEGER);
            CREATE TABLE orders (username TEXT, product TEXT);
            INSERT INTO products VALUES
                (1, 'Laptop', 50000),
                (2, 'Mobile', 20000),
                (3, 'Keyboard', 1000),
                (4, 'Mouse', 500),
                (5, 'Smartwatch', 8000),
                (6, 'Camera', 35000),
                (7, 'Tablet', 28000);
            INSERT INTO orders VALUES
                ('u1', 'Laptop'),
                ('u1', 'Mouse'),
                ('u2', 'Laptop'),
                ('u2', 'Keyboard'),
                ('u2', 'Smartwatch'),
                ('u2', 'Camera'),
                ('u3', 'Mobile'),
                ('u3', 'Keyboard'),
                ('u4', 'Mobile'),
                ('u4', 'Keyboard'),
                ('u4', 'Smartwatch'),
                ('u4', 'Tablet');
            """
        )

    def tearDown(self):
        self.connection.close()

    def test_personalizes_to_cart_interests_and_excludes_them(self):
        results = get_recommendations(self.connection, ["Laptop", "Mouse"])

        self.assertEqual(results[0]["name"], "Keyboard")
        self.assertNotIn("Laptop", [item["name"] for item in results])
        self.assertIn("Laptop", results[0]["reason"])

    def test_uses_popularity_for_new_shopper_without_history(self):
        results = get_recommendations(self.connection, [])

        self.assertEqual(results[0]["name"], "Keyboard")
        self.assertIn("Popular", results[0]["reason"])

    def test_new_product_cart_interests_surface_related_products(self):
        results = get_recommendations(self.connection, ["Smartwatch"])

        names = [item["name"] for item in results]
        self.assertIn("Camera", names)
        self.assertIn("Tablet", names)
        self.assertNotIn("Smartwatch", names)

    def test_handles_an_empty_order_history(self):
        self.connection.execute("DELETE FROM orders")

        results = get_recommendations(self.connection, [])

        self.assertEqual(results[0]["name"], "Laptop")
        self.assertEqual(results[0]["reason"], "A great place to start")

    def test_returns_no_more_than_the_requested_limit(self):
        results = get_recommendations(self.connection, ["Laptop"], limit=1)

        self.assertEqual(len(results), 1)


if __name__ == "__main__":
    unittest.main()
