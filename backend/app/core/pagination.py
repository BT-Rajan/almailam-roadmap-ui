from typing import Any

from sqlalchemy.orm import Query

MAX_PAGE_SIZE = 200
DEFAULT_PAGE_SIZE = 25


def sort_and_paginate(
    query: Query,
    model: type,
    sortable_fields: dict[str, Any] | list[str],
    sort: str | None,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    default_field: str = "id",
) -> dict:
    order_columns = []

    if sort:
        direction = "desc" if sort.startswith("-") else "asc"
        field = sort.lstrip("-")
        column = None
        if isinstance(sortable_fields, dict):
            column = sortable_fields.get(field)
        elif field in sortable_fields and hasattr(model, field):
            column = getattr(model, field)
        if column is not None:
            order_columns.append(column.desc() if direction == "desc" else column.asc())

    sorting_by_id = bool(order_columns) and sort is not None and sort.lstrip("-") == "id"

    if not order_columns:
        order_columns.append(getattr(model, default_field).desc())

    if not sorting_by_id and hasattr(model, "id"):
        order_columns.append(model.id.desc())

    query = query.order_by(*order_columns)

    total = query.count()
    page = max(page, 1)
    page_size = min(max(page_size, 1), MAX_PAGE_SIZE)
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if page_size else 0,
    }
