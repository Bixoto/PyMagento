import time
from json.decoder import JSONDecodeError
from logging import Logger
from os import environ
from typing import Optional, Sequence, Dict, Union, cast, Iterator, Iterable, List, Literal, Any

import requests
from api_session import APISession, escape_path, JSONDict
from requests.exceptions import HTTPError

from magento.exceptions import MagentoException, MagentoAssertionError
from magento.queries import Query, make_search_query, make_field_value_query
from magento.types import Product, SourceItem, Sku, Category, MediaEntry, MagentoEntity, Order, PathId, Customer, \
    SourceItemIn, BasePrice
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


def raise_for_response(response: requests.Response) -> None:
    """Equivalent of `requests.Response#raise_for_status` with some Magento specifics."""
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


class Magento(APISession):
    """Client for the Magento API."""
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
                 read_only: bool = False,
                 user_agent: Optional[str] = None,
                 *,
                 batch_page_size: Optional[int] = None,
                 **kwargs: Any):
        """Create a Magento client instance. All arguments are optional and fall back on environment variables named
        ``PYMAGENTO_ + argument.upper()`` (``PYMAGENTO_TOKEN``, ``PYMAGENTO_BASE_URL``, etc.).
        The ``token`` and ``base_url`` **must** be given either as arguments or environment variables.

        :param token: API integration token
        :param base_url: base URL of the Magento instance
        :param scope: API scope. Default on ``PYMAGENTO_SCOPE`` if set, or ``"all"``. Note this scope is mostly useless,
            see https://github.com/magento/magento2/issues/15461#issuecomment-1157935732.
        :param batch_page_size: if set, override the default page size used for batch queries.
        :param logger: optional logger.
        :param read_only: if True, raise on calls that write data, such as `POST`, `PUT`, `DELETE`.
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

    def delete_customer_address(self, address_id: int, **kwargs: Any) -> bool:
        """Delete customer address by ID."""
        deleted: bool = self.delete_json_api(f"/V1/addresses/{escape_path(address_id)}", **kwargs)
        return deleted

    # Apple Pay
    # =========

    def get_apple_pay_auth(self, **kwargs: Any) -> MagentoEntity:
        """Return details required to be able to submit a payment with Apple Pay.

        https://adobe-commerce.redoc.ly/2.4.6-admin/tag/applepayauth/#operation/GetV1ApplepayAuth
        """
        auth: MagentoEntity = self.get_json_api("/V1/applepay/auth", **kwargs)
        return auth

    # Attributes
    # ==========

    def save_attribute(self, attribute: MagentoEntity, *, with_defaults: bool = True, **kwargs: Any) -> MagentoEntity:
        """Save an attribute."""
        if with_defaults:
            base = DEFAULT_ATTRIBUTE_DICT.copy()
            base.update(attribute)
            attribute = base

        attribute = self.post_json_api("/V1/products/attributes", json={"attribute": attribute},
                                       **kwargs)
        return attribute

    def delete_attribute(self, attribute_code: str, **kwargs: Any) -> bool:
        """Delete an attribute."""
        ok: bool = self.delete_json_api(f"/V1/products/attributes/{escape_path(attribute_code)}", **kwargs)
        return ok

    # Attribute Sets
    # ==============

    def get_attribute_sets(self, query: Query = None, limit: int = -1, **kwargs: Any) -> Iterator[MagentoEntity]:
        """Get all attribute sets (generator)."""
        return self.get_paginated("/V1/eav/attribute-sets/list", query=query, limit=limit, **kwargs)

    def get_attribute_set_attributes(self, attribute_set_id: int, **kwargs: Any) -> List[MagentoEntity]:
        """Get all attributes for the given attribute set id."""
        attributes: List[MagentoEntity] = self.get_json_api(
            f"/V1/products/attribute-sets/{escape_path(attribute_set_id)}/attributes",
            **kwargs)
        return attributes

    def assign_attribute_set_attribute(self, attribute_set_id: int, attribute_group_id: int, attribute_code: str,
                                       sort_order: int = 0, **kwargs: Any) -> int:
        """Assign an attribute to an attribute set.

        https://adobe-commerce.redoc.ly/2.4.8-admin/tag/productsattribute-setsattributes#operation/PostV1ProductsAttributesetsAttributes

        :param attribute_set_id: ID of the attribute set.
        :param attribute_group_id: ID of the attribute group. It must be in the attribute set.
        :param attribute_code: code of the attribute to add in that attribute group and so in that attribute set.
        :param sort_order:
        :param kwargs:
        :return:
        """
        res: int = self.post_json_api("/V1/products/attribute-sets/attributes", json={
            "attributeCode": attribute_code,
            "attributeGroupId": attribute_group_id,
            "attributeSetId": attribute_set_id,
            "sortOrder": sort_order,
        }, **kwargs)
        return res

    def remove_attribute_set_attribute(self, attribute_set_id: int, attribute_code: str, **kwargs: Any) -> bool:
        """Remove an attribute from an attribute set."""
        path = f"/V1/products/attribute-sets/{escape_path(attribute_set_id)}/attributes/{escape_path(attribute_code)}"
        ok: bool = self.delete_json_api(path, **kwargs)
        return ok

    # Bulk Operations
    # ===============

    def get_bulk_operations(self, *, query: Query = None, limit: int = -1, **kwargs: Any) -> Iterator[MagentoEntity]:
        """List the bulk operation items.

        https://adobe-commerce.redoc.ly/2.4.8-admin/tag/bulk#operation/GetV1Bulk
        """
        return self.get_paginated("/V1/bulk", query=query, limit=limit, **kwargs)

    def get_bulk_status(self, bulk_uuid: str, none_on_404: bool = False, **kwargs: Any) -> MagentoEntity:
        """Get the status of an async/bulk operation."""
        status: MagentoEntity = self.get_json_api(f"/V1/bulk/{escape_path(bulk_uuid)}/status",
                                                  none_on_404=none_on_404,
                                                  none_on_empty=False,
                                                  **kwargs)
        return status

    def get_bulk_detailed_status(self, bulk_uuid: str, **kwargs: Any) -> MagentoEntity:
        """Get the detailed status of an async/bulk operation."""
        status: MagentoEntity = self.get_json_api(f"/V1/bulk/{escape_path(bulk_uuid)}/detailed-status", **kwargs)
        return status

    def get_bulk_operation_status_count(self, bulk_uuid: str, status: int, **kwargs: Any) -> int:
        """Get operations count by bulk UUID and status."""
        count: int = self.get_json_api(f"/V1/bulk/{escape_path(bulk_uuid)}/operation-status/{status}", **kwargs)
        return count

    # Carts
    # =====

    def get_cart(self, cart_id: PathId, **kwargs: Any) -> MagentoEntity:
        """Get a cart."""
        cart: MagentoEntity = self.get_json_api(f"/V1/carts/{escape_path(cart_id)}", **kwargs)
        return cart

    def get_carts(self, *, query: Query = None, limit: int = -1, **kwargs: Any) -> Iterator[MagentoEntity]:
        """Get all carts (generator)."""
        return self.get_paginated("/V1/carts/search", query=query, limit=limit, **kwargs)

    # Categories
    # ==========

    def get_categories(self, query: Query = None, path_prefix: Optional[str] = None, limit: int = -1, **kwargs: Any) \
            -> Iterator[Category]:
        """Yield all categories.

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

        return cast(Iterator[Category], self.get_paginated("/V1/categories/list", query=query, limit=limit, **kwargs))

    def get_category(self, category_id: PathId, **kwargs: Any) -> Optional[Category]:
        """Return a category given its id."""
        category: Optional[Category] = self.get_json_api(f"/V1/categories/{category_id}", **kwargs)
        return category

    def get_category_by_name(self, name: str, *, assert_one: bool = False, **kwargs: Any) -> Optional[Category]:
        """Return the first category with the given name.

        :param name: exact name of the category
        :param assert_one: if True, assert that either none or exactly one category matches this name
        :return:
        """
        limit = 2 if assert_one else 1
        categories = list(self.get_categories(make_field_value_query("name", name), limit=limit, **kwargs))

        if categories:
            if assert_one:
                assert len(categories) == 1, "There should not be more than one category with the name %s" % repr(name)

            return categories[0]

        return None

    def update_category(self, category_id: PathId, category_data: Category, **kwargs: Any) -> Category:
        """Update a category.

        :param category_id:
        :param category_data: (partial) category data to update
        :return: updated category
        """
        category: Category = self.put_json_api(f"/V1/categories/{escape_path(category_id)}",
                                               json={"category": category_data}, throw=True,
                                               **kwargs)
        return category

    def create_category(self, category: Category, **kwargs: Any) -> Category:
        """Create a new category and return it."""
        category = self.post_json_api("/V1/categories", json={"category": category}, **kwargs)
        return category

    def remove_category(self, category_id: PathId, **kwargs: Any) -> bool:
        """Remove a category.

        https://adobe-commerce.redoc.ly/2.4.6-admin/tag/categoriescategoryId/#operation/DeleteV1CategoriesCategoryId
        """
        ok: bool = self.delete_json_api(f"/V1/categories/{escape_path(category_id)}", **kwargs)
        return ok

    def get_child_categories(self, category_id: int, **kwargs: Any) -> Iterator[Category]:
        """Yield categories whose parent ID is the given ``category_id``."""
        return self.get_categories(
            query=make_field_value_query("parent_id", category_id),
            **kwargs,
        )

    def move_category(self, category_id: PathId, parent_id: int, *, after_id: Optional[int] = None, **kwargs: Any) \
            -> bool:
        """Move a category under a new parent.

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

        ok: bool = self.put_json_api(f"/V1/categories/{escape_path(category_id)}/move", json=params, **kwargs)
        return ok

    # Category products
    # -----------------

    def get_category_products(self, category_id: PathId, **kwargs: Any) -> List[MagentoEntity]:
        """Get products assigned to a category.

        https://adobe-commerce.redoc.ly/2.4.6-admin/tag/categoriescategoryIdproducts#operation/GetV1CategoriesCategoryIdProducts

        Example:

            {'sku': 'MYSKU123', 'position': 2, 'category_id': '17'}
        """
        products: List[MagentoEntity] = self.get_json_api(f"/V1/categories/{escape_path(category_id)}/products",
                                                          **kwargs)
        return products

    def add_product_to_category(self, category_id: PathId, product_link: MagentoEntity, **kwargs: Any) -> bool:
        """Assign a product to a category.

        https://adobe-commerce.redoc.ly/2.4.6-admin/tag/categoriescategoryIdproducts/#operation/PostV1CategoriesCategoryIdProducts

        :param category_id: ID of the category
        :param product_link: product link. See the Adobe Commerce documentation for the format.
        """
        ok: bool = self.post_json_api(f"/V1/categories/{escape_path(category_id)}/products",
                                      json={"productLink": product_link},
                                      **kwargs)
        return ok

    def remove_product_from_category(self, category_id: PathId, sku: Sku, **kwargs: Any) -> bool:
        """Remove a product from a category.

        https://adobe-commerce.redoc.ly/2.4.6-admin/tag/categoriescategoryIdproductssku/#operation/DeleteV1CategoriesCategoryIdProductsSku

        :param category_id: ID of the category
        :param sku: SKU of the product
        """
        ok: bool = self.delete_json_api(f"/V1/categories/{escape_path(category_id)}/products/{escape_path(sku)}",
                                        **kwargs)
        return ok

    # CMS
    # ===

    def get_cms_pages(self, *, query: Query = None, limit: int = -1, **kwargs: Any) -> Iterator[MagentoEntity]:
        """Get all CMS pages (generator)."""
        return self.get_paginated("/V1/cmsPage/search", query=query, limit=limit, **kwargs)

    def get_cms_blocks(self, *, query: Query = None, limit: int = -1, **kwargs: Any) -> Iterator[MagentoEntity]:
        """Get all CMS blocks (generator)."""
        return self.get_paginated("/V1/cmsBlock/search", query=query, limit=limit, **kwargs)

    def get_cms_block(self, block_id: str, **kwargs: Any) -> MagentoEntity:
        """Get a single CMS block."""
        block: MagentoEntity = self.get_json_api(f"/V1/cmsBlock/{escape_path(block_id)}", **kwargs)
        return block

    def delete_cms_block(self, block_id: str, **kwargs: Any) -> bool:
        """Delete a CMS block by ID."""
        ok: bool = self.delete_json_api(f"/V1/cmsBlock/{escape_path(block_id)}", **kwargs)
        return ok

    # Countries
    # =========

    def get_countries(self, **kwargs: Any) -> List[MagentoEntity]:
        """Get all countries and regions information for the store.

        https://adobe-commerce.redoc.ly/2.4.7-admin/tag/directorycountries
        """
        countries: List[MagentoEntity] = self.get_json_api("/V1/directory/countries", **kwargs)
        return countries

    def get_country(self, country_id: int, **kwargs: Any) -> MagentoEntity:
        """Get information about a single country or region for the store.

        https://adobe-commerce.redoc.ly/2.4.7-admin/tag/directorycountriescountryId
        """
        country: MagentoEntity = self.get_json_api(f"/V1/directory/countries/{escape_path(country_id)}", **kwargs)
        return country

    # Coupons
    # =======

    def create_coupon(self, coupon: MagentoEntity, **kwargs: Any) -> MagentoEntity:
        """Create a coupon."""
        coupon = self.post_json_api("/V1/coupons", json={"coupon": coupon}, **kwargs)
        return coupon

    def update_coupon(self, coupon_id: int, coupon: MagentoEntity, **kwargs: Any) -> MagentoEntity:
        """Update a coupon."""
        coupon = self.put_json_api(f"/V1/coupons/{escape_path(coupon_id)}", json={"coupon": coupon}, **kwargs)
        return coupon

    def get_coupons(self, *, query: Query = None, limit: int = -1, **kwargs: Any) -> Iterator[MagentoEntity]:
        """Get all coupons (generator)."""
        coupons: Iterator[MagentoEntity] = self.get_paginated("/V1/coupons/search", query=query, limit=limit,
                                                              **kwargs)
        return coupons

    def get_coupon(self, coupon_id: int, **kwargs: Any) -> MagentoEntity:
        """Get a coupon by ID."""
        coupon: MagentoEntity = self.get_json_api(f"/V1/coupons/{escape_path(coupon_id)}", **kwargs)
        return coupon

    def delete_coupon(self, coupon_id: int, **kwargs: Any) -> bool:
        """Delete a coupon by ID."""
        ok: bool = self.delete_json_api(f"/V1/coupons/{escape_path(coupon_id)}", **kwargs)
        return ok

    def delete_coupons(self, coupon_ids: Iterable[int], *, ignore_invalid_coupons: bool = True, **kwargs: Any):
        """Delete multiple coupons by ID."""
        return self.post_json_api("/V1/coupons/deleteByIds", json={
            "ids": list(coupon_ids),
            "ignoreInvalidCoupons": ignore_invalid_coupons,
        }, **kwargs)

    def delete_coupons_by_codes(self, coupon_codes: Iterable[str], *, ignore_invalid_coupons: bool = True,
                                **kwargs: Any):
        """Delete multiple coupons by code."""
        return self.post_json_api("/V1/coupons/deleteByIds", json={
            "codes": list(coupon_codes),
            "ignoreInvalidCoupons": ignore_invalid_coupons,
        }, **kwargs)

    # Customers
    # =========

    def get_customers(self, *, query: Query = None, limit: int = -1, **kwargs: Any) -> Iterator[Customer]:
        """Get all customers (generator)."""
        return self.get_paginated("/V1/customers/search", query=query, limit=limit, **kwargs)

    def get_customer(self, customer_id: Union[int, Literal["me"]], *,
                     none_on_404: bool = False,
                     none_on_empty: bool = False,
                     **kwargs: Any) -> Customer:
        """Return a single customer.

        :param customer_id: either a customer ID or the string `"me"`.
        :param none_on_404:
        :param none_on_empty:
        """
        return self.get_json_api(f"/V1/customers/{escape_path(customer_id)}",
                                 none_on_404=none_on_404,
                                 none_on_empty=none_on_empty,
                                 **kwargs)

    def get_current_customer(self, **kwargs: Any):
        """Return the current customer."""
        return self.get_customer("me", **kwargs)

    def activate_current_customer(self, confirmation_key: str, **kwargs: Any) -> Customer:
        """Activate a customer account using a key that was sent in a confirmation email.

        https://adobe-commerce.redoc.ly/2.4.7-admin/tag/customersmeactivate/

        :param confirmation_key: key from the confirmation email.
        :return: customer
        """
        return self.put_json_api("/V1/customers/me/activate",
                                 json={"confirmationKey": confirmation_key},
                                 **kwargs)

    def change_current_customer_password(self, current_password: str, new_password: str, **kwargs: Any) -> bool:
        """Change customer password.

        https://adobe-commerce.redoc.ly/2.4.7-admin/tag/customersmepassword#operation/PutV1CustomersMePassword
        """
        return self.put_json_api("/V1/customers/me/password",
                                 json={"currentPassword": current_password, "newPassword": new_password},
                                 **kwargs)

    # Customer groups
    # ---------------

    def get_customer_groups(self, *, query: Query = None, limit: int = -1, **kwargs: Any) -> Iterator[MagentoEntity]:
        """Get all customer groups (generator)."""
        return self.get_paginated("/V1/customerGroups/search", query=query, limit=limit, **kwargs)

    # Invoices
    # ========

    def create_order_invoice(self, order_id: PathId, payload: Optional[dict] = None, notify: bool = True,
                             **kwargs: Any):
        """Create an invoice for an order.

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

        return self.post_json_api(f"/V1/order/{escape_path(order_id)}/invoice", json=payload, **kwargs)

    def get_invoice(self, invoice_id: int, *,
                    none_on_404: bool = False,
                    none_on_empty: bool = False,
                    **kwargs: Any) -> MagentoEntity:
        """Get an invoice by ID."""
        return self.get_json_api(f"/V1/invoices/{escape_path(invoice_id)}",
                                 none_on_404=none_on_404,
                                 none_on_empty=none_on_empty,
                                 **kwargs)

    def get_invoice_by_increment_id(self, increment_id: str) -> Optional[MagentoEntity]:
        """Get an invoice by increment ID."""
        query = make_field_value_query("increment_id", increment_id)
        for invoice in self.get_invoices(query=query, limit=1):
            return invoice
        return None

    def get_invoices(self, query: Query = None, limit: int = -1, **kwargs: Any) -> Iterator[MagentoEntity]:
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
                   limit: int = -1,
                   query: Query = None,
                   retry=0,
                   **kwargs: Any) -> Iterator[Order]:
        """Return a generator of all orders with this status up to the limit.

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

    def get_last_orders(self, limit: int = 10) -> List[Order]:
        """Return a list of the last orders (default: 10)."""
        query = make_search_query([], sort_orders=[("increment_id", "DESC")])
        return list(self.get_orders(query=query, limit=limit))

    def get_orders_by_increment_ids(self, increment_ids: Iterable[str]) -> Dict[str, Order]:
        """Get multiple orders from an iterable of increment IDs. Return a dict of increment ID -> order."""
        query = make_search_query([
            [("increment_id", ",".join(increment_ids), "in")]
        ])
        return {
            order["increment_id"]: order
            for order in self.get_orders(query=query)
        }

    def get_order_item(self, order_item_id: int, **kwargs: Any) -> MagentoEntity:
        """Return a single order item."""
        return self.get_json_api(f"/V1/orders/items/{escape_path(order_item_id)}", **kwargs)

    def get_orders_items(self, *, sku: Optional[str] = None, query: Query = None, limit: int = -1, **kwargs: Any):
        """Return orders items.

        :param sku: filter orders items on SKU. This is a shortcut for ``query=make_field_value_query("sku", sku)``.
        :param query: optional query. This take precedence over ``sku``.
        :param limit:
        :return:
        """
        if query is None and sku is not None:
            query = make_field_value_query("sku", sku)

        return self.get_paginated("/V1/orders/items", query=query, limit=limit, **kwargs)

    def get_order(self, order_id: Union[str, int], *,
                  none_on_404: bool = False,
                  none_on_empty: bool = False,
                  **kwargs: Any) -> Order:
        """Get an order given its entity id."""
        return self.get_json_api(f"/V1/orders/{order_id}",
                                 none_on_404=none_on_404,
                                 none_on_empty=none_on_empty,
                                 **kwargs)

    def get_order_by_increment_id(self, increment_id: str, **kwargs: Any) -> Optional[Order]:
        """Get an order given its increment id. Return ``None`` if the order doesn’t exist."""
        query = make_field_value_query("increment_id", increment_id)
        for order in self.get_orders(query=query, limit=1, **kwargs):
            return order
        return None

    def hold_order(self, order_id: Union[str, int], **kwargs: Any):
        """Hold an order. This is the opposite of ``unhold_order``.

        :param order_id: order id (not increment id)
        """
        return self.post_json_api(f"/V1/orders/{escape_path(order_id)}/hold", **kwargs)

    def unhold_order(self, order_id: Union[str, int], **kwargs: Any):
        """Un-hold an order. This is the opposite of ``hold_order``.

        :param order_id: order id (not increment id)
        """
        return self.post_json_api(f"/V1/orders/{escape_path(order_id)}/unhold", **kwargs)

    def save_order(self, order: Order, **kwargs: Any):
        """Save an order."""
        return self.post_api("/V1/orders", json={"entity": order}, **kwargs)

    def set_order_status(self, order: Order, status: str, *, external_order_id: Optional[str] = None, **kwargs: Any):
        """Change the status of an order, and optionally set its ``ext_order_id``. This is a convenient wrapper around
        ``save_order``.
        Note it does not check if orders are on hold before, and may result in invalid states where an order has a state
        'holded' and a status that's not 'holded'.

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

        return self.save_order(payload, **kwargs)

    # Credit Memos
    # ============

    def get_credit_memos(self, query: Query = None, limit: int = -1, **kwargs: Any) -> Iterator[MagentoEntity]:
        """Get all credit memos (generator)."""
        return self.get_paginated("/V1/creditmemos", query=query, limit=limit, **kwargs)

    # Prices
    # ======

    # Base Prices
    # -----------

    def get_base_prices(self, skus: Sequence[Sku], *, store_id: Union[int, None] = None, **kwargs: Any) -> List[
        BasePrice]:
        """Get base prices for a sequence of SKUs.

        :param skus:
        :param store_id: Filter by store ID.
          This is done on the response as Magento doesn’t support this filter in the REST API.
        :param kwargs:
        :return:
        """
        prices = self.post_json_api("/V1/products/base-prices-information",
                                    json={"skus": skus}, bypass_read_only=True, **kwargs)

        if store_id is not None:
            prices = [price for price in prices
                      if price["store_id"] == store_id]

        return prices

    def save_base_prices(self, prices: Sequence[BasePrice], **kwargs: Any) -> List[JSONDict]:
        """Save base prices.

        Example:

            >>> self.save_base_prices([{"price": 3.14, "sku": "W1033", "store_id": 0}])

        :param prices: base prices to save.
        :return: a list of errors (if any)
        """
        return self.post_json_api("/V1/products/base-prices", json={"prices": prices}, **kwargs)

    # Special Prices
    # --------------

    def get_special_prices(self, skus: Sequence[Sku], *, store_id: Union[int, None] = None,
                           **kwargs: Any) -> List[MagentoEntity]:
        """Get special prices for a sequence of SKUs.

        :param skus:
        :param store_id: Filter by store ID.
          This is done on the response as Magento doesn’t support this filter in the REST API.
        :param kwargs:
        :return:
        """
        special_prices = self.post_json_api("/V1/products/special-price-information",
                                            json={"skus": skus}, bypass_read_only=True, **kwargs)
        if store_id is not None:
            special_prices = [special_price for special_price in special_prices
                              if special_price["store_id"] == store_id]

        return special_prices

    def save_special_prices(self, special_prices: Sequence[MagentoEntity], **kwargs: Any) -> List[JSONDict]:
        """Save a sequence of special prices.

        Example:
            >>> price_from = "2025-01-01 00:00:00"
            >>> price_to = "2025-01-31 23:59:59"
            >>> special_price = {"store_id": 0, "sku": "W1033", "price": 2.99, \
                                 "price_from": price_from, "price_to": price_to}
            >>> self.save_special_prices([special_price])

        :param special_prices: Special prices to save.
        :return: a list of errors (if any)
        """
        return self.post_json_api("/V1/products/special-price", json={"prices": special_prices}, **kwargs)

    def delete_special_prices(self, special_prices: Sequence[MagentoEntity], **kwargs: Any) -> List[JSONDict]:
        """Delete a sequence of special prices."""
        return self.post_json_api("/V1/products/special-price-delete", json={"prices": special_prices}, **kwargs)

    def delete_special_prices_by_sku(self, skus: Sequence[Sku], *, store_id: Union[int, None] = None,
                                     **kwargs: Any):
        """Equivalent of ``delete_special_prices(get_special_prices(skus))``."""
        special_prices = self.get_special_prices(skus, store_id=store_id, **kwargs)
        return self.delete_special_prices(special_prices, **kwargs)

    # Products
    # ========

    def get_products(self, limit: int = -1, query: Query = None, retry: int = 0, **kwargs: Any) -> Iterator[Product]:
        """Return a generator of all products.

        :param limit: -1 for unlimited.
        :param query:
        :param retry:
        :return:
        """
        return cast(Iterator[Product],
                    self.get_paginated("/V1/products/", query=query, limit=limit, retry=retry, **kwargs))

    def get_products_types(self, **kwargs: Any) -> Sequence[MagentoEntity]:
        """Get available product types."""
        return self.get_json_api("/V1/product/types", **kwargs)

    def get_product(self, sku: Sku, *,
                    none_on_404: bool = True,
                    **kwargs: Any) -> Optional[Product]:
        """Get a single product by SKU. Return ``None`` if it doesn’t exist.

        :param sku: SKU of the product.
        :param none_on_404:
        :param kwargs:
        :return:
        """
        return self.get_json_api(f"/V1/products/{escape_path(sku)}",
                                 none_on_404=none_on_404,
                                 **kwargs)

    def get_product_by_id(self, product_id: int, **kwargs: Any) -> Optional[Product]:
        """Get a product given its id. Return ``None`` if the product doesn’t exist.

        :param product_id: ID of the product
        :return:
        """
        query = make_field_value_query("entity_id", product_id)
        for product in self.get_products(query=query, limit=1, **kwargs):
            return product
        return None

    def get_product_by_query(self, query: Query, *, expect_one: bool = True, **kwargs: Any) -> Optional[Product]:
        """Get a product with a custom query. Return ``None`` if the query doesn’t return match any product, and raise
        an exception if it returns more than one, unless ``expect_one`` is set to ``False``.

        :param query:
        :param expect_one: if True (the default), raise an exception if the query returns more than one result.
        :return:
        """
        if not expect_one:
            for product in self.get_products(query=query, limit=1, **kwargs):
                return product
            return None

        products = list(self.get_products(query=query, limit=2, **kwargs))
        if not products:
            return None
        if len(products) == 1:
            return products[0]
        raise MagentoAssertionError("Got more than one product for query %r" % query)

    def get_product_medias(self, sku: Sku, **kwargs: Any) -> Sequence[MediaEntry]:
        """Get the list of gallery entries associated with the given product.

        :param sku: SKU of the product.
        :return:
        """
        return self.get_json_api(f"/V1/products/{escape_path(sku)}/media", **kwargs)

    def get_product_media(self, sku: Sku, media_id: PathId, **kwargs: Any) -> MediaEntry:
        """Return a gallery entry.

        :param sku: SKU of the product.
        :param media_id:
        :return:
        """
        return self.get_json_api(f"/V1/products/{escape_path(sku)}/media/{media_id}", **kwargs)

    def save_product_media(self, sku: Sku, media_entry: MediaEntry, **kwargs: Any):
        """Save a product media."""
        return self.post_json_api(f"/V1/products/{escape_path(sku)}/media", json={"entry": media_entry}, **kwargs)

    def delete_product_media(self, sku: Sku, media_id: PathId, **kwargs: Any):
        """Delete a media associated with a product.

        :param sku: SKU of the product
        :param media_id:
        :return:
        """
        return self.delete_json_api(f"/V1/products/{escape_path(sku)}/media/{media_id}", **kwargs)

    def save_product(self, product: Product, *, save_options: Optional[bool] = None, log_response: bool = True,
                     **kwargs: Any) -> Product:
        """Save a new product. To update a product, use `update_product`.

        :param product: product to save (can be partial).
        :param save_options: set the `saveOptions` attribute.
        :param log_response: log the Magento response
        :return:
        """
        payload: MagentoEntity = {"product": product}
        if save_options is not None:
            payload["saveOptions"] = save_options

        # throw=False so the log is printed before we raise
        resp = self.post_api("/V1/products", json=payload, throw=False, **kwargs)
        if log_response and self.logger:
            self.logger.debug("Save product response: %s" % resp.text)
        raise_for_response(resp)
        return cast(Product, resp.json())

    def update_product(self, sku: Sku, product: Product, *, save_options: Optional[bool] = None,
                       **kwargs: Any) -> Product:
        """Update a product.

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

        return cast(Product, self.put_json_api(f"/V1/products/{escape_path(sku)}", json=payload, **kwargs))

    def delete_product(self, sku: Sku, skip_missing: bool = False, throw: bool = True, **kwargs: Any) -> bool:
        """Delete a product given its SKU.

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

    def async_update_products(self, product_updates: Iterable[Product], **kwargs: Any):
        """Update multiple products using the async bulk API.

        Example:
            >>> Magento().async_update_products([{"sku": "SK123", "name": "Abc"}, {"sku": "SK4", "name": "Def"}])

        See https://devdocs.magento.com/guides/v2.4/rest/bulk-endpoints.html

        :param product_updates: sequence of product data dicts. They MUST contain an `sku` key.
        :return:
        """
        payload = [{"product": product_update} for product_update in product_updates]
        return self.put_json_api("/V1/products/bySku", json=payload, async_bulk=True, **kwargs)

    def get_product_stock_item(self, sku: Sku, *, none_on_404: bool = False, none_on_empty: bool = False,
                               **kwargs: Any) -> MagentoEntity:
        """Get the stock item for an SKU."""
        return self.get_json_api(f"/V1/stockItems/{escape_path(sku)}",
                                 none_on_404=none_on_404,
                                 none_on_empty=none_on_empty,
                                 **kwargs)

    def update_product_stock_item(self, sku: Sku, stock_item_id: int, stock_item: MagentoEntity, **kwargs: Any) -> int:
        """Update the stock item of a product.
        https://adobe-commerce.redoc.ly/2.4.6-admin/tag/productsproductSkustockItemsitemId/#operation/PutV1ProductsProductSkuStockItemsItemId

        :param sku: SKU of the product
        :param stock_item_id: stock item ID. Note that it’s not clear why this ID is needed; it seems to be ignored by
          Magento and products always have a single stock item anyway.
        :param stock_item:
        :return: the stock item ID
        """
        return self.put_json_api(f"/V1/products/{escape_path(sku)}/stockItems/{stock_item_id}", json={
            "stockItem": stock_item,
        }, **kwargs)

    def update_product_stock_item_quantity(self, sku: Sku, stock_item_id: int, quantity: int,
                                           is_in_stock: Optional[bool] = None, **kwargs: Any):
        """Update the stock item of a product to set its quantity.
        This is a simplified version of ``update_product_stock_item``.

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
        }, **kwargs)

    def get_product_stock_status(self, sku: Sku, none_on_404: bool = False, none_on_empty: bool = False,
                                 **kwargs: Any) -> MagentoEntity:
        """Get stock status for an SKU."""
        return self.get_json_api(f"/V1/stockStatuses/{escape_path(sku)}",
                                 none_on_404=none_on_404,
                                 none_on_empty=none_on_empty,
                                 **kwargs)

    def link_child_product(self, parent_sku: Sku, child_sku: Sku, **kwargs: Any):
        """Link two products, one as the parent of the other.

        :param parent_sku: SKU of the parent product
        :param child_sku: SKU of the child product
        :return: `requests.Response` object
        """
        return self.post_json_api(f"/V1/configurable-products/{escape_path(parent_sku)}/child",
                                  json={"childSku": child_sku}, **kwargs)

    def unlink_child_product(self, parent_sku: Sku, child_sku: Sku, **kwargs: Any):
        """Opposite of link_child_product().

        :param parent_sku: SKU of the parent product
        :param child_sku: SKU of the child product
        """
        return self.delete_json_api(
            f"/V1/configurable-products/{escape_path(parent_sku)}/children/{escape_path(child_sku)}",
            **kwargs)

    def save_configurable_product_option(self, sku: Sku, option: MagentoEntity, **kwargs: Any) -> int:
        """Save a configurable product option.

        :param sku: SKU of the product
        :param option: option to save
        :return:
        """
        return self.post_json_api(f"/V1/configurable-products/{escape_path(sku)}/options",
                                  json={"option": option}, **kwargs)

    def add_product_website_link(self, sku: Sku, website_id: int, **kwargs: Any) -> bool:
        """Assign a product to a website."""
        # The API also supports PUT but does not explain the difference with POST
        ok: bool = self.post_json_api(
            f"/V1/products/{escape_path(sku)}/websites",
            json={"productWebsiteLink": {"sku": sku, "website_id": website_id}},
            **kwargs,
        )
        return ok

    def remove_product_website_link(self, sku: Sku, website_id: int, **kwargs: Any) -> bool:
        """Remove a product from a website."""
        ok: bool = self.delete_json_api(
            f"/V1/products/{escape_path(sku)}/websites/{escape_path(website_id)}",
            **kwargs,
        )
        return ok

    # Products Attribute Options
    # --------------------------

    def get_products_attribute_options(self, attribute_code: str, *,
                                       none_on_404: bool = False,
                                       none_on_empty: bool = False,
                                       **kwargs: Any) -> Sequence[Dict[str, str]]:
        """Get all options for a products attribute."""
        response: Sequence[Dict[str, str]] = self.get_json_api(
            f"/V1/products/attributes/{escape_path(attribute_code)}/options",
            none_on_404=none_on_404,
            none_on_empty=none_on_empty,
            **kwargs)
        return response

    def add_products_attribute_option(self, attribute_code: str, option: Dict[str, str], **kwargs: Any) -> str:
        """Add an option to a products attribute.

        https://magento.redoc.ly/2.3.6-admin/#operation/catalogProductAttributeOptionManagementV1AddPost

        :param attribute_code:
        :param option: dict with label/value keys (mandatory)
        :return: new id
        """
        payload = {"option": option}
        ret: str = self.post_json_api(f"/V1/products/attributes/{escape_path(attribute_code)}/options",
                                      json=payload, **kwargs)

        if ret.startswith("id_"):
            ret = ret[3:]

        return ret

    def delete_products_attribute_option(self, attribute_code: str, option_id: PathId, **kwargs: Any) -> bool:
        """Remove an option to a products attribute.

        :param attribute_code:
        :param option_id:
        :return: boolean
        """
        ok: bool = self.delete_json_api(f"/V1/products/attributes/{escape_path(attribute_code)}/options/{option_id}",
                                        **kwargs)
        return ok

    # Aliases
    # -------

    def get_manufacturers(self, **kwargs: Any):
        """Shortcut for `.get_products_attribute_options("manufacturer")`."""
        return self.get_products_attribute_options("manufacturer", **kwargs)

    # Sales Rules
    # ===========

    def get_sales_rules(self, *, query: Query = None, limit: int = -1, **kwargs: Any) -> Iterator[MagentoEntity]:
        """Get all sales rules (generator)."""
        rules: Iterator[MagentoEntity] = self.get_paginated("/V1/salesRules/search", query=query, limit=limit, **kwargs)
        return rules

    # Shipments
    # =========

    def get_shipments(self, *, query: Query = None, limit: int = -1, **kwargs: Any) -> Iterator[MagentoEntity]:
        """Return shipments (generator)."""
        shipments: Iterator[MagentoEntity] = self.get_paginated("/V1/shipments", query=query, limit=limit, **kwargs)
        return shipments

    def ship_order(self, order_id: PathId, payload: MagentoEntity, **kwargs: Any) -> str:
        """Ship an order.

        Return the shipment ID as a string.
        """
        response = self.post_api(f"/V1/order/{order_id}/ship", json=payload, throw=True,
                                 **kwargs)
        # The documentation says this is an int, but in practice it’s an int as string
        body: Union[str, Dict[str, Any]] = response.json()

        if isinstance(body, dict):
            raise MagentoException(
                message=body["message"],
                parameters=body.get("parameters"),
                trace=body.get("trace"),
                response=response,
            )

        return body

    def get_order_shipments(self, order_id: Union[int, str], **kwargs: Any):
        """Get shipments for the given order id."""
        return self.get_shipments(query=make_field_value_query("order_id", order_id), **kwargs)

    # Stock
    # =====

    def get_stock_source_links(self, query: Query = None, limit: int = -1, **kwargs: Any) -> Iterator[MagentoEntity]:
        """Get stock source links."""
        return self.get_paginated("/V1/inventory/stock-source-links", query=query, limit=limit, **kwargs)

    # Stores
    # ======

    def get_store_configs(self, store_codes: Optional[List[str]] = None, **kwargs: Any) -> List[MagentoEntity]:
        """Get store configs."""
        params: Dict[str, List[str]] = {}
        if store_codes is not None:
            params = {"storeCodes[]": store_codes}

        return self.get_json_api("/V1/store/storeConfigs", params=params, **kwargs)

    def get_store_groups(self, **kwargs: Any) -> List[MagentoEntity]:
        """Get store groups."""
        return self.get_json_api("/V1/store/storeGroups", **kwargs)

    def get_store_views(self, **kwargs: Any) -> List[MagentoEntity]:
        """Get store views."""
        return self.get_json_api("/V1/store/storeViews", **kwargs)

    def get_websites(self, **kwargs: Any) -> List[MagentoEntity]:
        """Get websites."""
        return self.get_json_api("/V1/store/websites", **kwargs)

    def get_current_store_group_id(self, *, skip_store_groups: bool = False, scope: Optional[str] = None,
                                   **kwargs: Any) -> int:
        """Get the current store group id for the current scope. This is not part of Magento API.

        :param skip_store_groups: if True, assume the current scope is not already a store group.
        :param scope: Override the client's scope
        """
        if scope is None:
            scope = self.scope

        if not skip_store_groups:
            # If scope is already a store group
            for store_group in self.get_store_groups(**kwargs):
                if store_group["code"] == scope:
                    return store_group["id"]

        # If scope is a website
        for website in self.get_websites(**kwargs):
            if website["code"] == scope:
                return website["default_group_id"]

        # If scope is a view
        for view in self.get_store_views(**kwargs):
            if view["code"] == scope:
                return view["store_group_id"]

        raise RuntimeError("Can't determine the store group id of scope %r" % scope)

    def get_root_category_id(self, **kwargs: Any) -> int:
        """Get the root category id of the current scope. This is not part of Magento API."""
        store_group_root_category_id: Dict[int, int] = {}

        # We first iterate over store groups because it's faster (fewer API calls) than calling `get_current_store_group_id`.
        store_groups = list(self.get_store_groups(**kwargs))
        for store_group in store_groups:
            root_category_id: int = store_group["root_category_id"]

            # If scope is a store group
            if store_group["code"] == self.scope:
                return root_category_id

            store_group_root_category_id[store_group["id"]] = root_category_id

        return store_group_root_category_id[self.get_current_store_group_id(skip_store_groups=True, **kwargs)]

    # Sources
    # =======

    def get_sources(self, query: Query = None, limit: int = -1, **kwargs: Any) -> Iterator[MagentoEntity]:
        """Get all sources.

        https://adobe-commerce.redoc.ly/2.4.6-admin/tag/inventorysources#operation/GetV1InventorySources
        """
        return self.get_paginated("/V1/inventory/sources", query=query, limit=limit, **kwargs)

    def get_source(self, source_code: str, **kwargs: Any) -> Optional[MagentoEntity]:
        """Get a single source, or `None` if it doesn’t exist.

        https://adobe-commerce.redoc.ly/2.4.6-admin/tag/inventorysourcessourceCode#operation/GetV1InventorySourcesSourceCode
        """
        return self.get_json_api(f"/V1/inventory/sources/{escape_path(source_code)}", **kwargs)

    def save_source(self, source: MagentoEntity, **kwargs: Any):
        """Save a source.

        https://adobe-commerce.redoc.ly/2.4.6-admin/tag/inventorysources/#operation/PostV1InventorySources
        """
        return self.post_json_api("/V1/inventory/sources", json={"source": source}, **kwargs)

    # Source Items
    # ============

    def get_source_items(self, source_code: Optional[str] = None, sku: Optional[str] = None,
                         *,
                         skus: Optional[Iterable[str]] = None,
                         query: Query = None, limit: int = -1,
                         **kwargs: Any) -> Iterator[SourceItem]:
        """Return a generator of all source items.

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

        return cast(Iterator[SourceItem],
                    self.get_paginated("/V1/inventory/source-items", query=query, limit=limit, **kwargs))

    def save_source_items(self, source_items: Sequence[Union[SourceItem, SourceItemIn]], **kwargs: Any):
        """Save a sequence of source-items. Return None if the sequence is empty.

        :param source_items:
        :return:
        """
        if not source_items:
            return None
        return self.post_json_api("/V1/inventory/source-items", json={"sourceItems": source_items}, **kwargs)

    def delete_source_items(self, source_items: Iterable[Union[SourceItem, SourceItemIn]], **kwargs: Any):
        """Delete a sequence of source-items. Only the SKU and the source_code are used.

        Note: Magento returns an error if this is called with empty source_items.

        :param source_items:
        :param kwargs: keyword arguments passed to the underlying POST call.
        """
        payload = {
            "sourceItems": [{"sku": s["sku"], "source_code": s["source_code"]} for s in source_items],
        }
        return self.post_json_api("/V1/inventory/source-items-delete", json=payload, **kwargs)

    def delete_source_items_by_source_code(self, source_code: str, **kwargs: Any):
        """Delete all source items that have the given ``source_code``.

        :return: requests.Response object if there are source items, None otherwise.
        """
        source_items = list(self.get_source_items(source_code=source_code, **kwargs))
        if source_items:
            return self.delete_source_items(source_items, **kwargs)

    # Taxes
    # =====

    def get_tax_classes(self, *, query: Query = None, limit: int = -1, **kwargs: Any) -> Iterator[MagentoEntity]:
        """Get all tax classes (generator)."""
        return self.get_paginated("/V1/taxClasses/search", query=query, limit=limit, **kwargs)

    def get_tax_rates(self, *, query: Query = None, limit: int = -1, **kwargs: Any) -> Iterator[MagentoEntity]:
        """Get all tax rates (generator)."""
        return self.get_paginated("/V1/taxRates/search", query=query, limit=limit, **kwargs)

    def get_tax_rules(self, *, query: Query = None, limit: int = -1, **kwargs: Any) -> Iterator[MagentoEntity]:
        """Get all tax rules (generator)."""
        return self.get_paginated("/V1/taxRules/search", query=query, limit=limit, **kwargs)

    # Modules
    # =======

    def get_modules(self, query: Query = None, limit: int = -1, **kwargs: Any) -> Iterator[MagentoEntity]:
        """Get all enabled modules (generator)."""
        return self.get_paginated("/V1/modules", query=query, limit=limit, **kwargs)

    # Helpers
    # =======

    # Categories
    # ----------

    def get_categories_under_root(self, root_category_id: Optional[int] = None, include_root: bool = False,
                                  **kwargs: Any) -> Iterator[Category]:
        """Like get_categories(), but get only categories under a root id.

        :param root_category_id: optional root category to use.
          If not provided, defaults to the store’s root category id.
        :param include_root: if True, include the root category in the results (default: False).
        :return:
        """
        if root_category_id is None:
            root_category_id = self.get_root_category_id(**kwargs)

        root_category = self.get_category(root_category_id, **kwargs)
        if root_category is None:
            return

        path_prefix = root_category["path"]
        if not include_root:
            path_prefix += "/"

        yield from self.get_categories(path_prefix=path_prefix, **kwargs)

    # Products
    # --------

    def sku_exists(self, sku: str, **kwargs: Any) -> bool:
        """Test if a SKU exists in Magento."""
        # Query a single field to reduce the payload size
        # Update this if you find a more efficient way of doing it
        return self.get_product(sku, fields="id", **kwargs) is not None

    def sku_was_bought(self, sku: str, **kwargs: Any) -> bool:
        """Test if there exists at least one order with the given SKU."""
        for _ in self.get_orders_items(sku=sku, limit=1, fields="sku", **kwargs):
            return True
        return False

    def skus_were_bought(self, skus: List[str]) -> Dict[str, bool]:
        """Equivalent of ``sku_was_bought`` for multiple SKUs. Return a dict of {SKU -> bought?}.

        Note that if some of the SKUs were bought a lot of times it’s more efficient to call ``sku_was_bought`` on each SKU.
        """
        q = make_field_value_query("sku", ",".join(skus), "in")

        bought_skus_dict: Dict[str, bool] = {sku: False for sku in skus}
        for order_item in self.get_orders_items(query=q, fields="sku"):
            bought_skus_dict[order_item["sku"]] = True

            if all(bought_skus_dict.values()):
                break

        return bought_skus_dict

    # Internals
    # =========

    def request_api(self, method: str, path: str, *args: Any,  # type: ignore[override]
                    async_bulk: bool = False,
                    throw: bool = False,
                    retry: int = 0,
                    scope: Optional[str] = None,
                    fields: Optional[str] = None,
                    **kwargs: Any) -> requests.Response:
        """Equivalent of .request() that prefixes the path with the base API URL.

        :param method: HTTP method
        :param path: API path. This must start with "/V1/"
        :param args: arguments passed to ``.request()``
        :param async_bulk: if True, use the "/async/bulk" prefix.
            https://devdocs.magento.com/guides/v2.3/rest/bulk-endpoints.html
        :param throw: if True, raise an exception if the response is an error
        :param retry: if non-zero, retry the request that many times if there is an error, sleeping 10s between
            each request.
        :param scope: overrides the client's scope for this request
        :param fields: overrides the `params["fields"]`
        :param kwargs: keyword arguments passed to ``.request()``
        :return:
        """
        assert path.startswith("/V1/")

        full_path = "/rest"

        if scope is None:
            scope = self.scope

        if scope != "default":
            full_path += f"/{scope}"

        if async_bulk:
            full_path += "/async/bulk"

        full_path += path

        if fields is not None:
            kwargs.setdefault("params", {})
            kwargs["params"]["fields"] = fields

        if self.logger:
            self.logger.debug("%s %s" % (method, full_path))
        r = super().request_api(method, full_path, *args, throw=False, **kwargs)
        while not r.ok and retry > 0:
            retry -= 1
            time.sleep(10)
            r = super().request_api(method, full_path, *args, throw=False, **kwargs)

        if throw:
            raise_for_response(r)
        return r

    def get_paginated(self, path: str, *, query: Query = None, limit: int = -1, retry: int = 0,
                      page_size: Optional[int] = None,
                      fields: Optional[Dict[str, Any]] = None,
                      **kwargs: Any) -> Iterator[MagentoEntity]:
        """Get a paginated API path.

        :param path:
        :param query:
        :param limit: -1 for no limit
        :param retry:
        :param page_size: default is `self.PAGE_SIZE`
        :param fields: fields to retrieve for each item. Don't wrap them in `items[]`
        :return:
        """
        if limit == 0:
            return

        if page_size is None:
            page_size = self.PAGE_SIZE

        if 0 < limit < page_size:
            page_size = limit

        if query is not None:
            query = query.copy()
        else:
            query = {}

        query["searchCriteria[pageSize]"] = page_size

        if isinstance(fields, str):
            fields = f"items[{fields}],total_count"

        current_page = 1
        count = 0

        while True:
            page_query = query.copy()
            page_query["searchCriteria[currentPage]"] = current_page

            res = self.get_json_api(path, page_query,
                                    none_on_404=False,
                                    none_on_empty=False,
                                    retry=retry,
                                    fields=fields,
                                    **kwargs)
            items: List[Any] = res.get("items", [])
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

                if count >= limit > 0:
                    return

            current_page += 1
