from typing import List, Any, Union, Dict, Tuple
from django.db.models import QuerySet

def paginate_queryset(
    queryset: Union[QuerySet, List[Any]],
    page: int = 1,
    limit: int = 10,
    strict: bool = False  # Raise on invalid page if True
) -> Tuple[List[Any], Dict[str, Any]]:
    """
    Paginate a queryset or list with optional page bounds checking.
    """
    if page < 1:
        page = 1

    if isinstance(queryset, QuerySet):
        total_count = queryset.count()
        results_slice = queryset[(page - 1) * limit : page * limit]
        results = list(results_slice)
    else:
        total_count = len(queryset)
        results = queryset[(page - 1) * limit : page * limit]

    total_pages = (total_count + limit - 1) // limit or 1

    if strict and page > total_pages:
        raise ValueError(f"Page {page} exceeds total pages {total_pages}")

    results_meta = {
        "total_count": total_count,
        "total_pages": total_pages,
        "current_page": page,
        "per_page": limit,
        "next_page": page + 1 if page < total_pages else None,
        "prev_page": page - 1 if page > 1 else None,
    }
    return results, results_meta