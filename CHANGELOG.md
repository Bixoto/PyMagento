# PyMagento Changelog

## Unreleased

* Allow to override `Magento.PAGE_SIZE` when creating a client with the `batch_page_size` keyword argument

## 1.7.3 (2023/07/10)

* Uniformize the signatures of functions that return a generator. The following functions now support a `limit`:
  `get_categories` (#3), `get_stock_source_links`, `get_sources`. All these function now pass their additional keyword
  arguments to the internal `self.get_paginated` call.

## 1.7.2 (2023/07/04)

* Add `get_source`, `get_sources`, `save_source`

## 1.7.1 (2023/06/06)

* Support SKUs that contain slashes

## 1.7.0 (2023/05/24)

* Pass additional keyword arguments in `Magento()` to the underlying `APISession()` constructor
* Remove the `verbose` optional keyword option as well as the `log_response` parameter. Instead, use the `DEBUG` level
  for logging. Instead of setting these variables to `True`, set your logger level to `DEBUG`.

## 1.6.1 (2023/04/14)

* Fix `coerce_as` for list values in `get_custom_attribute`. The function now correctly gets each individual value
  rather than the whole list.
* Fix type hint for list values in `get_custom_attribute`

## 1.6.0 (2023/04/14)

* Remove `Magento.get_product_source_items` (deprecated since 1.3.3)
* Remove `pretty_custom_attributes` (deprecated since 1.3.4)
* Remove `log_progress` parameter to `Magento` (deprecated since 1.4.0)
* `get_custom_attribute`: add a more precise type hint on the return type

## 1.5.1 (2023/04/04)

* Add `get_product_by_query`
* `set_custom_attributes`, `set_custom_attribute` and `serialize_attribute_value` now support an optional
  `force_none=True` to prevent `None` values from being serialized as empty string. This can be useful to erase
  attributes.
* `MagentoAssertionError` is now accessible from the `magento` module (`magento.MagentoAssertionError`)

## 1.5.0 (2023/03/10)

### Breaking changes

* `save_product`: `log_response` must now be passed as a keyword argument. Before, you could use
  `.save_product(p, True)`; now you muse use `.save_product(p, log_response=True)`.
* `update_product`’s second argument is now called `product` instead of `product_data` to be consistent with
  `save_product`.

### Other changes

* Add `get_credit_memos` and `get_modules`
* Add `get_manufacturers` as a shortcut for `get_products_attribute_options("manufacturer")`
* `get_source_items` can now take a list of `skus` instead of a single one
* `save_product` and `update_product` now accept an optional `save_options` boolean
* Fix type hint of the `logger` parameter of the constructor of `Magento`

## 1.4.0 (2022/05/23)

* `get_order_shipping_address` now return a reference to the shipping address instead of a modified copy. This is a
  breaking change if you relied on this value to be a copy of the shipping address.
* Add `magento.format_datetime`
* Rename the parameter `log_progress` to `verbose`. Keep `log_progress` as an alias for backward compatibility.

## 1.3.4 (2022/05/04)

* Fix a bug in `BatchSaver` where the `batch_size` constructor argument was ignored
* Deprecate `pretty_custom_attributes`; use your own function instead
* Add `set_custom_attributes` and `serialize_attribute_value` functions
* Add `sort_orders` optional argument to `make_field_value_query`
* The dictionary returned by `get_custom_attributes_dict` is now ordered

## 1.3.3 (2022/04/14)

* Deprecate `get_product_source_items(sku)` in favor of `get_source_items(sku=sku)`, which returns exactly the same data
* Add `get_stock_source_links`, `get_product_stock_item` and `get_product_stock_status` methods
* Add `set_custom_attribute` function
* Document parameters of `unlink_child_product`

## 1.3.2 (2022/03/14)

* Improve docstrings of `magento.batches`
* Add missing search endpoints: `get_carts`, `get_cms_blocks`, `get_cms_pages`, `get_coupons`, `get_customer_groups`,
  `get_sales_rules`, `get_tax_rates`, `get_tax_rules`

## 1.3.1 (2022/03/10)

* Fix `get_products_attribute_options` that wasn’t throwing if it received an error response from Magento.
* Improve some docstrings

## 1.3.0 (2022/02/04)

* Add support for environment variables as a fallback for `Magento()` arguments: `PYMAGENTO_TOKEN`, `PYMAGENTO_BASE_URL`
  , `PYMAGENTO_SCOPE`, `PYMAGENTO_USER_AGENT`
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
