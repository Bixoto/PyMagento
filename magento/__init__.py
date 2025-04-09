"""Client and utilities to work with the Magento 2 REST API."""

from magento.attributes import (
    get_custom_attribute, get_boolean_custom_attribute, get_custom_attributes_dict,
    set_custom_attribute, set_custom_attributes, serialize_attribute_value,
    delete_custom_attribute, delete_custom_attributes,
)
from magento.client import Magento
from magento.dates import DATE_ISO_8601_FORMAT, format_datetime, parse_datetime
from magento.exceptions import MagentoException, MagentoAssertionError
from magento.order_helpers import is_order_on_hold, is_order_cash_on_delivery, get_order_shipping_address
from magento.queries import Query, make_field_value_query, make_search_query
from magento.types import (
    MagentoEntity,
    BasePrice,
    Customer,
    Order,
    Product,
    Category,
    MediaEntry,
    SourceItem,
    ShippingAddress,
    Sku,
)
from magento.version import __version__

__all__ = [
    "BasePrice",
    "Category",
    "Customer",
    "DATE_ISO_8601_FORMAT",
    "DISABLED_PRODUCT",
    "ENABLED_PRODUCT",
    "IMAGE_MIME_TYPES",
    "Magento",
    "MagentoAssertionError",
    "MagentoEntity",
    "MagentoException",
    "MediaEntry",
    "Order",
    "Product",
    "Query",
    "ROOT_CATEGORY_ID",
    "ShippingAddress",
    "Sku",
    "SourceItem",
    "VISIBILITY_IN_CATALOG",
    "VISIBILITY_IN_CATALOG_AND_SEARCH",
    "VISIBILITY_IN_SEARCH",
    "VISIBILITY_NOT_VISIBLE",
    "__version__",
    "delete_custom_attribute",
    "delete_custom_attributes",
    "format_datetime",
    "get_boolean_custom_attribute",
    "get_custom_attribute",
    "get_custom_attributes_dict",
    "get_order_shipping_address",
    "is_order_cash_on_delivery",
    "is_order_on_hold",
    "make_field_value_query",
    "make_search_query",
    "parse_datetime",
    "serialize_attribute_value",
    "set_custom_attribute",
    "set_custom_attributes",
]

ROOT_CATEGORY_ID = 1

# Magento's visibility options
# https://devdocs.magento.com/guides/v2.4/rest/tutorials/configurable-product/create-configurable-product.html
VISIBILITY_IN_CATALOG_AND_SEARCH = 4
VISIBILITY_IN_CATALOG = 2
VISIBILITY_IN_SEARCH = 3
VISIBILITY_NOT_VISIBLE = 1

# Magento product statuses
# https://magento.stackexchange.com/q/10693/92968
ENABLED_PRODUCT = 1
DISABLED_PRODUCT = 2

# https://magento.stackexchange.com/a/244151/92968
# https://github.com/magento/magento2/blob/ef6d9c80/lib/internal/Magento/Framework/Image/Adapter/Gd2.php#L30-L34
IMAGE_MIME_TYPES = {"image/gif", "image/jpeg", "image/png", "image/xbm", "image/wbmp"}
