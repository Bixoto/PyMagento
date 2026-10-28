import json
from collections import ChainMap
from typing import Any
from unittest import mock

import pytest
import requests
from pytest_mock import MockerFixture

import magento
from magento import client
# noinspection PyProtectedMember
from magento.client import raise_for_response, Magento


class TemporaryEnv:
    def __enter__(self):
        temporary_env: dict[str, str] = {}
        self._environ = client.environ
        client.environ = ChainMap(temporary_env, client.environ)  # type: ignore[assignment]
        return temporary_env

    def __exit__(self, exc_type, exc_val, exc_tb):
        client.environ = self._environ


# inspired by https://stackoverflow.com/a/64991421/735926
def fake_response(status_code, text):
    return mock.Mock(**{
        "json.return_value": json.loads(text),
        "text.return_value": text,
        "status_code": status_code,
        "ok": 200 <= status_code < 300,
    })


class MockError(Exception):
    pass


class DummyMagento(magento.Magento):
    def request(self, method, url, *args, **kwargs):
        if method == 'get':
            if url.endswith('/V1/test/url'):
                return fake_response(200, f'{{"url": "{url}"}}')
            if url.endswith('/V1/products/S200'):
                return fake_response(200, '{"sku": "S200"}')
            if url.endswith('/V1/products/S404'):
                return fake_response(404, '{}')

        raise MockError()

    def get(self, *args, **kwargs):
        raise MockError()

    def post(self, *args, **kwargs):
        raise MockError()

    def put(self, *args, **kwargs):
        raise MockError()

    def delete(self, *args, **kwargs):
        raise MockError()


def test_url(mocker: MockerFixture):
    mocker.patch('magento.Magento', DummyMagento)
    m = magento.Magento(base_url="http://test", token="secret", scope="toto")
    url = m.get_json_api('/V1/test/url')["url"]
    assert url == "http://test/rest/toto/V1/test/url"

    url = m.request_api('get', '/V1/test/url', async_bulk=True).json()["url"]
    assert url == "http://test/rest/toto/async/bulk/V1/test/url", url


def test_raise_for_response():
    response = requests.Response()
    response.status_code = 200
    # Should not raise
    raise_for_response(response)


def test_client_env():
    with pytest.raises(RuntimeError):
        Magento()

    token = "xx-token"
    base_url = "https://xxxx"

    with TemporaryEnv() as environ:
        environ["PYMAGENTO_TOKEN"] = token
        with pytest.raises(RuntimeError):
            Magento()

    with TemporaryEnv() as environ:
        environ["PYMAGENTO_BASE_URL"] = base_url
        with pytest.raises(RuntimeError):
            Magento()

        environ["PYMAGENTO_TOKEN"] = token
        m = Magento()
        assert m.base_url == base_url
        assert token in m.headers.get("authorization", "")
        assert m.scope == client.DEFAULT_SCOPE

        scope = "abc"
        environ["PYMAGENTO_SCOPE"] = scope
        assert Magento().scope == scope

        user_agent = "hello I'm a test"
        environ["PYMAGENTO_USER_AGENT"] = user_agent
        assert Magento().headers.get("user-agent") == user_agent


def test_id_sort_pagination():
    class FakeClient(magento.Magento):
        def __init__(self, *args: Any, **kwargs: Any):
            super().__init__(*args, **kwargs)
            self.page = 0
            self.expected_filter_index = 0

        # noinspection PyMethodOverriding
        def get_json_api(self, _path, query, **_kwargs):
            assert isinstance(query, dict)
            assert query[f"searchCriteria[filter_groups][0][filters][{self.expected_filter_index}][field]"] == "foo"
            assert query[f"searchCriteria[filter_groups][0][filters][{self.expected_filter_index}][condition_type]"] \
                   == "gt"

            if self.page == 0:
                assert query[f"searchCriteria[filter_groups][0][filters][{self.expected_filter_index}][value]"] == 0
                self.page += 1
                return {"items": [{"foo": 1}, {"foo": 42}], "total_count": 3}

            if self.page == 1:
                assert query[f"searchCriteria[filter_groups][0][filters][{self.expected_filter_index}][value]"] == 42
                return {"items": [], "total_count": 3}

            raise AssertionError()

    client = FakeClient(base_url="http://test", token="secret", scope="toto")

    assert list(client.get_paginated("/path", id_field="foo", id_pagination=True, limit=3)) \
           == [{"foo": 1}, {"foo": 42}]

    # Shift by one because there is a filter
    client.expected_filter_index = 1
    client.page = 0
    assert list(client.get_paginated("/path", id_field="foo", id_pagination=True, limit=3,
                                     query=magento.make_field_value_query("bar", 0, condition_type="gt"))) \
           == [{"foo": 1}, {"foo": 42}]


def test_save_order_address(mocker: MockerFixture):
    magento_client = Magento(base_url="http://test", token="secret", scope="es")
    address = {
        "entity_id": 408749,
        "parent_id": 204378,
        "address_type": "shipping",
        "postcode": "39740",
    }
    put_json_api = mocker.patch.object(magento_client, "put_json_api", return_value=address)

    assert magento_client.save_order_address(address) == address
    put_json_api.assert_called_once_with("/V1/orders/204378", json={"entity": address})


def test_save_shipment_track(mocker: MockerFixture):
    magento_client = Magento(base_url="http://test", token="secret", scope="es")
    track = {
        "order_id": 204378,
        "parent_id": 102345,
        "track_number": "6A12345678901",
        "carrier_code": "custom",
        "title": "Colissimo",
        "extension_attributes": {"foo": "bar"},
    }
    saved_track = {**track, "entity_id": 56789}
    post_json_api = mocker.patch.object(magento_client, "post_json_api", return_value=saved_track)

    assert magento_client.save_shipment_track(track, scope="all") == saved_track
    post_json_api.assert_called_once_with("/V1/shipment/track", json={"entity": track}, scope="all")
    # The payload is sent untouched
    assert post_json_api.call_args.kwargs["json"]["entity"] is track
    assert "entity_id" not in track


def test_save_shipment_track_existing(mocker: MockerFixture):
    magento_client = Magento(base_url="http://test", token="secret", scope="es")
    track = {
        "entity_id": 56789,
        "order_id": 204378,
        "parent_id": 102345,
        "track_number": "6A12345678902",
        "carrier_code": "custom",
        "title": "Colissimo",
    }
    post_json_api = mocker.patch.object(magento_client, "post_json_api", return_value=track)

    assert magento_client.save_shipment_track(track) == track
    post_json_api.assert_called_once_with("/V1/shipment/track", json={"entity": track})


@pytest.mark.parametrize("ok", (True, False))
def test_delete_shipment_track(mocker: MockerFixture, ok: bool):
    magento_client = Magento(base_url="http://test", token="secret", scope="es")
    delete_json_api = mocker.patch.object(magento_client, "delete_json_api", return_value=ok)

    assert magento_client.delete_shipment_track(56789, scope="all") is ok
    delete_json_api.assert_called_once_with("/V1/shipment/track/56789", scope="all")

    delete_json_api.reset_mock()
    magento_client.delete_shipment_track("12/3 4")
    delete_json_api.assert_called_once_with("/V1/shipment/track/12%2F3%204")


@pytest.mark.parametrize("ok", (True, False))
def test_notify_shipment(mocker: MockerFixture, ok: bool):
    magento_client = Magento(base_url="http://test", token="secret", scope="es")
    post_json_api = mocker.patch.object(magento_client, "post_json_api", return_value=ok)

    assert magento_client.notify_shipment(102345, scope="all") is ok
    post_json_api.assert_called_once_with("/V1/shipment/102345/emails", scope="all")

    post_json_api.reset_mock()
    magento_client.notify_shipment("12/3 4")
    post_json_api.assert_called_once_with("/V1/shipment/12%2F3%204/emails")


def test_shipment_tracks_read_only(mocker: MockerFixture):
    magento_client = Magento(base_url="http://test", token="secret", scope="es", read_only=True)
    request = mocker.patch.object(requests.Session, "request")
    track = {
        "order_id": 204378,
        "parent_id": 102345,
        "track_number": "6A12345678901",
        "carrier_code": "custom",
        "title": "Colissimo",
    }

    with pytest.raises(AssertionError, match="read-only"):
        magento_client.save_shipment_track(track)
    with pytest.raises(AssertionError, match="read-only"):
        magento_client.delete_shipment_track(56789)
    with pytest.raises(AssertionError, match="read-only"):
        magento_client.notify_shipment(102345)

    request.assert_not_called()
def make_response(status_code: int, body: str) -> requests.Response:
    response = requests.Response()
    response.status_code = status_code
    response._content = body.encode()
    return response


def test_get_product_salable_quantity(mocker: MockerFixture):
    magento_client = Magento(base_url="http://test", token="secret", scope="es")
    send = mocker.patch.object(magento_client, "send", return_value=make_response(200, "12.5"))

    assert magento_client.get_product_salable_quantity("AB/12 C", 2) == 12.5
    assert send.call_args.args[0].method == "GET"
    assert send.call_args.args[0].url == "http://test/rest/es/V1/inventory/get-product-salable-quantity/AB%2F12%20C/2"

    get_json_api = mocker.patch.object(magento_client, "get_json_api", return_value=99996367)
    assert magento_client.get_product_salable_quantity("JP05-A4", 1, scope="default") == 99996367
    get_json_api.assert_called_once_with("/V1/inventory/get-product-salable-quantity/JP05-A4/1",
                                         none_on_404=False, scope="default")


def test_are_products_salable(mocker: MockerFixture):
    magento_client = Magento(base_url="http://test", token="secret", scope="es")
    salabilities = [
        {"sku": "JP05-A4", "stock_id": 1, "salable": True},
        {"sku": "AB/12 C", "stock_id": 1, "salable": False},
    ]
    send = mocker.patch.object(magento_client, "send", return_value=make_response(200, json.dumps(salabilities)))

    assert magento_client.are_products_salable(["JP05-A4", "AB/12 C"], 1) == salabilities
    assert send.call_args.args[0].method == "GET"
    assert send.call_args.args[0].url == \
           "http://test/rest/es/V1/inventory/are-products-salable?skus%5B%5D=JP05-A4&skus%5B%5D=AB%2F12+C&stockId=1"

    get_json_api = mocker.patch.object(magento_client, "get_json_api", return_value=salabilities[:1])
    assert magento_client.are_products_salable(("JP05-A4",), 1, scope="default") == salabilities[:1]
    get_json_api.assert_called_once_with("/V1/inventory/are-products-salable",
                                         params={"skus[]": ["JP05-A4"], "stockId": 1},
                                         none_on_404=False, scope="default")


def test_are_products_salable_empty(mocker: MockerFixture):
    magento_client = Magento(base_url="http://test", token="secret", scope="es")
    send = mocker.patch.object(magento_client, "send")

    assert magento_client.are_products_salable([], 1) == []
    send.assert_not_called()


def test_get_stock_by_sales_channel(mocker: MockerFixture):
    magento_client = Magento(base_url="http://test", token="secret", scope="es")
    stock = {"stock_id": 2, "name": "EU stock", "extension_attributes": {}}
    send = mocker.patch.object(magento_client, "send", return_value=make_response(200, json.dumps(stock)))

    assert magento_client.get_stock_by_sales_channel("website", "eu/fr site") == stock
    assert send.call_args.args[0].method == "GET"
    assert send.call_args.args[0].url == "http://test/rest/es/V1/inventory/stock-resolver/website/eu%2Ffr%20site"

    get_json_api = mocker.patch.object(magento_client, "get_json_api", return_value=stock)
    assert magento_client.get_stock_by_sales_channel("website", "base", scope="default") == stock
    get_json_api.assert_called_once_with("/V1/inventory/stock-resolver/website/base",
                                         none_on_404=False, scope="default")


@pytest.mark.parametrize("call", [
    lambda m: m.get_product_salable_quantity("UNKNOWN", 1),
    lambda m: m.are_products_salable(["JP05-A4"], 42),
    lambda m: m.get_stock_by_sales_channel("website", "unknown"),
])
def test_salability_404_raises(mocker: MockerFixture, call):
    magento_client = Magento(base_url="http://test", token="secret", scope="es")
    # The client returns None on 404s by default; these methods must raise instead
    assert magento_client.none_on_404
    mocker.patch.object(magento_client, "send",
                        return_value=make_response(404, '{"message": "No such entity.", "parameters": []}'))

    with pytest.raises(magento.MagentoException, match="No such entity"):
        call(magento_client)
