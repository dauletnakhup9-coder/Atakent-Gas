from dataclasses import dataclass
from enum import Enum


class DDoSStatus(str, Enum):
    NORMAL = "normal"
    WARNING = "warning"
    ATTACK = "attack"
    UNKNOWN = "unknown"


@dataclass
class DDoSMetrics:
    current_rps: float

    average_rps_7d: float | None = None
    syn_recv: int | None = None
    error_rate_429_503: float | None = None
    inbound_traffic_percent: float | None = None
    requests_per_ip_minute: int | None = None
    unique_ip_spike_ratio: float | None = None


@dataclass
class DDoSResult:
    status: DDoSStatus
    warning_signals: list[str]
    attack_signals: list[str]
    unavailable_signals: list[str]

    @property
    def warning_count(self) -> int:
        return len(self.warning_signals)

    @property
    def attack_count(self) -> int:
        return len(self.attack_signals)

    @property
    def unavailable_count(self) -> int:
        return len(self.unavailable_signals)


def detect_ddos(metrics: DDoSMetrics) -> DDoSResult:
    warning_signals: list[str] = []
    attack_signals: list[str] = []
    unavailable_signals: list[str] = []

    # ---------------------------------------------------------
    # 1. RPS compared with the 7-day average
    # ---------------------------------------------------------

    if metrics.average_rps_7d is None:
        unavailable_signals.append("average_rps_7d")

    elif metrics.average_rps_7d > 0:
        rps_ratio = metrics.current_rps / metrics.average_rps_7d

        if rps_ratio >= 10:
            attack_signals.append("rps_spike")
        elif rps_ratio >= 3:
            warning_signals.append("rps_spike")

    # ---------------------------------------------------------
    # 2. TCP connections in SYN_RECV state
    # ---------------------------------------------------------

    if metrics.syn_recv is None:
        unavailable_signals.append("syn_recv")

    elif metrics.syn_recv > 1000:
        attack_signals.append("syn_recv")

    elif metrics.syn_recv > 200:
        warning_signals.append("syn_recv")

    # ---------------------------------------------------------
    # 3. HTTP 429/503 error percentage
    # ---------------------------------------------------------

    if metrics.error_rate_429_503 is None:
        unavailable_signals.append("http_429_503")

    elif metrics.error_rate_429_503 > 20:
        attack_signals.append("http_429_503")

    elif metrics.error_rate_429_503 > 5:
        warning_signals.append("http_429_503")

    # ---------------------------------------------------------
    # 4. Incoming traffic percentage
    # ---------------------------------------------------------

    if metrics.inbound_traffic_percent is None:
        unavailable_signals.append("inbound_traffic")

    elif metrics.inbound_traffic_percent > 85:
        attack_signals.append("inbound_traffic")

    elif metrics.inbound_traffic_percent > 60:
        warning_signals.append("inbound_traffic")

    # ---------------------------------------------------------
    # 5. Requests from one IP per minute
    # ---------------------------------------------------------

    if metrics.requests_per_ip_minute is None:
        unavailable_signals.append("single_ip_rate")

    elif metrics.requests_per_ip_minute > 1000:
        attack_signals.append("single_ip_rate")

    elif metrics.requests_per_ip_minute > 300:
        warning_signals.append("single_ip_rate")

    # ---------------------------------------------------------
    # 6. Spike in new unique IP addresses
    # ---------------------------------------------------------

    if metrics.unique_ip_spike_ratio is None:
        unavailable_signals.append("unique_ip_spike")

    elif metrics.unique_ip_spike_ratio >= 20:
        attack_signals.append("unique_ip_spike")

    elif metrics.unique_ip_spike_ratio >= 5:
        warning_signals.append("unique_ip_spike")

    # ---------------------------------------------------------
    # Final DDoS status
    # ---------------------------------------------------------

    # At least two attack-level signals indicate an attack.
    if len(attack_signals) >= 2:
        status = DDoSStatus.ATTACK

    # Any warning-level signal or one attack-level signal
    # indicates a warning.
    elif warning_signals or attack_signals:
        status = DDoSStatus.WARNING

    # If no threat is detected but some monitoring signals
    # are unavailable, we must not report a false NORMAL state.
    elif unavailable_signals:
        status = DDoSStatus.UNKNOWN

    else:
        status = DDoSStatus.NORMAL

    return DDoSResult(
        status=status,
        warning_signals=warning_signals,
        attack_signals=attack_signals,
        unavailable_signals=unavailable_signals,
    )