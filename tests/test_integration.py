import unittest

from simulator import run_from_texts


class IntegrationTests(unittest.TestCase):
    def test_fixed_arrival_run(self) -> None:
        settings_text = """
        [general]
        simulation_minutes = 20
        arrival_mode = fixed
        seed = 11
        target_wait_minutes = 15

        [tables]
        2
        4

        [queues]
        small = 1-2
        large = 3-6
        """
        arrivals_text = """
        group_id,arrival_time,size,service_duration
        A1,0,2,8
        A2,0,4,10
        A3,1,1,5
        """
        result = run_from_texts(settings_text, arrivals_text)
        self.assertEqual(result.served_groups, 3)
        self.assertEqual(result.unserved_groups, 0)
        self.assertGreaterEqual(result.minute_summaries[-1].minute, 1)

    def test_generated_run(self) -> None:
        settings_text = """
        [general]
        simulation_minutes = 25
        arrival_mode = generated
        seed = 5
        target_wait_minutes = 12

        [tables]
        2
        4
        4

        [queues]
        small = 1-2
        medium = 3-4

        [arrivals]
        arrival_probability_per_minute = 0.6
        generated_group_size_range = 1-4
        generated_service_time_range = 5-15
        """
        result = run_from_texts(settings_text)
        self.assertGreaterEqual(result.total_runtime_minutes, 25)
        self.assertEqual(len(result.groups), result.served_groups + result.unserved_groups)
        self.assertTrue(all(group.queue_name is not None for group in result.groups))


if __name__ == "__main__":
    unittest.main()

