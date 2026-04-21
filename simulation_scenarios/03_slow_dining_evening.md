# Scenario 3: Slow Dining Evening

This tests the effect of customers staying longer at tables.

Mode to choose on the website: `Generated`

## Paste into Restaurant config file

```txt
[general]
simulation_minutes = 240
arrival_mode = generated
seed = 42
target_wait_minutes = 20

[tables]
T1 = 2
T2 = 2
T3 = 4
T4 = 4
T5 = 4
T6 = 6

[queues]
small = 1-2
medium = 3-4
large = 5-6

[arrivals]
arrival_probability_per_minute = 0.65
generated_group_size_range = 1-6
generated_service_time_range = 45-90
```

## Arrivals file

Leave this field empty because this scenario uses generated arrivals.

## What to check

Check whether table utilisation becomes high while service level becomes worse. This helps show the effect of slow turnover.

