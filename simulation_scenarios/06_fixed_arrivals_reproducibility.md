# Scenario 6: Fixed Arrivals Reproducibility

This proves that the same input data gives the same output every time.

Mode to choose on the website: `Fixed arrivals`

## Paste into Restaurant config file

```txt
[general]
simulation_minutes = 180
arrival_mode = fixed
seed = 2026
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

## Paste into Arrivals file

```txt
group_id,arrival_time,size,service_duration
G1,0,2,35
G2,4,4,55
G3,5,1,22
G4,7,3,40
G5,10,5,70
G6,12,2,30
G7,20,6,80
G8,28,4,50
G9,35,3,45
G10,44,2,25
G11,52,4,55
G12,65,5,60
```

## What to check

Run it twice and confirm the metrics are identical. This is useful for the report because it proves reproducibility.

