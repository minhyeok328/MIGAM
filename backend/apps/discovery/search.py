from dataclasses import dataclass
from enum import StrEnum
import re
from typing import Protocol

from django.db import OperationalError, connection, transaction

from backend.apps.catalog.models import Exhibition
from backend.apps.discovery.models import SearchDocument


SEARCH_DOCUMENT_VERSION = "1.0.0"
DEFAULT_PAGE_SIZE = 24
MAX_PAGE_SIZE = 24
MAX_QUERY_LENGTH = 100
_TOKEN_PATTERN = re.compile(r"[^\W_]+", flags=re.UNICODE)


class SearchResultType(StrEnum):
    EXHIBITION = "EXHIBITION"
    INSTITUTION = "INSTITUTION"
    ALL = "ALL"


class SearchSort(StrEnum):
    RELEVANCE = "RELEVANCE"
    LATEST_START = "LATEST_START"
    ENDING_SOON = "ENDING_SOON"
    UPCOMING_START = "UPCOMING_START"


class InvalidSearchQuery(ValueError):
    pass


class SearchBackendUnavailable(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class SearchQuery:
    query: str | None = None
    result_type: SearchResultType | str = SearchResultType.EXHIBITION
    lifecycles: tuple[str, ...] = ()
    region_area: str = ""
    region_district: str = ""
    sort: SearchSort | str = SearchSort.RELEVANCE
    page: int = 1
    page_size: int = DEFAULT_PAGE_SIZE


@dataclass(frozen=True, slots=True)
class SearchHit:
    document_id: int
    result_type: SearchResultType
    object_id: int
    score: float | None


@dataclass(frozen=True, slots=True)
class SearchPage:
    total: int
    page: int
    page_size: int
    has_more: bool
    results: tuple[SearchHit, ...]


class SearchService(Protocol):
    def search(self, query: SearchQuery) -> SearchPage: ...


@dataclass(frozen=True, slots=True)
class _ValidatedQuery:
    query: str
    match_expression: str | None
    result_type: SearchResultType
    lifecycles: tuple[str, ...]
    region_area: str
    region_district: str
    sort: SearchSort
    page: int
    page_size: int


class SQLiteFTS5SearchService:
    @transaction.atomic
    def search(self, query: SearchQuery) -> SearchPage:
        validated = _validate_query(query)
        if connection.vendor != "sqlite":
            raise SearchBackendUnavailable(
                "SQLite FTS5 search requires the SQLite database backend."
            )

        join_sql = ""
        rank_sql = "NULL"
        conditions: list[str] = []
        parameters: list[object] = []

        if validated.match_expression is not None:
            join_sql = (
                " JOIN discovery_searchdocument_fts"
                " ON discovery_searchdocument_fts.rowid = d.id"
            )
            conditions.append("discovery_searchdocument_fts MATCH %s")
            parameters.append(validated.match_expression)
            rank_sql = "bm25(discovery_searchdocument_fts, 8.0, 3.0, 1.0)"

        if validated.result_type != SearchResultType.ALL:
            conditions.append("d.result_type = %s")
            parameters.append(validated.result_type.value)

        lifecycle_placeholders = ", ".join("%s" for _ in validated.lifecycles)
        if validated.result_type == SearchResultType.EXHIBITION:
            conditions.append(f"d.lifecycle IN ({lifecycle_placeholders})")
            parameters.extend(validated.lifecycles)
        elif validated.result_type == SearchResultType.ALL:
            conditions.append(
                "(d.result_type = 'INSTITUTION'"
                f" OR d.lifecycle IN ({lifecycle_placeholders}))"
            )
            parameters.extend(validated.lifecycles)

        if validated.region_area:
            conditions.append("d.region_area = %s")
            parameters.append(validated.region_area)
        if validated.region_district:
            conditions.append("d.region_district = %s")
            parameters.append(validated.region_district)

        where_sql = " AND ".join(conditions) if conditions else "1 = 1"
        order_sql = _order_sql(validated.sort, has_query=bool(validated.query))
        offset = (validated.page - 1) * validated.page_size

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT COUNT(*) FROM discovery_searchdocument d"
                    f"{join_sql} WHERE {where_sql}",
                    parameters,
                )
                total = int(cursor.fetchone()[0])
                rows: list[tuple[object, ...]] = []
                if offset < total:
                    cursor.execute(
                        "SELECT d.id, d.result_type, d.object_id,"
                        f" {rank_sql} AS rank"
                        " FROM discovery_searchdocument d"
                        f"{join_sql} WHERE {where_sql}"
                        f" ORDER BY {order_sql} LIMIT %s OFFSET %s",
                        [*parameters, validated.page_size, offset],
                    )
                    rows = cursor.fetchall()
        except OperationalError as error:
            raise SearchBackendUnavailable(
                "SQLite FTS5 search index is unavailable."
            ) from error

        results = tuple(
            SearchHit(
                document_id=int(document_id),
                result_type=SearchResultType(result_type),
                object_id=int(object_id),
                score=float(rank) if rank is not None else None,
            )
            for document_id, result_type, object_id, rank in rows
        )
        return SearchPage(
            total=total,
            page=validated.page,
            page_size=validated.page_size,
            has_more=offset + len(results) < total,
            results=results,
        )


def get_search_service() -> SearchService:
    return SQLiteFTS5SearchService()


def _validate_query(query: SearchQuery) -> _ValidatedQuery:
    try:
        result_type = SearchResultType(query.result_type)
    except (TypeError, ValueError) as error:
        raise InvalidSearchQuery("type is invalid") from error
    try:
        sort = SearchSort(query.sort)
    except (TypeError, ValueError) as error:
        raise InvalidSearchQuery("sort is invalid") from error

    if isinstance(query.page, bool) or not isinstance(query.page, int) or query.page < 1:
        raise InvalidSearchQuery("page must be at least 1")
    if (
        isinstance(query.page_size, bool)
        or not isinstance(query.page_size, int)
        or not 1 <= query.page_size <= MAX_PAGE_SIZE
    ):
        raise InvalidSearchQuery(
            f"page_size must be between 1 and {MAX_PAGE_SIZE}"
        )

    raw_query = query.query or ""
    if not isinstance(raw_query, str):
        raise InvalidSearchQuery("q must be a string")
    normalized_query = raw_query.strip()
    if len(normalized_query) > MAX_QUERY_LENGTH:
        raise InvalidSearchQuery(
            f"q must be at most {MAX_QUERY_LENGTH} characters"
        )
    tokens = _TOKEN_PATTERN.findall(normalized_query)
    if normalized_query and not tokens:
        raise InvalidSearchQuery("q must contain a letter or number")
    match_expression = " AND ".join(f'"{token}"*' for token in tokens) or None

    allowed_lifecycles = {
        Exhibition.Lifecycle.CURRENT,
        Exhibition.Lifecycle.UPCOMING,
        Exhibition.Lifecycle.ENDED,
        Exhibition.Lifecycle.CANCELED,
    }
    lifecycles = tuple(dict.fromkeys(query.lifecycles))
    if any(lifecycle not in allowed_lifecycles for lifecycle in lifecycles):
        raise InvalidSearchQuery("lifecycle is invalid")
    if not lifecycles:
        lifecycles = (
            Exhibition.Lifecycle.CURRENT,
            Exhibition.Lifecycle.UPCOMING,
            Exhibition.Lifecycle.ENDED,
        ) if normalized_query else (
            Exhibition.Lifecycle.CURRENT,
            Exhibition.Lifecycle.UPCOMING,
        )

    if not isinstance(query.region_area, str) or not isinstance(
        query.region_district, str
    ):
        raise InvalidSearchQuery("region filters must be strings")

    return _ValidatedQuery(
        query=normalized_query,
        match_expression=match_expression,
        result_type=result_type,
        lifecycles=lifecycles,
        region_area=query.region_area.strip(),
        region_district=query.region_district.strip(),
        sort=sort,
        page=query.page,
        page_size=query.page_size,
    )


def _order_sql(sort: SearchSort, *, has_query: bool) -> str:
    lifecycle_order = (
        "CASE d.lifecycle"
        " WHEN 'CURRENT' THEN 0"
        " WHEN 'UPCOMING' THEN 1"
        " WHEN 'ENDED' THEN 2"
        " WHEN 'CANCELED' THEN 3"
        " ELSE 4 END"
    )
    type_order = "CASE d.result_type WHEN 'EXHIBITION' THEN 0 ELSE 1 END"
    if sort == SearchSort.LATEST_START:
        return (
            f"{type_order}, d.start_date IS NULL, d.start_date DESC,"
            " d.title COLLATE NOCASE, d.id"
        )
    if sort == SearchSort.ENDING_SOON:
        return (
            "CASE d.lifecycle WHEN 'CURRENT' THEN 0 WHEN 'UPCOMING' THEN 1"
            " WHEN 'ENDED' THEN 2 ELSE 3 END,"
            " d.end_date IS NULL, d.end_date ASC,"
            f" {type_order}, d.title COLLATE NOCASE, d.id"
        )
    if sort == SearchSort.UPCOMING_START:
        return (
            "CASE d.lifecycle WHEN 'UPCOMING' THEN 0 WHEN 'CURRENT' THEN 1"
            " WHEN 'ENDED' THEN 2 ELSE 3 END,"
            " d.start_date IS NULL, d.start_date ASC,"
            f" {type_order}, d.title COLLATE NOCASE, d.id"
        )
    if has_query:
        return (
            f"{lifecycle_order}, rank ASC, {type_order},"
            " d.title COLLATE NOCASE, d.id"
        )
    return (
        f"{lifecycle_order},"
        " CASE WHEN d.lifecycle = 'CURRENT' THEN d.end_date END ASC,"
        " CASE WHEN d.lifecycle = 'UPCOMING' THEN d.start_date END ASC,"
        f" {type_order}, d.title COLLATE NOCASE, d.id"
    )
