from __future__ import annotations

from typing import Any

import httpx
try:
    from curl_cffi.requests import AsyncSession as CurlAsyncSession
    from curl_cffi.requests.exceptions import RequestException as CurlRequestException
except ImportError:  # pragma: no cover - optional dependency fallback
    CurlAsyncSession = None
    CurlRequestException = None

from catchtable_cli.config import CatchTableConfig


class CatchTableAPIError(RuntimeError):
    """HTTP 200 응답 내 API 실패(isSuccess=false) 예외."""

    def __init__(
        self,
        result_code: str | int | None,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        self.result_code = result_code
        self.payload = payload or {}
        prefix = f"[{result_code}] " if result_code is not None else ""
        super().__init__(f"{prefix}{message}")


class CatchTableClient:
    """CatchTable ct-api.catchtable.co.kr 클라이언트.

    인증: x-ct-a 세션 쿠키 기반 (Bearer 아님).
    브라우저 로그인 후 x-ct-a 쿠키를 CT_SESSION_COOKIE 환경변수에 설정.
    """

    def __init__(self, config: CatchTableConfig | None = None) -> None:
        self.config = config or CatchTableConfig()
        self._httpx_client = httpx.AsyncClient(
            base_url=self.config.api_base_url,
            headers=self._build_headers(),
            cookies=self._build_cookies(),
            timeout=30.0,
        )
        self._use_curl_cffi = bool(
            self.config.use_curl_cffi and CurlAsyncSession is not None
        )
        self._curl_client: Any | None = None
        if self._use_curl_cffi:
            try:
                self._curl_client = CurlAsyncSession(
                    base_url=self.config.api_base_url,
                    headers=self._build_headers(),
                    cookies=self._build_cookies(),
                    timeout=30.0,
                    impersonate="chrome",
                )
            except Exception:
                self._use_curl_cffi = False
                self._curl_client = None

    def _build_headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
        }

    def _build_cookies(self) -> dict[str, str]:
        cookies: dict[str, str] = {}
        if self.config.session_cookie:
            cookies["x-ct-a"] = self.config.session_cookie
        return cookies

    def _build_absolute_url(self, url: str) -> str:
        if url.startswith(("http://", "https://")):
            return url
        return f"{self.config.api_base_url.rstrip('/')}/{url.lstrip('/')}"

    @staticmethod
    def _raise_if_api_error(payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        if payload.get("isSuccess") is False:
            result_code = payload.get("resultCode")
            message = (
                payload.get("resultMessage")
                or payload.get("displayMessage")
                or payload.get("message")
                or "CatchTable API request failed."
            )
            raise CatchTableAPIError(
                result_code=result_code,
                message=str(message),
                payload=payload,
            )

    @staticmethod
    def _should_fallback_to_httpx(exc: Exception) -> bool:
        if CurlRequestException is None:
            return False
        return isinstance(exc, CurlRequestException)

    def _raise_http_status_for_curl(
        self,
        *,
        method: str,
        url: str,
        params: dict[str, Any] | None,
        response: Any,
    ) -> None:
        status_code = int(getattr(response, "status_code", 0) or 0)
        if status_code < 400:
            return

        request = httpx.Request(
            method.upper(),
            self._build_absolute_url(url),
            params=params,
        )
        content = getattr(response, "content", b"")
        if isinstance(content, str):
            content = content.encode("utf-8", errors="ignore")
        headers = dict(getattr(response, "headers", {}) or {})
        httpx_response = httpx.Response(
            status_code=status_code,
            headers=headers,
            content=content or b"",
            request=request,
        )
        raise httpx.HTTPStatusError(
            message=f"HTTP Error {status_code}: {httpx_response.reason_phrase}",
            request=request,
            response=httpx_response,
        )

    async def _request_with_curl(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None,
        json_body: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if self._curl_client is None:
            raise RuntimeError("curl_cffi AsyncSession is not initialized.")

        resp = await self._curl_client.request(method, url, params=params, json=json_body)
        self._raise_http_status_for_curl(
            method=method,
            url=url,
            params=params,
            response=resp,
        )
        data = resp.json()
        self._raise_if_api_error(data)
        return data

    async def _request_with_httpx(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None,
        json_body: dict[str, Any] | None,
    ) -> dict[str, Any]:
        resp = await self._httpx_client.request(
            method,
            url,
            params=params,
            json=json_body,
        )
        resp.raise_for_status()
        data = resp.json()
        self._raise_if_api_error(data)
        return data

    async def _request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if self._use_curl_cffi and self._curl_client is not None:
            try:
                return await self._request_with_curl(
                    method,
                    url,
                    params=params,
                    json_body=json_body,
                )
            except CatchTableAPIError:
                raise
            except httpx.HTTPStatusError:
                raise
            except Exception as exc:
                if self._should_fallback_to_httpx(exc):
                    return await self._request_with_httpx(
                        method,
                        url,
                        params=params,
                        json_body=json_body,
                    )
                raise

        return await self._request_with_httpx(
            method,
            url,
            params=params,
            json_body=json_body,
        )

    async def autocomplete(self, query: str) -> dict[str, Any]:
        """POST /api/v5/autocomplete/_list — 자동완성 목록."""
        return await self._request(
            "POST",
            "/api/v5/autocomplete/_list",
            json_body={"query": query},
        )

    async def search(
        self,
        keyword: str | None = None,
        location: str | None = None,
        category: str | None = None,
        date: str | None = None,
        party_size: int | None = None,
        food_kind_code: str | None = None,
        sort_method: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> dict[str, Any]:
        """POST /api/v6/search/list — 매장 검색."""
        offset = (page - 1) * size
        body: dict[str, Any] = {"paging": {"page": page, "size": size, "offset": offset}}
        if keyword:
            body["keyword"] = keyword
        if location:
            body["region"] = location
        if category:
            body["category"] = category
        if date:
            body["visitDate"] = date
        if party_size is not None:
            body["personCount"] = party_size
        if food_kind_code:
            body["foodKindCode"] = food_kind_code
        if sort_method:
            body["sortMethod"] = sort_method
        return await self._request(
            "POST",
            "/api/v6/search/list",
            json_body=body,
        )

    async def resolve_alias(self, alias: str) -> dict[str, Any]:
        """GET /api/v3/shop/valid-url — URL alias를 shopRef로 변환."""
        return await self._request(
            "GET",
            "/api/v3/shop/valid-url", params={"shopUrl": alias}
        )

    async def get_shop(self, shop_ref: str) -> dict[str, Any]:
        """GET /api/v4/shops/{shopRef} — 매장 상세 (Chrome RE 확인)."""
        return await self._request("GET", f"/api/v4/shops/{shop_ref}")

    async def get_shop_detail_settings(self, shop_ref: str) -> dict[str, Any]:
        """GET /api/display/v2/shops/{shopRef}/detail-settings — 상세 설정."""
        return await self._request(
            "GET",
            f"/api/display/v2/shops/{shop_ref}/detail-settings"
        )

    async def get_shop_menu(self, shop_ref: str) -> dict[str, Any]:
        """GET /api/display/v2/shops/{shopRef}/tabs/menu — 메뉴 조회."""
        return await self._request(
            "GET",
            f"/api/display/v2/shops/{shop_ref}/tabs/menu"
        )

    async def get_day_slots(self, shop_ref: str) -> dict[str, Any]:
        """GET /api/reservation/v1/dining/day-slots — 예약 가능 날짜 (Chrome RE 확인)."""
        return await self._request(
            "GET",
            "/api/reservation/v1/dining/day-slots",
            params={"shopRef": shop_ref, "tableSeqs": "", "personCounts": ""},
        )

    async def check_availability(
        self,
        shop_ref: str,
        date: str,
        party_size: int,
    ) -> dict[str, Any]:
        """POST /api/reservation/v1/dining/time-slots — 예약 가능 시간."""
        return await self._request(
            "POST",
            "/api/reservation/v1/dining/time-slots",
            json_body={
                "shopRef": shop_ref,
                "visitYymmdd": date.replace("-", ""),
                "personCount": party_size,
            },
        )

    async def reserve(
        self,
        shop_id: str,
        date: str,
        time: str,
        party_size: int,
    ) -> dict[str, Any]:
        """POST /api/reservation/v2/dinings/create — 예약 생성."""
        return await self._request(
            "POST",
            "/api/reservation/v2/dinings/create",
            json_body={
                "shopRef": shop_id,
                "visitYymmdd": date.replace("-", ""),
                "visitHhmi": time.replace(":", ""),
                "personCount": party_size,
            },
        )

    async def list_reservations(
        self,
        status: str = "PLANNED",
        size: int = 10,
    ) -> dict[str, Any]:
        """GET /api/v4/user/reservations/_list — 내 예약 목록."""
        return await self._request(
            "GET",
            "/api/v4/user/reservations/_list",
            params={"statusGroup": status, "sortCode": "DESC", "size": size},
        )

    async def close(self) -> None:
        if self._curl_client is not None:
            await self._curl_client.close()
        await self._httpx_client.aclose()
