import re
import requests
from typing import List, Optional, Union, Dict, cast

RE_PARAM = re.compile(r"%([A-Za-z0-9]+)")

__all__ = ('build_exception_text', 'MagentoException', 'MagentoAssertionError')


def build_exception_text(message: str, parameters: Optional[Union[Dict[str, str], List[str]]]):
    if not parameters:
        return message

    # Magento sometimes return a dict, sometimes a list.
    # For example:
    #   message = "%fieldName is a required field."
    #   parameters = {"fieldName":"product"}
    if isinstance(parameters, dict):
        return cast(str, RE_PARAM.sub(lambda m: str(parameters[m.group(1)]), message))  # type: ignore

    # For example:
    #   message = 'El atributo "%1" no incluye una opción con el ID "%2".'
    #   parameters = ['manufacturer', '17726']
    if isinstance(parameters, list):
        return cast(str, RE_PARAM.sub(lambda m: str(parameters[int(m.group(1)) - 1]), message))  # type: ignore

    # Ok fallback
    return str((message, parameters))


class MagentoException(Exception):
    def __init__(self, message,
                 parameters: Optional[Union[Dict[str, str], List[str]]] = None,
                 trace: Optional[str] = None,
                 response: Optional[requests.Response] = None):
        self.message = message
        self.parameters = parameters
        self.response = response
        self.trace = trace

        text = build_exception_text(message, parameters)
        super().__init__(text)


class MagentoAssertionError(AssertionError):
    """
    Exception raised by ``Magento#get_product_by_query`` when the query returns more than one product.

    This exception doesn’t inherit from ``MagentoException`` because it’s not a Magento error per se.
    """
    pass
