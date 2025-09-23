import sys
from typing import Union, TypedDict, Literal, List, Any, Dict

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
    'CustomAttributeDict',
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
    'WithExtensionAttributesDict',
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
ProductLink = MagentoEntity


class WithExtensionAttributesDict(TypedDict):
    """A dict with an extension_attributes key."""
    extension_attributes: Dict[str, Any]


class CustomAttributeDict(TypedDict):
    """A custom attribute dict, as found on products."""
    attribute_code: str
    value: Union[str, List[str], None]
    """A string value or a list of strings. This can be ``None`` to delete a custom attribute,
    but it will never be ``None`` in a Magento response.
    """


# Products
# ========

class Product(WithExtensionAttributesDict):
    """A product."""
    id: int
    sku: str
    name: str
    status: int
    attribute_set_id: int
    created_at: str
    updated_at: str
    custom_attributes: List[CustomAttributeDict]
    media_gallery_entries: List[MediaEntry]
    options: List[Any]
    price: float
    product_links: List[ProductLink]
    tier_prices: List[Any]
    type_id: str
    visibility: int
    weight: NotRequired[float]


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
    failed_items: List[Any]
    missing_items: List[Any]


class ErrorDict(TypedDict):
    """Error dict."""
    message: str
    parameters: List[str]


class PriceUpdateResultDict(ErrorDict, WithExtensionAttributesDict):
    """Response from the `products/base-prices` endpoint."""
    pass
