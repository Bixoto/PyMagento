from magento import Magento

"""
This code exists only to validate types with Mypy; it's not supposed to be run.

We don't use pytest-mypy-testing because it's not flexible enough here.
"""


def mypy_test_source_items():
    m = Magento()
    source_items = m.get_source_items(source_code="_test")
    m.delete_source_items(source_items)
    m.save_source_items(list(source_items))
