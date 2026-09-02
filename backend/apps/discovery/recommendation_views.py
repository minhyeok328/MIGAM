from typing import Any

from django.db import transaction
from rest_framework import serializers, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.apps.catalog.models import (
    AccessibilityFact,
    ReservationInfo,
    SensoryNotice,
)
from backend.apps.discovery.models import ContentFeatureAssertion
from backend.apps.discovery.recommendation import (
    DurationPreference,
    FeaturePreference,
    InvalidRecommendationRequest,
    PreferenceMode,
    RecommendationQuery,
    RegionFilter,
    ReservationPreference,
    VisitDateRange,
    get_recommendation_service,
)
from backend.apps.discovery.recommendation_presenters import (
    present_recommendation_result,
)


ERROR_MESSAGE = "추천 조건을 확인해주세요."
MAX_SIGNAL_ITEMS = 100
FEATURE_VALUE_REGEX = r"^[A-Z0-9][A-Z0-9_:-]{0,63}$"


class StrictSerializer(serializers.Serializer):
    def to_internal_value(self, data: Any) -> dict[str, object]:
        if isinstance(data, dict):
            unknown_fields = set(data) - set(self.fields)
            if unknown_fields:
                raise serializers.ValidationError(
                    {
                        field: ["허용되지 않은 필드입니다."]
                        for field in sorted(unknown_fields)
                    }
                )
        return super().to_internal_value(data)


class RegionSerializer(StrictSerializer):
    area = serializers.CharField(max_length=100, trim_whitespace=True)
    district = serializers.CharField(
        required=False,
        default="",
        allow_blank=True,
        max_length=100,
        trim_whitespace=True,
    )


class VisitDateRangeSerializer(StrictSerializer):
    start = serializers.DateField()
    end = serializers.DateField()

    def validate(self, attrs: dict[str, object]) -> dict[str, object]:
        if attrs["start"] > attrs["end"]:
            raise serializers.ValidationError(
                {"end": ["종료일은 시작일보다 빠를 수 없습니다."]}
            )
        return attrs


class ReservationPreferenceSerializer(StrictSerializer):
    mode = serializers.ChoiceField(choices=tuple(item.value for item in PreferenceMode))
    types = serializers.ListField(
        child=serializers.ChoiceField(
            choices=tuple(
                item
                for item in ReservationInfo.Type.values
                if item != ReservationInfo.Type.UNKNOWN
            )
        ),
        allow_empty=False,
        max_length=MAX_SIGNAL_ITEMS,
    )


class DurationPreferenceSerializer(StrictSerializer):
    mode = serializers.ChoiceField(choices=tuple(item.value for item in PreferenceMode))
    minimum_minutes = serializers.IntegerField(required=False, min_value=1)
    maximum_minutes = serializers.IntegerField(required=False, min_value=1)

    def validate(self, attrs: dict[str, object]) -> dict[str, object]:
        minimum = attrs.get("minimum_minutes")
        maximum = attrs.get("maximum_minutes")
        if minimum is None and maximum is None:
            raise serializers.ValidationError(
                {"non_field_errors": ["관람시간 범위를 하나 이상 입력해주세요."]}
            )
        if minimum is not None and maximum is not None and minimum > maximum:
            raise serializers.ValidationError(
                {"maximum_minutes": ["최대 시간은 최소 시간보다 작을 수 없습니다."]}
            )
        return attrs


class FeaturePreferenceSerializer(StrictSerializer):
    axis = serializers.ChoiceField(
        choices=tuple(ContentFeatureAssertion.Axis.values)
    )
    value = serializers.RegexField(
        regex=FEATURE_VALUE_REGEX,
        max_length=64,
    )


class RecommendationRequestSerializer(StrictSerializer):
    region = RegionSerializer(required=False)
    visit_dates = VisitDateRangeSerializer(required=False)
    max_budget_krw = serializers.IntegerField(required=False, min_value=0)
    required_accessibility = serializers.ListField(
        child=serializers.ChoiceField(
            choices=tuple(AccessibilityFact.Kind.values)
        ),
        required=False,
        default=tuple,
        max_length=MAX_SIGNAL_ITEMS,
    )
    avoided_sensory = serializers.ListField(
        child=serializers.ChoiceField(choices=tuple(SensoryNotice.Kind.values)),
        required=False,
        default=tuple,
        max_length=MAX_SIGNAL_ITEMS,
    )
    reservation = ReservationPreferenceSerializer(required=False)
    duration = DurationPreferenceSerializer(required=False)
    preferred_features = FeaturePreferenceSerializer(
        many=True,
        required=False,
        default=tuple,
    )
    liked_exhibition_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        default=tuple,
        max_length=MAX_SIGNAL_ITEMS,
    )
    liked_institution_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        default=tuple,
        max_length=MAX_SIGNAL_ITEMS,
    )
    limit = serializers.IntegerField(required=False, default=6, min_value=1, max_value=24)


class InternalRecommendationView(APIView):
    authentication_classes: list[type] = []
    permission_classes: list[type] = []

    def post(self, request: Request) -> Response:
        serializer = RecommendationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return _invalid_response(serializer.errors)

        try:
            query = _build_query(serializer.validated_data)
            with transaction.atomic():
                result = get_recommendation_service().recommend(query)
                payload = present_recommendation_result(result)
        except InvalidRecommendationRequest as error:
            return _invalid_response({"non_field_errors": [str(error)]})

        return Response(payload)


def _build_query(data: dict[str, object]) -> RecommendationQuery:
    region_data = data.get("region")
    visit_date_data = data.get("visit_dates")
    reservation_data = data.get("reservation")
    duration_data = data.get("duration")
    return RecommendationQuery(
        region=(
            RegionFilter(
                area=region_data["area"],
                district=region_data.get("district", ""),
            )
            if region_data is not None
            else None
        ),
        visit_dates=(
            VisitDateRange(
                start=visit_date_data["start"],
                end=visit_date_data["end"],
            )
            if visit_date_data is not None
            else None
        ),
        max_budget_krw=data.get("max_budget_krw"),
        required_accessibility=tuple(data.get("required_accessibility", ())),
        avoided_sensory=tuple(data.get("avoided_sensory", ())),
        reservation=(
            ReservationPreference(
                mode=reservation_data["mode"],
                types=tuple(reservation_data["types"]),
            )
            if reservation_data is not None
            else None
        ),
        duration=(
            DurationPreference(
                mode=duration_data["mode"],
                minimum_minutes=duration_data.get("minimum_minutes"),
                maximum_minutes=duration_data.get("maximum_minutes"),
            )
            if duration_data is not None
            else None
        ),
        preferred_features=tuple(
            FeaturePreference(axis=item["axis"], value=item["value"])
            for item in data.get("preferred_features", ())
        ),
        liked_exhibition_ids=tuple(data.get("liked_exhibition_ids", ())),
        liked_institution_ids=tuple(data.get("liked_institution_ids", ())),
        limit=data.get("limit", 6),
    )


def _invalid_response(details: Any) -> Response:
    return Response(
        {
            "error": {
                "code": "INVALID_RECOMMENDATION_REQUEST",
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
