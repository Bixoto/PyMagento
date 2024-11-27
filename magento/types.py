import sys
from typing import Union, TypedDict

from api_session import JSONDict

if sys.version_info >= (3, 11):
    from typing import NotRequired
else:
    from typing_extensions import NotRequired

__all__ = (
    'Category',
    'Customer',
    'MagentoEntity',
    'MediaEntry',
    'Order',
    'PathId',
    'Product',
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
