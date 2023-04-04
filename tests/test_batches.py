import pytest

from magento import Magento
from magento.batches import ProductBatchSaver, ProductBatchGetter, BatchGetter, BatchSaver
from magento.queries import Query


@pytest.fixture()
def test_client():
    return Magento(token="123", base_url="https://example.com", read_only=True, scope="toto")


def test_batch_saver(test_client):
    put_batches = []

    class TestBatchSaver(BatchSaver):
        def _put_batch(self):
            put_batches.append(self._batch)

    bs = TestBatchSaver(client=test_client, api_path="test", batch_size=4)

    for n in range(15):
        bs.add_item({"t": n})

    assert bs.finalize() == {"sent_batches": 4, "sent_items": 15}

    bs.send_batch()  # this should be a no-op
    assert bs.finalize() == {"sent_batches": 4, "sent_items": 15}

    assert put_batches == [
        [{"t": n} for n in range(4)],
        [{"t": n} for n in range(4, 8)],
        [{"t": n} for n in range(8, 12)],
        [{"t": n} for n in range(12, 15)],
    ]


def test_product_batch_saver(test_client):
    put_batches = []

    class TestProductBatchSaver(ProductBatchSaver):
        def _put_batch(self):
            put_batches.append(self._batch)

    p = TestProductBatchSaver(test_client)
    with p as p_:
        p_.save_product({"sku": "A123"})

    assert p._sent_items == 1
    assert p._sent_batches == 1
    assert put_batches == [[{"product": {"sku": "A123"}}]]


def test_batch_getter():
    def dummy_getter(query: Query, limit: int):
        assert limit == 2
        assert isinstance(query, dict)
        assert query['searchCriteria[filter_groups][0][filters][0][condition_type]'] == 'in'
        assert query['searchCriteria[filter_groups][0][filters][0][field]'] == 'my_field'
        values = [int(n) for n in query['searchCriteria[filter_groups][0][filters][0][value]'].split(",")]
        return (value * 2 for value in values)

    bg = BatchGetter(dummy_getter, "my_field", range(20), batch_size=2)
    assert list(bg) == list(range(0, 40, 2))


def test_product_batch_getter():
    client = Magento(token="123", base_url="https://example.com", read_only=True, scope="toto")
    p = ProductBatchGetter(client, [])

    assert list(p) == []
