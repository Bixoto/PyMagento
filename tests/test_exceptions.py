from magento import MagentoException


def test_exception():
    e = MagentoException(message='El atributo "%1" no incluye una opción con el ID "%2".',
                         parameters=['manufacturer', '17726'])

    assert isinstance(e, Exception)
    assert str(e) == 'El atributo "manufacturer" no incluye una opción con el ID "17726".'

    e = MagentoException(message="single message")
    assert str(e) == "single message"

    e = MagentoException(message="Hello %name!", parameters={"name": "Jane"})
    assert str(e) == "Hello Jane!"

    # unknown/invalid parameters type
    e = MagentoException(message="blabla", parameters=42)  # type: ignore
    assert str(e) == "('blabla', 42)"
