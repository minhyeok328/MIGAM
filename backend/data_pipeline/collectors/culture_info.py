from collections.abc import Callable, Mapping
from dataclasses import dataclass
from time import monotonic, sleep
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlencode
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ElementTree

from backend.data_pipeline.models import RawExhibitionRecord
from backend.data_pipeline.registry import SourceRegistry


class CultureInfoApiError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class ParsedXmlResponse:
    records: tuple[dict[str, str], ...]
    total_count: int | None = None
    page_no: int | None = None
    rows_per_page: int | None = None


class XmlTransport(Protocol):
    def get(self, url: str, params: Mapping[str, str]) -> bytes: ...


class UrllibXmlTransport:
    RATE_LIMIT_RETRIES = 3

    def __init__(
        self,
        timeout: float = 15.0,
        minimum_interval_seconds: float = 0.5,
        clock: Callable[[], float] = monotonic,
        sleeper: Callable[[float], None] = sleep,
    ) -> None:
        self.timeout = timeout
        self.minimum_interval_seconds = minimum_interval_seconds
        self.clock = clock
        self.sleeper = sleeper
        self._last_request_at: float | None = None

    def _wait_for_request_slot(self) -> None:
        if self._last_request_at is not None:
            remaining = self.minimum_interval_seconds - (
                self.clock() - self._last_request_at
            )
            if remaining > 0:
                self.sleeper(remaining)
        self._last_request_at = self.clock()

    def get(self, url: str, params: Mapping[str, str]) -> bytes:
        normalized_params = dict(params)
        if "serviceKey" in normalized_params:
            normalized_params["serviceKey"] = unquote(normalized_params["serviceKey"])
        request = Request(
            f"{url}?{urlencode(normalized_params)}",
            headers={"Accept": "application/xml", "User-Agent": "MIGAM/0.1"},
        )
        for attempt in range(self.RATE_LIMIT_RETRIES + 1):
            self._wait_for_request_slot()
            try:
                with urlopen(request, timeout=self.timeout) as response:
                    return response.read()
            except HTTPError as error:
                if error.code == 429 and attempt < self.RATE_LIMIT_RETRIES:
                    retry_after = (
                        error.headers.get("Retry-After") if error.headers else None
                    )
                    try:
                        delay = float(retry_after) if retry_after else 2**attempt
                    except ValueError:
                        delay = 2**attempt
                    self.sleeper(min(30.0, max(0.0, delay)))
                    continue
                raise CultureInfoApiError(
                    f"culture API HTTP error: {error.code}"
                ) from error
            except URLError as error:
                raise CultureInfoApiError("culture API request failed") from error
        raise CultureInfoApiError("culture API request failed")


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _element_text_map(element: ElementTree.Element) -> dict[str, str]:
    return {
        _local_name(child.tag): (child.text or "").strip()
        for child in list(element)
    }


def _parse_response(payload: bytes) -> ParsedXmlResponse:
    try:
        root = ElementTree.fromstring(payload)
    except ElementTree.ParseError as error:
        raise CultureInfoApiError("culture API returned malformed XML") from error

    response_fields = {
        _local_name(element.tag): (element.text or "").strip()
        for element in root.iter()
        if _local_name(element.tag) in {"resultCode", "resultMsg"}
    }
    result_code = response_fields.get("resultCode")
    if result_code and result_code != "00":
        message = response_fields.get("resultMsg") or "unknown error"
        raise CultureInfoApiError(f"culture API error {result_code}: {message}")

    records: list[dict[str, str]] = []
    for element in root.iter():
        fields = _element_text_map(element)
        if fields.get("seq"):
            records.append(fields)

    metadata = {
        _local_name(element.tag).casefold(): (element.text or "").strip()
        for element in root.iter()
        if _local_name(element.tag).casefold()
        in {"totalcount", "pageno", "numofrows"}
    }
    return ParsedXmlResponse(
        records=tuple(records),
        total_count=_optional_positive_int(metadata.get("totalcount")),
        page_no=_optional_positive_int(metadata.get("pageno")),
        rows_per_page=_optional_positive_int(metadata.get("numofrows")),
    )


def _optional_positive_int(value: str | None) -> int | None:
    if not value:
        return None
    try:
        parsed = int(value)
    except ValueError:
        return None
    return parsed if parsed > 0 else None


def _positive_int_parameter(params: Mapping[str, str], name: str, default: int) -> int:
    value = str(params.get(name, default))
    try:
        parsed = int(value)
    except ValueError as error:
        raise ValueError(f"{name} must be a positive integer") from error
    if parsed < 1:
        raise ValueError(f"{name} must be a positive integer")
    return parsed


def _clean(value: object) -> str | None:
    cleaned = "" if value is None else str(value).strip()
    return cleaned or None


class CultureInfoApiCollector:
    SOURCE_ID = "kcisa-cultureinfo"

    def __init__(
        self,
        registry: SourceRegistry,
        service_key: str,
        transport: XmlTransport | None = None,
    ) -> None:
        if not service_key.strip():
            raise ValueError("CULTURE_PORTAL_SERVICE_KEY is required")
        self.registry = registry
        self.service_key = service_key
        self.transport = transport or UrllibXmlTransport()

    def collect(self, period_params: Mapping[str, str]) -> list[RawExhibitionRecord]:
        source = self.registry.source(self.SOURCE_ID)
        base_url = source["base_url"].rstrip("/")
        endpoints = source["endpoints"]
        key_parameter = source["authentication"]["parameter"]

        initial_page = _positive_int_parameter(period_params, "PageNo", 1)
        requested_page_size = _positive_int_parameter(
            period_params, "numOfrows", 100
        )
        list_params = {key: str(value) for key, value in period_params.items()}
        list_params["numOfrows"] = str(requested_page_size)
        list_params.setdefault("serviceTp", "A")
        list_params[key_parameter] = self.service_key

        page = initial_page
        collected: list[RawExhibitionRecord] = []
        seen: set[str] = set()
        while True:
            list_params["PageNo"] = str(page)
            list_payload = self.transport.get(
                base_url + endpoints["list"], list_params
            )
            parsed_list = _parse_response(list_payload)

            for summary in parsed_list.records:
                seq = summary["seq"]
                if seq in seen:
                    continue
                seen.add(seq)
                detail_payload = self.transport.get(
                    base_url + endpoints["detail"],
                    {key_parameter: self.service_key, "seq": seq},
                )
                detail_records = _parse_response(detail_payload).records
                detail = next(
                    (record for record in detail_records if record.get("seq") == seq),
                    None,
                )
                if detail is None:
                    raise CultureInfoApiError(f"detail response omitted seq {seq}")
                institution = self._matching_institution(detail)
                if institution is None:
                    continue
                collected.append(self._to_record(source, institution, detail))

            if not parsed_list.records:
                break
            response_page_size = parsed_list.rows_per_page or requested_page_size
            if parsed_list.total_count is not None:
                if page * response_page_size >= parsed_list.total_count:
                    break
            elif len(parsed_list.records) < requested_page_size:
                break
            page += 1
        return collected

    def _matching_institution(
        self, detail: Mapping[str, str]
    ) -> Mapping[str, object] | None:
        for institution in self.registry.institutions_for_source(self.SOURCE_ID):
            filters = institution.get("source_filter", {})
            fact_filters = {
                key: expected
                for key, expected in filters.items()
                if not key.endswith("_host")
            }
            if all(_clean(detail.get(key)) == expected for key, expected in fact_filters.items()):
                return institution
        return None

    def _to_record(
        self,
        source: Mapping[str, object],
        institution: Mapping[str, object],
        detail: Mapping[str, str],
    ) -> RawExhibitionRecord:
        fields = source["fields"]
        assert isinstance(fields, Mapping)
        region = institution.get("region", {})
        assert isinstance(region, Mapping)
        selected_raw = {
            source_field: _clean(detail.get(source_field))
            for source_field in fields.values()
        }
        return RawExhibitionRecord(
            source_id=self.SOURCE_ID,
            institution_id=str(institution["id"]),
            source_record_id=_clean(detail.get(str(fields["record_id"]))) or "",
            source_owner=str(source["owner"]),
            title=_clean(detail.get(str(fields["title"]))),
            start_date=_clean(detail.get(str(fields["start_date"]))),
            end_date=_clean(detail.get(str(fields["end_date"]))),
            venue=_clean(detail.get(str(fields["venue"]))),
            region_area=(
                _clean(detail.get(str(fields.get("region", ""))))
                or _clean(region.get("area"))
            ),
            region_district=(
                _clean(detail.get(str(fields.get("district", ""))))
                or _clean(region.get("district"))
            ),
            official_url=_clean(detail.get(str(fields["official_url"]))),
            raw=selected_raw,
        )
