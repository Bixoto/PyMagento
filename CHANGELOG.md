# PyMagento Changelog

## 2.8.0 (unreleased)

* `get_special_prices`: deduplicate prices by default
* Add `get_shipment`, `get_shipment_label`, `get_shipment_comments`

## 2.7.1 (2025/10/10)

* Expose `CATEGORY_ENTITY_TYPE_ID`, `CATALOG_PRODUCT_ENTITY_TYPE_ID`

## 2.7.0 (2025/09/22)

### 2.7.0a2 (2025/09/22)

* Adapt `magento.attributes` code to work with the new types

### 2.7.0a1 (2025/09/22)

* Add `Product`, `CustomAttributeDict` types

## 2.6.0 (2025/09/22)

* Add `async_add_products_to_categories`, `async_remove_products_from_categories`
* Add stricter type hints
* Add official support for Python 3.14

## 2.5.0 (2025/08/28)

* Breaking: `ship_order` now returns the shipment ID or raises in case of error, instead of returning the raw response
* Add more type hints

## 2.4.1 (2025/04/09)

* Explicitly export attributes under `magento`
  to fix the error `Module "magento" does not explicitly export attribute ...` when using Mypy in strict mode
* Add more type hints

## 2.4.0 (2025/04/02)

* `get_order_shipping_address` now returns the typed dict `ShippingAddress`
* Remove the wrong return type hints of `link_child_product` and `unlink_child_product`
* Add more type hints

## 2.3.0 (2025/01/27)

* `get_store_configs`: fix the `store_codes` filter
* Add an optional `fields` parameter to `request_api` and `get_paginated` as an alias for `params={"fields": ...}`
  to filter the response fields
    * Use it to largely reduce the network usage of `sku_exists`, `sku_was_bought`, `skus_were_bought`
* `get_product`: allow to pass `none_on_404=False` to throw if the product doesn't exist

## 2.2.2 (2025/01/09)

* Fix an issue in the `store_id` filter added in the previous release when the store ID is `0`

## 2.2.1 (2025/01/09)

* `get_special_prices`, `delete_special_prices_by_sku`, and `get_base_prices`: allow to filter by `store_id`
* `save_base_prices`: fix outdated documentation on the return type

## 2.2.0 (2025/01/09)

* `save_special_prices`: add a type hint and document the return value
* `delete_special_prices`: add a type hint for the return value
* Add the `TypedDict` `BasePrice` for `get_base_prices` and `save_base_prices`
* Add the `skus_were_bought` helper

## 2.1.0 (2024/11/27)

* Define `SourceItem` as a `TypedDict`
* Clarify the return type of paginated methods: `Iterator` instead of `Iterable`
* Add missing docstrings

## 2.0.2 (2024/11/13)

* Add `get_orders_by_increment_ids`
* Fix the docstring of `delete_source_items_by_source_code`

## 2.0.1 (2024/09/23)

* Fix the type hints of `order_id` in `get_order`, `hold_order`, `unhold_order`

## 2.0.0 (2024/08/26)

* Add `add_product_website_link` and `remove_product_website_link`

### Breaking changes

* Remove the functions deprecated since 1.11.2 and before: `set_product_stock_item`, `delete_default_source_items`,
  `VISIBILITY_BOTH`
* Some functions that were previously returning a `requests.Response` object now return the JSON-parsed payload:
    * `add_product_to_category`
    * `assign_attribute_set_attribute`
    * `delete_attribute`
    * `delete_product_media`
    * `delete_source_items`
    * `delete_special_prices`
    * `hold_order`
    * `link_child_product`
    * `remove_category`
    * `remove_attribute_set_attribute`
    * `remove_product_from_category`
    * `save_base_prices`
    * `save_configurable_product_option`
    * `save_special_prices`
    * `unlink_child_product`
    * `unhold_order`

  This means they raise in case of error response instead of silently ignoring it.

## 1.11.6 (2024/08/23)

* All methods now pass down their additional `**kwargs` to the underlying `request_api` method call
* Add official support for Python 3.13.0-rc.1

## 1.11.5 (2024/08/23)

* Allow to override the `scope` on a per-request basis

## 1.11.4 (2024/08/21)

* `delete_source_items_by_source_code`: don't call the Magento API if there is no item to delete

## 1.11.3 (2024/08/19)

* `get_order`, `get_bulk_status`, `get_customer`, `get_invoice`, `get_product_stock_item`, `get_product_stock_status`:
  add keyword parameter `none_on_404`

## 1.11.2 (2024/08/01)

* `get_order_item`: accept the item ID as a positional argument
* Add `delete_source_items_by_source_code` and deprecate `delete_default_source_items`
* Bump `api-session` to 1.4.1

## 1.11.1 (2024/07/08)

* Add `get_order_item`, `get_customer("me")`
* Add `get_current_customer`, `activate_current_customer`, `change_current_customer_password`
* Add `get_countries`, `get_country`
* `get_cart` now accepts the cart ID as a positional argument (not only as a keyword argument)
* Expose `magento.types.*` under `magento`
* Escape path arguments in all calls

## 1.11.0 (2024/04/12)

* `get_category_by_name`: add `assert_one` optional keyword parameter
* Add `move_category`, `get_child_categories`

### Breaking changes

* `create_category` now returns the created category rather than a `Response` object

## 1.10.3 (2024/02/15)

* fix `get_source_items` to accept an empty list of SKUs. In previous versions `skus=[]` (filter on an empty list) was
  interpreted the same way as `skus=None` (don’t filter at all)
* fix `get_store_configs` to accept an empty list of `store_codes`
* `update_product_stock_item`: improve the docstring

## 1.10.2 (2024/02/14)

* Implement more methods:
    * `get_apple_pay_auth`
    * `get_bulk_operations`, `get_bulk_detailed_status`, `get_bulk_operation_status_count`
    * `update_product_stock_item`
* Add `update_product_stock_item_quantity` and deprecate `set_product_stock_item`
* Allow to override the `page_size` in `get_paginated` and all methods that use it

## 1.10.1 (2024/02/07)

* Implement more methods:
    * `get_cms_block`, `delete_cms_block`
    * `create_coupon`, `update_coupon`, `get_coupon`, `delete_coupon`, `delete_coupons`, `delete_coupons_by_codes`
    * `delete_customer_address`
* Add helpers `sku_exists`, `sku_was_bought`, `get_categories_under_root`
* `remove_product_from_category`: fix for SKUs that contain slashes
* Improve some type hints on attributes methods

## 1.10.0 (2024/01/25)

* `save_product`: add `log_response` to be able to disable the log of the Magento response
* Add `delete_custom_attribute` and `delete_custom_attributes`
* Deprecate `VISIBILITY_BOTH` in favor of `VISIBILITY_IN_CATALOG_AND_SEARCH`
* Simplify some code using [`api-session`](https://github.com/bixoto/api-session) 1.3.6

### Breaking changes

* `get_order` and `save_attribute`: remove the `throw` parameter; the default was `True` but even if one passed `False`
  the method would still throw when trying to JSON-decode the error responses.

## 1.9.3 (2024/01/08)

* Add `get_cart`
* `BatchSaver.send_batch` now returns the response from the Magento API

## 1.9.2 (2023/10/06)

* Add `remove_category`
* Limit the query made by `get_category_by_name` to a single result

## 1.9.1 (2023/10/05)

* Add `get_category_products`, `add_product_to_category`, and `remove_product_from_category`

## 1.9.0 (2023/09/28)

* `get_categories`: add optional `path_prefix` to filter categories by path
* Add `magento.parse_datetime`
* Add `magento.IMAGE_MIME_TYPES` and `magento.DATE_ISO_8601_FORMAT`

### Breaking changes

* Remove `magento.DEFAULT_ROOT_CATEGORY_ID` as it can be confusing. Use `client.get_root_category_id()` instead.

## 1.8.0 (2023/09/12)

* Add `get_store_configs`, `get_store_groups`, `get_store_views`, `get_websites`
* Add helpers `get_current_store_group_id`, `get_root_category_id`
* All path components are now properly escaped in API calls
* Fix calls when using scope `default`
* Add official support for Python 3.12

### Breaking changes

* `get_product_media`: the second parameter is now called `media_id` instead of `entry_id` to be coherent with the API
* `magento.DEFAULT_CATEGORY_ID` is now named `magento.DEFAULT_ROOT_CATEGORY_ID`

## 1.7.4 (2023/07/11)

* Allow to override `Magento.PAGE_SIZE` when creating a client with the `batch_page_size` keyword argument
* Remove `Magento.TOKEN_LIFETIME`; it wasn’t used for anything

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
