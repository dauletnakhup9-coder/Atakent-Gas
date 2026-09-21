import asyncio
import json
import math
import socket
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen


PROMETHEUS_URL = "http://prometheus:9090"


class PrometheusError(RuntimeError):
    pass


def _request(query: str) -> dict:
    params = urlencode({"query": query})
    url = f"{PROMETHEUS_URL}/api/v1/query?{params}"

    try:
        with urlopen(url, timeout=5) as response:
            raw_data = response.read().decode("utf-8")
            payload = json.loads(raw_data)

    except (
        HTTPError,
        URLError,
        TimeoutError,
        socket.gaierror,
        ConnectionError,
        json.JSONDecodeError,
        OSError,
    ) as exc:
        raise PrometheusError(
            "Prometheus unavailable"
        ) from exc

    if payload.get("status") != "success":
        raise PrometheusError(
            "Prometheus query failed"
        )

    return payload


async def query(query_text: str) -> dict:
    try:
        return await asyncio.to_thread(
            _request,
            query_text,
        )

    except PrometheusError:
        raise

    except Exception as exc:
        raise PrometheusError(
            "Prometheus unavailable"
        ) from exc


async def query_value(
    query_text: str,
    default: float | None = None,
) -> float | None:
    try:
        payload = await query(query_text)

        results = (
            payload
            .get("data", {})
            .get("result", [])
        )

        if not results:
            return default

        value = results[0].get("value")

        if not value or len(value) < 2:
            return default

        number = float(value[1])

        if not math.isfinite(number):
            return default

        return number

    except (
        PrometheusError,
        TypeError,
        ValueError,
        IndexError,
    ):
        return default


async def is_available() -> bool:
    try:
        await query("up")
        return True

    except Exception:
        return False


async def collect_ddos_metrics() -> dict | None:
    """
    Collect metrics required by ddos_monitor.py.

    Missing Prometheus data is represented by None instead
    of zero so unavailable monitoring data cannot produce
    a false NORMAL DDoS status.
    """

    if not await is_available():
        return None

    try:
        (
            current_rps,
            average_rps_7d,
            syn_recv,
            error_rate_429_503,
            inbound_traffic_percent,
            requests_per_ip_minute,
            unique_ip_spike_ratio,
        ) = await asyncio.gather(

            # Current Nginx requests per second.
            query_value(
                (
                    "sum("
                    "rate("
                    "nginx_http_requests_total[1m]"
                    ")"
                    ")"
                )
            ),

            # Average requests per second over seven days.
            query_value(
                (
                    "avg_over_time("
                    "("
                    "sum("
                    "rate("
                    "nginx_http_requests_total[1m]"
                    ")"
                    ")"
                    ")[7d:1m]"
                    ")"
                )
            ),

            # Dedicated SYN_RECV collector.
            # Until that collector is connected,
            # this value can legitimately be None.
            query_value(
                "utility_tcp_syn_recv"
            ),

            # Percentage of backend responses that
            # are HTTP 429 or 503.
            query_value(
                (
                    "100 * "
                    "sum("
                    "rate("
                    "utility_http_requests_total"
                    '{status=~"429|503"}[1m]'
                    ")"
                    ") "
                    "/ "
                    "clamp_min("
                    "sum("
                    "rate("
                    "utility_http_requests_total[1m]"
                    ")"
                    "), "
                    "0.001"
                    ")"
                )
            ),

            query_value(
                "utility_inbound_traffic_percent"
            ),

            query_value(
                "max("
                "utility_requests_per_ip_minute"
                ")"
            ),

            query_value(
                "utility_unique_ip_spike_ratio"
            ),
        )

    except Exception:
        return None

    # Without current traffic data we cannot reliably
    # evaluate DDoS status.
    if current_rps is None:
        return None

    return {
        "current_rps": current_rps,

        "average_rps_7d":
            average_rps_7d,

        "syn_recv": (
            int(syn_recv)
            if syn_recv is not None
            else None
        ),

        "error_rate_429_503":
            error_rate_429_503,

        "inbound_traffic_percent":
            inbound_traffic_percent,

        "requests_per_ip_minute": (
            int(requests_per_ip_minute)
            if requests_per_ip_minute is not None
            else None
        ),

        "unique_ip_spike_ratio":
            unique_ip_spike_ratio,
    }