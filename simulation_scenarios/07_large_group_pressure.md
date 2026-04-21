# Scenario 7: Large Group Pressure

This tests how the restaurant handles many groups of 5-6 people.

Mode to choose on the website: `Fixed arrivals`

## Paste into Restaurant config file

```txt
[general]
simulation_minutes = 180
arrival_mode = fixed
seed = 2026
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
arrival_probability_per_minute = 0.70
generated_group_size_range = 1-6
generated_service_time_range = 30-70
```

## Paste into Arrivals file

```txt
group_id,arrival_time,size,service_duration
G1,0,6,70
G2,3,5,65
G3,5,2,30
G4,8,6,75
G5,11,4,45
G6,15,5,60
G7,20,6,80
G8,25,3,40
G9,30,5,65
G10,36,2,35
G11,42,6,70
G12,50,5,60
```

## What to check

Focus on the large queue. If wait times are high, explain that the restaurant may need more 6-seat tables or a different table layout.

