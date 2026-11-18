# SubSweep

SubSweep is a local Python MVP that identifies recurring subscription payments
and predicts upcoming charges from bank transaction data. It uses Ward
hierarchical clustering to group transactions by merchant, amount, and elapsed
time before applying recurring-payment filters.

Version 1 uses CSV files only, so it is simple to run, inspect, and replace
with streaming infrastructure later.

## Architecture (v1)

```text
┌────────────────────────────────────────────────────────┐
│ main.py                                                │
│ Generate missing data -> Detect subscriptions -> Alert  │
└───────┬───────────────────────────────┬────────────────┘
        │                               │
        v                               v
┌───────────────────┐           ┌────────────────────────┐
│ generate_data.py  │           │ detector.py            │
│ Synthetic CSV     │           │ CSV -> Features ->     │
│ transaction maker │           │ StandardScaler -> Ward │
└─────────┬─────────┘           └───────────┬────────────┘
          │                                 │
          v                                 v
┌────────────────────────────────────────────────────────┐
│ data/mock_transactions.csv                             │
│ transaction_id | merchant | amount | date              │
└───────────────────────────────┬────────────────────────┘
                                │
                                v
                       ┌─────────────────┐
                       │ alerts.py       │
                       │ Due dates +     │
                       │ ghost alerts    │
                       └────────┬────────┘
                                │
                                v
                     Formatted terminal report
```

## Setup

Python 3.10 or newer is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

Running `main.py` creates `data/mock_transactions.csv` when it does not exist.
The generator produces approximately 200 transactions from five merchants and
five recurring subscriptions, including "Ghost SaaS Trial". Delete the CSV
when you want to regenerate the demo dataset.

## What It Detects

A merchant cluster is considered a valid recurring subscription when it has:

- at least three transactions;
- a mean interval between 28 and 32 days;
- no more than 9 days of interval variance;
- low amount variation (coefficient of variation at or below 8%).

The report includes the average amount and interval, last charge, predicted
next charge, and the number of observed transactions. Charges due in the next
five calendar days receive an "UPCOMING CHARGE ALERT". Obscure or trial-style
charges receive a "GHOST SUBSCRIPTION" warning.

## Project Structure

```text
SubSweep/
├── data/.gitkeep
├── src/
│   ├── __init__.py
│   ├── generate_data.py
│   ├── detector.py
│   └── alerts.py
├── main.py
├── requirements.txt
└── README.md
```

## Roadmap

### v2: Redis caching

- Cache normalized feature frames and detection results.
- Use short-lived Redis keys for recent merchant histories.
- Add configurable TTLs and background cache refresh.
- Keep the detector interface stable for live and batch calls.

### v3: Apache Kafka real-time streaming

- Consume transaction events from a Kafka topic.
- Incrementally update merchant histories and emit detection events.
- Publish upcoming-charge and ghost-subscription alerts to an alert topic.
- Add durable event schemas, partitioning, replay support, and monitoring.