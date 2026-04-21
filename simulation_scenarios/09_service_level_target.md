# Scenario 9: Stricter Service Level Target

This tests how the service-level metric changes when the target wait time is stricter.

Mode to choose on the website: `Generated`

## Paste into Restaurant config file

```txt
[general]
simulation_minutes = 180
arrival_mode = generated
seed = 42
target_wait_minutes = 10

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

Compare this to Scenario 1. The restaurant layout is the same, but the target is stricter, so service level should become harder to achieve.

