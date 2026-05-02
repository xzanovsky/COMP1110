# Restaurant Queue Simulation

A Flask-based COMP1110 project that simulates restaurant queueing, seating, dining, and departure with a shared Python backend and a lightweight browser UI.

## Features

- Fixed-arrival runs from `restaurant.txt` and `arrivals.txt`
- Generated-arrival runs with reproducible random seeds
- Queue assignment by size band
- Seating policy based on the smallest suitable table and longest-waiting compatible queue
- Metrics for wait time, queue length, groups served, table utilisation, and service level
- Flask UI for single-run analysis and two-scenario comparison
- Colab-friendly notebook that reuses the same parser and simulator modules

## Project Structure

- `models.py` - shared data classes
- `parser.py` - plain-text parsing helpers
- `simulator.py` - simulation engine and comparison helpers
- `metrics.py` - serialisation and comparison metrics
- `frontend_contract.py` - UI adapter layer between Flask and backend
- `main.py` - Flask application entrypoint
- `templates/` - server-rendered HTML templates
- `static/` - CSS and browser-side JavaScript
- `tests/` - unit and integration tests
- `notebooks/` - notebook deliverable
- `simulation_scenarios/` - ready-to-paste scenario documents for website testing and report case studies

## Input Format

### `restaurant.txt`

The restaurant settings file uses named sections:

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

### `arrivals.txt`

Fixed-arrival runs use CSV:

```txt
group_id,arrival_time,size,service_duration
G1,0,2,35
G2,4,4,55
```

## Running Locally

Install Python 3.11+ first, then:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m unittest discover -s tests
python main.py
```

Open `http://127.0.0.1:5000/` for the landing page, `/run` for a single scenario, and `/compare` for side-by-side comparison.

## Simulation Scenarios

The `simulation_scenarios/` folder contains ten prepared scenario documents. Each file explains what the scenario tests and includes text blocks that can be pasted directly into the website.

Use them like this:

1. Open a scenario file, for example `simulation_scenarios/01_baseline_normal_day.md`.
2. Copy the `Restaurant config file` block into the website's restaurant config text area.
3. If the scenario includes an `Arrivals file` block, copy it into the arrivals text area.
4. Choose the mode shown in the scenario document, such as `Generated` or `Fixed arrivals`.
5. Run the simulation on `/run`, or compare two scenarios on `/compare`.

These scenarios are also used as case-study inputs for the final report. They cover baseline demand, lunch rush, slow dining, more small tables, more large tables, fixed-arrival reproducibility, large-group pressure, queue-band experiments, service-level targets, and an improved configuration proposal.

## Notebook

Open `notebooks/restaurant_simulation_colab.ipynb` in Colab after uploading the project files or mounting the repo. The notebook uses `load_restaurant_file`, `load_arrivals_file`, and `run_simulation` from the shared backend modules.
