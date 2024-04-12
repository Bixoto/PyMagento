# PyMagento

[![PyPI version](https://img.shields.io/pypi/v/pymagento)](https://pypi.org/project/pymagento/) [![PyPI downloads](https://img.shields.io/pypi/dm/pymagento)](https://pypi.org/project/pymagento/)

**PyMagento** is a Python client for the Magento 2 API. Its goal is to provide an easy-to-use Pythonic interface
to the Magento 2 API, while being lightweight and extendable.

* [Read the docs](https://pymagento2.readthedocs.io/)

Features:
* Lightweight: entities are returned as plain dictionaries; there is no custom `Order` or `Product` class
* Easy to extend: subclass `magento.Magento` and add your own methods
* Transparent pagination: functions that make paginated queries return lazy iterables (generators)
* Fully typed: all functions have type hints if necessary
* Production-ready: at Bixoto, we use PyMagento in production since 2020
* Python 3.8+ support
* MIT license

Note: PyMagento is not affiliated to nor endorsed by Adobe or the Magento team.

## Install

### Pip

    python -m pip install pymagento

### Poetry

    poetry add pymagento

## Usage

```python
import magento

client = magento.Magento(base_url="...", token="...", scope="all")

product = client.get_product("SKU123")
print(magento.get_custom_attribute(product, "description"))

# Get orders by status
for order in client.get_orders(status="processing"):
    print(order["increment_id"], order["grand_total"])

# Make more complex queries
query = magento.make_search_query([
    [("customer_email", "billgates@example.com", "eq")],
    [("status", "complete", "eq")],
])

for order in client.get_orders(query=query, limit=10):
    print(order["increment_id"], len(order["items"]))
```

For more information, [read the docs](https://pymagento2.readthedocs.io/).

Note: not all endpoints are implemented with dedicated methods. You can call them with
`client.get_json_api("/V1/...")` for `GET` endpoints and `client.post_json_api("/V1/...", json=...)`.

## License

Copyright 2020-2024 [Bixoto](https://bixoto.com/). See the [`LICENSE`](./LICENSE).

## Other projects

* [MyMagento](https://github.com/TDKorn/my-magento): new project started in 2022; MyMagento didn’t exist when we started PyMagento.
  This is a more high-level API that can be a good fit if you’re not familiar with Magento’s API.
* [PyMagento-REST](https://pypi.org/project/PyMagento-REST/) (abandoned)
* [bialecki/pymagento](https://github.com/bialecki/pymagento): Magento 1.x only (abandoned)
* [python-magento](https://github.com/bernieke/python-magento): Magento 1.x only (abandoned)
