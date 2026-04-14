"""Core data models for the restaurant queue simulation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple


@dataclass(frozen=True, slots=True)
class QueueBand:
    """A size band that groups customers into a named queue."""

    name: str
    min_size: int
    max_size: int

    def contains(self, group_size: int) -> bool:
        return self.min_size <= group_size <= self.max_size

    def distance_to(self, group_size: int) -> int:
        if self.contains(group_size):
            return 0
        if group_size < self.min_size:
            return self.min_size - group_size
        return group_size - self.max_size


@dataclass(slots=True)
class Table:
    """A physical table in the restaurant."""

    id: str
    capacity: int
    free_at_time: int = 0
    occupied_group_id: Optional[str] = None

    def is_free(self, minute: int) -> bool:
        return self.free_at_time <= minute


@dataclass(slots=True)
class CustomerGroup:
    """A group waiting for a table."""

    id: str
    size: int
    arrival_time: int
    service_duration: int
    queue_name: Optional[str] = None
    seated_time: Optional[int] = None
    departure_time: Optional[int] = None
    table_id: Optional[str] = None
    source: str = "fixed"

    @property
    def wait_time(self) -> int:
        if self.seated_time is None:
            return 0
        return self.seated_time - self.arrival_time


@dataclass(frozen=True, slots=True)
class ArrivalGeneration:
    """Settings for probabilistic arrival generation."""

    arrival_probability_per_minute: float = 0.0
    group_size_min: int = 1
    group_size_max: int = 6
    service_time_min: int = 10
    service_time_max: int = 30
    target_wait_minutes: int = 15


@dataclass(slots=True)
class RestaurantSettings:
    """Parsed runtime settings for a simulation."""

    tables: Tuple[Table, ...]
    queue_bands: Tuple[QueueBand, ...]
    simulation_minutes: int
    arrival_mode: str = "generated"
    seed: int = 0
    arrival_generation: ArrivalGeneration = field(default_factory=ArrivalGeneration)

    def queue_for_size(self, group_size: int) -> QueueBand:
        for band in self.queue_bands:
            if band.contains(group_size):
                return band
        if not self.queue_bands:
            raise ValueError("restaurant settings do not define any queue bands")
        return min(
            self.queue_bands,
            key=lambda band: (band.distance_to(group_size), band.min_size, band.max_size),
        )

    def clone_tables(self) -> list[Table]:
        return [Table(id=table.id, capacity=table.capacity) for table in self.tables]

    def active_minutes(self, last_event_time: Optional[int] = None) -> int:
        end_point = self.simulation_minutes
        if last_event_time is not None:
            end_point = max(end_point, last_event_time)
        return max(1, end_point)


@dataclass(slots=True)
class MinuteSnapshot:
    """State captured at a single simulation minute."""

    minute: int
    arrivals: Tuple[str, ...] = ()
    seated: Tuple[str, ...] = ()
    queue_lengths: Dict[str, int] = field(default_factory=dict)
    occupied_tables: Tuple[str, ...] = ()


@dataclass(slots=True)
class SimulationResult:
    """Complete output from a simulation run."""

    settings: RestaurantSettings
    groups: Tuple[CustomerGroup, ...]
    minute_summaries: Tuple[MinuteSnapshot, ...]
    queue_max_lengths: Dict[str, int]
    served_groups: int
    unserved_groups: int
    average_wait_minutes: float
    max_wait_minutes: int
    service_level: float
    total_occupied_minutes: int
    total_runtime_minutes: int
    table_utilisation: float
    table_utilisation_by_table: Dict[str, float]

    def to_dict(self) -> Dict[str, object]:
        return {
            "served_groups": self.served_groups,
            "unserved_groups": self.unserved_groups,
            "average_wait_minutes": self.average_wait_minutes,
            "max_wait_minutes": self.max_wait_minutes,
            "service_level": self.service_level,
            "total_occupied_minutes": self.total_occupied_minutes,
            "total_runtime_minutes": self.total_runtime_minutes,
            "table_utilisation": self.table_utilisation,
            "table_utilisation_by_table": dict(self.table_utilisation_by_table),
            "queue_max_lengths": dict(self.queue_max_lengths),
        }

    def wait_times(self) -> list[int]:
        return [group.wait_time for group in self.groups if group.seated_time is not None]

    def completed_groups(self) -> list[CustomerGroup]:
        return [group for group in self.groups if group.seated_time is not None]

