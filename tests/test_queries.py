from magento import queries as q


def test_make_search_query():
    assert (
            q.make_search_query([[("a", 1, "gt"), ("b", 2, "eq")], [("c", 3, None)]],
                                page_size=12, current_page=4)
            ==
            {
                'searchCriteria[pageSize]': 12,
                'searchCriteria[currentPage]': 4,
                'searchCriteria[filter_groups][0][filters][0][field]': 'a',
                'searchCriteria[filter_groups][0][filters][0][value]': 1,
                'searchCriteria[filter_groups][0][filters][0][condition_type]': 'gt',
                'searchCriteria[filter_groups][0][filters][1][field]': 'b',
                'searchCriteria[filter_groups][0][filters][1][value]': 2,
                'searchCriteria[filter_groups][0][filters][1][condition_type]': 'eq',
                'searchCriteria[filter_groups][1][filters][0][field]': 'c',
                'searchCriteria[filter_groups][1][filters][0][value]': 3, }
    )


def test_make_field_value_query():
    assert (
            q.make_field_value_query("status", "awaiting_shipping", page_size=100)
            ==
            {
                "searchCriteria[filter_groups][0][filters][0][field]": "status",
                "searchCriteria[filter_groups][0][filters][0][value]": "awaiting_shipping",
                "searchCriteria[pageSize]": 100
            }
    )

    assert (
            q.make_field_value_query("source_code", "default", page_size=1, current_page=1)
            ==
            {
                "searchCriteria[filter_groups][0][filters][0][field]": "source_code",
                "searchCriteria[filter_groups][0][filters][0][value]": "default",
                "searchCriteria[pageSize]": 1,
                "searchCriteria[currentPage]": 1
            }
    )

    assert (
            q.make_field_value_query("source_code", "default",
                                     condition_type="eq", page_size=34, current_page=42)
            ==
            {
                "searchCriteria[filter_groups][0][filters][0][field]": "source_code",
                "searchCriteria[filter_groups][0][filters][0][value]": "default",
                "searchCriteria[filter_groups][0][filters][0][condition_type]": "eq",
                "searchCriteria[pageSize]": 34,
                "searchCriteria[currentPage]": 42
            }
    )

    assert (
            q.make_field_value_query("source_code", "default",
                                     condition_type="eq", page_size=34, current_page=42,
                                     sort_orders=[("sku", "desc")])
            ==
            {
                "searchCriteria[filter_groups][0][filters][0][field]": "source_code",
                "searchCriteria[filter_groups][0][filters][0][value]": "default",
                "searchCriteria[filter_groups][0][filters][0][condition_type]": "eq",
                "searchCriteria[pageSize]": 34,
                "searchCriteria[currentPage]": 42,
                "searchCriteria[sortOrders][0][field]": "sku",
                "searchCriteria[sortOrders][0][direction]": "desc",
            }
    )
