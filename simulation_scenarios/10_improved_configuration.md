# Scenario 10: Improved Configuration Proposal

This is the final proposed setup after testing the earlier scenarios.

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
T3 = 2
T4 = 4
T5 = 4
T6 = 4
T7 = 6
T8 = 6

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

Compare this to Scenario 1. The goal is to show whether the improved table mix lowers wait times and improves service level while keeping utilisation reasonable.

