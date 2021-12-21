from typing import List, Callable, Iterable, TypeVar, Generic

from .client import Magento, make_field_value_query
from .types import MagentoEntity

BATCH_SIZE = 500


class BatchSaver:
    def __init__(self, client: Magento, api_path: str, batch_size=BATCH_SIZE):
        self.client = client
        self.path = api_path
        self.batch_size = batch_size
        self._batch: List[MagentoEntity] = []
        # some stats
        self._sent_batches = 0
        self._sent_items = 0

    def add_item(self, item_data):
        self._batch.append(item_data)
        if len(self._batch) >= BATCH_SIZE:
            self.send_batch()

    def send_batch(self):
        if not self._batch:
            return

        sent = len(self._batch)
        # Note this raises on error
        _resp = self.client.put_api(self.path, json=self._batch, throw=True, async_bulk=True).json()
        self._sent_items += sent
        self._sent_batches += 1
        self._batch = []

    def finalize(self):
        self.send_batch()
        return {
            "sent_batches": self._sent_batches,
            "sent_items": self._sent_items,
        }

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.finalize()


class ProductBatchSaver(BatchSaver):
    def __init__(self, client: Magento, batch_size=BATCH_SIZE):
        super().__init__(client, '/V1/products/bySku', batch_size=batch_size)

    def save_product(self, product_data):
        self.add_item({"product": product_data})


T = TypeVar('T')


class BatchGetter(Generic[T]):
    """
    Base class to create generators of Magento items that can be retrieved from the API using queries.
    This retrieves items in batches but can be iterated on like any iterator.
    """

    def __init__(self, getter: Callable[..., Iterable[T]], key_field: str, keys: Iterable, batch_size=50):
        self.batch_size = batch_size
        self.getter = getter
        self.key_field = key_field
        self.keys = keys
        self._batch: List[str] = []

    def _get_batch(self) -> Iterable[T]:
        if not self._batch:
            return

        in_ = ",".join(self._batch)
        q = make_field_value_query(field=self.key_field, value=in_, condition_type="in")
        yield from self.getter(query=q, limit=len(self._batch))

        self._batch = []

    def __iter__(self):
        for key in self.keys:
            self._batch.append(str(key))
            if len(self._batch) < self.batch_size:
                continue

            yield from self._get_batch()

        yield from self._get_batch()


class ProductBatchGetter(BatchGetter[dict]):
    """
    Get a bunch of products from an iterable of SKUs:

        >>> products = ProductBatchGetter(Magento(...), ["sku1", "sku2", ...])
        >>> for product in products:
        ...     print(product)
    """

    def __init__(self, client: Magento, skus: Iterable[str]):
        super().__init__(client.get_products, "sku", skus)
