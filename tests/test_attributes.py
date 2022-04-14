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


def test_get_custom_attribute(product0, product1, product2):
    assert attributes.get_custom_attribute(product0, "foo") is None
    assert attributes.get_custom_attribute(product1, "idontexist") is None
    assert attributes.get_custom_attribute(product2, "idontexist") is None
    assert attributes.get_custom_attribute(product1, "foo") == "bar"

    product = {
        "custom_attributes": [
            {"attribute_code": "int", "value": "42"},
            {"attribute_code": "float", "value": "3.14"},
            {"attribute_code": "true", "value": "1"},
            {"attribute_code": "false", "value": "0"},
        ]
    }

    for typ in (bool, int, float):
        assert attributes.get_custom_attribute(product, "foo", typ) is None

    assert attributes.get_custom_attribute(product, "int") == "42"
    assert attributes.get_custom_attribute(product, "int", int) == 42
    assert attributes.get_custom_attribute(product, "int", bool) == True

    assert attributes.get_custom_attribute(product, "float") == "3.14"
    assert attributes.get_custom_attribute(product, "float", float) == 3.14

    assert attributes.get_custom_attribute(product, "true") == "1"
    assert attributes.get_custom_attribute(product, "true", int) == 1
    assert attributes.get_custom_attribute(product, "true", bool)

    assert attributes.get_custom_attribute(product, "false") == "0"
    assert attributes.get_custom_attribute(product, "false", int) == 0
    assert not attributes.get_custom_attribute(product, "false", bool)


def test_get_boolean_custom_attribute(product0, product1, product2, product3):
    assert attributes.get_boolean_custom_attribute(product0, "foo") is None
    assert attributes.get_boolean_custom_attribute(product3, "yes") is True
    assert attributes.get_boolean_custom_attribute(product3, "nope") is False


def test_get_custom_attributes_dict(product0, product1, product2):
    assert attributes.get_custom_attributes_dict(product0) == {}
    assert attributes.get_custom_attributes_dict(product1) == {"foo": "bar"}
    assert attributes.get_custom_attributes_dict(product2) == {"foo": "bar", "bar": "foo foo"}


def test_pretty_custom_attributes(custom_attributes1, custom_attributes2):
    assert attributes.pretty_custom_attributes([]) == ""
    assert attributes.pretty_custom_attributes(custom_attributes1) == "foo='bar'"
    assert attributes.pretty_custom_attributes(custom_attributes2) == "foo='bar', bar='foo foo'"


def test_set_custom_attribute_empty_item():
    assert attributes.set_custom_attribute({}, "a", True) == \
           {"custom_attributes": [{"attribute_code": "a", "value": "1"}]}
    assert attributes.set_custom_attribute({}, "a", False) == \
           {"custom_attributes": [{"attribute_code": "a", "value": "0"}]}
    assert attributes.set_custom_attribute({}, "a", None) == \
           {"custom_attributes": [{"attribute_code": "a", "value": ""}]}
    assert attributes.set_custom_attribute({}, "a", 42) == \
           {"custom_attributes": [{"attribute_code": "a", "value": "42"}]}
    assert attributes.set_custom_attribute({}, "a", "b") == \
           {"custom_attributes": [{"attribute_code": "a", "value": "b"}]}


def test_set_custom_attribute(product3):
    product4 = {}
    for attribute in product3["custom_attributes"]:
        product4 = attributes.set_custom_attribute(product4, attribute["attribute_code"], attribute["value"])
    assert product4 == product3
