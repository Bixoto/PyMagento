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


TIER_PRICES = [
    {"price": 2.99, "price_type": "fixed", "website_id": 0, "sku": "W1033",
     "customer_group": "ALL GROUPS", "quantity": 10},
    {"price": 5, "price_type": "discount", "website_id": 1, "sku": "W1033",
     "customer_group": "NOT LOGGED IN", "quantity": 50},
    {"price": 1.5, "price_type": "fixed", "website_id": 0, "sku": "W1034",
     "customer_group": "Wholesale", "quantity": 2.5},
]

PRICE_ERRORS = [
    {"message": "Invalid attribute %fieldName = %fieldValue.", "parameters": ["SKU", "W1035"],
     "extension_attributes": {}},
]


def test_get_tier_prices(mocker: MockerFixture):
    magento_client = Magento(base_url="http://test", token="secret", scope="es")
    post_json_api = mocker.patch.object(magento_client, "post_json_api", return_value=TIER_PRICES)

    assert magento_client.get_tier_prices(["W1033", "W1034"], scope="all") == TIER_PRICES
    post_json_api.assert_called_once_with("/V1/products/tier-prices-information",
                                          json={"skus": ["W1033", "W1034"]}, bypass_read_only=True, scope="all")


@pytest.mark.parametrize(("method_name", "path"), [
    ("save_tier_prices", "/V1/products/tier-prices"),
    ("delete_tier_prices", "/V1/products/tier-prices-delete"),
])
@pytest.mark.parametrize("errors", [[], PRICE_ERRORS])
def test_save_delete_tier_prices(mocker: MockerFixture, method_name: str, path: str, errors: list[Any]):
    magento_client = Magento(base_url="http://test", token="secret", scope="es")
    post_json_api = mocker.patch.object(magento_client, "post_json_api", return_value=errors)

    assert getattr(magento_client, method_name)(TIER_PRICES, retry=2) == errors
    post_json_api.assert_called_once_with(path, json={"prices": TIER_PRICES}, retry=2)


def test_tier_prices_read_only(mocker: MockerFixture):
    magento_client = Magento(base_url="http://test", token="secret", scope="es", read_only=True)
    session_request = mocker.patch.object(requests.Session, "request", return_value=fake_response(200, "[]"))

    assert magento_client.get_tier_prices(["W1033"]) == []
    session_request.assert_called_once()
    assert session_request.call_args.args[:2] == ("post", "http://test/rest/es/V1/products/tier-prices-information")
    session_request.reset_mock()

    with pytest.raises(AssertionError, match="read-only"):
        magento_client.save_tier_prices(TIER_PRICES)
    with pytest.raises(AssertionError, match="read-only"):
        magento_client.delete_tier_prices(TIER_PRICES)
    session_request.assert_not_called()
