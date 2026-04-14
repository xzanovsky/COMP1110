import unittest

from models import CustomerGroup, QueueBand, RestaurantSettings, Table
from simulator import run_simulation


def build_settings(seed: int = 1, mode: str = "fixed") -> RestaurantSettings:
    return RestaurantSettings(
        tables=(Table("T1", 2), Table("T2", 4)),
        queue_bands=(QueueBand("small", 1, 2), QueueBand("large", 3, 6)),
        simulation_minutes=30,
        arrival_mode=mode,
        seed=seed,
    )


class SimulatorTests(unittest.TestCase):
    def test_seats_longest_waiting_compatible_group(self) -> None:
        settings = build_settings()
        arrivals = [
            CustomerGroup("A", 2, 0, 10),
            CustomerGroup("B", 4, 0, 10),
            CustomerGroup("C", 1, 1, 10),
        ]
        result = run_simulation(settings, arrivals)
        seated_order = [group.id for group in result.completed_groups()]
        self.assertEqual(seated_order[0], "A")
        self.assertIn("B", seated_order)
        self.assertIn("C", seated_order)
        self.assertLessEqual(result.max_wait_minutes, 10)

    def test_queue_assignment_for_out_of_band_sizes(self) -> None:
        settings = build_settings()
        arrivals = [
            CustomerGroup("A", 1, 0, 10),
            CustomerGroup("B", 7, 0, 10),
        ]
        result = run_simulation(settings, arrivals)
        self.assertEqual(result.groups[0].queue_name, "small")
        self.assertEqual(result.groups[1].queue_name, "large")

    def test_generated_runs_are_deterministic(self) -> None:
        settings = build_settings(seed=42, mode="generated")
        settings.arrival_generation = settings.arrival_generation.__class__(
            arrival_probability_per_minute=0.75,
            group_size_min=1,
            group_size_max=4,
            service_time_min=5,
            service_time_max=12,
            target_wait_minutes=15,
        )
        first = run_simulation(settings)
        second = run_simulation(settings)
        self.assertEqual(
            [(g.arrival_time, g.size, g.service_duration) for g in first.groups],
            [(g.arrival_time, g.size, g.service_duration) for g in second.groups],
        )
        self.assertEqual(first.to_dict(), second.to_dict())

    def test_table_release_and_utilisation(self) -> None:
        settings = build_settings()
        arrivals = [CustomerGroup("A", 2, 0, 5)]
        result = run_simulation(settings, arrivals)
        self.assertEqual(result.served_groups, 1)
        self.assertGreater(result.table_utilisation, 0.0)
        self.assertIn("T1", result.table_utilisation_by_table)


if __name__ == "__main__":
    unittest.main()

