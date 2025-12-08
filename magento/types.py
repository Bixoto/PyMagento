import sys
from typing import Union, TypedDict, Literal, List, Any, Dict

from api_session import JSONDict

if sys.version_info >= (3, 11):
    from typing import NotRequired
else:
    # noinspection PyUnreachableCode
    from typing_extensions import NotRequired

__all__ = (
    'Attribute',
    'AttributeSet',
    'AttributeStoreLabel',
    'AttributeOption',
    'BasePrice',
    'Cart',
    'Category',
    'CategoryProduct',
    'Customer',
    'CustomAttributeDict',
    'DeleteCouponsResponseDict',
    'MagentoEntity',
    'MediaGalleryEntry',
    'MediaGalleryEntryContent',
    'Order',
    'OrderItem',
    'OrderStatusHistory',
    'PathId',
    'ErrorDict',
    'PriceUpdateResultDict',
    'Product',
    'Address',
    'Sku',
    'SourceItem',
    'SourceItemIn',
    'StockItem',
    'StockStatus',
    'WithExtensionAttributesDict',
)

MagentoEntity = JSONDict

PathId = Union[int, str]
Sku = str

# TODO: proper typing
Attribute = MagentoEntity
AttributeSet = MagentoEntity
Cart = MagentoEntity
StockItem = MagentoEntity
StockStatus = MagentoEntity


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


class AttributeStoreLabel(TypedDict):
    """A store label for a select attribute."""
    store_id: int
    label: str


class AttributeOption(TypedDict):
    """Option for a select attribute."""
    label: str
    value: str
    sort_order: NotRequired[int]
    is_default: NotRequired[bool]
    store_labels: NotRequired[List[AttributeStoreLabel]]


# Products
# ========

class MediaGalleryEntryContent(TypedDict):
    """Content of a media gallery entry."""
    base64_encoded_data: str
    type: str
    name: str


class MediaGalleryEntry(WithExtensionAttributesDict):
    """A media gallery entry."""
    id: NotRequired[int]
    media_type: str
    label: str
    position: int
    disabled: bool
    types: List[str]
    file: str
    content: MediaGalleryEntryContent


class ProductLink(WithExtensionAttributesDict):
    """A product link."""
    sku: str
    link_type: str
    linked_product_sku: str
    linked_product_type: str
    position: int


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
    media_gallery_entries: List[MediaGalleryEntry]
    options: List[Any]
    price: float
    product_links: List[ProductLink]
    tier_prices: List[Any]
    type_id: str
    visibility: int
    weight: NotRequired[float]


# Categories
# ==========

class Category(WithExtensionAttributesDict):
    """A category."""
    id: int
    parent_id: int
    name: str
    is_active: bool
    position: int
    level: int
    children: str
    created_at: str
    updated_at: str
    path: str
    available_sort_by: List[str]
    include_in_menu: bool
    custom_attributes: List[CustomAttributeDict]


class CategoryProduct(TypedDict):
    """A category-product link."""
    sku: str
    position: int
    category_id: str


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

class Address(TypedDict):
    """Billing and/or shipping address dict."""
    address_type: Literal["billing", "shipping"]
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
    vat_id: NotRequired[str]


class OrderItem(WithExtensionAttributesDict):
    """An order item."""
    # Field based on a sample of 200k real-world order items

    item_id: int
    order_id: int
    product_id: int
    quote_item_id: int
    store_id: int
    sku: Sku
    name: str
    product_type: str
    created_at: str
    updated_at: str
    parent_item_id: NotRequired[int]
    parent_item: NotRequired["OrderItem"]
    applied_rule_ids: NotRequired[str]

    # Monetary amounts
    amount_refunded: float
    base_amount_refunded: float
    base_discount_amount: float
    base_discount_tax_compensation_amount: NotRequired[float]
    base_original_price: NotRequired[float]
    base_price: float
    base_price_incl_tax: NotRequired[float]
    base_row_invoiced: float
    base_row_total: float
    base_row_total_incl_tax: float
    base_tax_amount: float
    base_tax_invoiced: float
    discount_amount: float
    discount_invoiced: float
    discount_tax_compensation_amount: NotRequired[float]
    discount_tax_compensation_invoiced: NotRequired[float]
    original_price: float
    price: float
    price_incl_tax: NotRequired[float]
    row_invoiced: float
    row_total: float
    row_total_incl_tax: float
    tax_amount: float
    tax_invoiced: NotRequired[float]
    base_discount_invoiced: NotRequired[float]
    base_discount_tax_compensation_invoiced: NotRequired[float]
    discount_tax_compensation_canceled: NotRequired[float]
    tax_canceled: NotRequired[float]
    discount_refunded: NotRequired[float]
    tax_refunded: NotRequired[float]
    base_discount_tax_compensation_refunded: NotRequired[float]
    base_discount_refunded: NotRequired[float]
    discount_tax_compensation_refunded: NotRequired[float]
    base_tax_refunded: NotRequired[float]

    discount_percent: float
    free_shipping: int
    is_qty_decimal: int
    is_virtual: int
    no_discount: int
    tax_percent: float

    locked_do_invoice: NotRequired[int]
    locked_do_ship: NotRequired[int]
    product_option: NotRequired[MagentoEntity]

    # Quantities
    qty_canceled: float
    qty_invoiced: float
    qty_ordered: float
    qty_refunded: float
    qty_shipped: float

    # Weight
    row_weight: float
    weight: NotRequired[float]

    # Misc
    weee_tax_applied: NotRequired[str]


class OrderStatusHistory(TypedDict):
    """An order status history entry."""
    comment: Union[str, None]
    created_at: str
    entity_id: int
    entity_name: str
    is_customer_notified: Union[str, None]
    is_visible_on_front: int
    parent_id: int
    status: str


class Order(WithExtensionAttributesDict):
    """An order."""
    # Field based on a sample of 100k real-world orders

    billing_address_id: int
    created_at: str
    email_sent: NotRequired[int]
    entity_id: int
    increment_id: str
    is_virtual: int
    protect_code: str
    quote_id: int
    remote_ip: NotRequired[str]
    x_forwarded_for: NotRequired[str]
    store_id: int
    store_name: str
    total_item_count: int
    total_qty_ordered: float
    updated_at: str
    weight: float

    ext_order_id: NotRequired[str]

    state: str
    status: str

    hold_before_status: NotRequired[Union[str, None]]
    hold_before_state: NotRequired[Union[str, None]]

    adjustment_negative: NotRequired[float]
    adjustment_positive: NotRequired[float]
    applied_rule_ids: NotRequired[str]
    base_adjustment_negative: NotRequired[float]
    base_adjustment_positive: NotRequired[float]
    base_currency_code: str
    base_discount_amount: float
    base_discount_canceled: NotRequired[float]
    base_discount_invoiced: NotRequired[float]
    base_discount_refunded: NotRequired[float]
    base_discount_tax_compensation_amount: float
    base_discount_tax_compensation_invoiced: NotRequired[float]
    base_discount_tax_compensation_refunded: NotRequired[float]
    base_grand_total: float
    base_shipping_amount: float
    base_shipping_canceled: NotRequired[float]
    base_shipping_discount_amount: float
    base_shipping_discount_tax_compensation_amnt: NotRequired[float]
    base_shipping_incl_tax: float
    base_shipping_invoiced: NotRequired[float]
    base_shipping_refunded: NotRequired[float]
    base_shipping_tax_amount: float
    base_shipping_tax_refunded: NotRequired[float]
    base_subtotal: float
    base_subtotal_canceled: NotRequired[float]
    base_subtotal_incl_tax: NotRequired[float]
    base_subtotal_invoiced: NotRequired[float]
    base_subtotal_refunded: NotRequired[float]
    base_tax_amount: float
    base_tax_canceled: NotRequired[float]
    base_tax_invoiced: NotRequired[float]
    base_tax_refunded: NotRequired[float]
    base_to_global_rate: float
    base_to_order_rate: float
    base_total_canceled: NotRequired[float]
    base_total_due: float
    base_total_invoiced: NotRequired[float]
    base_total_invoiced_cost: NotRequired[float]
    base_total_offline_refunded: NotRequired[float]
    base_total_online_refunded: NotRequired[float]
    base_total_paid: NotRequired[float]
    base_total_refunded: NotRequired[float]
    discount_amount: float
    discount_canceled: NotRequired[float]
    discount_invoiced: NotRequired[float]
    discount_refunded: NotRequired[float]
    discount_tax_compensation_amount: float
    discount_tax_compensation_invoiced: NotRequired[float]
    discount_tax_compensation_refunded: NotRequired[float]
    global_currency_code: str
    grand_total: float
    order_currency_code: str
    shipping_amount: float
    shipping_canceled: NotRequired[float]
    shipping_discount_amount: float
    shipping_discount_tax_compensation_amount: float
    shipping_incl_tax: float
    shipping_invoiced: NotRequired[float]
    shipping_refunded: NotRequired[float]
    shipping_tax_amount: float
    shipping_tax_refunded: NotRequired[float]
    store_currency_code: str
    store_to_base_rate: float
    store_to_order_rate: float
    subtotal: float
    subtotal_canceled: NotRequired[float]
    subtotal_incl_tax: float
    subtotal_invoiced: NotRequired[float]
    subtotal_refunded: NotRequired[float]
    tax_amount: float
    tax_canceled: NotRequired[float]
    tax_invoiced: NotRequired[float]
    tax_refunded: NotRequired[float]
    total_canceled: NotRequired[float]
    total_due: float
    total_invoiced: NotRequired[float]
    total_offline_refunded: NotRequired[float]
    total_online_refunded: NotRequired[float]
    total_paid: NotRequired[float]
    total_refunded: NotRequired[float]

    coupon_code: NotRequired[str]
    discount_description: NotRequired[str]

    # Customer information
    customer_email: str
    customer_firstname: NotRequired[str]
    customer_gender: NotRequired[int]
    customer_group_id: NotRequired[int]
    customer_id: NotRequired[int]
    customer_is_guest: int
    customer_lastname: NotRequired[str]
    customer_note_notify: int
    customer_taxvat: NotRequired[str]

    shipping_description: str

    relation_parent_id: NotRequired[str]
    original_increment_id: NotRequired[str]
    edit_increment: NotRequired[int]
    relation_parent_real_id: NotRequired[str]
    relation_child_real_id: NotRequired[str]
    relation_child_id: NotRequired[str]

    # Nested objects
    billing_address: Address
    items: list[OrderItem]
    payment: MagentoEntity
    status_histories: list[OrderStatusHistory]


# Customers
# =========

class Customer(WithExtensionAttributesDict):
    """A customer."""
    # Unclear what's really always present here
    id: NotRequired[int]
    group_id: NotRequired[int]
    default_billing: NotRequired[str]
    default_shipping: NotRequired[str]
    confirmation: NotRequired[str]
    created_at: str
    updated_at: str
    created_in: NotRequired[str]
    dob: NotRequired[str]
    email: str
    firstname: str
    lastname: str
    middlename: NotRequired[str]
    prefix: NotRequired[str]
    suffix: NotRequired[str]
    gender: NotRequired[int]
    store_id: NotRequired[int]
    taxvat: NotRequired[str]
    website_id: NotRequired[int]
    addresses: NotRequired[List[Address]]
    disable_auto_group_change: NotRequired[int]
    custom_attributes: List[CustomAttributeDict]


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
