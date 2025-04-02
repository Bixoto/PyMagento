import sys
from typing import Union, TypedDict, Literal, List

from api_session import JSONDict

if sys.version_info >= (3, 11):
    from typing import NotRequired
else:
    from typing_extensions import NotRequired

__all__ = (
    'BasePrice',
    'Category',
    'Customer',
    'MagentoEntity',
    'MediaEntry',
    'Order',
    'PathId',
    'Product',
    'ShippingAddress',
    'Sku',
    'SourceItem',
    'SourceItemIn',
)

MagentoEntity = JSONDict

Category = MagentoEntity
Customer = MagentoEntity
MediaEntry = MagentoEntity
Order = MagentoEntity
PathId = Union[int, str]
Product = MagentoEntity
Sku = str


# Source items
# ============
# See https://developer.adobe.com/commerce/webapi/rest/inventory/manage-source-items/

class SourceItemIn(TypedDict):
    """Input source item."""
    sku: Sku
    source_code: str
    quantity: NotRequired[int]
    status: NotRequired[int]


class SourceItem(TypedDict):
    """Source item as returned by Magento."""
    sku: Sku
    source_code: str
    quantity: int
    status: int


# Prices
# ======

class BasePrice(TypedDict):
    """Base price dict."""
    price: Union[int, float]
    store_id: int
    sku: Sku


# Orders
# ======

class ShippingAddress(TypedDict):
    """Shipping address dict."""
    address_type: Literal["shipping"]
    entity_id: int
    parent_id: int
    firstname: str
    lastname: str
    email: str
    street: List[str]
    city: str
    postcode: str
    region: NotRequired[str]
    region_code: str
    region_id: int
    country_id: str
    telephone: str
    company: NotRequired[str]
