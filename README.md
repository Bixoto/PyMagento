# PyMagento

**PyMagento** is a Python client for the Magento 2 API.

Note: PyMagento is not affiliated to nor endorsed by Adobe or the Magento team.

## Install

    pip install pymagento

This supports only Python 3.8+.

## Usage

```python
import magento

client = magento.Magento(base_url="...", token="...", scope="all")

product = client.get_product("SKU123")
print(magento.get_custom_attribute(product, "description"))
```

## License

Copyright 2020-2021 [Bixoto](https://bixoto.com/).
