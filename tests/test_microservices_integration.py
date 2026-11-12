import importlib
import logging
import os
import tempfile
import threading
import unittest
from pathlib import Path

from werkzeug.serving import make_server


class MicroserviceIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_directory = tempfile.TemporaryDirectory(prefix="goodfind-services-")
        cls.previous_environment = {
            key: os.environ.get(key)
            for key in (
                "DB_PATH",
                "CATALOG_URL",
                "CART_URL",
                "RECOMMENDATIONS_URL",
                "ORDERS_URL",
                "FLASK_SECRET_KEY",
            )
        }
        cls.modules = {}
        for name in (
            "catalog",
            "cart",
            "recommendations",
            "orders",
            "inventory",
        ):
            os.environ["DB_PATH"] = str(
                Path(cls.temp_directory.name) / f"{name}.db"
            )
            cls.modules[name] = importlib.import_module(f"microservices.{name}")

        servers = {}
        for name, module in cls.modules.items():
            server = make_server("127.0.0.1", 0, module.app, threaded=True)
            server_thread = threading.Thread(target=server.serve_forever, daemon=True)
            server_thread.start()
            servers[name] = (server, server_thread)
        cls.servers = servers
        urls = {
            name: f"http://127.0.0.1:{server.server_port}"
            for name, (server, _) in servers.items()
        }

        cls.modules["cart"].CATALOG_URL = urls["catalog"]
        cls.modules["orders"].CATALOG_URL = urls["catalog"]
        cls.modules["orders"].CART_URL = urls["cart"]
        cls.modules["orders"].INVENTORY_URL = urls["inventory"]
        cls.modules["recommendations"].CATALOG_URL = urls["catalog"]
        cls.modules["recommendations"].ORDERS_URL = urls["orders"]
        os.environ.update(
            {
                "CATALOG_URL": urls["catalog"],
                "CART_URL": urls["cart"],
                "RECOMMENDATIONS_URL": urls["recommendations"],
                "ORDERS_URL": urls["orders"],
                "FLASK_SECRET_KEY": "integration-test-secret",
            }
        )
        os.environ.pop("DB_PATH", None)
        cls.gateway = importlib.import_module("app").app
        logging.getLogger("werkzeug").setLevel(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        for server, server_thread in cls.servers.values():
            server.shutdown()
            server_thread.join(timeout=2)
        cls.temp_directory.cleanup()
        for key, value in cls.previous_environment.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_browse_recommend_checkout_and_reserve_inventory(self):
        client = self.gateway.test_client()

        shop = client.get("/")
        self.assertEqual(shop.status_code, 200)
        self.assertEqual(shop.data.count(b'class="product-card"'), 10)

        added = client.post(
            "/cart/add",
            data={"product_id": "1", "return_to": "shop"},
            follow_redirects=True,
        )
        self.assertEqual(added.status_code, 200)
        self.assertIn(b"Added to your bag", added.data)

        recommendations = client.get("/recommendations")
        self.assertEqual(recommendations.status_code, 200)
        self.assertIn(b"Inspired by Laptop", recommendations.data)
        self.assertIn(b"Keyboard", recommendations.data)

        confirmation = client.post("/checkout", follow_redirects=True)
        self.assertEqual(confirmation.status_code, 200)
        self.assertIn(b"Order confirmed", confirmation.data)
        self.assertIn(b"Laptop", confirmation.data)

        cart = client.get("/cart")
        self.assertIn(b"Your bag is taking a moment", cart.data)

        inventory = self.modules["inventory"].app.test_client().get(
            "/api/inventory"
        )
        stock = next(
            item["available"]
            for item in inventory.get_json()
            if item["product_id"] == 1
        )
        self.assertEqual(stock, 24)


if __name__ == "__main__":
    unittest.main()
