from rest_framework import serializers, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.apps.discovery.detail import exhibition_detail, institution_detail


def _not_found() -> Response:
    return Response(
        {"error": {"code": "NOT_FOUND", "message": "정보를 찾을 수 없습니다.", "details": {}}},
        status=status.HTTP_404_NOT_FOUND,
    )


class InternalExhibitionDetailView(APIView):
    authentication_classes: list[type] = []
    permission_classes: list[type] = []

    def get(self, request: Request, id: int) -> Response:
        result = exhibition_detail(id)
        return Response(result) if result is not None else _not_found()


class InstitutionDetailQuerySerializer(serializers.Serializer):
    page = serializers.IntegerField(required=False, default=1, min_value=1)
    page_size = serializers.IntegerField(required=False, default=24, min_value=1, max_value=24)


class InternalInstitutionDetailView(APIView):
    authentication_classes: list[type] = []
    permission_classes: list[type] = []

    def get(self, request: Request, id: int) -> Response:
        query = InstitutionDetailQuerySerializer(data=request.query_params)
        if not query.is_valid():
            return Response(
                {"error": {
                    "code": "INVALID_DETAIL_QUERY", "message": "페이지 조건을 확인해주세요.",
                    "details": {field: [str(error) for error in errors] for field, errors in query.errors.items()},
                }},
                status=status.HTTP_400_BAD_REQUEST,
            )
        result = institution_detail(id, **query.validated_data)
        return Response(result) if result is not None else _not_found()
