"""Custom pagination classes for the Nautobot VPN plugin API."""

from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination for API endpoints.

    - Supports dynamic page sizes via `?page_size=X`
    - Prevents excessive page loads with `max_page_size=100`
    - Defaults to 25 results per page
      for a better balance of performance and usability.
    """

    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 200
    last_page_strings = ("last",)


class LargeResultsSetPagination(PageNumberPagination):
    """Large pagination class for bulk API requests.

    - Used for bulk exports or high-performance endpoints.
    """

    page_size = 100  # ✅ Larger page size for bulk operations
    page_size_query_param = "page_size"
    max_page_size = 500  # ✅ Allows exporting up to 500 records per request


class SmallResultsSetPagination(PageNumberPagination):
    """Smaller pagination for lightweight API endpoints.

    - Useful for quick-loading small lists.
    """

    page_size = 5  # ✅ Minimal results for quick API calls
    page_size_query_param = "page_size"
    max_page_size = 50  # ✅ Ensures no overload
