from typing import Optional, Any, Dict, Sequence, Tuple

__all__ = (
    'Query', 'make_search_query', 'make_field_value_query',
)

Query = Optional[Dict[str, Any]]


def make_search_query(filter_groups: Sequence[Sequence[Tuple[str, Any, Optional[str]]]],
                      *,
                      sort_orders: Optional[Sequence[Tuple[str, str]]] = None,
                      page_size: Optional[int] = None,
                      current_page: Optional[int] = None) -> Dict[str, Any]:
    """Build a search query.

    Documentation: https://devdocs.magento.com/guides/v2.4/rest/performing-searches.html

    Filter groups are AND clauses while filters are OR clauses:

        [[("a", 1, "eq"), ("b", 2, "eq")], [("c", 3, "eq")]]

    Means ``(a=1 OR b=2) AND c=3``. There’s no way to do an OR between AND clauses.

    :param filter_groups: sequence of filters. Each filter is a sequence of conditions.
        Each condition is a tuple of (field, value, condition_type). The condition_type can be None if it's "eq"
        (the default). See the documentation for the list of possible condition_types.
    :param sort_orders: sequence of tuples (field, direction) for the sort order.
        The direction should be "asc" or "desc".
    :param page_size:
    :param current_page:
    :return:
    """
    query_params: Dict[str, Any] = {}
    if page_size is not None:
        query_params["searchCriteria[pageSize]"] = page_size

    if current_page is not None:
        query_params["searchCriteria[currentPage]"] = current_page

    for filter_group_index, filter_group in enumerate(filter_groups):
        for filter_index, filter_ in enumerate(filter_group):
            for k, v in (
                    ("field", filter_[0]),
                    ("value", filter_[1]),
                    ("condition_type", filter_[2]),
            ):
                # NOTE: from the doc, "condition_type is optional if the operator is eq".
                if k == "condition_type" and v is None:
                    continue
                query_params[f"searchCriteria[filter_groups][{filter_group_index}][filters][{filter_index}][{k}]"] = v

    if sort_orders:
        for i, (field, direction) in enumerate(sort_orders):
            query_params[f"searchCriteria[sortOrders][{i}][field]"] = field
            query_params[f"searchCriteria[sortOrders][{i}][direction]"] = direction

    return query_params


def make_field_value_query(field: str, value: Any,
                           condition_type: Optional[str] = None,
                           page_size: Optional[int] = None,
                           current_page: Optional[int] = None,
                           *,
                           sort_orders: Optional[Sequence[Tuple[str, str]]] = None) -> Dict[str, Any]:
    """Create a query params dictionary for Magento. This is a simplified version of ``make_search_query``.

    :param field:
    :param value:
    :param condition_type: "eq", "neq", or another.
        See https://devdocs.magento.com/guides/v2.4/rest/performing-searches.html for the full list.
    :param page_size:
    :param current_page:
    :param sort_orders: sequence of tuples (field, direction) for the sort order.
    :return:
    """
    return make_search_query([[(field, value, condition_type)]],
                             page_size=page_size, current_page=current_page, sort_orders=sort_orders)
