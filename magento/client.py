from json.decoder import JSONDecodeError
from logging import Logger
import time
from os import environ
from typing import Optional, Sequence, Dict, Union, cast, Iterator, Iterable, List
from datetime import timedelta
from api_session import APISession
import requests
from requests.exceptions import HTTPError

from magento.types import Product, SourceItem, Sku, Category, MediaEntry, MagentoEntity, Order, PathId
from magento.version import __version__
from magento.exceptions import MagentoException

from magento.queries import Query, make_search_query, make_field_value_query

__all__ = (
    'Magento',
)

USER_AGENT = f'Bixoto/PyMagento {__version__} +git.io/JDp0h'

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
    Equivalent of requests.Response#raise_for_status with some Magento specifics.
    """
    if response.ok:
        return

    if response.text and response.text[0] == '{':
        try:
            body = response.json()
        except (ValueError, JSONDecodeError):
            pass
        else:
            if isinstance(body, dict) and "message" in body:
                raise MagentoException(body["message"], parameters=body.get("parameters"),
                                       trace=body.get("trace"), response=response)

    response.raise_for_status()


class Magento(APISession):
    """
    Client for the Magento API.
    """
    # default batch size for paginated requests
    # Note increasing it doesn???t create a significant time improvement.
    # For example, in one test on Bixoto production in 2021, getting 2k products using a page size of 1k took 28s.
    # The same query with a page size of 2k still took 26s.
    PAGE_SIZE = 1000

    # default is 4 hours for admin tokens (the ones we use)
    TOKEN_LIFETIME = timedelta(hours=3)

    def __init__(self,
                 token: Optional[str] = None,
                 base_url: Optional[str] = None,
                 scope: Optional[str] = None,
                 logger: Logger = None,
                 read_only=False,
                 user_agent=None,
                 verbose=False,
                 # Deprecated
                 log_progress=False):
        """
        Create a Magento client instance. All arguments are optional and fall back on environment variables named
        ``PYMAGENTO_ + argument.upper()`` (``PYMAGENTO_TOKEN``, ``PYMAGENTO_BASE_URL``, etc).
        The ``token`` and ``base_url`` **must** be given either as arguments or environment variables.

        :param token: API integration token
        :param base_url: base URL of the Magento instance
        :param scope: API scope
        :param logger: optional logger.
        :param verbose: if True, log the progress of get_paginated. This has no effect if logger is not set.
        :param read_only: if True,
        :param user_agent: User-Agent
        :param log_progress: deprecated alias for `verbose`.
        """
        token = token or environ.get("PYMAGENTO_TOKEN")
        base_url = base_url or environ.get("PYMAGENTO_BASE_URL")
        scope = scope or environ.get("PYMAGENTO_SCOPE") or DEFAULT_SCOPE
        user_agent = user_agent or environ.get("PYMAGENTO_USER_AGENT") or USER_AGENT

        if token is None:
            raise RuntimeError("Missing API token")
        if base_url is None:
            raise RuntimeError("Missing API base URL")

        super().__init__(base_url=base_url, user_agent=user_agent, read_only=read_only)

        if log_progress:
            verbose = True

        self.scope = scope
        self.logger = logger
        self.verbose = verbose if logger else False
        self.headers['Authorization'] = f"Bearer {token}"

    # Attributes
    # ==========

    def save_attribute(self, attribute: MagentoEntity, *, with_defaults=True, throw=True, **kwargs) -> MagentoEntity:
        if with_defaults:
            base = DEFAULT_ATTRIBUTE_DICT.copy()
            base.update(attribute)
            attribute = base

        return self.post_api('/V1/products/attributes', json={"attribute": attribute}, throw=throw, **kwargs).json()

    def delete_attribute(self, attribute_code: str, **kwargs):
        return self.delete_api(f"/V1/products/attributes/{attribute_code}", **kwargs)

    # Attribute Sets
    # ==============

    def get_attribute_sets(self, limit=-1, **kwargs) -> Iterable[MagentoEntity]:
        """Get all attribute sets (generator)."""
        return self.get_paginated("/V1/eav/attribute-sets/list", limit=limit, **kwargs)

    def get_attribute_set_attributes(self, attribute_set_id: int, **kwargs):
        """Get all attributes for the given attribute set id."""
        return self.get_json_api(f"/V1/products/attribute-sets/{attribute_set_id}/attributes", **kwargs)

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
        return self.delete_api(f"/V1/products/attribute-sets/{attribute_set_id}/attributes/{attribute_code}", **kwargs)

    # Bulk Operations
    # ===============

    def get_bulk_status(self, bulk_uuid: str) -> MagentoEntity:
        """
        Get the status of an async/bulk operation.
        """
        return self.get_api(f'/V1/bulk/{bulk_uuid}/status', throw=True).json()

    # Carts
    # =====

    def get_carts(self, *, query: Query = None, limit=-1) -> Iterable[MagentoEntity]:
        """Get all carts (generator)."""
        return self.get_paginated("/V1/carts/search", query=query, limit=limit)

    # Categories
    # ==========

    def get_categories(self, query: Query = None) -> Iterable[Category]:
        """
        Yield all categories.

        :param query:
        :return:
        """
        return self.get_paginated('/V1/categories/list', query=query)

    def get_category(self, category_id: PathId) -> Optional[Category]:
        """
        Return a category given its id.

        :param category_id:
        :return:
        """
        return self.get_json_api(f"/V1/categories/{category_id}")

    def get_category_by_name(self, name: str) -> Optional[Category]:
        """
        Return the first category with the given name.

        :param name: exact name of the category
        :return:
        """
        for category in self.get_categories(make_field_value_query("name", name)):
            return category

        return None

    def update_category(self, category_id: PathId, category_data: Category) -> Category:
        """
        Update a category.

        :param category_id:
        :param category_data: (partial) category data to update
        :return: updated category
        """
        return cast(Category, self.put_api(f'/V1/categories/{category_id}',
                                           json={"category": category_data}, throw=True).json())

    def create_category(self, category: Category, throw=False):
        """
        Create a new category.
        """
        return self.post_api('/V1/categories', json={"category": category}, throw=throw)

    # CMS
    # ===

    def get_cms_pages(self, *, query: Query = None, limit=-1) -> Iterable[MagentoEntity]:
        """Get all CMS pages (generator)."""
        return self.get_paginated("/V1/cmsPage/search", query=query, limit=limit)

    def get_cms_blocks(self, *, query: Query = None, limit=-1) -> Iterable[MagentoEntity]:
        """Get all CMS blocks (generator)."""
        return self.get_paginated("/V1/cmsBlock/search", query=query, limit=limit)

    # Coupons
    # =======

    def get_coupons(self, *, query: Query = None, limit=-1) -> Iterable[MagentoEntity]:
        """Get all coupons (generator)."""
        return self.get_paginated("/V1/coupons/search", query=query, limit=limit)

    # Customers
    # =========

    def get_customers(self, *, query: Query = None, limit=-1) -> Iterable[MagentoEntity]:
        """Get all customers (generator)."""
        return self.get_paginated("/V1/customers/search", query=query, limit=limit)

    def get_customer(self, customer_id: int) -> dict:
        """Return a single customer."""
        return self.get_api(f"/V1/customers/{customer_id}", throw=True).json()

    def get_customer_groups(self, *, query: Query = None, limit=-1) -> Iterable[MagentoEntity]:
        """Get all customer groups (generator)."""
        return self.get_paginated("/V1/customerGroups/search", query=query, limit=limit)

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

        return self.post_api(f"/V1/order/{order_id}/invoice", json=payload, throw=True).json()

    def get_invoice(self, invoice_id: int) -> MagentoEntity:
        return self.get_api(f"/V1/invoices/{invoice_id}", throw=True).json()

    def get_invoice_by_increment_id(self, increment_id: str) -> Optional[MagentoEntity]:
        query = make_field_value_query("increment_id", increment_id)
        for invoice in self.get_invoices(query=query, limit=1):
            return invoice
        return None

    def get_invoices(self, query: Query = None, limit=-1) -> Iterable[MagentoEntity]:
        """Get all invoices (generator)."""
        return self.get_paginated("/V1/invoices", query=query, limit=limit)

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
                   retry=0) -> Iterator[Order]:
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
        if status:
            query = make_field_value_query("status", status, condition_type=status_condition_type)

        return self.get_paginated("/V1/orders", limit=limit, query=query, retry=retry)

    def get_last_orders(self, limit=10) -> List[Order]:
        """Return a list of the last orders (default: 10)."""
        query = make_search_query([], sort_orders=[("increment_id", "DESC")])
        return list(self.get_orders(query=query, limit=limit))

    def get_orders_items(self, *, sku: Optional[str] = None, query: Query = None, **kwargs):
        """
        Return orders items.

        :param sku: filter orders items on SKU. This is a shortcut for ``query=make_field_value_query("sku", sku)``.
        :param query: optional query. This take precedence over ``sku``.
        :return:
        """
        if query is None and sku is not None:
            query = make_field_value_query("sku", sku)

        return self.get_paginated("/V1/orders/items", query=query, **kwargs)

    def get_order(self, order_id: str, throw=True) -> Optional[Order]:
        """
        Get an order given its (entity) id.
        """
        return self.get_api(f'/V1/orders/{order_id}', throw=throw).json()

    def get_order_by_increment_id(self, increment_id: str) -> Optional[Order]:
        """
        Get an order given its increment id. Return ``None`` if the order doesn???t exist.

        :param increment_id:
        :return:
        """
        query = make_field_value_query("increment_id", increment_id)
        for order in self.get_orders(query=query, limit=1):
            return order
        return None

    def hold_order(self, order_id: str, **kwargs):
        return self.post_api(f'/V1/orders/{order_id}/hold', **kwargs)

    def unhold_order(self, order_id: str, **kwargs):
        return self.post_api(f'/V1/orders/{order_id}/unhold', **kwargs)

    def save_order(self, order: Order):
        return self.post_api(f'/V1/orders', json={"entity": order})

    def set_order_status(self, order: Order, status: str, *, external_order_id: Optional[str] = None):
        payload = {
            "entity_id": order["entity_id"],
            "status": status,
            "increment_id": order["increment_id"],  # we need to repeat increment_id, otherwise it is regenerated
        }
        if external_order_id is not None:
            payload["ext_order_id"] = external_order_id

        return self.save_order(payload)

    # Prices
    # ======

    # Base Prices
    # -----------

    def get_base_prices(self, skus: Sequence[Sku]) -> List[MagentoEntity]:
        """
        Get base prices for a sequence of SKUs.
        """
        return self.post_api("/V1/products/base-prices-information",
                             json={"skus": skus}, throw=True, bypass_read_only=True).json()

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

        :param skus:
        :return:
        """
        return self.post_api('/V1/products/special-price-information',
                             json={"skus": skus}, throw=True, bypass_read_only=True).json()

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
        return self.post_api('/V1/products/special-price', json={"prices": special_prices})

    def delete_special_prices(self, special_prices: Sequence[MagentoEntity]):
        """
        Delete a sequence of special prices.

        :param special_prices:
        :return:
        """
        return self.post_api('/V1/products/special-price-delete', json={"prices": special_prices})

    def delete_special_prices_by_sku(self, skus: Sequence[Sku]):
        """
        Equivalent of `delete_special_prices(get_special_prices(skus))`.

        :param skus:
        :return:
        """
        special_prices = self.get_special_prices(skus)
        return self.delete_special_prices(special_prices)

    # Products
    # ========

    def get_products(self, limit=-1, query: Query = None, retry=0) -> Iterator[Product]:
        """
        Return a generator of all products.

        :param limit: -1 for unlimited.
        :param query:
        :param retry:
        :return:
        """
        return cast(Iterator[Product], self.get_paginated("/V1/products/", limit=limit, query=query, retry=retry))

    def get_products_types(self) -> Sequence[MagentoEntity]:
        """Get available product types."""
        return self.get_json_api('/V1/product/types')

    def get_product(self, sku: Sku) -> Optional[Product]:
        """
        Get a single product. Return ``None`` if it doesn???t exist.

        :param sku:
        :return:
        """
        return self.get_json_api(f'/V1/products/{sku}')

    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """
        Get a product given its id. Return ``None`` if the product doesn???t exist.

        :param product_id:
        :return:
        """
        query = make_field_value_query("entity_id", product_id)
        for product in self.get_products(query=query, limit=1):
            return product
        return None

    def get_product_medias(self, sku: Sku) -> Sequence[MediaEntry]:
        """
        Get the list of gallery entries associated with the given product.

        :param sku: SKU of the product.
        :return:
        """
        return self.get_json_api(f'/V1/products/{sku}/media')

    def get_product_media(self, sku: Sku, entry_id: PathId) -> MediaEntry:
        """
        Return a gallery entry.

        :param sku: SKU of the product.
        :param entry_id:
        :return:
        """
        return self.get_json_api(f'/V1/products/{sku}/media/{entry_id}')

    def save_product_media(self, sku: Sku, media_entry: MediaEntry):
        return self.post_api(f'/V1/products/{sku}/media', json={"entry": media_entry}, throw=True).json()

    def delete_product_media(self, sku: Sku, media_id: PathId, throw=False):
        return self.delete_api(f'/V1/products/{sku}/media/{media_id}', throw=throw)

    def save_product(self, product, log_response=False) -> Product:
        """
        Save a product.

        :param product: (partial) product to save.
        :param log_response: if True and ``self.logger`` is set, log the response.
        :return:
        """
        # throw=False so the log is printed before we raise
        resp = self.post_api('/V1/products', json={"product": product}, throw=False)
        if log_response and self.logger:
            self.logger.info("Save product response: %s", resp.text)
        raise_for_response(resp)
        return cast(Product, resp.json())

    def update_product(self, sku: Sku, product_data: Product) -> Product:
        """
        Update a product.

        Example:
            >>> Magento().update_product("SK1234", {"name": "My New Name"})

        :param sku: SKU of the product to update
        :param product_data: (partial) product data to update
        :return: updated product
        """
        return cast(Product, self.put_api(f'/V1/products/{sku}', json={"product": product_data}, throw=True).json())

    def delete_product(self, sku: Sku, skip_missing=False, throw=True, **kwargs) -> bool:
        """
        Delete a product given its SKU.

        :param sku:
        :param skip_missing: if true, don't raise if the product is missing, and return False.
        :param throw: throw on error response
        :param kwargs: keyword arguments passed to all underlying methods.
        :return: a boolean indicating success.
        """
        try:
            response = self.delete_api(f'/V1/products/{sku}', throw=throw, **kwargs)
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
            >>> Magento().async_update_products([{"sku": "SK123", "name": "Abc"}), {"sku": "SK4", "name": "Def"}])

        See https://devdocs.magento.com/guides/v2.4/rest/bulk-endpoints.html

        :param product_updates: sequence of product data dicts. They MUST contain an 'sku' key.
        :return:
        """
        payload = [{"product": product_update} for product_update in product_updates]
        return self.put_api('/V1/products/bySku', json=payload, throw=True, async_bulk=True).json()

    def get_product_source_items(self, sku) -> Iterable[SourceItem]:
        """
        Deprecated. Use `.get_source_items(sku=sku)` instead, which is equivalent.
        """
        return self.get_source_items(sku=sku)

    def set_product_stock_item(self, sku: Sku, quantity: int, is_in_stock=1):
        """
        :param sku:
        :param quantity:
        :param is_in_stock:
        :return: requests.Response
        """
        payload = {"stockItem": {"qty": quantity, "is_in_stock": is_in_stock}}
        return self.put_api(f'/V1/products/{sku}/stockItems/1', json=payload, throw=True)

    def get_product_stock_status(self, sku: Sku) -> MagentoEntity:
        """Get stock status for an SKU."""
        return self.get_api(f"/V1/stockStatuses/{sku}", throw=True).json()

    def get_product_stock_item(self, sku: Sku) -> MagentoEntity:
        """Get the stock item for an SKU."""
        return self.get_api(f"/V1/stockItems/{sku}", throw=True).json()

    def link_child_product(self, parent_sku: Sku, child_sku: Sku, **kwargs) -> requests.Response:
        """
        Link two products, one as the parent of the other.

        :param parent_sku: SKU of the parent product
        :param child_sku: SKU of the child product
        :return: `requests.Response` object
        """
        return self.post_api(f'/V1/configurable-products/{parent_sku}/child',
                             json={"childSku": child_sku}, **kwargs)

    def unlink_child_product(self, parent_sku: Sku, child_sku: Sku, **kwargs) -> requests.Response:
        """
        Opposite of link_child_product().

        :param parent_sku: SKU of the parent product
        :param child_sku: SKU of the child product
        :return: `requests.Response` object
        """
        return self.delete_api(f"/V1/configurable-products/{parent_sku}/children/{child_sku}", **kwargs)

    def save_configurable_product_option(self, sku: Sku, option: MagentoEntity, throw=False):
        """
        Save a configurable product option.

        :param sku: SKU of the product
        :param option: option to save
        :param throw:
        :return: `requests.Response` object
        """
        return self.post_api(f'/V1/configurable-products/{sku}/options', json={"option": option}, throw=throw)

    # Products Attribute Options
    # --------------------------

    def get_products_attribute_options(self, attribute_code: str) -> Sequence[Dict[str, str]]:
        """
        Get all options for a products attribute.

        :param attribute_code:
        :return: sequence of option dicts.
        """
        response = self.get_api(f'/V1/products/attributes/{attribute_code}/options', throw=True)
        return cast(Sequence[Dict[str, str]], response.json())

    def add_products_attribute_option(self, attribute_code: str, option: Dict[str, str]) -> str:
        """
        Add an option to a products attribute.

        :param attribute_code:
        :param option: dict with label/value keys (mandatory).
          See https://magento.redoc.ly/2.3.6-admin/#operation/catalogProductAttributeOptionManagementV1AddPost
          for the optional keys.
        :return: new id
        """
        payload = {"option": option}
        response = self.post_api(f'/V1/products/attributes/{attribute_code}/options', json=payload, throw=True)
        ret = cast(str, response.json())

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
        response = self.delete_api(f'/V1/products/attributes/{attribute_code}/options/{option_id}', throw=True)
        return cast(bool, response.json())

    # Sales Rules
    # ===========

    def get_sales_rules(self, *, query: Query = None, limit=-1) -> Iterable[MagentoEntity]:
        """Get all sales rules (generator)."""
        return self.get_paginated("/V1/salesRules/search", query=query, limit=limit)

    # Shipments
    # =========

    def get_shipments(self, **kwargs) -> Iterable[MagentoEntity]:
        """Return shipments."""
        return self.get_paginated("/V1/shipments", **kwargs)

    def ship_order(self, order_id: PathId, payload: MagentoEntity):
        """
        Ship an order.
        """
        return self.post_api(f'/V1/order/{order_id}/ship', json=payload)

    def get_order_shipments(self, order_id: Union[int, str]):
        """Get shipments for the given order id."""
        return self.get_shipments(query=make_field_value_query("order_id", order_id))

    # Stock
    # =====

    def get_stock_source_links(self, query: Query = None) -> Iterable[MagentoEntity]:
        return self.get_paginated("/V1/inventory/stock-source-links", query=query)

    # Source Items
    # ============

    def get_source_items(self, source_code: Optional[str] = None, sku: Optional[str] = None,
                         *, query: Query = None, limit=-1) -> Iterable[MagentoEntity]:
        """
        Return a generator of all source items.

        :param source_code: optional source_code to filter on. This takes precedence over the query parameter.
        :param sku: option SKU to filter on. This takes precedence over the query parameter.
        :param query: optional query.
        :param limit: -1 for unlimited.
        :return:
        """
        if source_code or sku:
            filter_groups = []
            if source_code:
                filter_groups.append([("source_code", source_code, "eq")])
            if sku:
                filter_groups.append([("sku", sku, "eq")])

            query = make_search_query(filter_groups)

        return self.get_paginated("/V1/inventory/source-items", limit=limit, query=query)

    def save_source_items(self, source_items: Sequence[SourceItem]):
        """
        Save a sequence of source-items. Return None if the sequence is empty.

        :param source_items:
        :return:
        """
        if not source_items:
            return
        return self.post_api('/V1/inventory/source-items', json={"sourceItems": source_items}, throw=True).json()

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
        return self.post_api('/V1/inventory/source-items-delete', json=payload, throw=throw, **kwargs)

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

    def get_tax_classes(self, *, query: Query = None, limit=-1) -> Iterable[MagentoEntity]:
        """Get all tax classes (generator)."""
        return self.get_paginated("/V1/taxClasses/search", query=query, limit=limit)

    def get_tax_rates(self, *, query: Query = None, limit=-1) -> Iterable[MagentoEntity]:
        """Get all tax rates (generator)."""
        return self.get_paginated("/V1/taxRates/search", query=query, limit=limit)

    def get_tax_rules(self, *, query: Query = None, limit=-1) -> Iterable[MagentoEntity]:
        """Get all tax rules (generator)."""
        return self.get_paginated("/V1/taxRules/search", query=query, limit=limit)

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

        full_path = f"/rest/{self.scope}"

        if async_bulk:
            full_path += '/async/bulk'

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

    def get_paginated(self, path: str, *, query: Query = None, limit=-1, retry=0):
        """
        Get a paginated API path.

        :param path:
        :param query:
        :param limit: -1 for no limit
        :param retry:
        :return:
        """
        if limit == 0:
            return

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

            res = self.get_api(path, page_query, throw=True, retry=retry).json()
            items = res.get('items', [])
            if not items:
                break

            total_count = res["total_count"]

            for item in items:
                if self.verbose and self.logger and count and count % 1000 == 0:
                    self.logger.info(f'loaded {count} items')
                yield item
                count += 1
                if count >= total_count:
                    return

                if is_limited and count >= limit:
                    return

            current_page += 1
