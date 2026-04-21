# Scenario 1: Baseline Normal Day

Use this as the main reference scenario.

Mode to choose on the website: `Generated`

## Paste into Restaurant config file

```txt
[general]
simulation_minutes = 180
arrival_mode = generated
seed = 42
target_wait_minutes = 15

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
arrival_probability_per_minute = 0.70
generated_group_size_range = 1-6
generated_service_time_range = 25-60
```

## Arrivals file

Leave this field empty because this scenario uses generated arrivals.

## What to check

Record average wait, max wait, max queue length, groups served, table utilisation, and service level. Use these results as the baseline for all other scenarios.

