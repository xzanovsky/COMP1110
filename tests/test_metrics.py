import unittest

from metrics import comparison_metrics, compute_metrics
from models import CustomerGroup, QueueBand, RestaurantSettings, Table
from simulator import run_simulation


class MetricsTests(unittest.TestCase):
    def test_compute_metrics(self) -> None:
        settings = RestaurantSettings(
            tables=(Table("T1", 2),),
            queue_bands=(QueueBand("small", 1, 2),),
            simulation_minutes=20,
            arrival_mode="fixed",
            seed=1,
        )
        result = run_simulation(settings, [CustomerGroup("A", 2, 0, 10)])
        metrics = compute_metrics(result)
        self.assertEqual(metrics["served_groups"], 1)
        self.assertAlmostEqual(metrics["average_wait_minutes"], 0.0)
        self.assertAlmostEqual(metrics["table_utilisation"], result.table_utilisation)

    def test_comparison_metrics(self) -> None:
        settings = RestaurantSettings(
            tables=(Table("T1", 2),),
            queue_bands=(QueueBand("small", 1, 2),),
            simulation_minutes=20,
            arrival_mode="fixed",
            seed=1,
        )
        a = run_simulation(settings, [CustomerGroup("A", 2, 0, 10)])
        b = run_simulation(settings, [CustomerGroup("A", 2, 0, 5)])
        comparison = comparison_metrics(a, b)
        self.assertIn("average_wait_minutes", comparison)
        self.assertIn("absolute", comparison["served_groups"])


if __name__ == "__main__":
    unittest.main()

