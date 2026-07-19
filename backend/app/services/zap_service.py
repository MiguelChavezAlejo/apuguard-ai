import time
from typing import Any
from urllib.parse import urlparse

import httpx
from fastapi import HTTPException, status

from app.core.config import settings


class ZapService:
    def __init__(self) -> None:
        self.base_url = settings.zap_base_url.rstrip("/")
        self.api_key = settings.zap_api_key
        self.poll_interval = settings.zap_poll_interval_seconds

    def _params(self, **kwargs: Any) -> dict[str, Any]:
        params: dict[str, Any] = {
            key: value
            for key, value in kwargs.items()
            if value is not None
        }

        if self.api_key:
            params["apikey"] = self.api_key

        return params

    def _get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        try:
            response = httpx.get(
                f"{self.base_url}{path}",
                params=params,
                timeout=timeout,
            )
            response.raise_for_status()
            return response.json()

        except httpx.ConnectError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No fue posible conectar con OWASP ZAP.",
            ) from exc

        except httpx.TimeoutException as exc:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="OWASP ZAP excedió el tiempo de respuesta.",
            ) from exc

        except (httpx.HTTPStatusError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="OWASP ZAP devolvió una respuesta inválida.",
            ) from exc

    @staticmethod
    def validate_target_url(target_url: str) -> None:
        parsed = urlparse(target_url)

        if parsed.scheme not in {"http", "https"}:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La URL debe utilizar HTTP o HTTPS.",
            )

        if not parsed.hostname:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La URL objetivo no contiene un host válido.",
            )

        allowed_hosts = {
            "juice-shop",
            "localhost",
            "127.0.0.1",
        }

        if parsed.hostname not in allowed_hosts:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Por seguridad, la demostración solo permite analizar "
                    "el laboratorio OWASP Juice Shop local."
                ),
            )

    def check_health(self) -> str:
        data = self._get("/JSON/core/view/version/")
        return str(data.get("version", "unknown"))

    def access_url(self, target_url: str) -> None:
        self._get(
            "/JSON/core/action/accessUrl/",
            params=self._params(
                url=target_url,
                followRedirects="true",
            ),
            timeout=60.0,
        )

    def start_spider(self, target_url: str) -> str:
        data = self._get(
            "/JSON/spider/action/scan/",
            params=self._params(
                url=target_url,
                maxChildren=20,
                recurse="true",
                subtreeOnly="true",
            ),
            timeout=60.0,
        )

        scan_id = data.get("scan")

        if scan_id is None:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="ZAP no devolvió el identificador del Spider.",
            )

        return str(scan_id)

    def wait_for_spider(self, scan_id: str) -> None:
        started_at = time.monotonic()

        while True:
            data = self._get(
                "/JSON/spider/view/status/",
                params=self._params(scanId=scan_id),
            )

            progress = int(data.get("status", 0))

            if progress >= 100:
                return

            if (
                time.monotonic() - started_at
                > settings.zap_spider_timeout_seconds
            ):
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail="El Spider de ZAP excedió el tiempo permitido.",
                )

            time.sleep(self.poll_interval)

    def wait_for_passive_scan(self) -> None:
        started_at = time.monotonic()

        while True:
            data = self._get(
                "/JSON/pscan/view/recordsToScan/",
            )

            remaining = int(data.get("recordsToScan", 0))

            if remaining <= 0:
                return

            if (
                time.monotonic() - started_at
                > settings.zap_spider_timeout_seconds
            ):
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail="El escaneo pasivo excedió el tiempo permitido.",
                )

            time.sleep(self.poll_interval)

    def start_active_scan(self, target_url: str) -> str:
        data = self._get(
            "/JSON/ascan/action/scan/",
            params=self._params(
                url=target_url,
                recurse="true",
                inScopeOnly="false",
            ),
            timeout=60.0,
        )

        scan_id = data.get("scan")

        if scan_id is None:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="ZAP no devolvió el identificador del Active Scan.",
            )

        return str(scan_id)

    def wait_for_active_scan(self, scan_id: str) -> None:
        started_at = time.monotonic()

        while True:
            data = self._get(
                "/JSON/ascan/view/status/",
                params=self._params(scanId=scan_id),
            )

            progress = int(data.get("status", 0))

            if progress >= 100:
                return

            if (
                time.monotonic() - started_at
                > settings.zap_active_scan_timeout_seconds
            ):
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail="El Active Scan excedió el tiempo permitido.",
                )

            time.sleep(self.poll_interval)

    def get_alerts(self, target_url: str) -> list[dict[str, Any]]:
        data = self._get(
            "/JSON/core/view/alerts/",
            params=self._params(
                baseurl=target_url,
                start=0,
                count=5000,
            ),
            timeout=60.0,
        )

        alerts = data.get("alerts", [])

        if not isinstance(alerts, list):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="ZAP devolvió un formato de alertas no válido.",
            )

        return alerts

    def run_full_scan(self, target_url: str) -> list[dict[str, Any]]:
        self.validate_target_url(target_url)
        self.check_health()
        self.access_url(target_url)

        spider_id = self.start_spider(target_url)
        self.wait_for_spider(spider_id)
        self.wait_for_passive_scan()

        active_scan_id = self.start_active_scan(target_url)
        self.wait_for_active_scan(active_scan_id)
        self.wait_for_passive_scan()

        return self.get_alerts(target_url)