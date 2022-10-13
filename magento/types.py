from typing import Union
from api_session import JSONDict

__all__ = (
    'MagentoEntity', 'Order', 'Product', 'Category', 'MediaEntry', 'SourceItem', 'Sku', 'PathId',
)

MagentoEntity = JSONDict
Order = MagentoEntity
Product = MagentoEntity
Category = MagentoEntity
MediaEntry = MagentoEntity
SourceItem = MagentoEntity
Sku = str
PathId = Union[int, str]
