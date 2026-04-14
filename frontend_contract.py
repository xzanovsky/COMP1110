from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha1
from random import Random
from typing import Any, Iterable

from werkzeug.datastructures import FileStorage, MultiDict


@dataclass(slots=True)
class ScenarioInput:
    label: str
    restaurant_text: str
    arrivals_text: str = ""
    mode: str = "generated"
    seed: str = ""
    notes: str = ""

    @classmethod
    def default(cls, label: str) -> "ScenarioInput":
        return cls(
            label=label,
            restaurant_text=_sample_restaurant_config(),
            arrivals_text=_sample_arrivals(),
            mode="fixed",
            seed="2026",
            notes="Sample configuration you can replace with your own text files or manual edits.",
        )


@dataclass(slots=True)
class ScenarioResult:
    label: str
    status: str
    metrics: dict[str, str]
    series: dict[str, list[float]]
    timeline: list[dict[str, Any]]
    tables: list[dict[str, Any]]
    fallback_notice: str | None = None
    raw: Any = None


@dataclass(slots=True)
class ComparisonResult:
    left: ScenarioResult
    right: ScenarioResult
    delta_metrics: list[dict[str, str]]
    chart: dict[str, list[float]]


def collect_scenario_input(request: Any, prefix: str = "") -> ScenarioInput | None:
    form: MultiDict[str, str] = request.form
    files = request.files

    label = form.get(f"{prefix}label", "").strip()
    restaurant_text = _resolve_uploaded_text(
        files.get(f"{prefix}restaurant_file"),
        form.get(f"{prefix}restaurant_text", ""),
    )
    arrivals_text = _resolve_uploaded_text(
        files.get(f"{prefix}arrivals_file"),
        form.get(f"{prefix}arrivals_text", ""),
    )
    mode = form.get(f"{prefix}mode", "generated").strip() or "generated"
    seed = form.get(f"{prefix}seed", "").strip()
    notes = form.get(f"{prefix}notes", "").strip()

    if not label and not restaurant_text.strip():
        return None

    return ScenarioInput(
        label=label or "Untitled scenario",
        restaurant_text=restaurant_text or _sample_restaurant_config(),
        arrivals_text=arrivals_text,
        mode=mode,
        seed=seed,
        notes=notes,
    )


def run_scenario(scenario: ScenarioInput) -> ScenarioResult:
    backend_result, fallback_notice = _run_backend_if_available(scenario)
    if backend_result is not None:
        return _coerce_result(backend_result, scenario.label, fallback_notice)

    return _demo_result(scenario, fallback_notice)


def compare_scenarios(left: ScenarioResult, right: ScenarioResult) -> ComparisonResult:
    delta_rows: list[dict[str, str]] = []
    for key, left_value in left.metrics.items():
        if key not in right.metrics:
            continue
        left_num = _parse_number(left_value)
        right_num = _parse_number(right.metrics[key])
        if left_num is None or right_num is None:
            continue
        delta = left_num - right_num
        pct = f"{(delta / right_num * 100):+.1f}%" if right_num else "n/a"
        delta_rows.append(
            {
                "metric": key,
                "left": left.metrics[key],
                "right": right.metrics[key],
                "delta": f"{delta:+.2f}",
                "percent": pct,
            }
        )

    chart = {
        "labels": ["Average wait", "Max queue", "Utilisation"],
        "left": [
            _parse_number(left.metrics.get("Average wait", "0")) or 0,
            _parse_number(left.metrics.get("Max queue length", "0")) or 0,
            _parse_number(left.metrics.get("Table utilisation", "0")) or 0,
        ],
        "right": [
            _parse_number(right.metrics.get("Average wait", "0")) or 0,
            _parse_number(right.metrics.get("Max queue length", "0")) or 0,
            _parse_number(right.metrics.get("Table utilisation", "0")) or 0,
        ],
    }

    return ComparisonResult(left=left, right=right, delta_metrics=delta_rows, chart=chart)


def _run_backend_if_available(scenario: ScenarioInput) -> tuple[Any | None, str | None]:
    try:
        from parser import parse_arrivals, parse_restaurant_settings
        from simulator import run_simulation
    except Exception:
        return None, "Frontend fallback is active because the backend parser or simulator could not be imported."

    try:
        settings = parse_restaurant_settings(scenario.restaurant_text)
        if scenario.mode.strip():
            settings.arrival_mode = scenario.mode.strip().lower()
        if scenario.seed.strip():
            try:
                settings.seed = int(scenario.seed)
            except ValueError:
                pass
        if scenario.mode.strip().lower() == "fixed":
            if not scenario.arrivals_text.strip():
                raise ValueError("Fixed arrival mode requires arrivals text or an arrivals file.")
            arrivals = parse_arrivals(scenario.arrivals_text)
        else:
            arrivals = None
        return run_simulation(settings, arrivals), "Results came from the repository backend simulator."
    except Exception as exc:
        return None, f"Frontend fallback is active because the backend simulation could not run: {exc}"


def _coerce_result(raw: Any, label: str, fallback_notice: str | None) -> ScenarioResult:
    if isinstance(raw, ScenarioResult):
        return raw
    if isinstance(raw, dict):
        data = raw
    else:
        data = _simulation_result_to_mapping(raw)

    metrics = _format_metrics(data)
    series = _extract_series(data)
    timeline = _extract_timeline(data)
    tables = _extract_tables(data)
    status = str(data.get("status", "completed"))
    return ScenarioResult(
        label=label,
        status=status,
        metrics=metrics,
        series=series,
        timeline=timeline,
        tables=tables,
        fallback_notice=fallback_notice,
        raw=raw,
    )


def _demo_result(scenario: ScenarioInput, fallback_notice: str | None) -> ScenarioResult:
    seed_source = "|".join([scenario.label, scenario.restaurant_text, scenario.arrivals_text, scenario.mode, scenario.seed])
    rng = Random(int(sha1(seed_source.encode("utf-8")).hexdigest(), 16))
    queue_lengths = [max(0, int(2 + rng.gauss(0, 1) + i * 0.15)) for i in range(12)]
    waits = [round(max(0.0, rng.gauss(12, 5)), 1) for _ in range(12)]
    utilisation = [round(min(1.0, max(0.2, 0.55 + rng.random() * 0.3)), 2) for _ in range(12)]
    metrics = {
        "Average wait": f"{sum(waits) / len(waits):.1f} min",
        "Max wait": f"{max(waits):.1f} min",
        "Max queue length": str(max(queue_lengths)),
        "Groups served": str(30 + rng.randint(0, 25)),
        "Table utilisation": f"{sum(utilisation) / len(utilisation):.0%}",
        "Service level": f"{70 + rng.randint(0, 20)}%",
    }
    timeline = [
        {
            "minute": str(index * 10),
            "arrivals": rng.randint(0, 4),
            "seated": rng.randint(0, 3),
            "waiting": queue_lengths[index],
        }
        for index in range(len(queue_lengths))
    ]
    tables = [
        {"table": f"T{index + 1}", "size": rng.choice([2, 4, 6, 8]), "utilisation": f"{rng.randint(55, 96)}%"}
        for index in range(5)
    ]
    series = {
        "labels": [str(index * 10) for index in range(len(queue_lengths))],
        "queue": queue_lengths,
        "wait": waits,
        "utilisation": utilisation,
    }
    return ScenarioResult(
        label=scenario.label,
        status="demo",
        metrics=metrics,
        series=series,
        timeline=timeline,
        tables=tables,
        fallback_notice=fallback_notice,
    )


def _format_metrics(value: Any) -> dict[str, str]:
    if isinstance(value, dict):
        metrics_source = value.get("metrics", value)
        if isinstance(metrics_source, dict):
            result = {
                "Average wait": _format_minutes(
                    metrics_source.get("average_wait_minutes")
                    or metrics_source.get("average_wait")
                    or metrics_source.get("Average wait")
                    or 0
                ),
                "Max wait": _format_minutes(
                    metrics_source.get("max_wait_minutes")
                    or metrics_source.get("max_wait")
                    or metrics_source.get("Max wait")
                    or 0
                ),
                "Max queue length": _format_integer(
                    metrics_source.get("max_queue_length")
                    or metrics_source.get("queue_max_lengths")
                    or metrics_source.get("Max queue length")
                    or 0
                ),
                "Groups served": _format_integer(
                    metrics_source.get("served_groups")
                    or metrics_source.get("groups_served")
                    or metrics_source.get("Groups served")
                    or 0
                ),
                "Table utilisation": _format_percent(
                    metrics_source.get("table_utilisation")
                    or metrics_source.get("Table utilisation")
                    or 0
                ),
                "Service level": _format_percent(
                    metrics_source.get("service_level")
                    or metrics_source.get("Service level")
                    or 0
                ),
            }
            if "queue_max_lengths" in metrics_source and isinstance(metrics_source["queue_max_lengths"], dict):
                result["Max queue length"] = _format_integer(max(metrics_source["queue_max_lengths"].values(), default=0))
            return result
    return {
        "Average wait": _format_minutes(getattr(value, "average_wait", "n/a")),
        "Max wait": _format_minutes(getattr(value, "max_wait", "n/a")),
        "Max queue length": _format_integer(getattr(value, "max_queue_length", "n/a")),
        "Groups served": _format_integer(getattr(value, "groups_served", "n/a")),
        "Table utilisation": _format_percent(getattr(value, "table_utilisation", "n/a")),
        "Service level": _format_percent(getattr(value, "service_level", "n/a")),
    }


def _extract_series(value: Any) -> dict[str, list[float]]:
    series: dict[str, list[float]] = {}
    for key in ("labels", "queue", "wait", "utilisation", "queue_length", "wait_time"):
        if isinstance(value, dict) and key in value and isinstance(value[key], Iterable) and not isinstance(value[key], (str, bytes)):
            series[key] = [float(item) for item in value[key]]
    if not series and isinstance(value, dict) and "minute_summaries" in value:
        summaries = value["minute_summaries"]
        if isinstance(summaries, Iterable):
            labels: list[float] = []
            queue: list[float] = []
            wait: list[float] = []
            for index, snapshot in enumerate(summaries):
                minute = getattr(snapshot, "minute", index)
                queue_lengths = getattr(snapshot, "queue_lengths", {}) or {}
                labels.append(float(minute))
                queue.append(float(max(queue_lengths.values(), default=0)))
                wait.append(float(len(getattr(snapshot, "arrivals", ()))))
            series["labels"] = labels
            series["queue"] = queue
            series["wait"] = wait
    return series


def _extract_timeline(value: Any) -> list[dict[str, Any]]:
    timeline: list[dict[str, Any]] = []
    if isinstance(value, dict) and "minute_summaries" in value:
        for snapshot in value["minute_summaries"]:
            minute = getattr(snapshot, "minute", None)
            arrivals = getattr(snapshot, "arrivals", ())
            seated = getattr(snapshot, "seated", ())
            queue_lengths = getattr(snapshot, "queue_lengths", {}) or {}
            timeline.append(
                {
                    "minute": minute,
                    "arrivals": len(arrivals),
                    "seated": len(seated),
                    "waiting": max(queue_lengths.values(), default=0),
                }
            )
    return timeline


def _extract_tables(value: Any) -> list[dict[str, Any]]:
    tables: list[dict[str, Any]] = []
    if isinstance(value, dict):
        util = value.get("table_utilisation_by_table", {})
        if isinstance(util, dict):
            for table_id, usage in util.items():
                tables.append({"table": table_id, "utilisation": f"{float(usage):.0%}"})
    return tables


def _simulation_result_to_mapping(result: Any) -> dict[str, Any]:
    mapping: dict[str, Any] = {}
    for name in (
        "settings",
        "groups",
        "minute_summaries",
        "queue_max_lengths",
        "served_groups",
        "unserved_groups",
        "average_wait_minutes",
        "max_wait_minutes",
        "service_level",
        "total_occupied_minutes",
        "total_runtime_minutes",
        "table_utilisation",
        "table_utilisation_by_table",
    ):
        if hasattr(result, name):
            mapping[name] = getattr(result, name)
    if hasattr(result, "to_dict"):
        try:
            mapping.update(result.to_dict())
        except Exception:
            pass
    return mapping


def _resolve_uploaded_text(upload: FileStorage | None, fallback: str) -> str:
    if upload and upload.filename:
        raw = upload.read()
        if isinstance(raw, bytes):
            return raw.decode("utf-8", errors="replace")
        return str(raw)
    return fallback.strip()


def _parse_number(value: str) -> float | None:
    digits = "".join(ch if ch.isdigit() or ch in ".-" else " " for ch in value)
    chunk = digits.split()
    if not chunk:
        return None
    try:
        return float(chunk[0])
    except ValueError:
        return None


def _stringify_number(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.1f}"
    if isinstance(value, int):
        return str(value)
    return str(value)


def _format_minutes(value: Any) -> str:
    if isinstance(value, str) and value.strip():
        return value if value.endswith("min") else f"{value} min"
    if isinstance(value, (int, float)):
        return f"{float(value):.1f} min"
    return str(value)


def _format_integer(value: Any) -> str:
    if isinstance(value, str) and value.strip():
        return value
    if isinstance(value, (int, float)):
        return str(int(round(float(value))))
    return str(value)


def _format_percent(value: Any) -> str:
    if isinstance(value, str) and value.strip():
        return value if value.endswith("%") else f"{value}%"
    if isinstance(value, (int, float)):
        ratio = float(value)
        if ratio <= 1:
            return f"{ratio:.0%}"
        return f"{ratio:.1f}%"
    return str(value)


def _sample_restaurant_config() -> str:
    return """[general]
simulation_minutes = 240
arrival_mode = generated
seed = 2026
target_wait_minutes = 15

[tables]
T1 = 2
T2 = 4
T3 = 4
T4 = 6
T5 = 8

[queues]
small = 1-2
medium = 3-4
large = 5-6
oversize = 7-10

[arrivals]
arrival_probability_per_minute = 0.85
generated_group_size_range = 1-6
generated_service_time_range = 30-70
"""


def _sample_arrivals() -> str:
    return """group_id,arrival_time,size,service_duration
G1,0,2,40
G2,10,4,55
G3,20,1,35
G4,35,6,70
G5,50,3,45
"""
