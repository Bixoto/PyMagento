from typing import Union

from api_session import JSONDict

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
)

MagentoEntity = JSONDict

Category = MagentoEntity
Customer = MagentoEntity
MediaEntry = MagentoEntity
Order = MagentoEntity
PathId = Union[int, str]
Product = MagentoEntity
Sku = str
SourceItem = MagentoEntity
