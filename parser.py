"""Parsing helpers for the restaurant queue simulation."""

from __future__ import annotations

import csv
import re
from pathlib import Path

from models import ArrivalGeneration, CustomerGroup, QueueBand, RestaurantSettings, Table


_SECTION_RE = re.compile(r"^\[(?P<section>[^\]]+)\]$")


def _strip_comment(line: str) -> str:
    if "#" in line:
        line = line.split("#", 1)[0]
    return line.strip()


def _parse_key_value(line: str) -> tuple[str, str] | None:
    if "=" in line:
        key, value = line.split("=", 1)
        return key.strip().lower(), value.strip()
    if ":" in line and not re.fullmatch(r"\d+\s*:\s*\d+", line):
        key, value = line.split(":", 1)
        return key.strip().lower(), value.strip()
    return None


def _parse_int_pair(value: str) -> tuple[int, int]:
    if "-" in value:
        left, right = value.split("-", 1)
    elif ":" in value:
        left, right = value.split(":", 1)
    else:
        raise ValueError(f"expected a range like 1-2, got {value!r}")
    return int(left.strip()), int(right.strip())


def _parse_number_list(value: str) -> list[int]:
    return [int(part.strip()) for part in re.split(r"[,\s]+", value.strip()) if part.strip()]


def _parse_sections(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {"general": [], "tables": [], "queues": [], "arrivals": []}
    current = "general"
    for raw_line in text.splitlines():
        line = _strip_comment(raw_line)
        if not line:
            continue
        match = _SECTION_RE.match(line)
        if match:
            current = match.group("section").strip().lower()
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return sections


def parse_restaurant_settings(text: str) -> RestaurantSettings:
    """Parse a restaurant configuration text block.

    Supported shape:
    - [general] section with key=value pairs
    - [tables] section with one capacity per line, or id=capacity
    - [queues] section with name=1-2
    - [arrivals] section for generated-arrival parameters
    """

    sections = _parse_sections(text)
    general_values: dict[str, str] = {}
    for line in sections.get("general", []):
        kv = _parse_key_value(line)
        if kv is None:
            raise ValueError(f"invalid general setting line: {line!r}")
        general_values[kv[0]] = kv[1]

    simulation_minutes = int(general_values.get("simulation_minutes", "0"))
    if simulation_minutes <= 0:
        raise ValueError("simulation_minutes must be a positive integer")

    arrival_mode = general_values.get("arrival_mode", "generated").strip().lower()
    seed = int(general_values.get("seed", "0"))

    arrival_values: dict[str, str] = {}
    for line in sections.get("arrivals", []):
        kv = _parse_key_value(line)
        if kv is None:
            raise ValueError(f"invalid arrivals setting line: {line!r}")
        arrival_values[kv[0]] = kv[1]

    arrival_probability = float(
        arrival_values.get(
            "arrival_probability_per_minute",
            general_values.get("arrival_probability_per_minute", "0.0"),
        )
    )
    group_size_min, group_size_max = _parse_int_pair(
        arrival_values.get(
            "generated_group_size_range",
            general_values.get("generated_group_size_range", "1-6"),
        )
    )
    service_time_min, service_time_max = _parse_int_pair(
        arrival_values.get(
            "generated_service_time_range",
            general_values.get("generated_service_time_range", "10-30"),
        )
    )
    target_wait_minutes = int(
        arrival_values.get(
            "target_wait_minutes",
            general_values.get("target_wait_minutes", "15"),
        )
    )

    tables: list[Table] = []
    table_counter = 1
    for index, line in enumerate(sections.get("tables", []), start=1):
        kv = _parse_key_value(line)
        if kv is None:
            capacities = _parse_number_list(line)
            if not capacities:
                raise ValueError(f"table line must contain at least one capacity, got {line!r}")
            for capacity in capacities:
                tables.append(Table(id=f"T{table_counter}", capacity=capacity))
                table_counter += 1
            continue
        capacities = _parse_number_list(kv[1])
        if not capacities:
            raise ValueError(f"table entry must contain at least one capacity, got {line!r}")
        if len(capacities) == 1:
            tables.append(Table(id=kv[0].upper(), capacity=capacities[0]))
            continue
        for offset, capacity in enumerate(capacities, start=1):
            tables.append(Table(id=f"{kv[0].upper()}_{offset}", capacity=capacity))

    if not tables:
        raise ValueError("at least one table must be defined")

    bands: list[QueueBand] = []
    for index, line in enumerate(sections.get("queues", []), start=1):
        kv = _parse_key_value(line)
        if kv is None:
            lower, upper = _parse_int_pair(line)
            bands.append(QueueBand(name=f"queue_{index}", min_size=lower, max_size=upper))
            continue
        lower, upper = _parse_int_pair(kv[1])
        bands.append(QueueBand(name=kv[0], min_size=lower, max_size=upper))

    if not bands:
        raise ValueError("at least one queue band must be defined")

    return RestaurantSettings(
        tables=tuple(tables),
        queue_bands=tuple(bands),
        simulation_minutes=simulation_minutes,
        arrival_mode=arrival_mode,
        seed=seed,
        arrival_generation=ArrivalGeneration(
            arrival_probability_per_minute=arrival_probability,
            group_size_min=group_size_min,
            group_size_max=group_size_max,
            service_time_min=service_time_min,
            service_time_max=service_time_max,
            target_wait_minutes=target_wait_minutes,
        ),
    )


def parse_arrivals(text: str) -> list[CustomerGroup]:
    """Parse explicit arrival rows.

    Accepts CSV with or without a header. Minimum fields are:
    group_id, arrival_time, size, service_duration
    """

    lines = [_strip_comment(row) for row in text.splitlines()]
    lines = [line for line in lines if line]
    if not lines:
        return []

    first_line = lines[0].lower()
    has_header = any(
        keyword in first_line
        for keyword in ("group_id", "arrival_time", "arrival", "size", "service_duration", "service_time")
    )

    rows: list[dict[str, str]] = []
    if has_header:
        reader = csv.DictReader(lines)
        for row in reader:
            rows.append({key.lower(): value for key, value in row.items() if key})
    else:
        reader = csv.reader(lines)
        for index, row in enumerate(reader, start=1):
            if len(row) < 4:
                raise ValueError("arrival rows must have at least four columns")
            rows.append(
                {
                    "group_id": row[0].strip() or f"G{index}",
                    "arrival_time": row[1].strip(),
                    "size": row[2].strip(),
                    "service_duration": row[3].strip(),
                }
            )

    groups: list[CustomerGroup] = []
    for index, row in enumerate(rows, start=1):
        group_id = (
            row.get("group_id")
            or row.get("id")
            or row.get("group")
            or f"G{index}"
        ).strip()
        arrival_time = row.get("arrival_time") or row.get("arrival") or row.get("minute")
        size = row.get("size") or row.get("group_size")
        service_duration = row.get("service_duration") or row.get("service_time") or row.get("dining_time")
        if arrival_time is None or size is None or service_duration is None:
            raise ValueError(f"arrival row missing required fields: {row!r}")
        groups.append(
            CustomerGroup(
                id=group_id,
                size=int(size),
                arrival_time=int(arrival_time),
                service_duration=int(service_duration),
                source="fixed",
            )
        )
    return groups


def load_restaurant_file(path: str | Path) -> RestaurantSettings:
    return parse_restaurant_settings(Path(path).read_text(encoding="utf-8"))


def load_arrivals_file(path: str | Path) -> list[CustomerGroup]:
    return parse_arrivals(Path(path).read_text(encoding="utf-8"))


def format_restaurant_settings(settings: RestaurantSettings) -> str:
    """Convenience helper for tests and fixtures."""

    lines = ["[general]"]
    lines.append(f"simulation_minutes = {settings.simulation_minutes}")
    lines.append(f"arrival_mode = {settings.arrival_mode}")
    lines.append(f"seed = {settings.seed}")
    lines.append(f"target_wait_minutes = {settings.arrival_generation.target_wait_minutes}")
    lines.append("")
    lines.append("[tables]")
    for table in settings.tables:
        lines.append(f"{table.id} = {table.capacity}")
    lines.append("")
    lines.append("[queues]")
    for band in settings.queue_bands:
        lines.append(f"{band.name} = {band.min_size}-{band.max_size}")
    lines.append("")
    lines.append("[arrivals]")
    lines.append(
        f"arrival_probability_per_minute = {settings.arrival_generation.arrival_probability_per_minute}"
    )
    lines.append(
        f"generated_group_size_range = {settings.arrival_generation.group_size_min}-{settings.arrival_generation.group_size_max}"
    )
    lines.append(
        f"generated_service_time_range = {settings.arrival_generation.service_time_min}-{settings.arrival_generation.service_time_max}"
    )
    return "\n".join(lines)
