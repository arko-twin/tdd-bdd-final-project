######################################################################
# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0
######################################################################

"""
Product API Service Test Suite

Test cases can be run with:
    nosetests
    coverage report -m
"""
import os
import logging
from unittest import TestCase
from service import app
from service.common import status
from service.models import db, init_db, Product, Category
from tests.factories import ProductFactory


# Disable all but critical errors during normal test run
logging.disable(logging.CRITICAL)

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)
BASE_URL = "/products"


######################################################################
# T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductRoutes(TestCase):
    """Product Service tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Product).delete()
        db.session.commit()

    def tearDown(self):
        """Runs after each test"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################
    def _create_products(self, count):
        """Factory method to create products in bulk"""
        products = []
        for _ in range(count):
            test_product = ProductFactory()
            response = self.client.post(BASE_URL, json=test_product.serialize())
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            new_product = response.get_json()
            test_product.id = new_product["id"]
            products.append(test_product)
        return products

    ######################################################################
    #  H O M E   A N D   H E A L T H
    ######################################################################
    def test_index(self):
        """It should return the index page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["message"], "OK")

    ######################################################################
    #  C R E A T E
    ######################################################################
    def test_create_product(self):
        """It should Create a new Product"""
        test_product = ProductFactory()
        response = self.client.post(BASE_URL, json=test_product.serialize())

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        new_product = response.get_json()
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["description"], test_product.description)
        self.assertEqual(new_product["available"], test_product.available)
        self.assertEqual(new_product["category"], test_product.category.name)

    def test_create_product_no_content_type(self):
        """It should not Create a Product with no Content-Type"""
        response = self.client.post(BASE_URL, data="bad data")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_product_wrong_content_type(self):
        """It should not Create a Product with wrong Content-Type"""
        response = self.client.post(
            BASE_URL,
            data="bad data",
            content_type="text/plain",
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_product_no_name(self):
        """It should not Create a Product without a name"""
        test_product = ProductFactory()
        product_data = test_product.serialize()
        del product_data["name"]

        response = self.client.post(BASE_URL, json=product_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    ######################################################################
    #  R E A D
    ######################################################################
    def test_get_product(self):
        """It should Get a single Product"""
        test_product = self._create_products(1)[0]

        response = self.client.get(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        product = response.get_json()
        self.assertEqual(product["id"], test_product.id)
        self.assertEqual(product["name"], test_product.name)

    def test_get_product_not_found(self):
        """It should not Get a Product thats not found"""
        response = self.client.get(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    ######################################################################
    #  U P D A T E
    ######################################################################
    def test_update_product(self):
        """It should Update a Product"""
        test_product = self._create_products(1)[0]

        test_product.name = "New Product Name"
        test_product.description = "Updated product description"

        response = self.client.put(
            f"{BASE_URL}/{test_product.id}",
            json=test_product.serialize(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        updated_product = response.get_json()
        self.assertEqual(updated_product["id"], test_product.id)
        self.assertEqual(updated_product["name"], "New Product Name")
        self.assertEqual(
            updated_product["description"],
            "Updated product description",
        )

    def test_update_product_not_found(self):
        """It should not Update a Product thats not found"""
        test_product = ProductFactory()
        response = self.client.put(f"{BASE_URL}/0", json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_product_wrong_content_type(self):
        """It should not Update a Product with wrong Content-Type"""
        test_product = self._create_products(1)[0]

        response = self.client.put(
            f"{BASE_URL}/{test_product.id}",
            data="bad data",
            content_type="text/plain",
        )

        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    ######################################################################
    #  D E L E T E
    ######################################################################
    def test_delete_product(self):
        """It should Delete a Product"""
        test_product = self._create_products(1)[0]

        response = self.client.delete(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        response = self.client.get(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_product_not_found(self):
        """It should Delete a Product even if not found"""
        response = self.client.delete(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    ######################################################################
    #  L I S T
    ######################################################################
    def test_list_products(self):
        """It should List all Products"""
        self._create_products(5)

        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.get_json()
        self.assertEqual(len(data), 5)

    def test_query_by_name(self):
        """It should Query Products by Name"""
        products = self._create_products(5)
        test_name = products[0].name

        response = self.client.get(BASE_URL, query_string=f"name={test_name}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.get_json()
        self.assertGreaterEqual(len(data), 1)

        for product in data:
            self.assertEqual(product["name"], test_name)

    def test_query_by_category(self):
        """It should Query Products by Category"""
        products = self._create_products(10)
        test_category = products[0].category.name

        response = self.client.get(BASE_URL, query_string=f"category={test_category}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.get_json()
        self.assertGreaterEqual(len(data), 1)

        for product in data:
            self.assertEqual(product["category"], test_category)

    def test_query_by_availability(self):
        """It should Query Products by Availability"""
        products = self._create_products(10)
        test_available = products[0].available

        response = self.client.get(
            BASE_URL,
            query_string=f"available={str(test_available).lower()}",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.get_json()
        self.assertGreaterEqual(len(data), 1)

        for product in data:
            self.assertEqual(product["available"], test_available)

    def test_query_by_category_lowercase(self):
        """It should Query Products by Category using lowercase category"""
        product = ProductFactory(category=Category.TOOLS)
        response = self.client.post(BASE_URL, json=product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get(BASE_URL, query_string="category=tools")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.get_json()
        self.assertGreaterEqual(len(data), 1)

        for product in data:
            self.assertEqual(product["category"], Category.TOOLS.name)
