# PyMagento Changelog

## 1.3.1 (2022/03/10)

* Fix `get_products_attribute_options` that wasn’t throwing if it received an error response from Magento.
* Improve some docstrings

## 1.3.0 (2022/02/04)

* Add support for environment variables as a fallback for `Magento()` arguments: `PYMAGENTO_TOKEN`, `PYMAGENTO_BASE_URL`, `PYMAGENTO_SCOPE`, `PYMAGENTO_USER_AGENT`
* Fix `user_agent` support ([`api-session` 1.1.1][as111])

[as111]: https://github.com/Bixoto/api-session/blob/main/CHANGELOG.md#111-20220204

## 1.2.0 (2022/02/03)

* Add `get_base_prices`
* Fix `get_special_prices` that was throwing an error when `read_only` was true

## 1.1.0 (2022/02/03)

* Add `save_product_media`, `delete_product_media`, `save_configurable_product_option`, `save_base_prices`,
  `get_special_prices`, `save_special_prices`, `delete_special_prices`, `delete_special_prices_by_sku`,
  `create_category`, `ship_order`
* Minor type hints improvements

## 1.0.0 (2021/12/21)

First public release.
