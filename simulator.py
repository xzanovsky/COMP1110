"""Discrete-event restaurant queue simulation."""

from __future__ import annotations

from collections import defaultdict
import random
from typing import Dict, Iterable, List

from models import CustomerGroup, MinuteSnapshot, RestaurantSettings, SimulationResult, Table


def _clone_group(group: CustomerGroup) -> CustomerGroup:
    return CustomerGroup(
        id=group.id,
        size=group.size,
        arrival_time=group.arrival_time,
        service_duration=group.service_duration,
        queue_name=group.queue_name,
        seated_time=group.seated_time,
        departure_time=group.departure_time,
        table_id=group.table_id,
        source=group.source,
    )


def _assign_queue_name(settings: RestaurantSettings, group_size: int) -> str:
    return settings.queue_for_size(group_size).name


def _generate_groups(settings: RestaurantSettings) -> list[CustomerGroup]:
    rng = random.Random(settings.seed)
    config = settings.arrival_generation
    groups: list[CustomerGroup] = []
    counter = 1
    for minute in range(settings.simulation_minutes):
        if rng.random() < config.arrival_probability_per_minute:
            size = rng.randint(config.group_size_min, config.group_size_max)
            service_duration = rng.randint(config.service_time_min, config.service_time_max)
            groups.append(
                CustomerGroup(
                    id=f"G{counter}",
                    size=size,
                    arrival_time=minute,
                    service_duration=service_duration,
                    source="generated",
                )
            )
            counter += 1
    return groups


def _release_tables(tables: List[Table], current_minute: int) -> None:
    for table in tables:
        if table.free_at_time <= current_minute:
            table.occupied_group_id = None


def _seat_waiting_groups(
    tables: List[Table],
    queue_map: Dict[str, List[CustomerGroup]],
    current_minute: int,
) -> list[CustomerGroup]:
    seated: list[CustomerGroup] = []
    free_tables = sorted(
        [table for table in tables if table.occupied_group_id is None],
        key=lambda table: (table.capacity, table.id),
    )

    for table in free_tables:
        candidates: list[tuple[int, str, CustomerGroup]] = []
        for queue_name, groups in queue_map.items():
            if not groups:
                continue
            eligible_group = next(
                (
                    group
                    for group in groups
                    if group.arrival_time <= current_minute and group.size <= table.capacity
                ),
                None,
            )
            if eligible_group is not None:
                candidates.append((eligible_group.arrival_time, queue_name, eligible_group))

        if not candidates:
            continue

        candidates.sort(key=lambda item: (item[0], item[1], item[2].id))
        _, queue_name, group = candidates[0]
        group_index = queue_map[queue_name].index(group)
        group = queue_map[queue_name].pop(group_index)
        group.seated_time = current_minute
        group.departure_time = current_minute + group.service_duration
        group.table_id = table.id
        table.occupied_group_id = group.id
        table.free_at_time = group.departure_time
        seated.append(group)
    return seated


def _queue_lengths(queue_map: Dict[str, List[CustomerGroup]]) -> dict[str, int]:
    return {queue_name: len(groups) for queue_name, groups in queue_map.items()}


def run_simulation(
    settings: RestaurantSettings,
    arrivals: Iterable[CustomerGroup] | None = None,
) -> SimulationResult:
    """Run a full simulation and return a rich summary."""

    tables = settings.clone_tables()
    input_groups = list(arrivals) if arrivals is not None else (
        _generate_groups(settings) if settings.arrival_mode.lower() == "generated" else []
    )
    groups = [_clone_group(group) for group in input_groups]
    groups.sort(key=lambda group: (group.arrival_time, group.id))

    queue_map: Dict[str, List[CustomerGroup]] = {band.name: [] for band in settings.queue_bands}
    arrival_lookup: Dict[int, list[CustomerGroup]] = defaultdict(list)
    max_table_capacity = max(table.capacity for table in tables)
    for group in groups:
        group.queue_name = _assign_queue_name(settings, group.size)
        if group.size <= max_table_capacity:
            arrival_lookup[group.arrival_time].append(group)

    minute_summaries: list[MinuteSnapshot] = []
    total_runtime = settings.simulation_minutes
    if groups:
        total_runtime = max(total_runtime, max(group.arrival_time for group in groups) + 1)

    current_minute = 0
    while True:
        _release_tables(tables, current_minute)

        arrivals_this_minute = arrival_lookup.get(current_minute, [])
        for group in arrivals_this_minute:
            queue_map[group.queue_name or settings.queue_for_size(group.size).name].append(group)

        queue_lengths_before_seating = _queue_lengths(queue_map)
        seated = _seat_waiting_groups(tables, queue_map, current_minute)

        minute_summaries.append(
            MinuteSnapshot(
                minute=current_minute,
                arrivals=tuple(group.id for group in arrivals_this_minute),
                seated=tuple(group.id for group in seated),
                queue_lengths=queue_lengths_before_seating,
                occupied_tables=tuple(
                    table.id for table in tables if table.occupied_group_id is not None
                ),
            )
        )

        current_minute += 1
        pending_arrivals = any(
            group.arrival_time >= current_minute
            for group in groups
            if group.seated_time is None and group.size <= max_table_capacity
        )
        pending_queue = any(queue_map.values())
        pending_tables = any(table.occupied_group_id is not None for table in tables)
        if current_minute >= total_runtime and not (pending_arrivals or pending_queue or pending_tables):
            break
        if current_minute < total_runtime:
            continue
        if not (pending_arrivals or pending_queue or pending_tables):
            break

    completed = [group for group in groups if group.seated_time is not None]
    wait_times = [group.wait_time for group in completed]
    total_occupied_minutes = sum(group.service_duration for group in completed)
    last_departure = max((group.departure_time or 0) for group in completed) if completed else 0
    total_runtime_minutes = settings.active_minutes(last_departure)
    denominator = max(1, total_runtime_minutes * len(settings.tables))
    table_utilisation = total_occupied_minutes / denominator
    table_utilisation_by_table: dict[str, float] = {}
    for table in settings.tables:
        minutes = sum(group.service_duration for group in completed if group.table_id == table.id)
        table_utilisation_by_table[table.id] = minutes / max(1, total_runtime_minutes)

    queue_max_lengths = {
        band.name: max((snapshot.queue_lengths.get(band.name, 0) for snapshot in minute_summaries), default=0)
        for band in settings.queue_bands
    }

    served_groups = len(completed)
    unserved_groups = len(groups) - served_groups
    average_wait_minutes = sum(wait_times) / served_groups if served_groups else 0.0
    max_wait_minutes = max(wait_times) if wait_times else 0
    target_wait = settings.arrival_generation.target_wait_minutes
    service_level = (
        sum(1 for wait in wait_times if wait <= target_wait) / served_groups if served_groups else 0.0
    )

    return SimulationResult(
        settings=settings,
        groups=tuple(groups),
        minute_summaries=tuple(minute_summaries),
        queue_max_lengths=queue_max_lengths,
        served_groups=served_groups,
        unserved_groups=unserved_groups,
        average_wait_minutes=average_wait_minutes,
        max_wait_minutes=max_wait_minutes,
        service_level=service_level,
        total_occupied_minutes=total_occupied_minutes,
        total_runtime_minutes=total_runtime_minutes,
        table_utilisation=table_utilisation,
        table_utilisation_by_table=table_utilisation_by_table,
    )


def run_from_texts(restaurant_text: str, arrivals_text: str | None = None) -> SimulationResult:
    from parser import parse_arrivals, parse_restaurant_settings

    settings = parse_restaurant_settings(restaurant_text)
    arrivals = parse_arrivals(arrivals_text) if arrivals_text else None
    return run_simulation(settings, arrivals)


def run_comparison(
    left_settings: RestaurantSettings,
    right_settings: RestaurantSettings,
    left_arrivals: Iterable[CustomerGroup] | None = None,
    right_arrivals: Iterable[CustomerGroup] | None = None,
) -> tuple[SimulationResult, SimulationResult]:
    return (
        run_simulation(left_settings, left_arrivals),
        run_simulation(right_settings, right_arrivals),
    )
