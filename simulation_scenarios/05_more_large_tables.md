# Scenario 5: More Large Tables

This tests whether larger tables improve service for medium and large groups.

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
T2 = 4
T3 = 4
T4 = 6
T5 = 6
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

Compare with Scenario 1. Check if large-group waiting improves, and whether small groups waste large table capacity.

