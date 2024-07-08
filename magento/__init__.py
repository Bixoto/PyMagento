from datetime import datetime

from magento.attributes import (
    get_custom_attribute, get_boolean_custom_attribute, get_custom_attributes_dict,
    set_custom_attribute, set_custom_attributes, serialize_attribute_value,
    delete_custom_attribute, delete_custom_attributes,
)
from magento.client import Magento
from magento.exceptions import MagentoException, MagentoAssertionError
from magento.order_helpers import is_order_on_hold, is_order_cash_on_delivery, get_order_shipping_address
from magento.queries import Query, make_field_value_query, make_search_query
from magento.types import (
    MagentoEntity,
    Customer,
    Order,
    Product,
    Category,
    MediaEntry,
    SourceItem,
    Sku,
)
from magento.version import __version__

ROOT_CATEGORY_ID = 1

# Magento's visibility options
# https://devdocs.magento.com/guides/v2.4/rest/tutorials/configurable-product/create-configurable-product.html
VISIBILITY_IN_CATALOG_AND_SEARCH = 4
VISIBILITY_IN_CATALOG = 2
VISIBILITY_IN_SEARCH = 3
VISIBILITY_NOT_VISIBLE = 1

# backward compatibility
VISIBILITY_BOTH = VISIBILITY_IN_CATALOG_AND_SEARCH

# Magento product statuses
# https://magento.stackexchange.com/q/10693/92968
ENABLED_PRODUCT = 1
DISABLED_PRODUCT = 2

# https://magento.stackexchange.com/a/244151/92968
# https://github.com/magento/magento2/blob/ef6d9c80/lib/internal/Magento/Framework/Image/Adapter/Gd2.php#L30-L34
IMAGE_MIME_TYPES = {"image/gif", "image/jpeg", "image/png", "image/xbm", "image/wbmp"}

DATE_ISO_8601_FORMAT = "%Y-%m-%d %H:%M:%S"


def format_datetime(dt: datetime):
    """Format a datetime for Magento."""
    # "2021-07-02 13:19:18.300700" -> "2021-07-02 13:19:18"
    return dt.isoformat(sep=" ").split(".", 1)[0]


def parse_datetime(s: str):
    """Parse a datetime string from Magento."""
    return datetime.strptime(s, DATE_ISO_8601_FORMAT)
