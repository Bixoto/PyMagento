# PyMagento

**PyMagento** is a Python client for the Magento 2 API. Its goal is to provide an easy-to-use
Pythonic interface to the Magento 2 API, while being lightweight and extendable.

* [Read the docs](https://pymagento2.readthedocs.io/)


Note: PyMagento is not affiliated to nor endorsed by Adobe or the Magento team.

## Install

We support Python 3.8+.

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

for order in client.get_orders(status="processing"):
    print(order["increment_id"], order["grand_total"])
```

For more information, [read the docs](https://pymagento2.readthedocs.io/).

Note: not all endpoints are implemented with dedicated methods; you can still call them with
`client.get_json_api("/V1/...")` for `GET` endpoints and `client.post_json_api("/V1/...", json=...)`.

## License

Copyright 2020-2024 [Bixoto](https://bixoto.com/).
