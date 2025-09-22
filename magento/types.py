import sys
from typing import Union, TypedDict, Literal, List, Any

from api_session import JSONDict

if sys.version_info >= (3, 11):
    from typing import NotRequired
else:
    # noinspection PyUnreachableCode
    from typing_extensions import NotRequired

__all__ = (
    'AttributeOption',
    'BasePrice',
    'Category',
    'Customer',
    'DeleteCouponsResponseDict',
    'MagentoEntity',
    'MediaEntry',
    'Order',
    'PathId',
    'ErrorDict',
    'PriceUpdateResultDict',
    'Product',
    'ShippingAddress',
    'Sku',
    'SourceItem',
    'SourceItemIn',
)

MagentoEntity = JSONDict

PathId = Union[int, str]
Sku = str

# TODO: proper types
AttributeOption = MagentoEntity
Category = MagentoEntity
Customer = MagentoEntity
MediaEntry = MagentoEntity
Order = MagentoEntity
Product = MagentoEntity


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


# Other types
# ===========

class DeleteCouponsResponseDict(TypedDict):
    """Response from the `coupons/deleteByIds` endpoint."""
    failed_items: list[Any]
    missing_items: list[Any]


class ErrorDict(TypedDict):
    """Error dict."""
    message: str
    parameters: list[str]


class PriceUpdateResultDict(ErrorDict):
    """Response from the `products/base-prices` endpoint."""
    extension_attributes: dict[str, Any]
