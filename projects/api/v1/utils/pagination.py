
def paginate_queryset(queryset, page: int = 1, limit: int = 10):
    total_count = queryset.count()
    total_pages = (total_count + limit - 1) // limit
    offset = (page - 1) * limit
    results = queryset[offset:offset + limit]

    return (
        list(results),
        {
            "pagination": {
                "total_count": total_count,
                "total_pages": total_pages,
                "current_page": page,
                "per_page": limit,
                "next_page": page + 1 if page < total_pages else None,
                "prev_page": page - 1 if page > 1 else None,
            }
        }
    )
