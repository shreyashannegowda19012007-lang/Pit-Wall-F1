"""
System Observability, Operations Counters & Alert Condition Engine.
Tracks real-time telemetry points, simulation executions, backtest decision evaluations,
and API error rates. Exposes Prometheus-compatible operational counters.
"""

from typing import Dict, List, Optional, Any
import threading
import datetime


class ObservabilityManager:
    """
    Operational Counters & System Metrics Collector.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self.telemetry_points_processed = 0
        self.simulations_executed = 0
        self.replay_decisions_evaluated = 0
        self.evaluation_cases_completed = 0
        self.api_requests_total = 0
        self.api_errors_total = 0
        self.start_time = datetime.datetime.now()

    def record_telemetry_points(self, count: int):
        with self._lock:
            self.telemetry_points_processed += count

    def record_simulations(self, count: int):
        with self._lock:
            self.simulations_executed += count

    def record_replay_decisions(self, count: int = 1):
        with self._lock:
            self.replay_decisions_evaluated += count

    def record_evaluation_cases(self, count: int = 1):
        with self._lock:
            self.evaluation_cases_completed += count

    def record_api_request(self, is_error: bool = False):
        with self._lock:
            self.api_requests_total += 1
            if is_error:
                self.api_errors_total += 1

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Returns active operational counters and alert status."""
        with self._lock:
            err_rate_pct = (self.api_errors_total / self.api_requests_total * 100.0) if self.api_requests_total > 0 else 0.0
            uptime_seconds = (datetime.datetime.now() - self.start_time).total_seconds()

            alerts = []
            if err_rate_pct > 5.0:
                alerts.append(f"HIGH_API_ERROR_RATE: {err_rate_pct:.1f}% exceeds 5.0% threshold.")

            return {
                "telemetry_points_processed": self.telemetry_points_processed,
                "simulations_executed": self.simulations_executed,
                "replay_decisions_evaluated": self.replay_decisions_evaluated,
                "evaluation_cases_completed": self.evaluation_cases_completed,
                "api_requests_total": self.api_requests_total,
                "api_errors_total": self.api_errors_total,
                "api_error_rate_pct": round(err_rate_pct, 2),
                "uptime_seconds": round(uptime_seconds, 1),
                "active_alerts": alerts,
                "status": "HEALTHY" if not alerts else "WARNING"
            }


# Global Observability Manager Singleton
obs_manager = ObservabilityManager()
