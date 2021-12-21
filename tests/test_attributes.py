from magento import attributes
from magento.types import Product

custom_attributes1 = [{"attribute_code": "foo", "value": "bar"}]
custom_attributes2 = [{"attribute_code": "foo", "value": "bar"},
                      {"attribute_code": "bar", "value": "foo foo"}]
custom_attributes3 = [{"attribute_code": "yes", "value": "1"},
                      {"attribute_code": "nope", "value": "0"}]

product0: Product = {"custom_attributes": []}
product1: Product = {"custom_attributes": custom_attributes1}
product2: Product = {"custom_attributes": custom_attributes2}
product3: Product = {"custom_attributes": custom_attributes3}


def test_get_custom_attribute():
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


def test_get_boolean_custom_attribute():
    assert attributes.get_boolean_custom_attribute(product0, "foo") is None
    assert attributes.get_boolean_custom_attribute(product3, "yes") is True
    assert attributes.get_boolean_custom_attribute(product3, "nope") is False


def test_get_custom_attributes_dict():
    assert attributes.get_custom_attributes_dict(product0) == {}
    assert attributes.get_custom_attributes_dict(product1) == {"foo": "bar"}
    assert attributes.get_custom_attributes_dict(product2) == {"foo": "bar", "bar": "foo foo"}


def test_pretty_custom_attributes():
    assert attributes.pretty_custom_attributes([]) == ""
    assert attributes.pretty_custom_attributes(custom_attributes1) == "foo='bar'"
    assert attributes.pretty_custom_attributes(custom_attributes2) == "foo='bar', bar='foo foo'"
