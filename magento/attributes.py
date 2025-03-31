"""Custom attributes utilities."""
from collections import OrderedDict
from typing import Callable, Optional, cast, Dict, Union, Sequence, List, Tuple, Iterable, \
    OrderedDict as OrderedDictType, overload, TypeVar, Any

from api_session import JSONDict

from .types import MagentoEntity

T = TypeVar('T')


@overload
def get_custom_attribute(item: JSONDict, attribute_code: str,
                         coerce_as: Callable[[str], T]) -> Union[None, T, List[T]]:  # pragma: nocover
    ...


@overload
def get_custom_attribute(item: JSONDict, attribute_code: str) -> Union[None, str, List[str]]:  # pragma: nocover
    ...


def get_custom_attribute(item: MagentoEntity, attribute_code: str, coerce_as: Union[Callable[[str], Any], None] = None) \
        -> Any:
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

    for attribute in item.get("custom_attributes", []):
        if attribute["attribute_code"] == attribute_code:
            value: Union[str, List[str]] = attribute["value"]
            if coerce_as is None:
                return value

            if isinstance(value, list):
                return [coerce_as(s) for s in value]

            return coerce_as(value)
    return None


def get_boolean_custom_attribute(item: JSONDict, attribute_code: str) -> Optional[bool]:
    """Equivalent of ``get_custom_attribute(item, attribute_code, coerce_as=bool)`` with proper typing."""
    return cast(Optional[bool], get_custom_attribute(item, attribute_code, coerce_as=bool))


def get_custom_attributes_dict(item: JSONDict) -> OrderedDictType[str, Union[Sequence[str], str]]:
    """Get all custom attributes from an item as an ordered dict of code->value."""
    d = OrderedDict()
    for attribute in item.get("custom_attributes", []):
        d[attribute["attribute_code"]] = attribute["value"]

    return d


def serialize_attribute_value(value: Union[str, int, float, bool, None], force_none: bool = False) -> Optional[str]:
    """Serialize a value to be stored in a Magento attribute."""
    if isinstance(value, bool):
        return "1" if value else "0"
    elif value is None:
        if force_none:
            return None
        return ""
    return str(value)


def set_custom_attribute(item: MagentoEntity, attribute_code: str, attribute_value: Union[str, int, float, bool, None],
                         *, force_none: bool = False) -> MagentoEntity:
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


def set_custom_attributes(item: MagentoEntity, attributes: Iterable[Tuple[str, Union[str, int, float, bool, None]]],
                          *, force_none: bool = False) -> MagentoEntity:
    """Set custom attributes in an item dict.
    Like ``set_custom_attribute`` but with an iterable of attributes.

    :param item: item dict. It’s modified in-place.
    :param attributes: iterable of label/value attribute tuples
    :param force_none: see ``set_custom_attribute`` for usage.
    :return: the modified item dict.
    """
    item_custom_attributes: List[Dict[str, Optional[str]]] = item.get("custom_attributes", [])

    attributes_index = {attribute["attribute_code"]: index for index, attribute in enumerate(item_custom_attributes)}

    for attribute_code, attribute_value in attributes:
        serialized_value = serialize_attribute_value(attribute_value, force_none=force_none)

        if attribute_code in attributes_index:
            index = attributes_index[attribute_code]
            item_custom_attributes[index]["value"] = serialized_value
        else:
            attributes_index[attribute_code] = len(item_custom_attributes)
            item_custom_attributes.append({
                "attribute_code": attribute_code,
                "value": serialized_value,
            })

    item["custom_attributes"] = item_custom_attributes

    return item


def delete_custom_attribute(item: MagentoEntity, attribute_code: str) -> MagentoEntity:
    """Delete a custom attribute by forcing its value to ``None``."""
    return delete_custom_attributes(item, [attribute_code])


def delete_custom_attributes(item: MagentoEntity, attributes: Iterable[str]) -> MagentoEntity:
    """Delete custom attributes by forcing their value to ``None``."""
    return set_custom_attributes(item, ((attribute, None) for attribute in attributes), force_none=True)
