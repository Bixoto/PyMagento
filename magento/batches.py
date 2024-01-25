from typing import List, Callable, Iterable, TypeVar, Generic

from api_session import JSONDict

from .client import Magento
from .queries import make_field_value_query
from .types import MagentoEntity

BATCH_SIZE = 500


class BatchSaver:
    """
    Base class to create context managers for asynchronous batches.
    """

    def __init__(self, client: Magento, api_path: str, batch_size=BATCH_SIZE):
        self.client = client
        self.path = api_path
        self.batch_size = batch_size
        self._batch: List[MagentoEntity] = []
        # some stats
        self._sent_batches = 0
        self._sent_items = 0

    def add_item(self, item_data: MagentoEntity):
        """
        Add an item to the current batch. If it makes the batch large enough, it’s sent to the API and a new empty
        batch is created.
        """
        self._batch.append(item_data)
        if len(self._batch) >= self.batch_size:
            self.send_batch()

    def send_batch(self):
        """
        Send the current pending batch (if any) and return the response from the Magento API.
        """
        if not self._batch:
            return None

        resp = self._put_batch()
        self._sent_items += len(self._batch)
        self._sent_batches += 1
        self._batch = []
        return resp

    def _put_batch(self) -> JSONDict:  # pragma: nocover
        return self.client.put_json_api(self.path, json=self._batch, async_bulk=True)

    def finalize(self):
        """
        Send the last pending batch (if any). This doesn’t need to be called when the object is used as a context
        manager.

        :return: a dictionary with the total number of batches and items
        """
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
    """
    Context manager to add products to an asynchronous batch job.

        >>> with ProductBatchSaver() as p:
        ...     for product_data in ...:
        ...         p.save_product(product_data)
    """

    def __init__(self, client: Magento, batch_size=BATCH_SIZE):
        super().__init__(client, '/V1/products/bySku', batch_size=batch_size)

    def save_product(self, product_data: dict):
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

        >>> products = ProductBatchGetter(Magento(), ["sku1", "sku2", ...])
        >>> for product in products:
        ...     print(product)
    """

    def __init__(self, client: Magento, skus: Iterable[str]):
        super().__init__(client.get_products, "sku", skus)
