import json
from unittest import mock

import requests
from pytest_mock import MockerFixture

import magento
from magento.client import make_search_query, make_field_value_query, raise_for_response


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
    client = magento.Magento(base_url="http://test", token="secret", scope="toto")
    url = client.get_api('/V1/test/url').json()["url"]
    assert url == "http://test/rest/toto/V1/test/url"

    url = client.request_api('get', '/V1/test/url', async_bulk=True).json()["url"]
    assert url == "http://test/rest/toto/async/bulk/V1/test/url", url


def test_make_search_query():
    assert (
            make_search_query([[("a", 1, "gt"), ("b", 2, "eq")], [("c", 3, None)]],
                              page_size=12, current_page=4)
            ==
            {
                'searchCriteria[pageSize]': 12,
                'searchCriteria[currentPage]': 4,
                'searchCriteria[filter_groups][0][filters][0][field]': 'a',
                'searchCriteria[filter_groups][0][filters][0][value]': 1,
                'searchCriteria[filter_groups][0][filters][0][condition_type]': 'gt',
                'searchCriteria[filter_groups][0][filters][1][field]': 'b',
                'searchCriteria[filter_groups][0][filters][1][value]': 2,
                'searchCriteria[filter_groups][0][filters][1][condition_type]': 'eq',
                'searchCriteria[filter_groups][1][filters][0][field]': 'c',
                'searchCriteria[filter_groups][1][filters][0][value]': 3, }
    )


def test_make_field_value_query():
    assert (
            make_field_value_query("status", "awaiting_shipping", page_size=100)
            ==
            {
                "searchCriteria[filter_groups][0][filters][0][field]": "status",
                "searchCriteria[filter_groups][0][filters][0][value]": "awaiting_shipping",
                "searchCriteria[pageSize]": 100
            }
    )

    assert (
            make_field_value_query("source_code", "default", page_size=1, current_page=1)
            ==
            {
                "searchCriteria[filter_groups][0][filters][0][field]": "source_code",
                "searchCriteria[filter_groups][0][filters][0][value]": "default",
                "searchCriteria[pageSize]": 1,
                "searchCriteria[currentPage]": 1
            }
    )

    assert (
            make_field_value_query("source_code", "default",
                                   condition_type="eq", page_size=34, current_page=42)
            ==
            {
                "searchCriteria[filter_groups][0][filters][0][field]": "source_code",
                "searchCriteria[filter_groups][0][filters][0][value]": "default",
                "searchCriteria[filter_groups][0][filters][0][condition_type]": "eq",
                "searchCriteria[pageSize]": 34,
                "searchCriteria[currentPage]": 42
            }
    )


def test_raise_for_response():
    response = requests.Response()
    response.status_code = 200
    # Should not raise
    raise_for_response(response)
