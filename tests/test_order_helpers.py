import magento


def test_is_order_on_hold():
    assert magento.is_order_on_hold({"status": "holded"})

    order = {"id": 123, "status": "awaiting_shipping"}
    assert not magento.is_order_on_hold(order)

    order["hold_before_state"] = "processing"
    assert magento.is_order_on_hold(order)


def test_is_order_cash_on_delivery():
    assert not magento.is_order_cash_on_delivery({"payment": {"method": "stripe_payments"}})
    assert not magento.is_order_cash_on_delivery({"payment": {"method": "paypal_express"}})
    assert magento.is_order_cash_on_delivery({"payment": {"method": "cashondelivery"}})


def test_get_order_shipping_address():
    order = {
        "extension_attributes": {
            "shipping_assignments": [
                {
                    "shipping": {
                        "address": {
                            "city": "Barcelona  ",
                            "postcode": " 12345",
                        },
                    }
                }
            ]
        }
    }
    assert magento.get_order_shipping_address(order) == {"city": "Barcelona", "postcode": "12345"}
