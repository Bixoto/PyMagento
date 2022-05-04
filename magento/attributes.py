"""
Custom attributes utilities.
"""
from collections import OrderedDict
from typing import Callable, Optional, cast, Dict, Any, Union, Sequence, List, Tuple, Iterable, \
    OrderedDict as OrderedDictType


def get_custom_attribute(item: dict, attribute_code: str, coerce_as: Optional[Callable] = None):
    """
    Get a custom attribute from an item given its code.

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
    for attribute in item.get("custom_attributes", []):
        if attribute["attribute_code"] == attribute_code:
            value = attribute["value"]
            if coerce_as:
                if coerce_as == bool:
                    # "0" -> False / "1" -> True
                    return bool(int(value))
                return coerce_as(value)
            return value


def get_boolean_custom_attribute(item: dict, attribute_code: str) -> Optional[bool]:
    """
    Equivalent of ``get_custom_attribute(item, attribute_code, coerce_as=bool)`` with proper typing.
    """
    return cast(Optional[bool], get_custom_attribute(item, attribute_code, coerce_as=bool))


def get_custom_attributes_dict(item: Dict[str, Any]) -> OrderedDictType[str, Union[Sequence[str], str]]:
    """
    Get all custom attributes from an item as an ordered dict of code->value.
    """
    d = OrderedDict()
    for attribute in item.get("custom_attributes", []):
        d[attribute["attribute_code"]] = attribute["value"]

    return d


def pretty_custom_attributes(custom_attributes: List[Dict[str, Any]]):  # pragma: nocover
    """
    [Deprecated] Return a human-friendly compact representation of a sequence of custom attributes.
    """
    attributes = get_custom_attributes_dict({"custom_attributes": custom_attributes})
    return ", ".join(f"{k}={repr(v)}" for k, v in attributes.items())


def serialize_attribute_value(value: Union[str, int, float, bool, None]):
    """
    Serialize a value to be stored in a Magento attribute.
    """
    if isinstance(value, bool):
        return "1" if value else "0"
    elif value is None:
        return ""
    return str(value)


def set_custom_attribute(item: dict, attribute_code: str, attribute_value: Union[str, int, float, bool, None]):
    """
    Set a custom attribute in an item dict.

    For example:
        >>> set_custom_attribute({}, "my_custom_attribute", 42)
        >>> set_custom_attribute({}, "my_custom_attribute", False)

    :param item: item dict. It’s modified in-place.
    :param attribute_code:
    :param attribute_value:
    :return: the modified item dict.
    """
    return set_custom_attributes(item, [(attribute_code, attribute_value)])


def set_custom_attributes(item: dict, attributes: Iterable[Tuple[str, Union[str, int, float, bool, None]]]):
    """
    Set custom attributes in an item dict.
    Like ``set_custom_attribute`` but with an iterable of attributes.

    :param item: item dict. It’s modified in-place.
    :param attributes: iterable of label/value attribute tuples
    :return: the modified item dict.
    """
    item_custom_attributes: List[Dict[str, str]] = item.get("custom_attributes", [])

    attributes_index = {attribute["attribute_code"]: index for index, attribute in enumerate(item_custom_attributes)}

    for attribute_code, attribute_value in attributes:
        serialized_value = serialize_attribute_value(attribute_value)

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
