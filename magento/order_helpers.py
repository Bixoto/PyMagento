from magento.types import Order, ShippingAddress

__all__ = (
    'is_order_on_hold',
    'is_order_cash_on_delivery',
    'get_order_shipping_address',
)


def is_order_on_hold(order: Order) -> bool:
    """Test if an order is on hold."""
    return order["status"] == "holded" or "hold_before_state" in order


def is_order_cash_on_delivery(order: Order) -> bool:
    """Test if an order is paid with 'cash-on-delivery'."""
    # From Magento\OfflinePayments\Model\Cashondelivery::PAYMENT_METHOD_CASHONDELIVERY_CODE
    # For some reason Mypy is too dumb to see this is a boolean
    b: bool = order["payment"]["method"] == 'cashondelivery'
    return b


def get_order_shipping_address(order: Order) -> ShippingAddress:
    """Return the first shipping address of an order.

    Note the returned dict is a reference, so if you modify it, it modifies the order.
    Make a copy if you want to modify the address without affecting the order.
    """
    address: ShippingAddress = order["extension_attributes"]["shipping_assignments"][0]["shipping"]["address"]
    return address
