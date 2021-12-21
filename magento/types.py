from typing import Dict, Any, Union

__all__ = (
    'MagentoEntity', 'Order', 'Product', 'Category', 'MediaEntry', 'SourceItem', 'Sku', 'PathId',
)

MagentoEntity = Dict[str, Any]
Order = MagentoEntity
Product = MagentoEntity
Category = MagentoEntity
MediaEntry = MagentoEntity
SourceItem = MagentoEntity
Sku = str
PathId = Union[int, str]
