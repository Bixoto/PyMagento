# PyMagento

**PyMagento** is a Python client for the Magento 2 API. Its goal is to provide an easy-to-use
Pythonic interface to the Magento 2 API, while being lightweight and extendable.

* [Read the docs](https://pymagento2.readthedocs.io/)


Note: PyMagento is not affiliated to nor endorsed by Adobe or the Magento team.

## Install

We support only Python 3.8+.

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
```

For more information, [read the docs](https://pymagento2.readthedocs.io/).

## License

Copyright 2020-2022 [Bixoto](https://bixoto.com/).
