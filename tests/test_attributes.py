from collections import OrderedDict
from typing import Any, Dict
from typing_extensions import reveal_type

import pytest

from magento import attributes


@pytest.fixture
def custom_attributes1():
    return [{"attribute_code": "foo", "value": "bar"}]


@pytest.fixture
def custom_attributes2():
    return [{"attribute_code": "foo", "value": "bar"},
            {"attribute_code": "bar", "value": "foo foo"}]


@pytest.fixture
def custom_attributes3():
    return [{"attribute_code": "yes", "value": "1"},
            {"attribute_code": "nope", "value": "0"}]


@pytest.fixture
def product0():
    return {"custom_attributes": []}


@pytest.fixture
def product1(custom_attributes1):
    return {"custom_attributes": custom_attributes1}


@pytest.fixture
def product2(custom_attributes2):
    return {"custom_attributes": custom_attributes2}


@pytest.fixture
def product3(custom_attributes3):
    return {"custom_attributes": custom_attributes3}


# Note this is really slow. Moving the test in its own file doesn't help.
# Doc: https://github.com/davidfritzsche/pytest-mypy-testing
@pytest.mark.mypy_testing
def mypy_test_get_custom_attribute_coerce_as_overload(product0):
    value = attributes.get_custom_attribute(product0, "something", coerce_as=int)
    reveal_type(value)  # N: Revealed type is 'Union[None, builtins.int, builtins.list[builtins.int]]'


def test_serialize_attribute_value_none():
    assert attributes.serialize_attribute_value(None) == ""
    assert attributes.serialize_attribute_value(None, force_none=False) == ""
    assert attributes.serialize_attribute_value(None, force_none=True) is None


def test_get_custom_attribute(product0, product1, product2):
    assert attributes.get_custom_attribute(product0, "foo") is None
    assert attributes.get_custom_attribute(product1, "i-dont-exist") is None
    assert attributes.get_custom_attribute(product2, "i-dont-exist") is None
    assert attributes.get_custom_attribute(product1, "foo") == "bar"

    product = {
        "custom_attributes": [
            {"attribute_code": "int", "value": "42"},
            {"attribute_code": "float", "value": "3.14"},
            {"attribute_code": "true", "value": "1"},
            {"attribute_code": "false", "value": "0"},
            {"attribute_code": "category_ids", "value": ["1", "2", "3"]},
        ]
    }

    for typ in (bool, int, float):
        assert attributes.get_custom_attribute(product, "foo", typ) is None

    assert attributes.get_custom_attribute(product, "int") == "42"
    assert attributes.get_custom_attribute(product, "int", int) == 42
    assert attributes.get_custom_attribute(product, "int", bool) is True

    assert attributes.get_custom_attribute(product, "float") == "3.14"
    assert attributes.get_custom_attribute(product, "float", float) == 3.14

    assert attributes.get_custom_attribute(product, "true") == "1"
    assert attributes.get_custom_attribute(product, "true", int) == 1
    assert attributes.get_custom_attribute(product, "true", bool)

    assert attributes.get_custom_attribute(product, "false") == "0"
    assert attributes.get_custom_attribute(product, "false", int) == 0
    assert not attributes.get_custom_attribute(product, "false", bool)

    assert attributes.get_custom_attribute(product, "category_ids") == ["1", "2", "3"]
    assert attributes.get_custom_attribute(product, "category_ids", int) == [1, 2, 3]


def test_get_boolean_custom_attribute(product0, product3):
    assert attributes.get_boolean_custom_attribute(product0, "foo") is None
    assert attributes.get_boolean_custom_attribute(product3, "yes") is True
    assert attributes.get_boolean_custom_attribute(product3, "nope") is False


def test_get_custom_attributes_dict(product0, product1, product2):
    assert attributes.get_custom_attributes_dict(product0) == {}
    assert attributes.get_custom_attributes_dict(product1) == {"foo": "bar"}
    assert attributes.get_custom_attributes_dict(product2) == {"foo": "bar", "bar": "foo foo"}


def test_set_custom_attribute_empty_item():
    assert attributes.set_custom_attribute({}, "a", True) == \
           {"custom_attributes": [{"attribute_code": "a", "value": "1"}]}
    assert attributes.set_custom_attribute({}, "a", False) == \
           {"custom_attributes": [{"attribute_code": "a", "value": "0"}]}
    assert attributes.set_custom_attribute({}, "a", None) == \
           {"custom_attributes": [{"attribute_code": "a", "value": ""}]}
    assert attributes.set_custom_attribute({}, "a", None, force_none=True) == \
           {"custom_attributes": [{"attribute_code": "a", "value": None}]}
    assert attributes.set_custom_attribute({}, "a", 42) == \
           {"custom_attributes": [{"attribute_code": "a", "value": "42"}]}
    assert attributes.set_custom_attribute({}, "a", "b") == \
           {"custom_attributes": [{"attribute_code": "a", "value": "b"}]}


def test_set_custom_attribute(product3):
    product4: Dict[str, Any] = {}
    for attribute in product3["custom_attributes"]:
        product4 = attributes.set_custom_attribute(product4, attribute["attribute_code"], attribute["value"])
    assert product4 == product3


def test_set_custom_attributes(product0):
    attrs = [("a", "a1"), ("b", "b1"), ("a", "a2"), ("a", "a3"), ("c", "c1"), ("d", "d1"), ("c", "c2")]

    expected_dict = OrderedDict([
        ("a", "a3"),
        ("b", "b1"),
        ("c", "c2"),
        ("d", "d1"),
    ])

    product = attributes.set_custom_attributes(product0, attrs)
    assert attributes.get_custom_attributes_dict(product) == expected_dict

    # setting them again doesn't change anything
    product = attributes.set_custom_attributes(product, attrs)
    assert attributes.get_custom_attributes_dict(product) == expected_dict


def test_delete_custom_attribute():
    assert attributes.get_custom_attributes_dict(attributes.delete_custom_attribute({}, "foo")) \
           == {"foo": None}


def test_delete_custom_attributes_empty():
    assert attributes.delete_custom_attributes({}, []) == {"custom_attributes": []}


def test_delete_custom_attributes(product3):
    assert attributes.get_custom_attributes_dict(attributes.delete_custom_attributes(product3, ["yes", "not-present"])) \
           == {"yes": None, "not-present": None, "nope": "0"}
