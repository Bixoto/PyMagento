import time
import warnings
from json.decoder import JSONDecodeError
from logging import Logger
from os import environ
from typing import Optional, Sequence, Dict, Union, cast, Iterator, Iterable, List, Literal
from urllib.parse import quote as urlquote

import requests
from api_session import APISession
from requests.exceptions import HTTPError

from magento.exceptions import MagentoException, MagentoAssertionError
from magento.queries import Query, make_search_query, make_field_value_query
from magento.types import Product, SourceItem, Sku, Category, MediaEntry, MagentoEntity, Order, PathId, Customer
from magento.version import __version__

__all__ = (
    "Magento",
)

USER_AGENT = f"Bixoto/PyMagento {__version__} +git.io/JDp0h"

DEFAULT_ATTRIBUTE_DICT = {
    "apply_to": [],
    "backend_type": "int",
    "custom_attributes": [],
    "entity_type_id": "4",
    "extension_attributes": {},
    "frontend_input": "select",
    "is_comparable": False,
    "is_filterable": False,
    "is_filterable_in_grid": False,
    "is_filterable_in_search": False,
    "is_html_allowed_on_front": False,
    "is_required": False,
    "is_searchable": False,
    "is_unique": False,
    "is_used_for_promo_rules": False,
    "is_used_in_grid": False,
    "is_user_defined": True,
    "is_visible": True,
    "is_visible_in_advanced_search": False,
    "is_visible_in_grid": False,
    "is_visible_on_front": True,
    "is_wysiwyg_enabled": False,
    "note": "",
    "position": 0,
    # This scope is required for configurable products
    # https://docs.magento.com/user-guide/catalog/product-attributes-add.html
    "scope": "global",
    "used_for_sort_by": False,
    "used_in_product_listing": False,
    "validation_rules": [],
}

DEFAULT_SCOPE = "all"


def raise_for_response(response: requests.Response):
    """
    Equivalent of `requests.Response#raise_for_status` with some Magento specifics.
    """
    if response.ok:
        return

    if response.text and response.text[0] == "{":
        try:
            body = response.json()
        except (ValueError, JSONDecodeError):
            pass
        else:
            if isinstance(body, dict) and "message" in body:
                raise MagentoException(
                    body["message"],
                    parameters=body.get("parameters"),
                    trace=body.get("trace"),
                    response=response,
                )

    response.raise_for_status()


def escape_path(x: Union[int, str]):
    return urlquote(str(x), safe="")


class Magento(APISession):
    """
    Client for the Magento API.
    """
    PAGE_SIZE = 1000
    """
    Default batch size for paginated requests.
    Note Magento supports hard limits on this:
      https://developer.adobe.com/commerce/webapi/get-started/api-security/
    """

    def __init__(self,
                 token: Optional[str] = None,
                 base_url: Optional[str] = None,
                 scope: Optional[str] = None,
                 logger: Optional[Logger] = None,
                 read_only=False,
                 user_agent=None,
                 *,
                 batch_page_size: Optional[int] = None,
                 **kwargs):
        """
        Create a Magento client instance. All arguments are optional and fall back on environment variables named
        ``PYMAGENTO_ + argument.upper()`` (``PYMAGENTO_TOKEN``, ``PYMAGENTO_BASE_URL``, etc.).
        The ``token`` and ``base_url`` **must** be given either as arguments or environment variables.

        :param token: API integration token
        :param base_url: base URL of the Magento instance
        :param scope: API scope. Default on ``PYMAGENTO_SCOPE`` if set, or ``"all"``
        :param batch_page_size: if set, override the default page size used for batch queries.
        :param logger: optional logger.
        :param read_only:
        :param user_agent: User-Agent
        """
        token = token or environ.get("PYMAGENTO_TOKEN")
        base_url = base_url or environ.get("PYMAGENTO_BASE_URL")
        scope = scope or environ.get("PYMAGENTO_SCOPE") or DEFAULT_SCOPE
        user_agent = user_agent or environ.get("PYMAGENTO_USER_AGENT") or USER_AGENT

        if token is None:
            raise RuntimeError("Missing API token")
        if base_url is None:
            raise RuntimeError("Missing API base URL")

        super().__init__(base_url=base_url, user_agent=user_agent, read_only=read_only, **kwargs)

        if batch_page_size is not None:
            self.PAGE_SIZE = batch_page_size

        self.scope = scope
        self.logger = logger
        self.headers["Authorization"] = f"Bearer {token}"

    # Addresses
    # =========

    def delete_customer_address(self, address_id: int) -> bool:
        """Delete customer address by ID."""
        return self.delete_json_api(f"/V1/addresses/{escape_path(address_id)}")

    # Apple Pay
    # =========

    def get_apple_pay_auth(self) -> MagentoEntity:
        """
        Returns details required to be able to submit a payment with Apple Pay.

        https://adobe-commerce.redoc.ly/2.4.6-admin/tag/applepayauth/#operation/GetV1ApplepayAuth
        """
        return self.get_json_api("/V1/applepay/auth")

    # Attributes
    # ==========

    def save_attribute(self, attribute: MagentoEntity, *, with_defaults=True, **kwargs) -> MagentoEntity:
        if with_defaults:
            base = DEFAULT_ATTRIBUTE_DICT.copy()
            base.update(attribute)
            attribute = base

        return self.post_json_api("/V1/products/attributes", json={"attribute": attribute}, **kwargs)

    def delete_attribute(self, attribute_code: str, **kwargs):
        return self.delete_api(f"/V1/products/attributes/{escape_path(attribute_code)}", **kwargs)

    # Attribute Sets
    # ==============

    def get_attribute_sets(self, query: Query = None, limit=-1, **kwargs) -> Iterable[MagentoEntity]:
        """Get all attribute sets (generator)."""
        return self.get_paginated("/V1/eav/attribute-sets/list", query=query, limit=limit, **kwargs)

    def get_attribute_set_attributes(self, attribute_set_id: int, **kwargs):
        """Get all attributes for the given attribute set id."""
        return self.get_json_api(f"/V1/products/attribute-sets/{escape_path(attribute_set_id)}/attributes",
                                 **kwargs)

    def assign_attribute_set_attribute(self, attribute_set_id: int, attribute_group_id: int, attribute_code: str,
                                       sort_order: int = 0, **kwargs):
        """
        Assign an attribute to an attribute set.

        :param attribute_set_id: ID of the attribute set.
        :param attribute_group_id: ID of the attribute group. It must be in the attribute set.
        :param attribute_code: code of the attribute to add in that attribute group and so in that attribute set.
        :param sort_order:
        :param kwargs:
        :return:
        """
        payload = {
            "attributeCode": attribute_code,
            "attributeGroupId": attribute_group_id,
            "attributeSetId": attribute_set_id,
            "sortOrder": sort_order,
        }
        return self.post_api("/V1/products/attribute-sets/attributes", json=payload, **kwargs)

    def remove_attribute_set_attribute(self, attribute_set_id: int, attribute_code: str, **kwargs):
        path = f"/V1/products/attribute-sets/{escape_path(attribute_set_id)}/attributes/{escape_path(attribute_code)}"
        return self.delete_api(path, **kwargs)

    # Bulk Operations
    # ===============

    def get_bulk_operations(self, *, query: Query = None, limit=-1, **kwargs):
        """Lists the bulk operation items."""
        return self.get_paginated("/V1/bulk", query=query, limit=limit, **kwargs)

    def get_bulk_status(self, bulk_uuid: str) -> MagentoEntity:
        """
        Get the status of an async/bulk operation.
        """
        return self.get_json_api(f"/V1/bulk/{escape_path(bulk_uuid)}/status",
                                 # backward compatibility
                                 none_on_404=False,
                                 none_on_empty=False)

    def get_bulk_detailed_status(self, bulk_uuid: str) -> MagentoEntity:
        """
        Get the detailed status of an async/bulk operation.
        """
        return self.get_json_api(f"/V1/bulk/{escape_path(bulk_uuid)}/detailed-status")

    def get_bulk_operation_status_count(self, bulk_uuid: str, status: int) -> int:
        """Get operations count by bulk UUID and status."""
        return self.get_json_api(f"/V1/bulk/{escape_path(bulk_uuid)}/operation-status/{status}")

    # Carts
    # =====

    def get_cart(self, cart_id: PathId, **kwargs) -> MagentoEntity:
        return self.get_json_api(f"/V1/carts/{escape_path(cart_id)}", **kwargs)

    def get_carts(self, *, query: Query = None, limit=-1, **kwargs) -> Iterable[MagentoEntity]:
        """Get all carts (generator)."""
        return self.get_paginated("/V1/carts/search", query=query, limit=limit, **kwargs)

    # Categories
    # ==========

    def get_categories(self, query: Query = None, path_prefix: Optional[str] = None, limit=-1, **kwargs) \
            -> Iterable[Category]:
        """
        Yield all categories.

        :param path_prefix: optional path prefix for the categories.
          Example: ``"1/2"`` for all categories whose path is ``"1/2/..."``, including ``"1/2"`` itself.
          Use ``"1/2/"`` to exclude ``"1/2"`` from the returned categories.
        :param query: optional query. This overrides ``path_prefix``.
        :param limit: optional limit
        """
        if query is None and path_prefix is not None:
            if path_prefix.endswith("/"):
                # "1/2/" -> LIKE "1/2/%"
                query = make_field_value_query("path", f"{path_prefix}%", "like")
            else:
                # "1/2" -> LIKE "1/2/%" OR = "1/2"
                query = make_search_query([[
                    ("path", f"{path_prefix}/%", "like"),
                    ("path", path_prefix, "eq"),
                ]])

        return self.get_paginated("/V1/categories/list", query=query, limit=limit, **kwargs)

    def get_category(self, category_id: PathId) -> Optional[Category]:
        """
        Return a category given its id.
        """
        return self.get_json_api(f"/V1/categories/{category_id}")

    def get_category_by_name(self, name: str, *, assert_one=False) -> Optional[Category]:
        """
        Return the first category with the given name.

        :param name: exact name of the category
        :param assert_one: if True, assert that either none or exactly one category matches this name
        :return:
        """
        limit = 2 if assert_one else 1
        categories = list(self.get_categories(make_field_value_query("name", name), limit=limit))

        if categories:
            if assert_one:
                assert len(categories) == 1, "There should not be more than one category with the name %s" % repr(name)

            return categories[0]

        return None

    def update_category(self, category_id: PathId, category_data: Category) -> Category:
        """
        Update a category.

        :param category_id:
        :param category_data: (partial) category data to update
        :return: updated category
        """
        return cast(Category, self.put_json_api(f"/V1/categories/{escape_path(category_id)}",
                                                json={"category": category_data}, throw=True))

    def create_category(self, category: Category, **kwargs) -> MagentoEntity:
        """
        Create a new category and return it.
        """
        return self.post_json_api("/V1/categories", json={"category": category}, **kwargs)

    def remove_category(self, category_id: PathId, **kwargs):
        """
        Remove a category.

        https://adobe-commerce.redoc.ly/2.4.6-admin/tag/categoriescategoryId/#operation/DeleteV1CategoriesCategoryId
        """
        return self.delete_api(f"/V1/categories/{escape_path(category_id)}", **kwargs)

    def get_child_categories(self, category_id: int, **kwargs):
        """
        Yield categories whose parent ID is the given ``category_id``.
        """
        return self.get_categories(
            query=make_field_value_query("parent_id", category_id),
            **kwargs,
        )

    def move_category(self, category_id: PathId, parent_id: int, *, after_id: Union[int, None] = None) -> bool:
        """
        Move a category under a new parent.

        :param category_id: ID of the category to move
        :param parent_id: ID of the new parent of the category
        :param after_id: optional ID of an existing child category
        :return: ``True``
        """
        params = {
            "parentId": parent_id,
        }
        if after_id is not None:
            params["afterId"] = after_id

        return self.put_json_api(f"/V1/categories/{escape_path(category_id)}/move", json=params)

    # Category products
    # -----------------

    def get_category_products(self, category_id: PathId, **kwargs) -> List[MagentoEntity]:
        """
        Get products assigned to a category.

        https://adobe-commerce.redoc.ly/2.4.6-admin/tag/categoriescategoryIdproducts#operation/GetV1CategoriesCategoryIdProducts

        Example:

            {'sku': 'MYSKU123', 'position': 2, 'category_id': '17'}
        """
        return self.get_json_api(f"/V1/categories/{escape_path(category_id)}/products", **kwargs)

    def add_product_to_category(self, category_id: PathId, product_link: MagentoEntity, **kwargs):
        """
        Assign a product to a category.

        https://adobe-commerce.redoc.ly/2.4.6-admin/tag/categoriescategoryIdproducts/#operation/PostV1CategoriesCategoryIdProducts

        :param category_id: ID of the category
        :param product_link: product link. See the Adobe Commerce documentation for the format.
        """
        return self.post_api(f"/V1/categories/{escape_path(category_id)}/products",
                             json={"productLink": product_link},
                             **kwargs)

    def remove_product_from_category(self, category_id: PathId, sku: Sku, **kwargs):
        """
        Remove a product from a category.

        https://adobe-commerce.redoc.ly/2.4.6-admin/tag/categoriescategoryIdproductssku/#operation/DeleteV1CategoriesCategoryIdProductsSku

        :param category_id: ID of the category
        :param sku: SKU of the product
        """
        return self.delete_api(f"/V1/categories/{escape_path(category_id)}/products/{escape_path(sku)}", **kwargs)

    # CMS
    # ===

    def get_cms_pages(self, *, query: Query = None, limit=-1, **kwargs) -> Iterable[MagentoEntity]:
        """Get all CMS pages (generator)."""
        return self.get_paginated("/V1/cmsPage/search", query=query, limit=limit, **kwargs)

    def get_cms_blocks(self, *, query: Query = None, limit=-1, **kwargs) -> Iterable[MagentoEntity]:
        """Get all CMS blocks (generator)."""
        return self.get_paginated("/V1/cmsBlock/search", query=query, limit=limit, **kwargs)

    def get_cms_block(self, block_id: str) -> MagentoEntity:
        """Get a single CMS block."""
        return self.get_json_api(f"/V1/cmsBlock/{escape_path(block_id)}")

    def delete_cms_block(self, block_id: str) -> bool:
        """Delete a CMS block by ID."""
        return self.delete_json_api(f"/V1/cmsBlock/{escape_path(block_id)}")

    # Countries
    # =========

    def get_countries(self) -> List[MagentoEntity]:
        """
        Get all countries and regions information for the store.

        https://adobe-commerce.redoc.ly/2.4.7-admin/tag/directorycountries
        """
        return self.get_json_api("/V1/directory/countries")

    def get_country(self, country_id: int) -> MagentoEntity:
        """
        Get information about a single country or region for the store.

        https://adobe-commerce.redoc.ly/2.4.7-admin/tag/directorycountriescountryId
        """
        return self.get_json_api(f"/V1/directory/countries/{escape_path(country_id)}")

    # Coupons
    # =======

    def create_coupon(self, coupon: MagentoEntity, **kwargs) -> MagentoEntity:
        """Create a coupon."""
        return self.post_json_api("/V1/coupons", json={"coupon": coupon}, **kwargs)

    def update_coupon(self, coupon_id: int, coupon: MagentoEntity, **kwargs) -> MagentoEntity:
        """Update a coupon."""
        return self.put_json_api(f"/V1/coupons/{escape_path(coupon_id)}", json={"coupon": coupon}, **kwargs)

    def get_coupons(self, *, query: Query = None, limit=-1, **kwargs) -> Iterable[MagentoEntity]:
        """Get all coupons (generator)."""
        return self.get_paginated("/V1/coupons/search", query=query, limit=limit, **kwargs)

    def get_coupon(self, coupon_id: int) -> MagentoEntity:
        """Get a coupon by ID."""
        return self.get_json_api(f"/V1/coupons/{escape_path(coupon_id)}")

    def delete_coupon(self, coupon_id: int) -> bool:
        """Delete a coupon by ID."""
        return self.delete_json_api(f"/V1/coupons/{escape_path(coupon_id)}")

    def delete_coupons(self, coupon_ids: Iterable[int], *, ignore_invalid_coupons=True, **kwargs):
        """Delete multiple coupons by ID."""
        return self.post_json_api("/V1/coupons/deleteByIds", json={
            "ids": list(coupon_ids),
            "ignoreInvalidCoupons": ignore_invalid_coupons,
        }, **kwargs)

    def delete_coupons_by_codes(self, coupon_codes: Iterable[str], *, ignore_invalid_coupons=True, **kwargs):
        """Delete multiple coupons by code."""
        return self.post_json_api("/V1/coupons/deleteByIds", json={
            "codes": list(coupon_codes),
            "ignoreInvalidCoupons": ignore_invalid_coupons,
        }, **kwargs)

    # Customers
    # =========

    def get_customers(self, *, query: Query = None, limit=-1, **kwargs) -> Iterable[Customer]:
        """Get all customers (generator)."""
        return self.get_paginated("/V1/customers/search", query=query, limit=limit, **kwargs)

    def get_customer(self, customer_id: Union[int, Literal["me"]], **kwargs) -> Customer:
        """
        Return a single customer.

        :param customer_id: either a customer ID or the string `"me"`.
        """
        # backward compatibility
        kwargs.setdefault("none_on_404", False)
        kwargs.setdefault("none_on_empty", False)
        return self.get_json_api(f"/V1/customers/{escape_path(customer_id)}",
                                 **kwargs)

    def get_current_customer(self, **kwargs):
        """Return the current customer."""
        return self.get_customer("me", **kwargs)

    def activate_current_customer(self, confirmation_key: str) -> Customer:
        """
        Activate a customer account using a key that was sent in a confirmation email.

        https://adobe-commerce.redoc.ly/2.4.7-admin/tag/customersmeactivate/

        :param confirmation_key: key from the confirmation email.
        :return: customer
        """
        return self.put_json_api("/V1/customers/me/activate", json={"confirmationKey": confirmation_key})

    def change_current_customer_password(self, current_password: str, new_password: str) -> bool:
        """
        Change customer password.

        https://adobe-commerce.redoc.ly/2.4.7-admin/tag/customersmepassword#operation/PutV1CustomersMePassword
        """
        return self.put_json_api("/V1/customers/me/password",
                                 json={"currentPassword": current_password, "newPassword": new_password})

    # Customer groups
    # ---------------

    def get_customer_groups(self, *, query: Query = None, limit=-1, **kwargs) -> Iterable[MagentoEntity]:
        """Get all customer groups (generator)."""
        return self.get_paginated("/V1/customerGroups/search", query=query, limit=limit, **kwargs)

    # Invoices
    # ========

    def create_order_invoice(self, order_id: PathId, payload: Optional[dict] = None, notify=True):
        """
        Create an invoice for an order.

        See:
        * https://devdocs.magento.com/guides/v2.4/rest/tutorials/orders/order-create-invoice.html
        * https://www.rakeshjesadiya.com/create-invoice-using-rest-api-magento-2/

        :param order_id: Order id.
        :param payload: payload to send to the API.
        :param notify: if True (default), notify the client. This is overridden by ``payload``.
        :return:
        """
        if payload is None:
            payload = {}

        payload.setdefault("notify", notify)

        return self.post_json_api(f"/V1/order/{escape_path(order_id)}/invoice", json=payload)

    def get_invoice(self, invoice_id: int) -> MagentoEntity:
        return self.get_json_api(f"/V1/invoices/{escape_path(invoice_id)}",
                                 # backward compatibility
                                 none_on_404=False,
                                 none_on_empty=False)

    def get_invoice_by_increment_id(self, increment_id: str) -> Optional[MagentoEntity]:
        query = make_field_value_query("increment_id", increment_id)
        for invoice in self.get_invoices(query=query, limit=1):
            return invoice
        return None

    def get_invoices(self, query: Query = None, limit=-1, **kwargs) -> Iterable[MagentoEntity]:
        """Get all invoices (generator)."""
        return self.get_paginated("/V1/invoices", query=query, limit=limit, **kwargs)

    def get_order_invoices(self, order_id: Union[int, str]):
        """Get invoices for the given order id."""
        return self.get_invoices(query=make_field_value_query("order_id", order_id))

    # Orders
    # ======

    def get_orders(self, *,
                   status: Optional[str] = None,
                   status_condition_type: Optional[str] = None,
                   limit=-1,
                   query: Query = None,
                   retry=0,
                   **kwargs) -> Iterator[Order]:
        """
        Return a generator of all orders with this status up to the limit.

        :param status: order status, e.g. "awaiting_shipping". This overrides ``query``.
        :param status_condition_type: condition type to use for the status. Default is "eq".
          This has no effect if ``status`` is not given.
        :param limit: maximum number of orders to yield (default: no limit).
        :param query: optional query.
        :param retry: max retries count
        :return: generator of orders
        """
        if status is not None:
            query = make_field_value_query("status", status, condition_type=status_condition_type)

        return self.get_paginated("/V1/orders", query=query, limit=limit, retry=retry, **kwargs)

    def get_last_orders(self, limit=10) -> List[Order]:
        """Return a list of the last orders (default: 10)."""
        query = make_search_query([], sort_orders=[("increment_id", "DESC")])
        return list(self.get_orders(query=query, limit=limit))

    def get_order_item(self, *, order_item_id: int, **kwargs) -> MagentoEntity:
        """Return a single order item."""
        return self.get_json_api(f"/V1/orders/items/{escape_path(order_item_id)}", **kwargs)

    def get_orders_items(self, *, sku: Optional[str] = None, query: Query = None, limit=-1, **kwargs):
        """
        Return orders items.

        :param sku: filter orders items on SKU. This is a shortcut for ``query=make_field_value_query("sku", sku)``.
        :param query: optional query. This take precedence over ``sku``.
        :param limit:
        :return:
        """
        if query is None and sku is not None:
            query = make_field_value_query("sku", sku)

        return self.get_paginated("/V1/orders/items", query=query, limit=limit, **kwargs)

    def get_order(self, order_id: str) -> Order:
        """
        Get an order given its entity id.
        """
        return self.get_json_api(f"/V1/orders/{order_id}",
                                 # backward compatibility
                                 none_on_404=False,
                                 none_on_empty=False)

    def get_order_by_increment_id(self, increment_id: str) -> Optional[Order]:
        """
        Get an order given its increment id. Return ``None`` if the order doesn’t exist.
        """
        query = make_field_value_query("increment_id", increment_id)
        for order in self.get_orders(query=query, limit=1):
            return order
        return None

    def hold_order(self, order_id: str, **kwargs):
        """
        Hold an order. This is the opposite of ``unhold_order``.

        :param order_id: order id (not increment id)
        """
        return self.post_api(f"/V1/orders/{escape_path(order_id)}/hold", **kwargs)

    def unhold_order(self, order_id: str, **kwargs):
        """
        Un-hold an order. This is the opposite of ``hold_order``.

        :param order_id: order id (not increment id)
        """
        return self.post_api(f"/V1/orders/{escape_path(order_id)}/unhold", **kwargs)

    def save_order(self, order: Order):
        """Save an order."""
        return self.post_api("/V1/orders", json={"entity": order})

    def set_order_status(self, order: Order, status: str, *, external_order_id: Optional[str] = None):
        """
        Change the status of an order, and optionally set its ``ext_order_id``. This is a convenient wrapper around
        ``save_order``.

        :param order: order payload
        :param status: new status
        :param external_order_id: optional external order id
        :return:
        """
        payload = {
            "entity_id": order["entity_id"],
            "status": status,
            "increment_id": order["increment_id"],  # we need to repeat increment_id, otherwise it is regenerated
        }
        if external_order_id is not None:
            payload["ext_order_id"] = external_order_id

        return self.save_order(payload)

    # Credit Memos
    # ============

    def get_credit_memos(self, query: Query = None, limit=-1, **kwargs) -> Iterable[MagentoEntity]:
        """Get all credit memos (generator)."""
        return self.get_paginated("/V1/creditmemos", query=query, limit=limit, **kwargs)

    # Prices
    # ======

    # Base Prices
    # -----------

    def get_base_prices(self, skus: Sequence[Sku]) -> List[MagentoEntity]:
        """
        Get base prices for a sequence of SKUs.
        """
        return self.post_json_api("/V1/products/base-prices-information",
                                  json={"skus": skus}, throw=True, bypass_read_only=True)

    def save_base_prices(self, prices: Sequence[MagentoEntity]):
        """
        Save base prices.

        Example:

            >>> self.save_base_prices([{"price": 3.14, "sku": "W1033", "store_id": 0}])

        :param prices: base prices to save.
        :return: `requests.Response` object
        """
        return self.post_api("/V1/products/base-prices", json={"prices": prices})

    # Special Prices
    # --------------

    def get_special_prices(self, skus: Sequence[Sku]) -> List[MagentoEntity]:
        """
        Get special prices for a sequence of SKUs.
        """
        return self.post_json_api("/V1/products/special-price-information",
                                  json={"skus": skus}, bypass_read_only=True)

    def save_special_prices(self, special_prices: Sequence[MagentoEntity]):
        """
        Save a sequence of special prices.

        Example:
            >>> price_from = "2022-01-01 00:00:00"
            >>> price_to = "2022-01-31 23:59:59"
            >>> special_price = {"store_id": 0, "sku": "W1033", "price": 2.99, \
                                 "price_from": price_from, "price_to": price_to}
            >>> self.save_special_prices([special_price])

        :param special_prices: Special prices to save.
        :return:
        """
        return self.post_api("/V1/products/special-price", json={"prices": special_prices})

    def delete_special_prices(self, special_prices: Sequence[MagentoEntity]):
        """
        Delete a sequence of special prices.
        """
        return self.post_api("/V1/products/special-price-delete", json={"prices": special_prices})

    def delete_special_prices_by_sku(self, skus: Sequence[Sku]):
        """
        Equivalent of ``delete_special_prices(get_special_prices(skus))``.
        """
        special_prices = self.get_special_prices(skus)
        return self.delete_special_prices(special_prices)

    # Products
    # ========

    def get_products(self, limit=-1, query: Query = None, retry=0, **kwargs):
        """
        Return a generator of all products.

        :param limit: -1 for unlimited.
        :param query:
        :param retry:
        :return:
        """
        return cast(Iterator[Product],
                    self.get_paginated("/V1/products/", query=query, limit=limit, retry=retry, **kwargs))

    def get_products_types(self) -> Sequence[MagentoEntity]:
        """Get available product types."""
        return self.get_json_api("/V1/product/types")

    def get_product(self, sku: Sku) -> Optional[Product]:
        """
        Get a single product. Return ``None`` if it doesn’t exist.

        :param sku: SKU of the product
        :return:
        """
        return self.get_json_api(f"/V1/products/{escape_path(sku)}", none_on_404=True)

    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """
        Get a product given its id. Return ``None`` if the product doesn’t exist.

        :param product_id: ID of the product
        :return:
        """
        query = make_field_value_query("entity_id", product_id)
        for product in self.get_products(query=query, limit=1):
            return product
        return None

    def get_product_by_query(self, query: Query, *, expect_one=True) -> Optional[Product]:
        """
        Get a product with a custom query. Return ``None`` if the query doesn’t return match any product, and raise
        an exception if it returns more than one, unless ``expect_one`` is set to ``False``.

        :param query:
        :param expect_one: if True (the default), raise an exception if the query returns more than one result.
        :return:
        """
        if not expect_one:
            for product in self.get_products(query=query, limit=1):
                return product
            return None

        products = list(self.get_products(query=query, limit=2))
        if not products:
            return None
        if len(products) == 1:
            return products[0]
        raise MagentoAssertionError("Got more than one product for query %r" % query)

    def get_product_medias(self, sku: Sku) -> Sequence[MediaEntry]:
        """
        Get the list of gallery entries associated with the given product.

        :param sku: SKU of the product.
        :return:
        """
        return self.get_json_api(f"/V1/products/{escape_path(sku)}/media")

    def get_product_media(self, sku: Sku, media_id: PathId) -> MediaEntry:
        """
        Return a gallery entry.

        :param sku: SKU of the product.
        :param media_id:
        :return:
        """
        return self.get_json_api(f"/V1/products/{escape_path(sku)}/media/{media_id}")

    def save_product_media(self, sku: Sku, media_entry: MediaEntry):
        """
        Save a product media.
        """
        return self.post_json_api(f"/V1/products/{escape_path(sku)}/media", json={"entry": media_entry})

    def delete_product_media(self, sku: Sku, media_id: PathId, throw=False):
        """
        Delete a media associated with a product.

        :param sku: SKU of the product
        :param media_id:
        :param throw:
        :return:
        """
        return self.delete_api(f"/V1/products/{escape_path(sku)}/media/{media_id}", throw=throw)

    def save_product(self, product, *, save_options: Optional[bool] = None, log_response=True) -> Product:
        """
        Save a product.

        :param product: product to save (can be partial).
        :param save_options: set the `saveOptions` attribute.
        :param log_response: log the Magento response
        :return:
        """
        payload: MagentoEntity = {"product": product}
        if save_options is not None:
            payload["saveOptions"] = save_options

        # throw=False so the log is printed before we raise
        resp = self.post_api("/V1/products", json=payload, throw=False)
        if log_response and self.logger:
            self.logger.debug("Save product response: %s", resp.text)
        raise_for_response(resp)
        return cast(Product, resp.json())

    def update_product(self, sku: Sku, product: Product, *, save_options: Optional[bool] = None) -> Product:
        """
        Update a product.

        Example:
            >>> Magento().update_product("SK1234", {"name": "My New Name"})

        To update the SKU of a product, pass its id along the new SKU and set `save_options=True`:

            >>> Magento().update_product("old-sku", {"id": 123, "sku": "new-sku"}, save_options=True)

        :param sku: SKU of the product to update
        :param product: (partial) product data to update
        :param save_options: set the `saveOptions` attribute.
        :return: updated product
        """
        payload: MagentoEntity = {"product": product}
        if save_options is not None:
            payload["saveOptions"] = save_options

        return cast(Product, self.put_json_api(f"/V1/products/{escape_path(sku)}", json=payload, throw=True))

    def delete_product(self, sku: Sku, skip_missing=False, throw=True, **kwargs) -> bool:
        """
        Delete a product given its SKU.

        :param sku:
        :param skip_missing: if true, don’t raise if the product is missing, and return False.
        :param throw: throw on error response
        :param kwargs: keyword arguments passed to all underlying methods.
        :return: a boolean indicating success.
        """
        try:
            response = self.delete_api(f"/V1/products/{escape_path(sku)}", throw=throw, **kwargs)
        except (HTTPError, MagentoException) as e:
            if skip_missing and e.response is not None and e.response.status_code == 404:
                return False
            raise

        # "Will returned True if deleted"
        # https://magento.redoc.ly/2.3.6-admin/tag/productssku#operation/catalogProductRepositoryV1DeleteByIdDelete
        return cast(bool, response.json())

    def async_update_products(self, product_updates: Iterable[Product]):
        """
        Update multiple products using the async bulk API.

        Example:
            >>> Magento().async_update_products([{"sku": "SK123", "name": "Abc"}, {"sku": "SK4", "name": "Def"}])

        See https://devdocs.magento.com/guides/v2.4/rest/bulk-endpoints.html

        :param product_updates: sequence of product data dicts. They MUST contain an `sku` key.
        :return:
        """
        payload = [{"product": product_update} for product_update in product_updates]
        return self.put_json_api("/V1/products/bySku", json=payload, throw=True, async_bulk=True)

    def get_product_stock_item(self, sku: Sku) -> MagentoEntity:
        """Get the stock item for an SKU."""
        return self.get_json_api(f"/V1/stockItems/{escape_path(sku)}",
                                 # backward compatibility
                                 none_on_404=False,
                                 none_on_empty=False)

    def update_product_stock_item(self, sku: Sku, stock_item_id: int, stock_item: dict) -> int:
        """
        Update the stock item of a product.
        https://adobe-commerce.redoc.ly/2.4.6-admin/tag/productsproductSkustockItemsitemId/#operation/PutV1ProductsProductSkuStockItemsItemId

        :param sku: SKU of the product
        :param stock_item_id: stock item ID. Note that it’s not clear why this ID is needed; it seems to be ignored by
          Magento and products always have a single stock item anyway.
        :param stock_item:
        :return: the stock item ID
        """
        return self.put_json_api(f"/V1/products/{escape_path(sku)}/stockItems/{stock_item_id}", json={
            "stockItem": stock_item,
        })

    def update_product_stock_item_quantity(self, sku: Sku, stock_item_id: int, quantity: int,
                                           is_in_stock: Optional[bool] = None):
        """
        Update the stock item of a product to set its quantity. This is a simplified version of
        ``update_product_stock_item``.

        :param sku: SKU of the product
        :param stock_item_id:
        :param quantity:
        :param is_in_stock: if not set, default to ``quantity > 0``
        :return: the stock item id
        """
        if is_in_stock is None:
            is_in_stock = quantity > 0

        return self.update_product_stock_item(sku, stock_item_id, {
            "qty": quantity,
            "is_in_stock": is_in_stock,
        })

    def set_product_stock_item(self, sku: Sku, quantity: int, is_in_stock=1):
        warnings.warn("set_product_stock_item is deprecated."
                      " Use update_product_stock_item_quantity(sku, stock_item_id, quantity) instead",
                      DeprecationWarning)
        return self.update_product_stock_item_quantity(sku,
                                                       1,
                                                       quantity=quantity,
                                                       is_in_stock=(is_in_stock == 1))

    def get_product_stock_status(self, sku: Sku) -> MagentoEntity:
        """Get stock status for an SKU."""
        return self.get_json_api(f"/V1/stockStatuses/{escape_path(sku)}",
                                 # backward compatibility
                                 none_on_404=False,
                                 none_on_empty=False)

    def link_child_product(self, parent_sku: Sku, child_sku: Sku, **kwargs) -> requests.Response:
        """
        Link two products, one as the parent of the other.

        :param parent_sku: SKU of the parent product
        :param child_sku: SKU of the child product
        :return: `requests.Response` object
        """
        return self.post_api(f"/V1/configurable-products/{escape_path(parent_sku)}/child",
                             json={"childSku": child_sku}, **kwargs)

    def unlink_child_product(self, parent_sku: Sku, child_sku: Sku, **kwargs) -> requests.Response:
        """
        Opposite of link_child_product().

        :param parent_sku: SKU of the parent product
        :param child_sku: SKU of the child product
        :return: `requests.Response` object
        """
        return self.delete_api(f"/V1/configurable-products/{escape_path(parent_sku)}/children/{escape_path(child_sku)}",
                               **kwargs)

    def save_configurable_product_option(self, sku: Sku, option: MagentoEntity, throw=False):
        """
        Save a configurable product option.

        :param sku: SKU of the product
        :param option: option to save
        :param throw:
        :return: `requests.Response` object
        """
        return self.post_api(f"/V1/configurable-products/{escape_path(sku)}/options",
                             json={"option": option}, throw=throw)

    # Products Attribute Options
    # --------------------------

    def get_products_attribute_options(self, attribute_code: str) -> Sequence[Dict[str, str]]:
        """
        Get all options for a products attribute.

        :param attribute_code:
        :return: sequence of option dicts.
        """
        response = self.get_json_api(f"/V1/products/attributes/{escape_path(attribute_code)}/options",
                                     # backward compatibility
                                     none_on_404=False,
                                     none_on_empty=False)
        return cast(Sequence[Dict[str, str]], response)

    def add_products_attribute_option(self, attribute_code: str, option: Dict[str, str]) -> str:
        """
        Add an option to a products attribute.

        https://magento.redoc.ly/2.3.6-admin/#operation/catalogProductAttributeOptionManagementV1AddPost

        :param attribute_code:
        :param option: dict with label/value keys (mandatory)
        :return: new id
        """
        payload = {"option": option}
        response = self.post_json_api(f"/V1/products/attributes/{escape_path(attribute_code)}/options",
                                      json=payload)
        ret = cast(str, response)

        if ret.startswith("id_"):
            ret = ret[3:]

        return ret

    def delete_products_attribute_option(self, attribute_code: str, option_id: PathId) -> bool:
        """
        Remove an option to a products attribute.

        :param attribute_code:
        :param option_id:
        :return: boolean
        """
        response = self.delete_api(f"/V1/products/attributes/{escape_path(attribute_code)}/options/{option_id}",
                                   throw=True)
        return cast(bool, response.json())

    # Aliases
    # -------

    def get_manufacturers(self):
        """
        Shortcut for `.get_products_attribute_options("manufacturer")`.
        """
        return self.get_products_attribute_options("manufacturer")

    # Sales Rules
    # ===========

    def get_sales_rules(self, *, query: Query = None, limit=-1, **kwargs) -> Iterable[MagentoEntity]:
        """Get all sales rules (generator)."""
        return self.get_paginated("/V1/salesRules/search", query=query, limit=limit, **kwargs)

    # Shipments
    # =========

    def get_shipments(self, *, query: Query = None, limit=-1, **kwargs) -> Iterable[MagentoEntity]:
        """Return shipments (generator)."""
        return self.get_paginated("/V1/shipments", query=query, limit=limit, **kwargs)

    def ship_order(self, order_id: PathId, payload: MagentoEntity):
        """
        Ship an order.
        """
        return self.post_api(f"/V1/order/{order_id}/ship", json=payload)

    def get_order_shipments(self, order_id: Union[int, str]):
        """Get shipments for the given order id."""
        return self.get_shipments(query=make_field_value_query("order_id", order_id))

    # Stock
    # =====

    def get_stock_source_links(self, query: Query = None, limit=-1, **kwargs) -> Iterable[MagentoEntity]:
        return self.get_paginated("/V1/inventory/stock-source-links", query=query, limit=limit, **kwargs)

    # Stores
    # ======

    def get_store_configs(self, store_codes: Optional[List[str]] = None) -> Iterable[MagentoEntity]:
        params: Dict[str, List[str]] = {}
        if store_codes is not None:
            params = {"storeCodes": store_codes}

        return self.get_json_api("/V1/store/storeConfigs", params=params)

    def get_store_groups(self) -> Iterable[MagentoEntity]:
        return self.get_json_api("/V1/store/storeGroups")

    def get_store_views(self) -> Iterable[MagentoEntity]:
        return self.get_json_api("/V1/store/storeViews")

    def get_websites(self) -> Iterable[MagentoEntity]:
        return self.get_json_api("/V1/store/websites")

    def get_current_store_group_id(self, *, skip_store_groups=False) -> int:
        """
        Get the current store group id for the current scope. This is not part of Magento API.

        :param skip_store_groups: if True, assume the current scope is not already a store group.
        """
        if not skip_store_groups:
            # If scope is already a store group
            for store_group in self.get_store_groups():
                if store_group["code"] == self.scope:
                    return store_group["id"]

        # If scope is a website
        for website in self.get_websites():
            if website["code"] == self.scope:
                return website["default_group_id"]

        # If scope is a view
        for view in self.get_store_views():
            if view["code"] == self.scope:
                return view["store_group_id"]

        raise RuntimeError("Can't determine the store group id of scope %r" % self.scope)

    def get_root_category_id(self) -> int:
        """
        Get the root category id of the current scope. This is not part of Magento API.
        """
        store_group_root_category_id: Dict[int, int] = {}

        store_groups = list(self.get_store_groups())
        for store_group in store_groups:
            root_category_id: int = store_group["root_category_id"]

            # If scope is a store group
            if store_group["code"] == self.scope:
                return root_category_id

            store_group_root_category_id[store_group["id"]] = root_category_id

        return store_group_root_category_id[self.get_current_store_group_id(skip_store_groups=True)]

    # Sources
    # =======

    def get_sources(self, query: Query = None, limit=-1, **kwargs) -> Iterable[MagentoEntity]:
        """
        Get all sources.

        https://adobe-commerce.redoc.ly/2.4.6-admin/tag/inventorysources#operation/GetV1InventorySources
        """
        return self.get_paginated("/V1/inventory/sources", query=query, limit=limit, **kwargs)

    def get_source(self, source_code: str) -> Optional[MagentoEntity]:
        """
        Get a single source, or `None` if it doesn’t exist.

        https://adobe-commerce.redoc.ly/2.4.6-admin/tag/inventorysourcessourceCode#operation/GetV1InventorySourcesSourceCode
        """
        return self.get_json_api(f"/V1/inventory/sources/{escape_path(source_code)}")

    def save_source(self, source: MagentoEntity):
        """
        Save a source.

        https://adobe-commerce.redoc.ly/2.4.6-admin/tag/inventorysources/#operation/PostV1InventorySources
        """
        return self.post_json_api("/V1/inventory/sources", json={"source": source})

    # Source Items
    # ============

    def get_source_items(self, source_code: Optional[str] = None, sku: Optional[str] = None,
                         *,
                         skus: Optional[Iterable[str]] = None,
                         query: Query = None, limit=-1,
                         **kwargs) -> Iterable[MagentoEntity]:
        """
        Return a generator of all source items.

        :param source_code: optional source_code to filter on. This takes precedence over the query parameter.
        :param sku: optional SKU to filter on. This takes precedence over the query and the skus parameter.
        :param skus: optional SKUs list to filter on. This takes precedence of the query parameter.
        :param query: optional query.
        :param limit: -1 for unlimited.
        :return:
        """
        if source_code is not None or sku is not None or skus is not None:
            filter_groups = []
            if source_code:
                filter_groups.append([("source_code", source_code, "eq")])
            if sku:
                filter_groups.append([("sku", sku, "eq")])
            elif skus:
                filter_groups.append([("sku", ",".join(skus), "in")])

            query = make_search_query(filter_groups)

        return self.get_paginated("/V1/inventory/source-items", query=query, limit=limit, **kwargs)

    def save_source_items(self, source_items: Sequence[SourceItem]):
        """
        Save a sequence of source-items. Return None if the sequence is empty.

        :param source_items:
        :return:
        """
        if not source_items:
            return None
        return self.post_json_api("/V1/inventory/source-items", json={"sourceItems": source_items})

    def delete_source_items(self, source_items: Iterable[SourceItem], throw=True, **kwargs):
        """
        Delete a sequence of source-items. Only the SKU and the source_code are used.
        Note: Magento returns an error if this is called with empty source_items.

        :param source_items:
        :param throw:
        :param kwargs: keyword arguments passed to the underlying POST call.
        :return: requests.Response object
        """
        payload = {
            "sourceItems": [{"sku": s["sku"], "source_code": s["source_code"]} for s in source_items],
        }
        return self.post_api("/V1/inventory/source-items-delete", json=payload, throw=throw, **kwargs)

    def delete_default_source_items(self):
        """
        Delete all source items that have a source_code=default.

        :return: requests.Response object if there are default source items, None otherwise.
        """
        # remove default source that is set for new products
        default_source_items = self.get_source_items(source_code="default")
        source_items = [{"sku": item["sku"], "source_code": "default"} for item in default_source_items]

        if source_items:
            return self.delete_source_items(source_items)

    # Taxes
    # =====

    def get_tax_classes(self, *, query: Query = None, limit=-1, **kwargs) -> Iterable[MagentoEntity]:
        """Get all tax classes (generator)."""
        return self.get_paginated("/V1/taxClasses/search", query=query, limit=limit, **kwargs)

    def get_tax_rates(self, *, query: Query = None, limit=-1, **kwargs) -> Iterable[MagentoEntity]:
        """Get all tax rates (generator)."""
        return self.get_paginated("/V1/taxRates/search", query=query, limit=limit, **kwargs)

    def get_tax_rules(self, *, query: Query = None, limit=-1, **kwargs) -> Iterable[MagentoEntity]:
        """Get all tax rules (generator)."""
        return self.get_paginated("/V1/taxRules/search", query=query, limit=limit, **kwargs)

    # Modules
    # =======

    def get_modules(self, query: Query = None, limit=-1, **kwargs) -> Iterable[MagentoEntity]:
        """Get all enabled modules (generator)."""
        return self.get_paginated("/V1/modules", query=query, limit=limit, **kwargs)

    # Helpers
    # =======

    # Categories
    # ----------

    def get_categories_under_root(self, root_category_id: Optional[int] = None, include_root=False):
        """
        Like get_categories(), but get only categories under a root id.

        :param root_category_id: optional root category to use.
          If not provided, defaults to the store’s root category id.
        :param include_root: if True, include the root category in the results (default: False).
        :return:
        """
        if root_category_id is None:
            root_category_id = self.get_root_category_id()

        root_category = self.get_category(root_category_id)
        if root_category is None:
            return

        path_prefix = root_category["path"]
        if not include_root:
            path_prefix += "/"

        yield from self.get_categories(path_prefix=path_prefix)

    # Products
    # --------

    def sku_exists(self, sku: str):
        """Test if a SKU exists in Magento."""
        # Update this if you find a more efficient way of doing it
        return self.get_product(sku) is not None

    def sku_was_bought(self, sku: str):
        """
        Test if there exists at least one order with the given SKU.
        """
        for _ in self.get_orders_items(sku=sku, limit=1):
            return True
        return False

    # Internals
    # =========

    def request_api(self, method: str, path: str, *args, async_bulk=False, throw=False, retry=0, **kwargs):
        """
        Equivalent of .request() that prefixes the path with the base API URL.

        :param method: HTTP method
        :param path: API path. This must start with "/V1/"
        :param args: arguments passed to ``.request()``
        :param async_bulk: if True, use the "/async/bulk" prefix.
            https://devdocs.magento.com/guides/v2.3/rest/bulk-endpoints.html
        :param throw: if True, raise an exception if the response is an error
        :param retry: if non-zero, retry the request that many times if there is an error, sleeping 10s between
            each request.
        :param kwargs: keyword arguments passed to ``.request()``
        :return:
        """
        assert path.startswith("/V1/")

        full_path = "/rest"
        if self.scope != "default":
            full_path += f"/{self.scope}"

        if async_bulk:
            full_path += "/async/bulk"

        full_path += path

        if self.logger:
            self.logger.debug("%s %s", method, full_path)
        r = super().request_api(method, full_path, *args, throw=False, **kwargs)
        while not r.ok and retry > 0:
            retry -= 1
            time.sleep(10)
            r = super().request_api(method, full_path, *args, throw=False, **kwargs)

        if throw:
            raise_for_response(r)
        return r

    def get_paginated(self, path: str, *, query: Query = None, limit=-1, retry=0, page_size: Optional[int] = None):
        """
        Get a paginated API path.

        :param path:
        :param query:
        :param limit: -1 for no limit
        :param retry:
        :param page_size: default is `self.PAGE_SIZE`
        :return:
        """
        if limit == 0:
            return

        if page_size is None:
            page_size = self.PAGE_SIZE
        is_limited = limit > 0

        if is_limited and limit < page_size:
            page_size = limit

        if query is not None:
            query = query.copy()
        else:
            query = {}

        query["searchCriteria[pageSize]"] = page_size

        current_page = 1
        count = 0

        while True:
            page_query = query.copy()
            page_query["searchCriteria[currentPage]"] = current_page

            res = self.get_json_api(path, page_query,
                                    none_on_404=False,
                                    none_on_empty=False,
                                    retry=retry)
            items: list = res.get("items", [])
            if not items:
                break

            total_count: int = res["total_count"]

            for item in items:
                if self.logger and count and count % 1000 == 0:
                    self.logger.debug(f"loaded {count} items")
                yield item
                count += 1
                if count >= total_count:
                    return

                if is_limited and count >= limit:
                    return

            current_page += 1
