from rest_framework import serializers, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.apps.catalog.models import ARTWORK_MEDIA_GROUPS
from backend.apps.discovery.artworks import artwork_detail, artwork_list


class ArtworkQuerySerializer(serializers.Serializer):
    q = serializers.CharField(required=False, default="", allow_blank=True, max_length=100)
    institution_id = serializers.IntegerField(required=False, min_value=1)
    media_group = serializers.ChoiceField(required=False, default="", choices=ARTWORK_MEDIA_GROUPS, allow_blank=True)
    page = serializers.IntegerField(required=False, default=1, min_value=1)
    page_size = serializers.IntegerField(required=False, default=24, min_value=1, max_value=24)


class InternalArtworkListView(APIView):
    authentication_classes: list[type] = []
    permission_classes: list[type] = []

    def get(self, request: Request) -> Response:
        query = ArtworkQuerySerializer(data=request.query_params)
        invalid_structure = any(
            field not in query.fields or len(request.query_params.getlist(field)) != 1
            for field in request.query_params
        )
        if invalid_structure or not query.is_valid():
            return Response({"error": {
                "code": "INVALID_ARTWORK_QUERY", "message": "작품 검색 조건을 확인해주세요.", "details": {},
            }}, status=status.HTTP_400_BAD_REQUEST)
        return Response(artwork_list(**query.validated_data))


class InternalArtworkDetailView(APIView):
    authentication_classes: list[type] = []
    permission_classes: list[type] = []

    def get(self, request: Request, id: int) -> Response:
        result = artwork_detail(id)
        if result is None:
            return Response({"error": {
                "code": "NOT_FOUND", "message": "정보를 찾을 수 없습니다.", "details": {},
            }}, status=status.HTTP_404_NOT_FOUND)
        return Response(result)
