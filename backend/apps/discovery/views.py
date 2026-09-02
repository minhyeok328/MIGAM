from typing import Any

from django.db import transaction
from rest_framework import serializers, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.apps.catalog.models import Exhibition
from backend.apps.discovery.presenters import present_search_hits
from backend.apps.discovery.search import (
    InvalidSearchQuery,
    SearchBackendUnavailable,
    SearchQuery,
    SearchResultType,
    SearchSort,
    get_search_service,
)


ERROR_MESSAGE = "검색 조건을 확인해주세요."


class SearchQuerySerializer(serializers.Serializer):
    q = serializers.CharField(
        source="query",
        required=False,
        default="",
        allow_blank=True,
        max_length=100,
        trim_whitespace=True,
    )
    type = serializers.ChoiceField(
        source="result_type",
        choices=tuple(item.value for item in SearchResultType),
        required=False,
        default=SearchResultType.EXHIBITION.value,
    )
    lifecycle = serializers.ListField(
        source="lifecycles",
        child=serializers.ChoiceField(
            choices=(
                Exhibition.Lifecycle.CURRENT,
                Exhibition.Lifecycle.UPCOMING,
                Exhibition.Lifecycle.ENDED,
                Exhibition.Lifecycle.CANCELED,
            )
        ),
        required=False,
        default=tuple,
    )
    region_area = serializers.CharField(
        required=False,
        default="",
        allow_blank=True,
        max_length=100,
        trim_whitespace=True,
    )
    region_district = serializers.CharField(
        required=False,
        default="",
        allow_blank=True,
        max_length=100,
        trim_whitespace=True,
    )
    sort = serializers.ChoiceField(
        choices=tuple(item.value for item in SearchSort),
        required=False,
        default=SearchSort.RELEVANCE.value,
    )
    page = serializers.IntegerField(required=False, default=1, min_value=1)
    page_size = serializers.IntegerField(
        required=False,
        default=24,
        min_value=1,
        max_value=24,
    )


class InternalSearchView(APIView):
    authentication_classes: list[type] = []
    permission_classes: list[type] = []

    def get(self, request: Request) -> Response:
        serializer = SearchQuerySerializer(data=_query_data(request))
        if not serializer.is_valid():
            return _invalid_response(serializer.errors)

        try:
            with transaction.atomic():
                page = get_search_service().search(
                    SearchQuery(**serializer.validated_data)
                )
                results = present_search_hits(page.results)
        except InvalidSearchQuery as error:
            field = str(error).split(" ", maxsplit=1)[0]
            if field not in {
                "q",
                "type",
                "lifecycle",
                "sort",
                "page",
                "page_size",
                "region",
            }:
                field = "non_field_errors"
            return _invalid_response({field: [str(error)]})
        except SearchBackendUnavailable:
            return Response(
                {
                    "error": {
                        "code": "SEARCH_BACKEND_UNAVAILABLE",
                        "message": "검색 서비스를 사용할 수 없습니다.",
                        "details": {},
                    }
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                "total": page.total,
                "page": page.page,
                "page_size": page.page_size,
                "has_more": page.has_more,
                "results": results,
            }
        )


def _query_data(request: Request) -> dict[str, object]:
    scalar_fields = {
        "q",
        "type",
        "region_area",
        "region_district",
        "sort",
        "page",
        "page_size",
    }
    data: dict[str, object] = {
        field: request.query_params.get(field)
        for field in scalar_fields
        if field in request.query_params
    }
    if "lifecycle" in request.query_params:
        data["lifecycle"] = request.query_params.getlist("lifecycle")
    return data


def _invalid_response(details: Any) -> Response:
    return Response(
        {
            "error": {
                "code": "INVALID_SEARCH_QUERY",
                "message": ERROR_MESSAGE,
                "details": _plain_error_details(details),
            }
        },
        status=status.HTTP_400_BAD_REQUEST,
    )


def _plain_error_details(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _plain_error_details(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain_error_details(item) for item in value]
    return str(value)
