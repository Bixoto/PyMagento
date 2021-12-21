from magento.client import Magento, make_field_value_query, make_search_query
from magento.version import __version__
from magento.exceptions import MagentoException
from magento.attributes import (
    get_custom_attribute, get_boolean_custom_attribute, get_custom_attributes_dict,
    pretty_custom_attributes
)
from magento.order_helpers import (
    is_order_on_hold, is_order_cash_on_delivery, get_order_shipping_address
)

# ids of the default categories in Magento
ROOT_CATEGORY_ID = 1
DEFAULT_CATEGORY_ID = 2

# Magento visibility options
# https://devdocs.magento.com/guides/v2.4/rest/tutorials/configurable-product/create-configurable-product.html
VISIBILITY_BOTH = 4
VISIBILITY_IN_CATALOG = 2
VISIBILITY_IN_SEARCH = 3
VISIBILITY_NOT_VISIBLE = 1

# Magento product statuses
# https://magento.stackexchange.com/q/10693/92968
ENABLED_PRODUCT = 1
DISABLED_PRODUCT = 2
