"""Custom attributes utilities."""
from collections import OrderedDict
from collections.abc import Callable, Iterable
from typing import cast, overload, TypeVar, Any

from .types import MagentoEntity, CustomAttributeDict, Product, Customer, Category

T = TypeVar('T')

Item = TypeVar('Item', bound=Category | Customer | Product | MagentoEntity)

# From Magento
CATEGORY_ENTITY_TYPE_ID = 3
CATALOG_PRODUCT_ENTITY_TYPE_ID = 4


@overload
def get_custom_attribute(item: Item, attribute_code: str,
                         coerce_as: Callable[[str], T]) -> None | T | list[T]:  # pragma: nocover
    ...


@overload
def get_custom_attribute(item: Item, attribute_code: str) \
        -> None | str | list[str]:  # pragma: nocover
    ...


def get_custom_attribute(item: Item, attribute_code: str,
                         coerce_as: Callable[[str], Any] | None = None) -> Any:
    """Get a custom attribute from an item given its code.

    For example:
        >>> get_custom_attribute(..., "my_custom_attribute")
        "0"

        >>> get_custom_attribute(..., "my_custom_attribute", bool)
        False

    :param item:
    :param attribute_code:
    :param coerce_as: optional callable that is called on the attribute value if it's set.
      This is useful to circumvent Magento's limitation where all attribute values are strings.
    :return: attribute value or None.
    """
    if coerce_as is bool:
        # "0" -> False / "1" -> True
        def coerce_as(s: str) -> bool:
            return bool(int(s))

    attributes = cast(list[CustomAttributeDict], item.get("custom_attributes", []))
    for attribute in attributes:
        if attribute["attribute_code"] == attribute_code:
            value = attribute["value"]
            if coerce_as is None or value is None:
                return value

            if isinstance(value, list):
                return [coerce_as(s) for s in value]

            return coerce_as(value)
    return None


def get_boolean_custom_attribute(item: Item, attribute_code: str) -> bool | None:
    """Equivalent of ``get_custom_attribute(item, attribute_code, coerce_as=bool)`` with proper typing."""
    return cast(bool | None, get_custom_attribute(item, attribute_code, coerce_as=bool))


def get_custom_attributes_dict(item: Item) -> OrderedDict[str, list[str] | str | None]:
    """Get all custom attributes from an item as an ordered dict of code->value."""
    d = OrderedDict()
    for attribute in cast(list[CustomAttributeDict], item.get("custom_attributes", [])):
        d[attribute["attribute_code"]] = attribute["value"]

    return d


def serialize_attribute_value(value: str | int | float | bool | None, force_none: bool = False) -> str | None:
    """Serialize a value to be stored in a Magento attribute."""
    if isinstance(value, bool):
        return "1" if value else "0"
    elif value is None:
        if force_none:
            return None
        return ""
    return str(value)


def set_custom_attribute(item: Item, attribute_code: str,
                         attribute_value: str | int | float | bool | None,
                         *, force_none: bool = False) -> Item:
    """Set a custom attribute in an item dict.

    For example:
        >>> set_custom_attribute({}, "my_custom_attribute", 42)
        >>> set_custom_attribute({}, "my_custom_attribute", False)

    :param item: item dict. It’s modified in-place.
    :param attribute_code:
    :param attribute_value:
    :param force_none: by default, the attribute value ``None`` is serialized as an empty string. Setting this parameter
      to ``True`` forces this attribute value to ``None`` instead. This can be used to delete attributes.
    :return: the modified item dict.
    """
    return set_custom_attributes(item, [(attribute_code, attribute_value)], force_none=force_none)


def set_custom_attributes(item: Item,
                          attributes: Iterable[tuple[str, str | int | float | bool | None]],
                          *, force_none: bool = False) -> Item:
    """Set custom attributes in an item dict.
    Like ``set_custom_attribute`` but with an iterable of attributes.

    :param item: item dict. It’s modified in-place.
    :param attributes: iterable of label/value attribute tuples
    :param force_none: see ``set_custom_attribute`` for usage.
    :return: the modified item dict.
    """
    item_custom_attributes = cast(list[CustomAttributeDict], item.get("custom_attributes", []))

    attributes_index = {attribute["attribute_code"]: index for index, attribute in enumerate(item_custom_attributes)}

    for attribute_code, attribute_value in attributes:
        serialized_value = serialize_attribute_value(attribute_value, force_none=force_none)

        if attribute_code in attributes_index:
            index = attributes_index[attribute_code]
            item_custom_attributes[index]["value"] = serialized_value
        else:
            attributes_index[attribute_code] = len(item_custom_attributes)
            item_custom_attributes.append(CustomAttributeDict(
                attribute_code=attribute_code,
                value=serialized_value,
            ))

    item["custom_attributes"] = item_custom_attributes

    return item


def delete_custom_attribute(item: Item, attribute_code: str) -> Item:
    """Delete a custom attribute by forcing its value to ``None``."""
    return delete_custom_attributes(item, [attribute_code])


def delete_custom_attributes(item: Item, attributes: Iterable[str]) -> Item:
    """Delete custom attributes by forcing their value to ``None``."""
    return set_custom_attributes(item, ((attribute, None) for attribute in attributes), force_none=True)
