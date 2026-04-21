# Scenario 4: More Small Tables

This tests whether adding more 2-seat tables improves service for small groups.

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
T4 = 2
T5 = 4
T6 = 4
T7 = 6

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

Compare with Scenario 1. Look for lower waiting time for small groups, but also check whether larger groups are served worse.

