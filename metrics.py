"""Metrics helpers for simulation results."""

from __future__ import annotations

from models import SimulationResult


def compute_metrics(result: SimulationResult) -> dict[str, float | int | dict[str, float] | dict[str, int]]:
    """Return a serialisable summary of a simulation result."""

    return {
        "served_groups": result.served_groups,
        "unserved_groups": result.unserved_groups,
        "average_wait_minutes": result.average_wait_minutes,
        "max_wait_minutes": result.max_wait_minutes,
        "service_level": result.service_level,
        "total_occupied_minutes": result.total_occupied_minutes,
        "total_runtime_minutes": result.total_runtime_minutes,
        "table_utilisation": result.table_utilisation,
        "table_utilisation_by_table": dict(result.table_utilisation_by_table),
        "queue_max_lengths": dict(result.queue_max_lengths),
    }


def comparison_metrics(before: SimulationResult, after: SimulationResult) -> dict[str, dict[str, float]]:
    """Compute absolute and percentage deltas between two scenarios."""

    def delta(left: float, right: float) -> dict[str, float]:
        absolute = right - left
        percentage = (absolute / left * 100.0) if left else 0.0
        return {"absolute": absolute, "percentage": percentage}

    return {
        "average_wait_minutes": delta(before.average_wait_minutes, after.average_wait_minutes),
        "max_wait_minutes": delta(before.max_wait_minutes, after.max_wait_minutes),
        "service_level": delta(before.service_level, after.service_level),
        "table_utilisation": delta(before.table_utilisation, after.table_utilisation),
        "served_groups": delta(before.served_groups, after.served_groups),
        "unserved_groups": delta(before.unserved_groups, after.unserved_groups),
    }

