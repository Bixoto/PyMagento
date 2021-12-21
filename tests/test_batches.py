from magento import Magento
from magento.batches import ProductBatchSaver, ProductBatchGetter, BatchGetter
from magento.client import Query


def test_product_batch_saver():
    client = Magento(token="123", base_url="https://example.com", read_only=True, scope="toto")
    p = ProductBatchSaver(client, [])
    with p as _:
        pass

    assert p._sent_items == 0
    assert p._sent_batches == 0


def test_batch_getter():
    def dummy_getter(query: Query, limit: int):
        assert limit == 2
        assert isinstance(query, dict)
        assert query['searchCriteria[filter_groups][0][filters][0][condition_type]'] == 'in'
        assert query['searchCriteria[filter_groups][0][filters][0][field]'] == 'myfield'
        values = [int(n) for n in query['searchCriteria[filter_groups][0][filters][0][value]'].split(",")]
        return (value * 2 for value in values)

    bg = BatchGetter(dummy_getter, "myfield", range(20), batch_size=2)
    assert list(bg) == list(range(0, 40, 2))


def test_product_batch_getter():
    client = Magento(token="123", base_url="https://example.com", read_only=True, scope="toto")
    p = ProductBatchGetter(client, [])

    assert list(p) == []
