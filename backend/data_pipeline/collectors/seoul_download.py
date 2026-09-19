"""Download the same approved CSV export linked by Seoul's public Sheet UI."""

from datetime import date, datetime, timezone
import hashlib
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


DATASETS = {"seoul-oa-2708-sejong": "OA-2708", "seoul-oa-15323-sema": "OA-15323"}
DOWNLOAD_URL = "https://datafile.seoul.go.kr/bigfile/iot/sheet/csv/download.do"
MAX_CSV_BYTES = 128 * 1024 * 1024


class DownloadError(RuntimeError):
    pass


class RetryableDownloadError(DownloadError):
    """An incomplete transfer may be attempted on a later daily run."""


class OfficialRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        destination = urlsplit(newurl)
        if destination.scheme != "https" or destination.netloc not in {
            "data.seoul.go.kr", "datafile.seoul.go.kr",
        }:
            raise DownloadError("unapproved redirect")
        return super().redirect_request(request, fp, code, msg, headers, newurl)


official_open = build_opener(OfficialRedirects()).open


def observed_revision(source_id, *, opener=official_open):
    dataset = DATASETS.get(source_id)
    if not dataset:
        raise DownloadError("unapproved CSV source")
    request = Request(f"https://data.seoul.go.kr/dataList/{dataset}/S/1/datasetView.do")
    try:
        with opener(request, timeout=20) as response:
            content = response.read(2 * 1024 * 1024 + 1)
            if response.status != 200 or len(content) > 2 * 1024 * 1024:
                raise DownloadError("invalid dataset metadata")
        text = re.sub(r"<[^>]+>", " ", content.decode("utf-8"))
        match = re.search(r"데이터\s*갱신일\s+(\d{4})\.(\d{2})\.(\d{2})\.", text)
        if not match:
            raise DownloadError("dataset revision is unavailable")
        return date(*map(int, match.groups())).isoformat()
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as error:
        raise DownloadError("official dataset metadata failed") from error


def download_csv(source_id, directory, *, opener=official_open):
    dataset = DATASETS.get(source_id)
    if dataset is None:
        raise DownloadError("unapproved CSV source")
    data = urlencode({"srvType": "S", "infId": dataset, "serviceKind": "1", "pageNo": "1",
                      "ssUserId": "SAMPLE_VIEW", "strWhere": "", "strOrderby": "",
                      "filterCol": "", "txtFilter": ""}).encode()
    request = Request(DOWNLOAD_URL, data=data, headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": f"https://data.seoul.go.kr/dataList/{dataset}/S/1/datasetView.do",
        "User-Agent": "MIGAM/0.1 (+https://github.com/minhyeok328/MIGAM)",
    })
    target = Path(directory) / f"{dataset}.csv"
    digest = hashlib.sha256()
    size = 0
    created = False
    try:
        with target.open("xb") as output:
            created = True
            with opener(request, timeout=45) as response:
                if response.status != 200:
                    raise DownloadError("official CSV download failed")
                while chunk := response.read(1024 * 1024):
                    size += len(chunk)
                    if size > MAX_CSV_BYTES:
                        raise DownloadError("official CSV exceeds size limit")
                    digest.update(chunk)
                    output.write(chunk)
        if not size:
            raise DownloadError("official CSV is empty")
    except (HTTPError, URLError, TimeoutError, OSError, DownloadError) as error:
        if created:
            target.unlink(missing_ok=True)
        if isinstance(error, (URLError, TimeoutError)) and not (
            isinstance(error, HTTPError) and error.code in (403, 429)
        ):
            raise RetryableDownloadError("official CSV transfer incomplete") from error
        # Do not retry 403/429, follow alternative endpoints, or leak request URLs.
        raise DownloadError("official CSV download failed") from error
    return target, {"source_id": source_id, "dataset_url": request.headers["Referer"],
                    "downloaded_at": datetime.now(timezone.utc).isoformat(),
                    "sha256": digest.hexdigest(), "bytes": size}
