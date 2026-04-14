import unittest

from parser import format_restaurant_settings, parse_arrivals, parse_restaurant_settings


class ParserTests(unittest.TestCase):
    def test_parse_restaurant_settings(self) -> None:
        text = """
        [general]
        simulation_minutes = 60
        arrival_mode = generated
        seed = 7
        target_wait_minutes = 12

        [tables]
        2
        T2 = 4
        6

        [queues]
        small = 1-2
        medium = 3-4
        large = 5-8

        [arrivals]
        arrival_probability_per_minute = 0.5
        generated_group_size_range = 1-5
        generated_service_time_range = 10-30
        """
        settings = parse_restaurant_settings(text)
        self.assertEqual(settings.simulation_minutes, 60)
        self.assertEqual(settings.seed, 7)
        self.assertEqual(len(settings.tables), 3)
        self.assertEqual(settings.tables[1].id, "T2")
        self.assertEqual(settings.queue_bands[0].name, "small")
        self.assertAlmostEqual(settings.arrival_generation.arrival_probability_per_minute, 0.5)
        self.assertEqual(settings.arrival_generation.target_wait_minutes, 12)

    def test_parse_arrivals(self) -> None:
        text = """
        group_id,arrival_time,size,service_duration
        A1,0,2,15
        A2,5,4,25
        """
        arrivals = parse_arrivals(text)
        self.assertEqual([group.id for group in arrivals], ["A1", "A2"])
        self.assertEqual(arrivals[1].arrival_time, 5)
        self.assertEqual(arrivals[1].size, 4)
        self.assertEqual(arrivals[1].service_duration, 25)

    def test_format_roundtrip(self) -> None:
        text = """
        [general]
        simulation_minutes = 30
        arrival_mode = fixed

        [tables]
        2

        [queues]
        small = 1-2

        [arrivals]
        arrival_probability_per_minute = 0.1
        """
        settings = parse_restaurant_settings(text)
        formatted = format_restaurant_settings(settings)
        roundtripped = parse_restaurant_settings(formatted)
        self.assertEqual(roundtripped.simulation_minutes, settings.simulation_minutes)
        self.assertEqual(roundtripped.tables[0].capacity, 2)


if __name__ == "__main__":
    unittest.main()

